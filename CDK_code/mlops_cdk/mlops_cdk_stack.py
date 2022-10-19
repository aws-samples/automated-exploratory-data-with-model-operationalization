from constructs import Construct
import aws_cdk as cdk
import os
from aws_cdk import (
    Duration,
    Stack,
    App,
    aws_iam as _iam,
    aws_s3 as _s3,
    aws_s3_notifications as _s3n,
    aws_codecommit as _ccommit,
    aws_ec2 as _ec2,
    aws_sagemaker as _sagemaker,
    CfnParameter as _cfn,
    aws_codecommit as _codecommit,
    aws_sns as _sns,
    aws_sns_subscriptions as subs,
    aws_lambda as _lambda,
    aws_apigateway as _apigateway,
    aws_events as _events,
    aws_events_targets as _targets,
    aws_stepfunctions as _sfn,
    aws_stepfunctions_tasks as _tasks,
    aws_lambda_destinations as _destinations,
    CfnOutput as _cfnOutput,
    aws_logs as _logs
    
)

class MlopsCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        Account_id=os.getenv('CDK_DEFAULT_ACCOUNT')
        Region=os.getenv('CDK_DEFAULT_REGION')
        
        
        # Create custom policy for Lamba Approval Function
        lambda_apigateway_policy_document= {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:PutLogEvents",
                        "logs:GetLogEvents",
                        "logs:FilterLogEvents",
                    ],
                    "Resource": f"arn:{cdk.Aws.PARTITION}:logs:*:*:*",
                    "Effect": "Allow"
                    
                },
                {
                    "Action": [
                        "states:SendTaskFailure",
                        "states:SendTaskSuccess"
                    ],
                    "Resource": "*",
                    "Effect": "Allow"
                }
            ]
            }
            
        lambda_apigateway_policy_document = _iam.PolicyDocument.from_json(lambda_apigateway_policy_document)
        
        
        #IAM Role : create Lambda Approval Function role
        LambdaApiGatewayIAMRole = _iam.Role(scope=self, id='LambdaApiGatewayIAMRole',
                                assumed_by =_iam.ServicePrincipal('lambda.amazonaws.com'),
                                role_name='LambdaApiGatewayIAMRole',
                                managed_policies=[
                                _iam.ManagedPolicy(self,"LambdaAPIPolicy", document=lambda_apigateway_policy_document)
                                ])
                                
        
        
        #AWS Lambda: Defining AWS Lambda Approval Function - that will be invoked by API Gateway
        lambda_approval_function = _lambda.Function(
            self, 'LambdaApprovalFunction',
            function_name='LambdaApprovalFunction',
            runtime=_lambda.Runtime.NODEJS_12_X,
            description='Lambda function that callback to AWS Step Functions',
            code=_lambda.Code.from_asset('lambda'),
            handler='LambdaApprovalFunction.handler',
            role= LambdaApiGatewayIAMRole,
        )
        
        
        # Execution API Gateway
        
        ## { OLD CODE HERE FOR EXECUTION API}
        ExecutionApi = _apigateway.LambdaRestApi(self, "ExecutionApi",
        rest_api_name="Human approval endpoint",
        description="HTTP Endpoint backed by API Gateway and Lambda",
        proxy=False,
        #cloud_watch_role=True,
        fail_on_warnings=True,
        handler=lambda_approval_function,
        deploy_options=_apigateway.StageOptions(stage_name="states")
        )
        
                    
        
        #Execution Resource
        ExecutionResource = ExecutionApi.root.add_resource('Execution')
        
        integration_response = [_apigateway.IntegrationResponse(
                        status_code="302",
                        response_parameters={
                        "method.response.header.Location" : "integration.response.body.headers.Location"
                        })]
        
        method_response = [_apigateway.MethodResponse(
                        status_code="302",
                        response_parameters={
                            "method.response.header.Location": True
                        })]
                        
        request_templates={
        "application/json":
            """{
              "body" : $input.json('$'),
              "headers": {
                #foreach($header in $input.params().header.keySet())
                "$header": "$util.escapeJavaScript($input.params().header.get($header))" #if($foreach.hasNext),#end
                #end
              }
              ,
              "method": "$context.httpMethod",
              "params": {
                #foreach($param in $input.params().path.keySet())
                "$param": "$util.escapeJavaScript($input.params().path.get($param))" #if($foreach.hasNext),#end

                #end
              },
              "query": {
                #foreach($queryParam in $input.params().querystring.keySet())
                "$queryParam": "$util.escapeJavaScript($input.params().querystring.get($queryParam))" #if($foreach.hasNext),#end

                #end
                }
            }""" }
            
        
        #Execution API Method
        ExecutionMethod=ExecutionResource.add_method("GET",
        _apigateway.LambdaIntegration(handler=lambda_approval_function, proxy=False,
        integration_responses=integration_response, request_templates=request_templates), 
        method_responses=method_response)
        
        
        LambdaApiGatewayInvoke = _lambda.CfnPermission(self, "LambdaApiGatewayInvoke",
                            action="lambda:InvokeFunction",
                            function_name= lambda_approval_function.function_name, ### FUNCTION NAME  
                            principal= 'apigateway.amazonaws.com',
                            source_arn= f"arn:aws:execute-api:{Region}:{Account_id}:{ExecutionApi.rest_api_id}/*"   ###  ExecutionApi ARN HERE
                        )
        
        ApiGatewayLogsPolicyDocument= {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:PutLogEvents",
                        "logs:GetLogEvents",
                        "logs:FilterLogEvents",
                    ],
                    "Resource": f"arn:{cdk.Aws.PARTITION}:logs:*:*:*",
                    "Effect": "Allow"
                    
                }]}
            
        ApiGatewayLogsPolicyDocument = _iam.PolicyDocument.from_json(ApiGatewayLogsPolicyDocument)
        
        ApiGatewayCloudWatchLogsRole = _iam.Role(scope=self, id='ApiGatewayCloudWatchLogsRole',
                                assumed_by =_iam.ServicePrincipal('apigateway.amazonaws.com'),
                                role_name='ApiGatewayCloudWatchLogsRole',
                                managed_policies=[
                                _iam.ManagedPolicy(self,"ApiGatewayLogsPolicy", document=ApiGatewayLogsPolicyDocument)
                                ])
        
        
        ApiGatewayAccount = _apigateway.CfnAccount(self, "ApiGatewayCloudWatchLogsRoleAccount",
        cloud_watch_role_arn=ApiGatewayCloudWatchLogsRole.role_arn)

        
        # SNS Email subscription for Human Approval
        SNSHumanApprovalEmailTopic = _sns.Topic(
            self, "SNSHumanApprovalEmailTopic"
        )
        email_address = _cfn(self, "Email-ID")
        SNSHumanApprovalEmailTopic.add_subscription(subs.EmailSubscription(email_address.value_as_string))
        
        # SNS notification on new object upload and State Machine Initiation
        SNSDataUploadTopic = _sns.Topic(
            self, "topic-lambda-s3-sns"
        )
        SNSDataUploadTopic.add_subscription(subs.EmailSubscription(email_address.value_as_string))
        
        
        LambdaSendEmail_PolicyDocument= {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:PutLogEvents",
                    ],
                    "Resource": f"arn:{cdk.Aws.PARTITION}:logs:*:*:*",
                    "Effect": "Allow"
                    },
                {
                     "Action": [
                        "SNS:Publish"
                    ],
                    "Resource": SNSHumanApprovalEmailTopic.topic_arn,
                    "Effect": "Allow"
                }
            ]
            }
        
        LambdaSendEmailPolicyDocument = _iam.PolicyDocument.from_json(LambdaSendEmail_PolicyDocument)
        
        LambdaSendEmailExecutionRole = _iam.Role(scope=self, id='LambdaSendEmailExecutionRole',
                                assumed_by =_iam.ServicePrincipal('lambda.amazonaws.com'),
                                role_name='LambdaSendEmailExecutionRole',
                                managed_policies=[
                                _iam.ManagedPolicy(self,"LambdaSendEmailPolicy", document=LambdaSendEmailPolicyDocument)
                                ])
                                
        
        
        # AWS Lambda Approval Send Email Function creation 
        LambdaHumanApprovalSendEmailFunction = _lambda.Function(
            self, 'LambdaHumanApprovalSendEmailFunction',
            runtime=_lambda.Runtime.NODEJS_12_X,
            function_name='LambdaHumanApprovalSendEmailFunction',
            description='Lambda function deployed using AWS CDK Python',
            code=_lambda.Code.from_asset('lambda'),
            handler='LambdaHumanApprovalSendEmailFunction.lambda_handler',
            role=LambdaSendEmailExecutionRole
        )
        
        # S3 bucket where new data will be uploaded
        data_bucket_name = _cfn(self, "DataBucketName", type="String",
        description="The name of the Amazon S3 bucket where uploaded files will be stored.")
        
        data_bucket = _s3.Bucket(self, 'data_bucket',
                        bucket_name=data_bucket_name.value_as_string,
                        auto_delete_objects=True,
                        block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
                        versioned=True,
                        public_read_access=False,
                        removal_policy=cdk.RemovalPolicy.DESTROY)
        
        
        # Lambda role IAM Policy 
        smlambdarole_PolicyDocument= {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    "Resource": f"arn:{cdk.Aws.PARTITION}:logs:*:*:*",
                    "Effect": "Allow"
                    },
                {
                    "Action": [
                        "states:CreateActivity",
                        "states:StartExecution",
                        "states:CreateStateMachine",
                        "states:Delete*",
                        "states:Describe*",
                        "states:Get*",
                        "states:Stop*",
                        "states:List*",
                        "states:Send*",
                        "states:UpdateStateMachine"
                    ],
                    "Resource": f"arn:aws:states:*:*:stateMachine:*",
                    "Effect": "Allow"
                },
                {
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "s3:GetBucketLocation",
                        "s3:ListAllMyBuckets",
                        "s3:DeleteObject"
                        ],
                    "Resource": f"arn:aws:s3:::{data_bucket}/*",
                    "Effect": "Allow"
                },
                {
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "s3:GetBucketLocation",
                        "s3:ListAllMyBuckets",
                        "s3:DeleteObject"
                        ],
                    "Resource": [
                    f"arn:aws:s3:::sagemaker-{Region}-{Account_id}/*",
                    f"arn:aws:s3:::sagemaker-{Region}-{Account_id}"
                    ] ,
                    "Effect": "Allow"
                },
                {
                    "Action": [
                        "SNS:Publish"
                        ],
                    "Resource": SNSDataUploadTopic.topic_arn,
                    "Effect": "Allow"
                },
                {
                    "Action": [
                        "sagemaker:Create*",
                        "sagemaker:Describe*",
                        "sagemaker:Delete*",
                        "sagemaker:InvokeEndpoint",
                        "sagemaker:List*",
                        "sagemaker:Update*",
                        "sagemaker:Stop*",
                        "sagemaker:PutModelPackageGroupPolicy",
                        "sagemaker:RetryPipelineExecution",
                        "sagemaker:SendPipelineExecutionStepFailure",
                        "sagemaker:SendPipelineExecutionStepSuccess",
                        "sagemaker:StartPipelineExecution"
                        ],
                    "Resource": "*",
                    "Effect": "Allow"
                }
            ]
            }
        
        smlambdarolePolicyDocument = _iam.PolicyDocument.from_json(smlambdarole_PolicyDocument)
        
        smlambdarole = _iam.Role(scope=self, id='smlambdarole',
                                assumed_by =_iam.CompositePrincipal(_iam.ServicePrincipal("lambda.amazonaws.com"),
                                                                    _iam.ServicePrincipal("sagemaker.amazonaws.com")),
                                role_name='smlambdarole',
                                managed_policies=[
                                _iam.ManagedPolicy(self,"smlambdarolePolicyDocument", document=smlambdarolePolicyDocument)
                                ])
        
                                
        #IAM Pass Role Policy
        smlambdarole.attach_inline_policy(_iam.Policy(self, "IAMPassRolePolicy",
            statements=[_iam.PolicyStatement(
            actions=
            [  
                "iam:GetRole",
                "iam:PassRole" ],
            resources=[smlambdarole.role_arn]
            )]))
        
         # AWS Lambda function for automatically triggering AWS StepFunctions on new data upload to S3
        LambdaStepFunctionsTriggerFunction = _lambda.Function(
            self, 'LambdaStepFunctionsTriggerFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='LambdaStepFunctionsTriggerFunction',
            description='AWS Lambda function for automatically triggering AWS StepFunctions',
            code=_lambda.Code.from_asset('lambda'),
            handler='LambdaStepFunctionsTriggerFunction.lambda_handler',
            environment={
                "flow_key":f"sagemaker-{Region}-{Account_id}/data_wrangler_flows",
                "flow_bucket":f"sagemaker-{Region}-{Account_id}",
                "SNS_ARN":SNSDataUploadTopic.topic_arn,
                "MY_STATE_MACHINE_ARN": f"arn:aws:states:{Region}:{Account_id}:stateMachine:HealthCareStateMachine"
            },
            timeout= Duration.seconds(30),
            role=smlambdarole ## SM LAMBDA ROLE CONFIGURATION 
        )
        
        LambdaEventInvokeConfig = _lambda.EventInvokeConfig(self, "LambdaEventInvokeConfig",
            function=LambdaStepFunctionsTriggerFunction,
            on_success= _destinations.SnsDestination(SNSDataUploadTopic),
            qualifier="$LATEST"
        )
        
        # AWS Lambda Function for automatically triggering data wrangler operation within step function
        LambdaWranglerFlowFunction = _lambda.Function(
            self, 'LambdaWranglerFlowFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='LambdaWranglerFlowFunction',
            description='Lambda Function for Automating Data Wrangler Operation',
            code=_lambda.Code.from_asset('lambda'),
            handler='LambdaWranglerFlowFunction.lambda_handler',
            environment={
                "APIGatewayEndpointARN": f"https://{ExecutionApi.rest_api_id}.execute-api.{Region}.amazonaws.com/states",                   #ExecutionMethod.method_arn, 
                "pipeline_name": "<ENTER_FEATURE_STORE_PIPELINE_NAME>",
                "pipeline_name2": "<ENTER_S3_PIPELINE_NAME>",
                "flow_key":f"sagemaker-{Region}-{Account_id}/data_wrangler_flows",
                "flow_bucket":f"sagemaker-{Region}-{Account_id}",
                "SNS_ARN":SNSDataUploadTopic.topic_arn,
                "SNS_HumanApprovalTopicARN": SNSHumanApprovalEmailTopic.topic_arn,
                "MY_STATE_MACHINE_ARN": f"arn:aws:states:{Region}:{Account_id}:stateMachine:HealthCareStateMachine" ## ENTER STATEMACHINE ARN
            },
            timeout= Duration.seconds(10),
            role=smlambdarole
        )
        
        
        # AWS Lambda Function for invoking the 2 SageMaker Pipelines 
        LambdaPipelineExecutionFunction = _lambda.Function(
            self, 'LambdaPipelineExecutionFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='LambdaPipelineExecutionFunction',
            description='AWS Lambda Function to execute SageMaker Pipelines',
            code=_lambda.Code.from_asset('lambda'),
            handler='LambdaPipelineExecutionFunction.lambda_handler',
            timeout= Duration.seconds(900),
            role=smlambdarole
        )
        
        # AWS Lambda Function for executing SageMaker AutoPilot Job and creating Model Deployment 
        LambdaAutomlEndpointFunction = _lambda.Function(
            self, 'LambdaAutomlEndpointFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='LambdaAutomlEndpointFunction',
            description='AWS Lambda Function to Execute SageMaker Autopilot Job',
            code=_lambda.Code.from_asset('lambda'),
            handler='LambdaAutomlEndpointFunction.lambda_handler',
             environment={
                "sagemaker_role": str(smlambdarole.role_arn)
            },
            timeout= Duration.seconds(900),
            role=smlambdarole
        )
        
        # State Machine IAM role policy
        LambdaStateMachineExecutionRole_policy_document= {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:PutLogEvents",
                        "logs:GetLogEvents",
                        "logs:FilterLogEvents",
                    ],
                    "Resource": f"arn:{cdk.Aws.PARTITION}:logs:*:*:*",
                    "Effect": "Allow"
                    
                },
                {
                    "Action": [
                        "lambda:InvokeFunction"],
                    "Resource": LambdaHumanApprovalSendEmailFunction.function_arn,
                    "Effect": "Allow"
                }
            ]
            }
            
        LambdaStateMachineExecutionRole_policy_document = _iam.PolicyDocument.from_json(LambdaStateMachineExecutionRole_policy_document)
        
        
        #IAM Role : create Lambda Approval Function role
        LambdaStateMachineExecutionRole = _iam.Role(scope=self, id='LambdaStateMachineExecutionRole',
                                assumed_by =_iam.ServicePrincipal('states.amazonaws.com'),
                                role_name='LambdaStateMachineExecutionRole',
                                managed_policies=[
                                _iam.ManagedPolicy.from_aws_managed_policy_name(
                                    'service-role/AWSLambdaBasicExecutionRole'),
                                _iam.ManagedPolicy(self,"StateMachinePolicy", document=LambdaStateMachineExecutionRole_policy_document)
                                ])
        
        
        # Define StepFunctions State Machine 
        
        waitSeconds=500
        
        Wait = _sfn.Wait(self, "Wait",
            time=_sfn.WaitTime.duration(cdk.Duration.seconds(waitSeconds))
            )
        
        Sagemaker_Pipeline_execution = _tasks.LambdaInvoke(self, "Sagemaker-Pipeline-execution",
                        lambda_function=LambdaPipelineExecutionFunction,
                        payload=_sfn.TaskInput.from_object({
                                                "data_bucket": _sfn.JsonPath.string_at("$.data_bucket"),
                                                "data_key": _sfn.JsonPath.string_at("$.data_key"),
                                                "flow_bucket": _sfn.JsonPath.string_at("$.flow_bucket"),
                                                "flow_key": _sfn.JsonPath.string_at("$.flow_key"),
                                                "pipeline_name": _sfn.JsonPath.string_at("$.pipeline_name"),
                                                "pipeline_name2": _sfn.JsonPath.string_at("$.pipeline_name2"),
                                                "new_flow_uri": _sfn.JsonPath.string_at("$.new_flow_uri"),
                                                "new_flow_key": _sfn.JsonPath.string_at("$.new_flow_key"),
                                                "SNS_HumanApprovalTopicARN": _sfn.JsonPath.string_at("$.SNS_HumanApprovalTopicARN")
                                                })).next(Wait).next(
                                                    _tasks.LambdaInvoke(self, "AutoML Model Job Creation & Model Deployment",
                                                    lambda_function=LambdaAutomlEndpointFunction,
                                                    output_path="$.Payload"
                                                    ))                    
        
        RejectedState=_sfn.Pass(self, "Rejected State")
        
        default = RejectedState

        StepFunctionsStateMachine = _sfn.StateMachine(self, "StepFunctionsStateMachine",
                                    role=LambdaStateMachineExecutionRole,
                                    state_machine_type=_sfn.StateMachineType.STANDARD,
                                    state_machine_name = "HealthCareStateMachine",
                                    definition=_tasks.LambdaInvoke(self, "DataWrangler Flow Creation",
                                            lambda_function=LambdaWranglerFlowFunction,
                                            timeout=cdk.Duration.seconds(3600),
                                            output_path="$.Payload"
                                            ).next(
                                            _tasks.LambdaInvoke(self, "User Callback Approval",
                                            result_path = "$.Payload",
                                            integration_pattern=_sfn.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
                                            lambda_function=LambdaHumanApprovalSendEmailFunction,
                                            payload=_sfn.TaskInput.from_object({
                                                "data_bucket": _sfn.JsonPath.string_at("$.data_bucket"),
                                                "ExecutionContext": _sfn.JsonPath.string_at("$$"),
                                                "data_key": _sfn.JsonPath.string_at("$.data_key"),
                                                "APIGatewayEndpoint": _sfn.JsonPath.string_at("$.APIGatewayEndpoint"),
                                                "pipeline_name": _sfn.JsonPath.string_at("$.pipeline_name"),
                                                "pipeline_name2": _sfn.JsonPath.string_at("$.pipeline_name2"),
                                                "new_flow_uri": _sfn.JsonPath.string_at("$.new_flow_uri"),
                                                "new_flow_key": _sfn.JsonPath.string_at("$.new_flow_key"),
                                                "SNS_HumanApprovalTopicARN": _sfn.JsonPath.string_at("$.SNS_HumanApprovalTopicARN")
                                                }))
                                                ).next(
                                                _sfn.Choice(self, "ManualApprovalChoiceState").when(_sfn.Condition.string_equals("$.Payload.Status", "Approved!"), Sagemaker_Pipeline_execution).when(_sfn.Condition.string_equals("$.Payload.Status", "Rejected!"), RejectedState).otherwise(default)
                                                )
                                            )
        
        
        StepFunctionsActivity= _sfn.Activity(self, "ManualStepActivity")
        
        # Add Event notifications to Trigger AWS Lambda Function
        data_bucket.add_event_notification(_s3.EventType.OBJECT_CREATED, 
                _s3n.LambdaDestination(LambdaStepFunctionsTriggerFunction),
                _s3.NotificationKeyFilter(
                prefix="healthcare/flow"))
        
        cdk.CfnOutput(self, "ApiGatewayInvokeURL",
            value=f"https://{ExecutionApi.rest_api_id}.execute-api.{Region}.amazonaws.com/states")