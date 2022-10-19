import json
import boto3
import os

s3 = boto3.resource('s3')
sm = boto3.client('sagemaker')
sns =boto3.client('sns')
s3_client= boto3.client('s3')


def lambda_handler(event, context):

  #Check version of Boto3 - It must be at least 1.16.55
  print(f"The version of Boto3 is {boto3.__version__}")
  
  data_bucket = event['data_bucket']
  data_key = event['data_key']
  flow_bucket = event['flow_bucket']
  flow_key = event['flow_key']
  new_flow_key=event['new_flow_key']
  pipeline_name = event['pipeline_name']
  new_flow_uri = f"s3://{flow_bucket}/{new_flow_key}"
  pipeline_name2 = event['pipeline_name2']
  
  
  #Start the pipeline execution
  start_pipeline = sm.start_pipeline_execution(
                      PipelineName=pipeline_name,
                      PipelineExecutionDisplayName="HealthcareReadmissionFeatureStore",
                      PipelineParameters=[
                          {
                              'Name': 'InputFlow',
                              'Value': new_flow_uri
                          },
                      ],
                      PipelineExecutionDescription="healthcare data readmission Feature Store Flow"
                      )
  print(start_pipeline)
  print("SageMaker Pipeline for feature Store has been successfully created")
  
  start_pipeline2 = sm.start_pipeline_execution(
                      PipelineName=pipeline_name2,
                      PipelineExecutionDisplayName="DataWranglerProcessing",
                      PipelineParameters=[
                          {
                              'Name': 'InputFlow',
                              'Value': new_flow_uri
                          },
                      ],
                      PipelineExecutionDescription="healthcare data readmission csv flow"
                      )
  print(start_pipeline2)
  print("SageMaker Pipeline for processing to S3 has been successfully created")