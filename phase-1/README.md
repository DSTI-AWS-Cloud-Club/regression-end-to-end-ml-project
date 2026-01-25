# Phase 1 - Deploy a **complex** ML model in the cloud

## 🎯 Lab Overview
Deploy the end-to-end ML pipeline by storing assets in S3 and invoking it through a Lambda-backed API.

### Learning Objectives
- Package a feature, training, and inference pipeline so it can execute inside AWS Lambda.
- Configure S3, Lambda, and API Gateway to serve predictions through a managed REST endpoint.
- Understand how lightweight encoders and model artifacts travel from local storage to the cloud.
- Exercise the complete inference path by calling the deployed API with realistic payloads.

### 🏗️ Project Components
1. **Pipelines in `src/`** – Feature, training, and inference flows that transform data and produce predictions.
2. **Model + encoders** – `freq_encoder.pkl`, `target_encoder.pkl`, and the trained model artifact pulled from S3 at runtime.
3. **Lambda handler** – `src/lambda_function.py` wires preprocessing, model loading, and prediction responses.
4. **API Gateway endpoint** – Exposes `/predict` so any client can send housing records and receive estimates.

### Cost: $0 (Free) 
The cost of deploying this lab in AWS is Free. The Lambda and API Gateway are free up to 1 million requests and the S3 bucket is not filled up to limit.

#### AWS S3 on 🎁 Free Tier

AWS S3 Free Tier gives you, per month for the first 12 months after account creation:

- **5 GB** of S3 Standard storage
- **20,000 GET** requests
- **2,000 PUT/COPY/POST/LIST** requests
- **15 GB of data transfer out to the internet** (per month, shared across AWS services)

#### API Gateway on 🎁 Free Tier
- **1 million REST API** calls per month  
- **1 million HTTP API** calls per month  
- **1 million WebSocket messages** plus **750,000 minutes of connection time** per month  
- Available **for up to 12 months** after account creation

#### Lambda on 🎁 Free Tier
- **1 million** free requests per month  
- **400,000 GB-seconds** of compute time per month
- **100 GiB** of response streaming per month beyond the first 6 MB per request free.

### AWS Services Involved

- **S3 Integration**: Data and model storage in an S3 bucket
- **Lambda** :  Functions that can run a python script
- **API Gateway**: REST API endpoint service

**💡 Insight**: Combined, these services let a Data Scientist host the complete pipeline in AWS while exposing predictions via an API endpoint.

### Architecture

![s3+lambda+api schema](/assets/phase1-s3+lambda+api-architecture.png)

## 📚 Table of Contents
1. [Lab Overview](#-lab-overview)
2. [Project Components](#-project-components)
3. [Cost](#cost-0-free)
4. [AWS Services Involved](#aws-services-involved)
5. [Architecture](#architecture)
6. [Part 1: Environment Setup](#part-1-environment-setup)
7. [Part 2: Understanding the Code](#part-2-understanding-the-code)
8. [Part 3: Download the data for the lab](#part-3-download-the-data-for-the-lab)
9. [Part 4: Create a Lambda function](#part-4-create-a-lambda-function)
10. [Part 5: Testing the lambda function](#part-5-testing-the-lambda-function)
11. [Part 6: Expose via API Gateway](#part-6-expose-via-api-gateway)
12. [Part 7: 🧪 Testing Your API](#part-7--testing-your-api)
13. [End of lab](#-end-of-lab)
14. [Part 8: About the S3 + Lambda + API Gateway approach](#part-8-about-the-s3--lambda--api-gateway-approach)
15. [Part 9: Extra resources](#part-9-extra-resources)

---

## Part 1: Environment Setup

### 1.1 Initialise python env
Open your IDE and open the cloned repo. Open a terminal and run:

```
cd phase-1
uv sync
```

#### 1.1.1 Activate environment

On Windows:
`.\.venv\Scripts\activate.ps1`  

On Linux:
`source .venv/bin/activate`

## Part 2: Understanding the Code

- Review the `src` directory and note that it contains three coordinated pipelines:

  - *Feature pipeline*: Handles the **loading**, **pre-processing** and **feature engineering** (LT) steps on the raw data. 
    - The output of this pipeline is the `feature_engineered_*.csv` files that you have in `data/processed`.
    - Generates two `.pkl` files:
      - `freq_encoder.pkl`: A python object to make the encoding of the zip codes **from raw data**
      - `target_encoder.pkl`: A python object to make the encoding of the city names **from raw data**

  - *Training pipeline*: Consumes the processed data and trains the model. 
    - `train.py`: trains a model and generates a `.pkl` file (python object in a file) containing our model. We will load this file into our Lambda function to make predictions !
    - `tune.py`: uses **Optuna** and **MLflow** to optimize the parameter tuning and to track the models into a database. Thanks to this we will be able to select the best model and track the options !

  - *Inference pipeline*: Reuses the feature pipeline to preprocess raw inputs and then loads the `model.pkl` artifact to produce **predictions**.

  - *lambda_function.py*: This Lambda handler orchestrates the inference pipeline to return predictions. It will:
    - Take the **raw input data** from a source (client using API)
    - Load the `*_encoder.pkl` files for treating the raw data
    - Treat the raw data into processed featured data (input of model)
    - Load the `model_*.pkl` file containing our **trained model**
    - Make a prediction with the model and the processed data.
    - Send back the prediction result

**💡 Insight**: :warning: **On this lab, we are going to focus on the deployment in AWS**. If you want to go further into details of the code, please refer to the source of the project [here](https://www.youtube.com/watch?v=Y0SbCp4fUvA).

## Part 3: Download the data for the lab and push it to S3
- Open `phase 1\notebooks\00_download_data.ipynb`
- When using the notebook for the first time, **choose a kernel** from the **top-right** of the notebook.
- Choose as kernel the uv environment we have installed in 1.1 `.venv/...`.
- Run the notebook `phase 1\notebooks\00_download_data.ipynb`.

The following directories will be created / populated by the download step:

```
data/
├── processed/
│   ├── train_data.csv
│   ├── validation_data.csv
│   └── test_data.csv
└── models/
|   └── (models and any other python objects files go here, e.g. lgbm_model.
|        pkl, freq_encoder)
└── layers/
    └── (.zip files containing the python environment of our Lambda function in AWS)    
```

### 3.1 Push the datasets, models and layer files to S3

The inference code depends on several artifacts to make predictions. Upload these assets to S3 so the Lambda function can fetch them at runtime, effectively wiring S3 to Lambda.

Therefore, upload every required file to S3 so the Lambda function can make predictions:
- The `.pkl` files for processing the raw data
- The `.pkl` files of our trained models
- The processed data files to verify the correct column order of our input data

**💡 Insight**: Centralizing the artifacts in S3 is what enables the Lambda function to stay lightweight while still producing predictions.

To upload the files in `data` to S3:
- Navigate to **S3 Console**. 
- Select **Create bucket**
- Give a unique name to your bucket `aws-cc-regression-lab_<unique_id>`
- Back in your IDE, open the notebook `phase 1\notebooks\01_S3_push_datasets_AWS.ipynb`
- change the variables `bucket = <your_bucket_name>` and `region = <your_aws_region>`. 
  You will find the name of your region on the **top-right** of the console, e.g. `Europe (Paris) eu-west-3`.
- **Select the kernel** for this notebook and execute it
- **Check** in AWS S3 that you have all the data uploaded to your S3 bucket

:warning: To make it work, be sure that you have configured aws CLI on your computer with your account credentials and that your user account has admin permissions.

```bash
# Configure AWS credentials
aws configure

# Enter your credentials:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1 (or your preferred region)
# Default output format: json
```


### 3.2 Run a smoke test
- Back in your IDE, open the notebook `phase 1\notebooks\02_smoke_test.ipynb`
- Run the cell to run a smoke test to verify that the inference pipeline works correctly

## Part 4: Create a Lambda function

- The scripts under `src` require an environment that exceeds 500 MB. 
- We must slim this down to fit within the 260 MB per-function limit in *AWS Lambda* by selecting only the essential packages. The dependencies are split into two bundles: 
  - **Core dependencies**: containing *numpy*, *pandas* and *joblib*. You have already downlaoded this pack in `/data/layers/core-layer.zip` 
  - **ML dependencies** : containing *lightgbm* and *scipy* packages. You have already downloaded this pack in `/data/layers/ml-layer.zip` 
-  To be able to reuse the packages separately, we are going to create **two Lambda Layers**. The lambda layers are going to be our **python environments** inside *AWS Lamda*. We can use **one layer** on **many lambda** functions, e.g. if we have a layer with *pandas* and *numpy*, we can use all the lambda functions we want using *numpy* and *pandas*.

**💡 Insight**: By doing this, we declare the environment (layer) **only once** in *AWS Lambda* instead of copying the whole environment everytime along with our function `lambda_function.py`.


### 4.1 Creating the Lambda Layers (environments)

The lambda function will use the Layers as its python environment.
To create the layers, follow the steps:

- Open a terminal in `data/layers`.
- Run the following AWS CLI commands, to create:

  - The **Core dependencies layer**:
```powershell / bash
# Core layer
aws lambda publish-layer-version --layer-name housing-regression-core-deps --zip-file fileb://data/layers/core-layer.zip --compatible-runtimes python3.11
```
  - And the **ML dependencies layer**:
```powershell / bash
# Modeling layer
aws lambda publish-layer-version --layer-name housing-regression-ml-deps --zip-file fileb://data/layers/ml-layer.zip --compatible-runtimes python3.11
```  

**💡 Insight**: Save the `LayerVersionArn` outputs; you will need them when attaching layers to the function.

**NB:** If you have not installed the AWS CLI, you can do it manually in the **Lambda Console**. 
- Go to **Layers**
- Create Layer
- **Layer Name:** `housing-regression-ml-deps`
- **Upload a zip file**: `ml-layer.zip`
- **Runtime**: `Python 3.11`

:warning: Do the same for the `core-layer.zip` file.

### 4.2 Creating the Lambda function

- In the AWS console: search for to the **Lambda Console**
- Click **Create Function**
- Function name: `PredictHousingPrices`
- Runtime: Python 3.11
- Execution role: "Create new role with basic Lambda Permission". We will change it later on.
- Click **Create function**

Next, assemble the code bundle that the Lambda function will execute.

#### 4.2.1. Package the Lambda handler ZIP

To fill up the lambda function in AWS, we will need to compress our code in a zip file and upload it.

This code compresses the `src` folder into a zip file.
:warning: **Always** run the terminal within `/phase-1` folder.

1. Clean the build folder.
   - PowerShell:
     ```powershell
     if (Test-Path build/function) { Remove-Item -Recurse -Force build/function }
     ```
   - Linux/macOS:
     ```bash
     rm -rf build/function
     ```
2. Install only the handler code (dependencies already live in the layers).
   - PowerShell:
     ```powershell
     mkdir build/function
     Copy-Item -Recurse src build/function/src
     ```
   - Linux/macOS:
     ```bash
     mkdir -p build/function
     cp -r src build/function/src
     ```
3. If you need extra local assets (e.g., schema files required at cold start), copy them under `build/function/` now.
4. Zip the contents so the archive root contains `src/`.
   - PowerShell:
     ```powershell
     Compress-Archive -Path build/function/* -DestinationPath build/src.zip -Force
     ```
   - Linux/macOS:
     ```bash
     (cd build/function && zip -r ../src.zip .)
     ```

### 4.2.2 Upload the code

- Inside your Lambda function go to **Upload from**
- Select .zip file
- Upload the `src.zip` file found in `phase-1/build` folder
- You will see the src folder uploaded in a VS Code within the Lambda function

:eyes: Look in the code that we use the `boto3` library to call the AWS S3 service and download the files into a `tmp` folder used by lambda.

### 4.3 Setting up the Lambda function

A few configuration tweaks are required before the Lambda function can run end to end.

If the console shows an error, point the runtime at the correct `lambda_handler` within `lambda_function.py`.

#### 4.3.1 Set the Lambda Handler
- Go to **Runtime settings** and click **Edit**
- In Handler: `src.lambda_function.lambda_handler`
- Now the code is loaded into the VS Code viewer in Lambda

#### 4.3.2 Set the Lambda Layers
- Go to **Layers** and click **Add a layer**
- Choose **Custom layers**
- Select `housing-regression-core-deps` and its last version
- Click **Add**

:warning: Do the same with the `housing-regression-ml-deps` layer

#### 4.3.3 Set the time out of our lambda function
The Lambda function will take up to 10 seconds to make a prediction.
We must set this to avoid the lambda functio to stop earlier.
:warning: The lambda function will consume up to 430 MB, so we need to give it enough memory !
- Inside the Lambda function
- Go to **Configuration**
- **General configuration** and **Edit**
- Memory: *512 MB*
- Timeout: *15 sec*

#### 4.3.4 Set the Lambda environment variables
- Inside the Lambda function
- Go to **Configuration**
- **Environment variables** and **Edit**
- **Add environment variable**
- Key: `S3_BUCKET`
- Value: `<bucket-name>` (name of the S3 bucket you have created)

:warning: Create another variable with
- Key: `REGION_NAME`
- Value: `<your_aws_region>` e.g. eu-west-3, us-east-1, etc...

#### 4.3.5. Update the Lambda execution role
The base role of a Lambda function just has access to Logs (AWS Watchlog service). 
We need to give it permissions to read and get objects from S3.
1. Go to **Configuration -> Permissions**
2. Click on the IAM role under **Role name** (linked under the Lambda function's Permissions tab). It will open the IAM Roles
3. Add an inline S3 read policy so the function can download the artifacts: 
   - Choose **Add permissions → Create inline policy**.
   - Switch to the JSON editor and paste:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": "s3:GetObject",
           "Resource": [
             "arn:aws:s3:::<bucket-name>/models/*",
             "arn:aws:s3:::<bucket-name>/processed/*"
           ]
         }
       ]
     }
     ```
   - :warning: remember to use your own **Bucket name!**
   - Validate, name it (e.g., `AllowLambdaModelArtifactsRead`), and save.

## Part 5: Testing the lambda function
Inside the Lambda console interface
- Go to Test
- In **Test event** put an Event Name `testingHousePrice`
- In **Event JSON** paste this API call with a raw data input:
   ```json
  {
    "resource": "/predict",
    "path": "/predict",
    "httpMethod": "POST",
    "headers": {
      "Content-Type": "application/json"
    },
    "isBase64Encoded": false,
    "body": "{\"records\":[{\"year\":2021,\"quarter\":3,\"month\":7,\"median_list_price\":259900.0,\"median_ppsf\":145.3961600865,\"median_list_ppsf\":140.9792442789,\"homes_sold\":104.0,\"pending_sales\":98.0,\"new_listings\":107.0,\"inventory\":66.0,\"median_dom\":48.0,\"avg_sale_to_list\":1.0160580397,\"sold_above_list\":0.4326923077,\"off_market_in_two_weeks\":0.8163265306,\"bank\":8.0,\"bus\":1.0,\"hospital\":0.0,\"mall\":2.0,\"park\":15.0,\"restaurant\":14.0,\"school\":19.0,\"station\":0.0,\"supermarket\":9.0,\"Total Population\":21501.0,\"Median Age\":40.0,\"Per Capita Income\":37886.0,\"Total Families Below Poverty\":21480.0,\"Total Housing Units\":9067.0,\"Median Rent\":943.0,\"Median Home Value\":182900.0,\"Total Labor Force\":10937.0,\"Unemployed Population\":250.0,\"Total School Age Population\":20604.0,\"Total School Enrollment\":20604.0,\"Median Commute Time\":10007.0,\"price\":255300.5620379616,\"lat\":39.0811,\"lng\":-84.4646,\"zipcode_freq\":94.0,\"city_encoded\":150644.1629528453}]}"
  }
   ```
   - Save the test and run it with **Test**

**💡 Insight**: You should obtain a result like this:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"predictions\": [235877.92183433237], \"count\": 1, \"actuals\": [255300.5620379616]}"
}
```

## Part 6: Expose via API Gateway

This section publishes the Lambda function through an API Gateway endpoint.

### 6.1 Create New API

1. **Navigate to API Gateway Console**
   - Search for "API Gateway"
   - Click **Create API**

2. **Choose API Type**
   - Select **REST API** (not Private)
   - Click **Build**

3. **Configure API**
   - Protocol: **REST**
   - Create new API: **New API**
   - API name: `HousePricesAPI`
   - Description: (optional) "House Prices Prediction API"
   - Endpoint Type: **Regional**
   - Click **Create API**

4. **Choose Security Policy**
   - When prompted for security policy, select:
   - ✅ **SecurityPolicy_TLS13_1_3_2025_09 (recommended)**
   
   > 💡 This is the latest TLS 1.3 policy and is recommended by AWS. It's secure and compatible with all modern clients (curl, browsers, Postman).

### 6.2 Create Resource

1. **Create Resource**
   - Click **Actions** → **Create Resource**
   - Or click **Create resource** button

2. **Resource Configuration**
   - Resource path: `/` (root)
   - Resource name: `predict_price`
   - ✅ **Enable CORS** (Check this box!)
   
   > ⚠️ **Important**: Enable CORS to allow web browsers to call your API. This is required for the HTML test page and any web applications.
   
   - Click **Create resource**

### 6.3 Create POST Method

1. **Add Method to Resource**
   - Select the `/predict_price` resource (click on it)
   - On **Methods** → **Create Method**
   - Select **POST** from dropdown

2. **Configure Method Integration**
   - Integration type: **Lambda Function**
   - ✅ **Use Lambda Proxy integration** (CHECK THIS BOX!)
   
   > ⚠️ **Critical**: Lambda Proxy integration must be enabled! Without it, API Gateway sends a different event format that our Lambda code doesn't expect, causing "Internal server error".
   
   - Lambda Region: Select your region (e.g., us-east-1)
   - Lambda Function: Start typing `PredictHousingPrices` and select it
   - Click **Save**

### 6.4 Deploy API

1. **Deploy the API**
   - Wait for any "API is updating" messages to clear (30-60 seconds)
   - On **Resources** → **Deploy API**

2. **Deployment Configuration**
   - Deployment stage: **[New Stage]**
   - Stage name: `prod` (or `testing`, `dev` - your choice)
   - Stage description: (optional)
   - Click **Deploy**

3. **Get Your API URL**
   - After deployment, you'll see **Invoke URL** at the top
   - Example: `https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod`
   - **Copy this URL!** You'll need it for testing

## Part 7: 🧪 Testing Your API

### Test 1: Using curl (Command Line)

Replace `$INVOKE_URL$` with your actual Invoke URL:

- On linux :
```bash
curl -X POST "$INVOKE_URL$/predict_price" -H "Content-Type: application/json" -d "{\"records\":[{\"year\":2021,\"quarter\":3,\"month\":7,\"median_list_price\":259900.0,\"median_ppsf\":145.3961600865,\"median_list_ppsf\":140.9792442789,\"homes_sold\":104.0,\"pending_sales\":98.0,\"new_listings\":107.0,\"inventory\":66.0,\"median_dom\":48.0,\"avg_sale_to_list\":1.0160580397,\"sold_above_list\":0.4326923077,\"off_market_in_two_weeks\":0.8163265306,\"bank\":8.0,\"bus\":1.0,\"hospital\":0.0,\"mall\":2.0,\"park\":15.0,\"restaurant\":14.0,\"school\":19.0,\"station\":0.0,\"supermarket\":9.0,\"Total Population\":21501.0,\"Median Age\":40.0,\"Per Capita Income\":37886.0,\"Total Families Below Poverty\":21480.0,\"Total Housing Units\":9067.0,\"Median Rent\":943.0,\"Median Home Value\":182900.0,\"Total Labor Force\":10937.0,\"Unemployed Population\":250.0,\"Total School Age Population\":20604.0,\"Total School Enrollment\":20604.0,\"Median Commute Time\":10007.0,\"price\":255300.5620379616,\"lat\":39.0811,\"lng\":-84.4646,\"zipcode_freq\":94.0,\"city_encoded\":150644.1629528453}]}"
  ```
- On windows:
```powershell
Invoke-RestMethod -Method Post -Uri "$INVOKE_URL$/predict_price" -ContentType "application/json" -Body "{"records":[{"year":2021,"quarter":3,"month":7,"median_list_price":259900.0,"median_ppsf":145.3961600865,"median_list_ppsf":140.9792442789,"homes_sold":104.0,"pending_sales":98.0,"new_listings":107.0,"inventory":66.0,"median_dom":48.0,"avg_sale_to_list":1.0160580397,"sold_above_list":0.4326923077,"off_market_in_two_weeks":0.8163265306,"bank":8.0,"bus":1.0,"hospital":0.0,"mall":2.0,"park":15.0,"restaurant":14.0,"school":19.0,"station":0.0,"supermarket":9.0,"Total Population":21501.0,"Median Age":40.0,"Per Capita Income":37886.0,"Total Families Below Poverty":21480.0,"Total Housing Units":9067.0,"Median Rent":943.0,"Median Home Value":182900.0,"Total Labor Force":10937.0,"Unemployed Population":250.0,"Total School Age Population":20604.0,"Total School Enrollment":20604.0,"Median Commute Time":10007.0,"price":255300.5620379616,"lat":39.0811,"lng":-84.4646,"zipcode_freq":94.0,"city_encoded":150644.1629528453}]}"
```
**Expected Response:**
```json
{"predictions": [235877.92183433237], "count": 1, "actuals": [255300.5620379616]}
```

### Test 2: Using Postman

1. **Create New Request**
   - Method: **POST**
   - URL: `https://$INVOKE_URL$/predict_price`
   
2. **Set Headers**
   - Key: `Content-Type`
   - Value: `application/json`

3. **Set Body**
   - Select **raw** and **JSON**
   - Enter:
   ```json
    {
    "records": [
      {
        "year": 2021,
        "quarter": 3,
        "month": 7,
        "median_list_price": 259900.0,
        "median_ppsf": 145.3961600865,
        "median_list_ppsf": 140.9792442789,
        "homes_sold": 104.0,
        "pending_sales": 98.0,
        "new_listings": 107.0,
        "inventory": 66.0,
        "median_dom": 48.0,
        "avg_sale_to_list": 1.0160580397,
        "sold_above_list": 0.4326923077,
        "off_market_in_two_weeks": 0.8163265306,
        "bank": 8.0,
        "bus": 1.0,
        "hospital": 0.0,
        "mall": 2.0,
        "park": 15.0,
        "restaurant": 14.0,
        "school": 19.0,
        "station": 0.0,
        "supermarket": 9.0,
        "Total Population": 21501.0,
        "Median Age": 40.0,
        "Per Capita Income": 37886.0,
        "Total Families Below Poverty": 21480.0,
        "Total Housing Units": 9067.0,
        "Median Rent": 943.0,
        "Median Home Value": 182900.0,
        "Total Labor Force": 10937.0,
        "Unemployed Population": 250.0,
        "Total School Age Population": 20604.0,
        "Total School Enrollment": 20604.0,
        "Median Commute Time": 10007.0,
        "price": 255300.5620379616,
        "lat": 39.0811,
        "lng": -84.4646,
        "zipcode_freq": 94.0,
        "city_encoded": 150644.1629528453
      }
    ]
    }
   ```

4. **Send Request**
   - Click **Send**
   - Check response at bottom

**Expected Response:**
```json
{"predictions": [235877.92183433237], "count": 1, "actuals": [255300.5620379616]}
```

## ✅ End of lab

:clap: Congratulations ! You have set up a Lambda function in AWS that takes raw data and returns predictions through an API ! 

:sunglasses: You can be proud :sunglasses:  
Now you can integrate **any** of your ML models into **an API Endpoint**.
Anyone having access to your invoke URL can now make predictions on **new data** :D  

## Part 8: About the S3 + Lambda + API Gateway approach

### Pros
- Only S3 storage generates a cost footprint
- Lambda and API Gateway are serverless, scaling with demand and charging per request
- Ideal for lightweight projects that need to go live quickly

### Cons
- **We depend on uploading all on S3**: every `.pkl` artifact and related asset must reside in S3.
- **250 MB limitation**: When the dependency stack exceeds 250 MB, the ZIP no longer fits. We mitigate this by favoring lightweight replacements (e.g., custom encoders) and moving heavy packages into dedicated layers. 
- **No control over environment**: Building and maintaining the layers adds overhead; **Docker** would provide a more customizable runtime.
- **Not a product, just a brick**. There is no user interface—only backend integration.
- **This is not a valid approach for project using big libraries**. 
:warning: For instance, if we wanted to use the library `xgboost` in our project, it will be too big for fitting it into a layer ! :warning:

## Part 9: Extra resources

### E-1. How to (re-)build dependency layers
Use these steps only when you must refresh the `housing-regression-core-deps` or `housing-regression-ml-deps` layers.

**CAREFUL !** Compile the dependencies **ONLY on Linux** so the resulting wheels match **Amazon Linux** and remain Lambda-compatible.

#### 1.1 Compilation of the dependencies
- Linux ONLY:

The code below:
- Compiles the two packages
- Strips the non-necessary *tests* and *pycache* folders
- Compresses the two packages into separated *.zip* files
```bash
rm -rf build/layers/core build/layers/ml
mkdir -p build/layers/core/python build/layers/ml/python

# Core/data tooling layer (single source of numpy)

pip install --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.11 --target build/layers/core/python pandas==2.2.3 joblib==1.4.2 numpy==2.2.0 python-dateutil==2.9.0.post0 pytz==2025.1 tzdata==2025.3 six==1.16.0


# Modeling layer (reuse numpy from core via --no-deps)
pip install --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.11 --target build/layers/ml/python --no-deps scipy==1.13.1 

pip install --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.11 --target build/layers/ml/python --no-deps lightgbm==3.3.5 

# Strip tests/docs/caches to stay < 262 MB combined
find build/layers -type d -name "__pycache__" -prune -exec rm -rf {} +
rm -rf build/layers/core/python/pandas/tests \
  build/layers/core/python/pandas/io/tests \
  build/layers/core/python/numpy/tests \
  build/layers/core/python/numpy/doc
rm -rf build/layers/ml/python/scipy/tests \
  build/layers/ml/python/scipy/fft/tests \
  build/layers/ml/python/scipy/integrate/tests \
  build/layers/ml/python/scipy/interpolate/tests \
  build/layers/ml/python/scipy/linalg/tests \
  build/layers/ml/python/scipy/optimize/tests \
  build/layers/ml/python/scipy/signal/tests \
  build/layers/ml/python/scipy/sparse/tests \
  build/layers/ml/python/scipy/spatial/tests \
  build/layers/ml/python/scipy/stats/tests

# Quick size check (expect core ≈90 MB, ml ≈122 MB → total ≈210 MB < 262 MB)
du -sh build/layers/core build/layers/ml

# Package layers (zip roots must contain python/)
(cd build/layers/core && zip -r ../../core-layer.zip .)
(cd build/layers/ml && zip -r ../../ml-layer.zip .)
```
After installing, confirm no duplicate `numpy*` folders exist under `build/layers/ml/python`. Both layers combined should now stay under ~255 MB when uncompressed.