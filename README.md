# Amazon Connect Power Dialer
This project contains source code and supporting files for supporting native and scheduled callback use case.


## Deployed resources

The project includes a cloud formation template with a Serverless Application Model (SAM) transform to deploy resources as follows:

### AWS Lambda functions

- dial: Places calls using Amazon Connect boto3's start_outbound_voice_contact method.
- getAvailAgents: Gets agents available in the associated queue.
- evaluateCallBack: Replies with a valid tier depending on the remaining contact center hours of opperation remaining time.
- removeFromQueue: Removes contact from queue.
- scheduleCall: Adds contact to scheduled calls list.
- startScheduledCalls: Trigger based on an evenbrige schedule, queries for scheduled calls and places respective calls.
- notify: Send an SMS message using Amazon Pinpoint.

### Secrets Manager Secrets
A secret will be created to store the associated configuration.

### Step Functions

- CBHelperdial: Provides the dialing functionality.

### DynamoDB tables
- scheduledCalls: Dialing list for the contacts.

### IAM roles
- dialSFRole: Dialing Step Functions state Machine IAM role.
- LambdaRole: Lambda Functions IAM role.


## Prerequisites.
1. Amazon Connect Instance already set up.
2. AWS Console Access with administrator account.
3. Cloud9 IDE or AWS and SAM tools installed and properly configured with administrator credentials.

## Deploy the solution
1. Clone this repo.

`git clone https://github.com/aws-samples/amazon-connect-callback-helper`

2. Build the solution with SAM.

`sam build` 

if you get an error message about requirements you can try using containers.

`sam build -u` 


3. Deploy the solution.

`sam deploy -g`

SAM will ask for the name of the application (use "PowerDialer" or something similar) as all resources will be grouped under it; Region and a confirmation prompt before deploying resources, enter y.
SAM can save this information if you plan un doing changes, answer Y when prompted and accept the default environment and file name for the configuration.

4. Claim a number within Amazon Pinpoint.

In the region selected for deployment, create an Amazon Pinpoint project, enable SMS on the configuration and claim a number to be used. Keep record of the region, project ID and number.

## Callback helper parameters.

In the Lambda console, from the Applications tab, identify the Secrets Manager secret.
In the Secrets Manager console, locate the associated secret and replace the default values with the associated parameters from your instance and Amazon Pinpoint project.

| parameter   | currentValue |
|----------|:-------------:|
| connectid |  Connect instance ID |
| contactflowID |ID of the contactflow to be used for call backs. |
|queueId | Id of the Connect queue to be used for call backs.|
| PP_REGION | Region where your Amazon Pinpoint project is located. | 
| PP_ORIGINATING_NUMBER | Claimed number in Amazon Pinpoint. |
| PP_PROJECT_ID | Amazon Pinpoint project ID.|


5. Add functions to Amazon Connect

In the Amazon Connect console (General instance configuration), add the following Lambda functions in the contact flows section:

- evaluateCallBack. 
- removeFromQueue.
- scheduleCall.
- notify.


6. Add functions to the contactflow.

On the contactflow, add Lamda invokation for the following functions:

- evaluateCallBack. 
- removeFromQueue.
- scheduleCall.
- notify.

Input to functions needs to be specified as contact attributes using the "Set contact attributes". Select "User Defined" and specify the required inputs as shown below.
Functions output needs to be added as contact attributes with the "Set contact attributes" block. Select "User Defined" as the Destination Type and use the same output name as the Destination Attribute. Select "Use Attribute" -> "External" and specify the function output name.


| function | input | Notes |
|:--------:|:-------------:|:-------------:|
|evaluateCallBack | timezone [REQUIRED]| Timezone such as: US/Central.|
|evaluateCallBack |minimumperiod [OPTIONAL]| Minimum period of time in minutes to accept calls.If omitted, a default of 60 is considered |
|evaluateCallBack |maximumcbcontacts [OPTIONAL] | Number of contacts to accept for callback.|
|evaluateCallBack |slopedperiod [True/False] [OPTIONAL]| Indicates if a callbacks should be accepted at reduced rate when approaching the closing hours.| 

|scheduleCall. | timezone | Timezone such as:  US/Central|
|scheduleCall. |  wakeTime | 24 hour time string such as: 1830 |
|notify.|wakeTime |24 hour time string such as: 1830

|  function | output | values |
|:--------:|:-------------:|:-------------:|
|evaluateCallBack. | cbTier | valid/notvalid or below100/below75/below50/below25 if 
|removeFromQueue. | None | |
|scheduleCall. | None | |
|notify.|

7. Create outbound whisper.

Create outbound whisper contact flow with an Lambda function invoke and select the removeFromQueue function. This will remove the contact from the scheduledCalls table.


## Resource deletion
1. Back on the cloudformation console, select the stack and click on Delete and confirm it by pressing Delete Stack. 
