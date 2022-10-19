import json
import boto3
import os
import urllib.parse
from time import gmtime, strftime, sleep

sm = boto3.client('sagemaker')
sns = boto3.client('sns')
s3 = boto3.client('s3')
region = os.environ['AWS_REGION']
s3_client = boto3.resource('s3', region_name=region)

def lambda_handler(event, context):
  
  try:
      #Get AWS Account-ID of the user 
      aws_account_id = context.invoked_function_arn.split(":")[4]
      bucket_name= "sagemaker-" + str(region) + "-" + str(aws_account_id)
      
      bucket = s3_client.Bucket(bucket_name)
      
      for object_summary in bucket.objects.filter(Prefix="WrangledOutput/"):
          key = object_summary.key
          if key.endswith(".csv"):
              print(key)
          
      obj = s3_client.Object(bucket, key= key)
      
      timestamp_suffix = strftime('%d-%H-%M', gmtime())
  
   #Create Automl experiment
      
      default_autopilot_job_name = f'aws-autopilot-{timestamp_suffix}'
      autopilot_job_name = f'autopilot-healthcare-{timestamp_suffix}'
      input_data= f"s3://{bucket.name}/{key}" 
      print ("input data is " + str(input_data))
      
      target_column = 'readmitted'
      job_execution_role = os.environ['sagemaker_role']
      output_path = f's3://{bucket.name}/AutoPilotJob/'
      
      
      autopilot_job_config: dict = {
          'CompletionCriteria': {
              'MaxRuntimePerTrainingJobInSeconds': 500, 
              'MaxCandidates': 2,
              'MaxAutoMLJobRuntimeInSeconds': 4500 
                  }
              }
      
      
      autopilot_input_data_config = [
          {
              'DataSource': {
                  'S3DataSource': {
                      'S3DataType': 'S3Prefix',
                      'S3Uri': input_data
                  }
              },
              'TargetAttributeName': target_column
          }
      ]

      autopilot_output_data_config = {
          'S3OutputPath': output_path
      }
      
      autopilot_model_deploy_config = { 
      'AutoGenerateEndpointName': False,
      'EndpointName' : 'AutopilotHealthcareEndpoint'
      }
      
      # Tags="autopilot_job"
      response = sm.create_auto_ml_job(
          AutoMLJobName=autopilot_job_name,
          InputDataConfig=autopilot_input_data_config,
          OutputDataConfig=autopilot_output_data_config,
          AutoMLJobConfig=autopilot_job_config,
          ModelDeployConfig = autopilot_model_deploy_config,
          RoleArn=os.environ['sagemaker_role']
          )
      
      
      describe_response = sm.describe_auto_ml_job(AutoMLJobName=autopilot_job_name)
      
      print(describe_response["AutoMLJobStatus"] + " - " + describe_response["AutoMLJobSecondaryStatus"])
      job_run_status = describe_response["AutoMLJobStatus"]

      print('SageMaker model training has been successfully completed')
      
  except Exception as e:
      print(e)
      print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
      raise e 