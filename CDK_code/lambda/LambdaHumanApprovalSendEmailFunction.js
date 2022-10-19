console.log('Loading function');
const AWS = require('aws-sdk');
exports.lambda_handler = (event, context, callback) => {
    console.log('event= ' + JSON.stringify(event));
    console.log('context= ' + JSON.stringify(context));
    
    // fetching step function parsed parameters across lambda functions
    const data_bucket = event.data_bucket;
    const data_key = event.data_key;
    const flow_bucket = event.flow_bucket;
    const flow_key = event.flow_key;
    const pipeline_name = event.pipeline_name;
    const new_flow_key = event.new_flow_key;
    const new_flow_uri = event.new_flow_uri;
    const human_approval_topic = event.SNS_HumanApprovalTopicARN;

    const executionContext = event.ExecutionContext;
    console.log('executionContext= ' + executionContext);

    const executionName = executionContext.Execution.Name;
    console.log('executionName= ' + executionName);

    const statemachineName = executionContext.StateMachine.Name;
    console.log('statemachineName= ' + statemachineName);

    const taskToken = executionContext.Task.Token;
    console.log('taskToken= ' + taskToken);

    const apigwEndpint = event.APIGatewayEndpoint;
    console.log('apigwEndpint = ' + apigwEndpint)

    const approveEndpoint = apigwEndpint + "/Execution?action=approve&ex=" + executionName + "&sm=" + statemachineName + "&taskToken=" + encodeURIComponent(taskToken);
    console.log('approveEndpoint= ' + approveEndpoint);

    const rejectEndpoint = apigwEndpint + "/Execution?action=reject&ex=" + executionName + "&sm=" + statemachineName + "&taskToken=" + encodeURIComponent(taskToken);
    console.log('rejectEndpoint= ' + rejectEndpoint);
    
    console.log('emailSnsTopic= ' + human_approval_topic);

    var emailMessage = 'Welcome! \n\n';
    emailMessage += 'This is an email requiring an approval for a step functions execution. \n\n'
    emailMessage += 'Please check the following information and click "Approve" link if you want to approve. \n\n'
    emailMessage += 'Execution Name -> ' + executionName + '\n\n'
    emailMessage += 'Approve ' + approveEndpoint + '\n\n'
    emailMessage += 'Reject ' + rejectEndpoint + '\n\n'
    emailMessage += 'Thanks for using Step functions!'
    
    const sns = new AWS.SNS();
    var params = {
      Message: emailMessage,
      Subject: "Required approval from AWS Step Functions",
      TopicArn: human_approval_topic
    };

    sns.publish(params)
      .promise()
      .then(function(data) {
        console.log("MessageID is " + data.MessageId);
        callback(null);
      }).catch(
        function(err) {
        console.error(err, err.stack);
        callback(err);
      });
    
    var step_dict = {'new_flow_key': new_flow_key, 
        'data_bucket': data_bucket,
        'data_key': data_key,
        'new_flow_uri': new_flow_uri, 
        'flow_bucket': flow_bucket, 
        'flow_key': flow_key, 
        'pipeline_name': pipeline_name,
        'SNS_HumanApprovalTopicARN': human_approval_topic
    };

    return step_dict;
}