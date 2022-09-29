# Automated Exploratory Data Analysis and Model Operationalization framework with Human in the loop

## Overview

In this repository, we present artifacts corresponding an intelligent framework that provides automated Data transformations and optimal model deployment, to accelerate accurate and timely inspection of data and model quality checks, and facilitate the productivity of distinguished Data and ML teams across the organization.

## Dataset

In order to demonstrate the orchestrated workflow, we use the example of ![Patient Diabetic Readmission Dataset](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Dataset/HealthcareDiabeticReadmission.csv). This data comprises of historical representation of patient and hospital outcomes, wherein the goal involves building a machine learning (ML) to predict hospital readmission. The model has to predict whether the high-risk diabetic-patients is likely to get readmitted to hospital after previous encounter within thirty days or after thirty days or not. Since this use case deal with multiple outcomes, this ML problem is called "Multi-class Classification". 


## Prerequisites

* An [AWS account](https://portal.aws.amazon.com/billing/signup/resume&client_id=signup)
* An [Amazon SageMaker Studio domain](https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-quick-start.html) with managed policy [attached to the IAM execution role](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html#add-policies-console) as shown in the blog
* An [Amazon S3 Bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)


## Walkthrough

For a full walkthrough of Automating Exploratory Data Analysis and Model Operationalization with Amazon Sagemaker, see this blog post. <Link here>

Our solution demonstrates an automated end-to-end approach to perform Exploratory Data Analysis (EDA) with human in the loop to determine the model quality thresholds and approve the optimal/qualified data to be pushed into Sagemaker pipeline in order to push the final data into feature store, thereby speeding the executional framework. 

Further, the approach shows deploying the best candidate model and creating the model endpoint on the transformed dataset that was automatically processed as new data arrives into the framework.


Below is the initial setup for data preprocessing step prior to automating the workflow:

![dataops.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/dataops.png)



This step comprises of data flow initiation to process the raw data stored in S3 bucket. A sequence of steps in the data wrangler UI are created to perform feature engineering on the data. Then, Sagemaker processing job is executed to save the flow to S3 and storing the transformed features into Sagemaker feature Store for reusable purposes.

Once the flow has been created which includes the recipe of instructions to be executed on the data pertaining to the use case, the goal is to automate the process of creating the flow on any new incoming data, and initiate the process of extracting model quality insights, parsing the information to an authorized user to inspect the data quality and waiting for approval to execute the model building and deployment step automatically.  

The architecture below showcases the end-to-end automation of data transformation followed by human in the loop approval to facilitate the steps of model training and deployment. 

![stepfunction.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/stepfunction.png)


## Deployment Steps

### Data Wrangler Initial Data Ops Flow 

Prior to automating using Step functions workflow, we need to perform a sequence of data transformations to create a flow. 

To start using Data Wrangler, complete the following steps:
1.	In a Sagemaker Studio domain, on the Launcher tab, choose “New data flow”.
2.	Import the Patient Readmission Dataset HealthcareDiabeticReadmission.csv from its location in Amazon S3.
3.	Choose Import dataset.

![importdataset.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/importdataset.png)

Now, we can start with data transformation in data wrangler UI. We are going to perform a sequence of 8 steps to process, clean and transform the data along with some analysis dashboards to do an initial data and model quality checks.

- Since we intend to view the data quality and model checks initially, start with clicking on “Analysis” tab next to “data” tab and click on `Create new analysis`.
- Under create analysis section, choose analysis type as `Data Quality and Insights Report`, target column as `readmitted` and problem type as `Classification` as shown below. Then, click on create. 

![dataqualityanalysis.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/dataqualityanalysis.png)


A summary report will be created providing dataset statistics, information regarding target columns, a quick model summary, confusion matrix and feature details. This gives an insight into the data and model quality based on current imported data. 

![summary.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/summary.png)

Similarly, other analysis reports can be created to determine additional insights that can be easily gathered from the data using Data Wrangler. 
-	Choose Analysis type as `Bias Report`. You can use this bias report in Data Wrangler to uncover potential biases in your data. Select the target column to be predicted, i.e., `readmitted` for our use case. Bias Report analysis uses Amazon SageMaker Clarify to perform bias analysis.
-	You can choose the predicted column value as `no` indicating the patient will not be readmitted. 
-	Select gender as `male` or `female` as shown below and click on `check for bias` and `save` to save the bias report. 

![biasreport.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/biasreport.png)

- After inspecting the bias, you can also create feature correlation chart to determine the correlation between various features which can help determine the features which can be dropped or used for predicting the target column.

![featurecorrelation.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/featurecorrelation.png)

- Other analysis charts can also be created. For brevity, I have created the following analysis charts as shown below. 

![reports.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/reports.png)

- Now that we have inspected the data, we can move to the next step of performing some data transformations using Data Wrangler UI. We will execute the following steps in data wrangler UI. 

![wrangled.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/wrangled.png)

- Go back the data tab and start with `Drop column` step. Drop `max_glu_cerum` and `a1c_result` since they have low impact on the target column as inspected from the analysis reports. Click on `preview` and then `update`.

![dropcol.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/dropcol.png)

- Next, choose `Impute` as Transform step, select `Numeric` as column type and select `time_in_hospital`, `num_procedures`, `num_medications`, `number_diagnosis`, `change` and `diabetes_med` with Imputing Strategy as `Approximate Median`. This will assist in replacing the missing values in the respective columns with median values for that column. Click on `preview` and then `Update` to reflect the changes in the dataset.  

![impute.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/impute.png)

- Based on the analysis, we can also remove additional unwanted columns which can tend to bring bias in the data. We will drop `gender`, `num_procedures` and `number_outpatient` in the next step as shown below. You can execute the same step in the primary drop columns section as well, but if you looked at detailed insights from analysis tab, you can later determine to drop additional columns that won’t help in predicting the target column. 


![drop2.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/drop2.png)

-	Since our source dataset has features with special characters, we need to clean them before training. Let's use `Search and Edit` Transform.
-	In order to further clean the data, Pick `Search and edit` from the list of transforms on the right panel. Select `Find and replace substring`
-	Select the target column `race` for Input column and use `\?` regex for Pattern. For the `Replacement String` use `Other`. Let’s leave `Output Column` blank for in-place replacements.
-	Once reviewed, click `Add` to add the transform to your data-flow.


![substring.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/substring.png)


-	Since we will be storing the transformed features in `Sagemaker Feature Store` for reusability purpose, we need to add the Event Time and a unique record ID as additional columns to timestamp the features. These 2 fields are required by Sagemaker Feature Store to store them to create Feature groups and store the transformed features in the feature store. We use Data Wrangler’s custom transform option with Pandas and add the following code as shown below:

![pandas.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/pandas.png)

Code snippet:

```
    #Table is available as variable `df`
    import time
    from uuid import uuid4
    import datetime as dt
    import pandas as pd

    rec_id=[]

    for i in range(len(df)):
        unique_id = str(uuid4())
        rec_id.append(str(unique_id))
        #print('{} : {}'.format(age, unique_id))

    df['Record_id']=rec_id

    df['EventTime'] = time.time()

    df = df.dropna()
```

-	Next, since the `readmitted` column comprises of `<30, >30 and no` as the respective column values, with imbalance for <30 and >30 values as seen in the bias report, we can convert his into binary class classification by merging <30 and >30 as a numerical output of 1 as shown. Select `Find and Replace substring` as transform step, with Input columns as `readmitted` and `<30|>30` regex pattern and Replacement string as `1`. 

![substring2.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/substring2.png)


-	Similarly, chose `Find and Replace Substring` with same Input Column, regex Pattern as `no` and Replacement String as `0`. Click on preview and update to reflect in the transformed dataset. 
readmit

![readmit.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/readmit.png)

-	Upon further inspection, since `race` column might not benefit the target column prediction, we can drop `race` as well as shown. You should be able to see the sequence of steps performed as per the depicted picture below.

![race.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/race.png)

Note that you can perform a lot of alternative transformations for your specific dataset and use case when performing the initial data transformation steps. 

-	Now, after executing the final step, navigate to `Analysis` tab and create `Data Quality and Insights` Report and `Quick Model` report to inspect the transformed data statistics. 

![report2.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/report2.png)

-	As per your inspection of the `Data Quality and Insights` Report, you should have the 100% Valid Data with no missing values and 0% Duplicate rows in the transformed dataset. 

![summary2.png](https://github.com/aws-samples/automated-exploratory-data-with-model-operationalization/blob/main/Images/summary2.png)

Now, after defining all of the transformations to perform over the dataset, you can export the resulting ML features to Feature Store as shown in the blog. 

## Clean-up

To avoid any recurring charges, stop any running Data Wrangler and Jupyter Notebook instances within Studio when not in use. Make sure to delete the Sagemaker endpoint. Also, delete the output files in Amazon S3 you created while running the orchestration workflow via step function. You have to delete the data in the S3 buckets before you can delete the buckets.  

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

