import json
import boto3
import os

s3 = boto3.resource('s3')
sm = boto3.client('sagemaker')
sns= boto3.client('sns')
sf = boto3.client('stepfunctions')

def lambda_handler(event, context):
    
    data_bucket = event['data_bucket']
    data_key = event['data_key']
    
    #Update values for where Data Wrangler .flow is saved
    flow_bucket = os.environ['flow_bucket']
    flowfilelocation=s3.Bucket(flow_bucket)

    for object_summary in flowfilelocation.objects.filter(Prefix='data_wrangler_flows/'):
        key = object_summary.key
        if key.endswith(".flow"):
            print(key)
    
    flow_key=key
    pipeline_name = os.environ['pipeline_name']
    pipeline_name2 = os.environ['pipeline_name2']
    
    execution_display = f"{data_key.split('/')[-1].replace('_','').replace('.csv','')}"
    
    #Get .flow file from Amazon S3
    get_object = s3.Object(flow_bucket,flow_key)
    get_flow = get_object.get()

    HumanApprovalTopicARN= os.environ['SNS_HumanApprovalTopicARN']
    
    #Read, update and save the .flow file
    flow_content = json.loads(get_flow['Body'].read())
    flow_content['nodes'][0]['parameters']['dataset_definition']['name'] = data_key.split('/')[-1]
    flow_content['nodes'][0]['parameters']['dataset_definition']['s3ExecutionContext']['s3Uri'] = f"s3://{data_bucket}/{data_key}"
    new_flow_key = flow_key.replace('.flow', '-' + data_key.split('/')[-1].replace('.csv','') + '.flow')
    new_flow_uri = f"s3://{flow_bucket}/{new_flow_key}"
    put_object = s3.Object(flow_bucket,new_flow_key)
    put_flow = put_object.put(Body=json.dumps(flow_content))
    print("new flow uri is: " + str(new_flow_uri))
    
    # ---------------------------------------------------#
    
    #Send SNS Notification to the authorized person
    sns_message = str("This Email Represents a File with datawrangler - found in one of your Buckets \n\n BUCKET NAME: "+ flow_bucket +"\n\n FILE NAME: " + new_flow_key + "\n\n" 
    + " You can download the above newly generated Wrangler flow file stored in the respective bucket. Further, you can import the file in Sagemaker studio within Data Wrangler UI and inspect data insights, on the new dataset in Sagemaker Studio.")
    message="This file got uploaded: " + new_flow_key + " to this bucket : " + flow_bucket 
    print(message)
    subject= "S3 Bucket[" + flow_bucket + "] "
    sns_response = sns.publish(
        TargetArn=os.environ['SNS_ARN'],
        Message= str(sns_message),
        Subject= str(subject))
    
    # Parsing API Gateway endpoint as parameter for Step Functions Human intervention flow
    APIGatewayEndpoint = os.environ['APIGatewayEndpointARN']
    step_dict = {'data_bucket': data_bucket, 'data_key': data_key, 'flow_bucket' : flow_bucket, 'flow_key' : flow_key, 'pipeline_name':  pipeline_name, 'pipeline_name2': pipeline_name2, 'new_flow_key': new_flow_key, 'new_flow_uri': new_flow_uri, 'APIGatewayEndpoint': APIGatewayEndpoint, 'SNS_HumanApprovalTopicARN': HumanApprovalTopicARN}
 
    out = step_dict
    return(out)