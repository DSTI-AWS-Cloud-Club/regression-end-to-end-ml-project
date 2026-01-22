# Phase 1 - Deploy a **complex** ML model in the cloud
Integrate a ML end-to-end pipeline into S3 and using Lambda call through an API

## The AWS services involved

- **S3 Integration**: Data and model storage in an S3 bucket
- **Lambda** :  Functions that can run a python script
- **API Gateway**: REST API endpoint service

These services will permit a Data Scientist to deploy its ML end-to-end pipeline into AWS and expose it through an API Endpoint.

![s3+lambda+api schema](/assets/s3+lambda+api-diagram.png)

## Step 1. Initialise python env
Open your IDE and open the cloned repo. Open a terminal and run:

```
cd phase-1
uv sync
```

### 1.1 Activate environment

On Windows:
`.\.venv\Scripts\activate.ps1`  

On Linux:
`source .venv/bin/activate`

## Step 2. Understanding the code

- Take a look at the code in `src`. Check that there are three pipelines

  - *Feature pipeline*: Does the **loading**, **pre-processing** and **feature engineering** (LT) on the raw data. 
    - The output of this pipeline is the `feature_engineered_*.csv` files that you have in `data/processed`.
    - Generates two `.pkl` files:
      - `freq_encoder.pkl`: A python object to make the encoding of the zip codes **from raw data**
      - `target_encoder.pkl`: A python object to make the encoding of the city names **from raw data**

  - *Training pipeline*: This pipeline takes the processed data and trains the the model. 
    - `train.py`: trains a model and generates a `.pkl` file (python object in a file) containing our model. We will load this file into our Lambda function to make predictions !
    - `tune.py`: uses **Optuna** and **MLflow** to optimize the parameter tuning and to track the models into a database. Thanks to this we will be able to select the best model and track the options !

  - *Inference pipeline*: It uses the **feature pipeline** to preprocess the raw data into the processed data and then imports the `model.pkl` file to generate **predictions**.

  - *lambda_function.py*: This is the lambda function that will use the inference pipeline to generate the predictions. It will:
    - Take the **raw input data** from a source (client using API)
    - Load the `*_encoder.pkl` files for treating the raw data
    - Treat the raw data into processed featured data (input of model)
    - Load the `model_*.pkl` file containing our **trained model**
    - Make a prediction with the model and the processed data.
    - Send back the prediction result

:warning: **On this lab, we are going to focus on the deployment in AWS**. If you want to go further into details of the code, please refer to the source of the project [here](https://www.youtube.com/watch?v=Y0SbCp4fUvA).

## Step 3. Download the data for the lab
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

Our code needs files to be able to make predictions. Those files we are going to upload them to S3 so Lambda has access to them. We are going to connect the S3 service with Lambda.

Thus, are going to upload to S3 all the necessary files for the Lambda function to make predictions:
- The `.pkl` files for processing the raw data
- The `.pkl` files of our trained models
- The processed data files to verify the correct column order of our input data

To upload the files in `data` to S3:
- Navigate to **S3 Console**. 
- Select **Create bucket**
- Give a unique name to your bucket `aws-cc-regression-lab_<unique_id>`
- Back in your IDE, open the notebook `phase 1\notebooks\01_S3_push_datasets_AWS.ipynb`
- change the variables `bucket = <your_bucket_name>` and `region = <your_aws_region>`. 
  You will find the name of your region on the **top-right** of the console, e.g. `Europe (Paris) eu-west-3`.
- **Select the kernel** for this notebook and execute it
- **Check** in AWS S3 that you have all the data uploaded to your S3 bucket

### 3.2 Run a smoke test
- Back in your IDE, open the notebook `phase 1\notebooks\02_smoke_test.ipynb`
- Run the cell to run a smoke test to verify that the inference pipeline works correctly

## Step 4. Create a Lambda function

- In order to run the srcripts in the `src` folder our environment makes more than 500 MB. 
- We need to reduce it in order to put it inside the Lambda function. In *AWS Lambda* we have a 260 MB limiation per function, we will have to reduce the size and pick the essential packages. The packages were divided in two: 
  - **Core dependencies**: containing *numpy*, *pandas* and *joblib*. You have already downlaoded this pack in `/data/layers/core-layer.zip` 
  - **ML dependencies** : containing *lightgbm* and *scipy* packages. You have already downloaded this pack in `/data/layers/ml-layer.zip` 
-  To be able to reuse the packages separately, we are going to create **two Lambda Layers**. The lambda layers are going to be our **python environments** inside *AWS Lamda*. We can use **one layer** on **many lambda** functions, e.g. if we have a layer with *pandas* and *numpy*, we can use all the lambda functions we want using *numpy* and *pandas*. By doing this, we declare the environment (layer) **only once** in *AWS Lambda* instead of copying the whole environment everytime along with our function `lambda_function.py`.


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

Save the `LayerVersionArn` outputs; you will need them when attaching layers to the function.

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

We need to build up the code and dependencies of our Lambda function.

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

We need to set up some things for the Lambda function to work.

See that the code is throwing an error.  
We need to specify the path to our `lambda_handler` function inside `lambda_function.py`.

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
2. Add an inline S3 read policy so the function can download the artifacts: 
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
   - Validate, name it (e.g., `AllowModelArtifactsRead`), and save.

### Step 5. :microscope: Testing the lambda function
Inside the lambda function Interface
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

You should obtain a result like this:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"predictions\": [235877.92183433237], \"count\": 1, \"actuals\": [255300.5620379616]}"
}
```

## Step 6. Expose via API Gateway

We are going to expose our Lambda function to an API Endpoint.

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

## Step 7: 🧪 Testing Your API

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

# End of lab

:clap: Congratulations ! You have set up a Lambda function in AWS that takes raw data and returns predictions through an API ! 

:sunglasses: You can be proud :sunglasses:  
Now you can integrate **any** of your ML models into **an API Endpoint**.
Anyone having access to your invoke URL can now make predictions on **new data** :D  

# About the S3 + Lambda + API Gateway approach
## Pros
- We consume only S3 storage
- Lambda and API Gateway are Serverless (they size according to demand and they have a cost per request)
- For a simple project could work very well and rapidly

#### API Gateway on 🎁 Free Tier
- **1 million REST API** calls per month  
- **1 million HTTP API** calls per month  
- **1 million WebSocket messages** plus **750,000 minutes of connection time** per month  
- Available **for up to 12 months** after account creation

#### Lambda on 🎁 Free Tier
- **1 million** free requests per month  
- **400,000 GB-seconds** of compute time per month
- **100 GiB** of response streaming per month beyond the first 6 MB per request free.

## Cons
- **We depend on uploading all on S3**: we must upload the `.pkl` files and other files to S3.
- **250 MB limitation**: If the environment (python packages and other dependencies) grows beyond 250 MB we can't deploy as a ZIP. We mitigated this by replacing heavy dependencies (like category-encoders) with lightweight in-house code and, if needed, offloading the rest to Lambda layers. 
- **No control over environment**: It adds extra handling on the compilation of the layers. **Docker** could solve this
- **Not a product, just a brick**. No user interface, just backend integration.
- **This is not a valid approach for project using big libraries**. 
:warning: For instance, if we wanted to use the library `xgboost` in our project, it will be too big for fitting it into a layer ! :warning:

## Extra resources
### E-1. How to (re-)build dependency layers
Use this only when you need to refresh the `housing-regression-core-deps` or `housing-regression-ml-deps` layers.

**CAREFUL !** The compilation of the dependencies must be done **ONLY on Linux** to be compatible with **AWS Lambda Layers** because these wheels are compiled for **Amazon Linux**

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