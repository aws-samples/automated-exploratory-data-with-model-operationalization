import json
import boto3
import os

s3 = boto3.resource('s3')
sns= boto3.client('sns')
sf = boto3.client('stepfunctions')

def lambda_handler(event, context):

  #Get location for where the new data (csv) file was uploaded
  data_bucket = event['Records'][0]['s3']['bucket']['name']
  data_key = event['Records'][0]['s3']['object']['key']
  print(f"A new file named {data_key} was just uploaded to Amazon S3 in {data_bucket}")
  
  input_dict = {'data_bucket': data_bucket, 'data_key': data_key}

  # ---------------------------------------------------#

  # Initiate the Step Function
  my_state_machine_arn = os.environ['MY_STATE_MACHINE_ARN']
  client = boto3.client('stepfunctions')
  response = sf.start_execution(stateMachineArn=my_state_machine_arn, input = json.dumps(input_dict))
  print("response is : ")
  print(response)
  print("\n Input Dictionary: ")
  print(input_dict)

  return('Step function has been successfully initiated')