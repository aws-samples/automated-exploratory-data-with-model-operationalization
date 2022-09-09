# Automated Exploratory Data Analysis and Model Operationalization framework with Human in the loop

## Overview

In this repository, we present artifacts corresponding an intelligent framework that provides automated Data transformations and optimal model deployment, to accelerate accurate and timely inspection of data and model quality checks, and facilitate the productivity of distinguished Data and ML teams across the organization.

## Dataset

In order to demonstrate the orchestrated workflow, we use the example of ![Patient Diabetic Readmission Dataset](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/tree/main/Dataset/HealthcareDiabeticReadmission.csv). This data comprises of historical representation of patient and hospital outcomes, wherein the goal involves building a machine learning (ML) to predict hospital readmission. The model has to predict whether the high-risk diabetic-patients is likely to get readmitted to hospital after previous encounter within thirty days or after thirty days or not. Since this use case deal with multiple outcomes, this ML problem is called "Multi-class Classification". 


## Prerequisites

* An AWS account
* A SageMaker Studio domain with the “AmazonSageMakerFeatureStoreAccess” managed policy attached to the AWS Identity and Access Management (IAM) execution role
* An S3 bucket


### Walkthrough

For a full walkthrough of Automating Exploratory Data Analysis and Model Operationalization with Amazon Sagemaker, see this blog post. 

Our solution demonstrates an automated end-to-end approach to perform Exploratory Data Analysis (EDA) with human in the loop to determine the model quality thresholds and approve the optimal/qualified data to be pushed into Sagemaker pipeline in order to push the final data into feature store, thereby speeding the executional framework. 

Further, the approach shows deploying the best candidate model and creating the model endpoint on the transformed dataset that was automatically processed as new data arrives into the framework.


Below is the initial setup for data preprocessing step prior to automating the workflow:

![Dataops.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/tree/main/Images/Dataops.png)

This step comprises of data flow initiation to process the raw data stored in S3 bucket. A sequence of steps in the data wrangler UI are created to perform feature engineering on the data. Then, Sagemaker processing job is executed to save the flow to S3 and storing the transformed features into Sagemaker feature Store for reusable purposes.

Once the flow has been created which includes the recipe of instructions to be executed on the data pertaining to the use case, the goal is to automate the process of creating the flow on any new incoming data, and initiate the process of extracting model quality insights, parsing the information to an authorized user to inspect the data quality and waiting for approval to execute the model building and deployment step automatically.  

The architecture below showcases the end-to-end automation of data transformation followed by human in the loop approval to facilitate the steps of model training and deployment. 

![Stepfunction.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/tree/main/Images/Stepfunction.png)

## Clean-up

To avoid any recurring charges, stop any running Data Wrangler and Jupyter Notebook instances within Studio when not in use. Also, delete endpoints created in the Sagemaker dashboard. 

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

