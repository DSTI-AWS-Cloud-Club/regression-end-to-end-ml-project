# AWS Lambda Function Lab: Demand Prediction REST API

## Lab Overview
In this beginner-friendly lab, you'll learn how to deploy a machine learning model as a serverless REST API using AWS Lambda, S3, and API Gateway. You'll create a demand prediction service that forecasts product demand based on pricing.

**Duration**: 60-90 minutes  
**Cost**: Free tier eligible  
**Prerequisites**: AWS Account

---

## What You'll Build

A REST API endpoint that:
- Accepts product prices as input
- Returns predicted demand for multiple products (Milk, Chocolate, Soup, Ramen)
- Runs on AWS Lambda (serverless, pay-per-use)
- Stores training data in S3 (cloud storage)
- Exposes an HTTP endpoint via API Gateway

---

## AWS Services Overview

### 1. **Amazon S3 (Simple Storage Service)**
Think of S3 as a massive hard drive in the cloud. It's perfect for storing files like CSV datasets, images, or backups.

**Key Concepts**:
- **Bucket**: A container for your files (like a folder on your computer)
- **Object**: A file stored in a bucket
- **Public vs Private**: Control who can access your files

**Why we use it**: Store our demand data CSV file that the Lambda function will read

---

### 2. **AWS Lambda**
Lambda lets you run code without managing servers. You pay only when your code runs!

**Key Concepts**:
- **Function**: Your Python code that runs on demand
- **Handler**: The entry point function that AWS calls
- **Runtime**: The programming language version (Python 3.12)
- **Timeout**: Maximum time your function can run (default 3 seconds, max 15 minutes)
- **Memory**: RAM allocated to your function (128 MB to 10 GB)

**Why we use it**: Run our demand prediction logic without maintaining servers

---

### 3. **Amazon API Gateway**
API Gateway creates a front door for your Lambda function, giving it an HTTP URL that anyone can call.

**Key Concepts**:
- **REST API**: A web service that responds to HTTP requests
- **Resource**: A URL path (e.g., `/predict`)
- **Method**: HTTP verb (GET, POST, PUT, DELETE)
- **Stage**: Environment version (dev, test, prod)

**Why we use it**: Transform our Lambda function into a publicly accessible web API

---
## :warning: Installation of pre-requisites

Common pre-requisites to all AWS labs are:

1. Have an **AWS Free Tier account** (an account creation gives you $100 credit and **up to $200**)
    1.1. You have installed the `aws` CLI on our computer. Go [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and install it depending on your OS.
    1.2 Make sure you create an `admin` user instead of a `root` user to avoid security problems. 
    - [Here](https://docs.aws.amazon.com/streams/latest/dev/setting-up.html#setting-up-next-step-2) you will find the steps to do it. 
    - Make sure that within the **Permissions policies** of your user you have added `AdministratorAccess`.
0
2. Have installed an IDE (VSCode, PyCharm) that has **Colab** extension installed
3. Make sure `UV` is installed in your computer. If not installed go [here](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1) and install it depending on your OS. 
    2.1. *To test it*: run `uv` in a terminal in your computer without throwing an error.
4. Make sure `Git` is installed in your computer. 
    4.1. *To test it*: run `git` in a terminal in your computer without throwing an error.

### Step 1.1 Change AWS root account to an admin account

Make sure you create an `admin` user instead of a `root` user to avoid security problems. 
    - [Here](https://docs.aws.amazon.com/streams/latest/dev/setting-up.html#setting-up-next-step-2) you will find the steps to do it. 
    - Make sure that within the **Permissions policies** of your user you have added `AdministratorAccess`.

### Step 1.2 Install AWS CLI

- Go to IAM and create an access key

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
### etc etc

---

## Lab Steps

### Part 0. Clone the repository and environment setup

### 0.1. Clone the repository

Create a folder in your local system and clone the repository:

`git clone https://github.com/DSTI-AWS-Cloud-Club/regression-end-to-end-ml-project.git`

### 0.2. Initialise python environment
Open your IDE and open the cloned repo. Open a terminal and run:

```
cd phase-0
uv sync
```

#### 2.3 Activate environment

On Windows:
`.\.venv\Scripts\activate.ps1`  

On Linux:
`source .venv/bin/activate`

---

### Part 1: Upload Data to S3

#### Step 1: Create an S3 Bucket
1. Sign in to the AWS Console
2. Search for **S3** in the services search bar and click it
3. Click **"Create bucket"**
4. Configure your bucket:
   - **Bucket name**: `demand-prediction-data-[your-initials]-[random-number]`
     - Example: `demand-prediction-data-js-12345`
     - Must be globally unique across all AWS accounts
   - **AWS Region**: Choose the closest to you (e.g., `us-east-1`)
   - **Block Public Access settings**: Keep all checkboxes CHECKED (recommended for security)
5. Leave other settings as default
6. Click **"Create bucket"**

**✅ Success Check**: You should see your new bucket in the S3 buckets list

---

#### Step 2: Upload the Demand Data
1. Click on your newly created bucket name
2. Click **"Upload"**
3. Click **"Add files"**
4. Select the `demand_data.csv` file from your local `phase-0/data/` folder
5. Click **"Upload"**
6. Wait for the upload to complete (you'll see a green success message)
7. Click **"Close"**

**✅ Success Check**: You should see `demand_data.csv` in your bucket

---

#### Step 3: Note Your S3 Details
Write down the following (you'll need them later):
- **Bucket name**: `_________________________`
- **Region**: `_________________________`

---

### Part 2: Create the Lambda Function

#### Step 1: Create a New Lambda Function
1. Search for **Lambda** in the AWS Console services
2. Click **"Create function"**
3. Select **"Author from scratch"**
4. Configure basic information:
   - **Function name**: `DemandPredictionFunction`
   - **Runtime**: Python 3.12 (or latest Python 3.x available)
   - **Architecture**: x86_64
5. Expand **"Change default execution role"**
   - Select **"Create a new role with basic Lambda permissions"**
6. Click **"Create function"**

**What just happened?**
- AWS created a Lambda function with a default IAM role
- The role has permission to write logs to CloudWatch (for debugging)
- But it doesn't have S3 permissions yet!

---

#### Step 2: Add S3 Permissions to Lambda
Your Lambda needs permission to read from S3.

1. On your Lambda function page, click the **"Configuration"** tab
2. Click **"Permissions"** in the left sidebar
3. Under "Execution role", click the role name (looks like `DemandPredictionFunction-role-xxxxx`)
   - This opens the IAM console in a new tab
4. In the IAM role page, click **"Add permissions"** → **"Attach policies"**
5. Search for `AmazonS3ReadOnlyAccess`
6. Check the box next to **AmazonS3ReadOnlyAccess**
7. Click **"Add permissions"**

**✅ Success Check**: You should see "AmazonS3ReadOnlyAccess" in the role's permissions policies

**Alternative (More Secure)**: If you get Access Denied errors, create a custom policy:
1. In the IAM role page, click **"Add permissions"** → **"Create inline policy"**
2. Click the **JSON** tab
3. Paste this policy (replace `YOUR-BUCKET-NAME` with your actual bucket name):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::YOUR-BUCKET-NAME",
           "arn:aws:s3:::YOUR-BUCKET-NAME/*"
         ]
       }
     ]
   }
   ```
4. Click **"Review policy"**
5. Name it `S3BucketReadPolicy`
6. Click **"Create policy"**

---

#### Step 3: Add the Lambda Function Code
1. Go back to your Lambda function tab
2. Click the **"Code"** tab
3. In the code editor, **delete all existing code**
4. Copy and paste the entire `lambda_function.py` code (provided separately)
5. Update the following variables at the top of the code:
   ```python
   BUCKET_NAME = "your-bucket-name-here"  # Replace with your actual bucket name
   DATA_KEY = "demand_data.csv"
   REGION = "us-east-1"  # Replace with your region
   ```
6. Click **"Deploy"** (orange button at the top)

**⚠️ Important**: Make sure to click "Deploy" or your changes won't be saved!

---

#### Step 4: Configure Lambda Settings
1. Click the **"Configuration"** tab
2. Click **"General configuration"** → **"Edit"**
3. Update settings:
   - **Timeout**: 30 seconds (prediction might take a few seconds)
   - **Memory**: 256 MB
4. Click **"Save"**

**Why these settings?**
- More timeout gives the function time to download data from S3 and compute predictions
- More memory can make the function run faster

---

#### Step 5: Test Your Lambda Function
1. Click the **"Test"** tab
2. Click **"Create new event"**
3. Configure test event:
   - **Event name**: `TestPrediction`
   - **Event JSON**: Replace with this:
     ```json
     {
       "prices": [3.5, 4.0, 4.5, 2.5]
     }
     ```
4. Click **"Save"**
5. Click **"Test"** button

**Expected Result**:
- **Status**: Succeeded (green)
- **Response**: JSON with predicted demands
  ```json
  {
    "predictions": {
      "Milk": 850.23,
      "Chocolate": 120.45,
      "Soup": 180.67,
      "Ramen": 200.89
    },
    "input_prices": [3.5, 4.0, 4.5, 2.5]
  }
  ```

**🐛 Troubleshooting**:
- **Error: Access Denied** → Check S3 permissions (Step 2)
- **Error: Timeout** → Increase timeout in Configuration
- **Error: No module named 'X'** → Code uses only built-in Python libraries

---

### Part 3: Create API Gateway

#### Step 1: Create a REST API
1. Search for **API Gateway** in AWS Console services
2. Click **"Create API"**
3. Find **REST API** (not Private or HTTP API) and click **"Build"**
4. Configure:
   - **Choose the protocol**: REST
   - **Create new API**: New API
   - **API name**: `DemandPredictionAPI`
   - **Description**: `REST API for demand prediction`
   - **Endpoint Type**: Regional
   - **Security policy**: SecurityPolicy_TLS13_1_2_2021_06
5. Click **"Create API"**

---

#### Step 2: Create a Resource
1. Click **"Actions"** → **"Create Resource"**
2. Configure:
   - **Resource Name**: `predict`
   - **Resource Path**: `predict` (automatically filled)
   - Check **"Enable API Gateway CORS"** (allows web browsers to call your API)
3. Click **"Create Resource"**

**What's a resource?**
It's a URL path. You're creating `/predict` endpoint.

---

#### Step 3: Create a POST Method
1. With `/predict` selected, click **"Actions"** → **"Create Method"**
2. From the dropdown, select **POST** and click the checkmark ✓
3. Configure the method:
   - **Integration type**: Lambda Function
   - **Use Lambda Proxy integration**: ✓ CHECK THIS BOX
   - **Lambda Region**: Choose your Lambda's region
   - **Lambda Function**: Start typing `DemandPredictionFunction` and select it
4. Click **"Create method"**

**Why POST?**
POST methods accept a body (JSON data), perfect for sending prices.

---

#### Step 4: Deploy the API
1. Click **"Actions"** → **"Deploy API"**
2. Configure:
   - **Deployment stage**: [New Stage]
   - **Stage name**: `prod`
   - **Stage description**: `Production stage`
3. Click **"Deploy"**

**✅ Success**: You'll see a screen with an **"Invoke URL"** at the top!

---

#### Step 5: Copy Your API Endpoint
At the top of the page, you'll see:
```
Invoke URL: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
```

Your complete endpoint URL is:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/predict
```

**Write this down!** You'll use it to call your API.

---

### Part 4: Test Your API

#### Option 1: Test with curl (Command Line)
Open a terminal and run:

```bash
curl -X POST https://YOUR-API-URL-HERE/predict \
  -H "Content-Type: application/json" \
  -d '{"prices": [3.5, 4.0, 4.5, 2.5]}'
```
**Important:** Make sure to include `/predict` at the end of the URL!

#### Option 2: Test with PowerShell (Windows)
```powershell
# Create the request body
$body = @{
    prices = @(3.5, 4.0, 4.5, 2.5)
} | ConvertTo-Json

# Make the API request (replace with YOUR actual API URL)
Invoke-RestMethod -Uri "https://YOUR-API-URL-HERE/predict" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

**Note:** Copy and paste each command separately, or copy all lines together. Make sure there's a blank line or semicolon between the two commands.

#### Option 3: Test with Python
```python
import requests
import json

url = "https://YOUR-API-URL-HERE/predict"
data = {"prices": [3.5, 4.0, 4.5, 2.5]}

response = requests.post(url, json=data)
print(response.json())
```

**Expected Response**:
```json
{
  "predictions": {
    "Milk": 850.23,
    "Chocolate": 120.45,
    "Soup": 180.67,
    "Ramen": 200.89
  },
  "input_prices": [3.5, 4.0, 4.5, 2.5]
}
```

---

## Understanding the Architecture

```
┌─────────┐       ┌──────────────┐       ┌─────────┐       ┌────────┐
│ Client  │──────▶│ API Gateway  │──────▶│ Lambda  │──────▶│   S3   │
│(Browser)│       │   /predict   │       │Function │       │ Bucket │
└─────────┘       └──────────────┘       └─────────┘       └────────┘
     │                    │                     │                │
     │                    │                     │                │
     └────────────────────┴─────────────────────┴────────────────┘
              Response flows back through the same path
```

**Flow**:
1. Client sends POST request with prices to API Gateway
2. API Gateway triggers Lambda function
3. Lambda downloads training data from S3
4. Lambda trains model and makes predictions
5. Lambda returns predictions to API Gateway
6. API Gateway returns response to client

---

## Cost Breakdown

**S3**:
- Storage: $0.023 per GB per month
- For 1 MB CSV: ~$0.00002/month (essentially free)

**Lambda**:
- First 1 million requests/month: FREE
- First 400,000 GB-seconds compute: FREE
- Your function uses ~0.5 seconds → 2,000 free requests/month

**API Gateway**:
- First 1 million requests/month: $3.50
- After that: $3.50 per million requests

**Total for this lab**: $0 (under free tier limits)

---

## Clean Up (Optional)

To avoid any charges, delete resources when done:

1. **Delete API Gateway**:
   - API Gateway → Select your API → Actions → Delete API

2. **Delete Lambda Function**:
   - Lambda → Select function → Actions → Delete

3. **Delete S3 Bucket**:
   - S3 → Select bucket → Empty bucket → Delete bucket

4. **Delete IAM Role** (optional):
   - IAM → Roles → Search for "DemandPredictionFunction" → Delete

---

## Common Issues & Solutions

### Issue: Lambda returns "Access Denied" or "AccessDenied when calling GetObject"
This is the most common issue. Follow this checklist **in order**:

**Step 1: Verify Lambda code has correct values**
1. Go to Lambda → Code tab
2. Check lines 21-23 at the top:
   ```python
   BUCKET_NAME = "your-bucket-name-here"  # Did you update this?
   DATA_KEY = "demand_data.csv"
   REGION = "us-east-1"  # Did you update this?
   ```
3. Make sure `BUCKET_NAME` matches your S3 bucket **exactly** (case-sensitive)
4. Make sure `REGION` matches where you created your bucket
5. Click **"Deploy"** if you made changes

**Step 2: Verify the bucket and file exist**
1. Open S3 in a new tab
2. Find your bucket - does it exist?
3. Click into the bucket - do you see `demand_data.csv`?
4. Note the region shown at the top (e.g., US East (N. Virginia) = us-east-1)

**Step 3: Check IAM permissions**
1. Go to Lambda → Configuration → Permissions
2. Click the execution role name (opens IAM console)
3. Under "Permissions policies", you should see ONE of these:
   - `AmazonS3ReadOnlyAccess` (AWS managed policy), OR
   - `S3BucketReadPolicy` (inline policy you created)
4. If you have the inline policy, click on it and verify:
   - The bucket name in the policy matches your actual bucket name
   - The ARN format is correct: `arn:aws:s3:::your-actual-bucket-name`

**Step 4: Test the inline policy (if using)**
If the inline policy exists but still fails, **delete it and recreate**:
1. In IAM role, remove the inline policy
2. Click "Add permissions" → "Create inline policy"
3. Paste this (replace `YOUR-ACTUAL-BUCKET-NAME` with your bucket from S3):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::YOUR-ACTUAL-BUCKET-NAME",
           "arn:aws:s3:::YOUR-ACTUAL-BUCKET-NAME/*"
         ]
       }
     ]
   }
   ```
4. Name it `S3BucketReadPolicy` and create
5. **Wait 10-30 seconds** for permissions to propagate
6. Test Lambda again

**Step 5: Check CloudWatch Logs**
1. Lambda → Monitor → "View logs in CloudWatch"
2. Click the latest log stream
3. Look for the line that says "Attempting to download from S3..."
4. Verify the Bucket, Key, and Region match your expectations

**Still failing?** Common issues:
- Typo in bucket name (double-check character by character)
- Bucket is in different region than you specified
- You're using `AmazonS3ReadOnlyAccess` but your bucket has special restrictions
- KMS encryption on bucket (requires additional KMS permissions)

### Issue: API Gateway returns 502 Bad Gateway
**Solution**: Your Lambda function is crashing. Check CloudWatch Logs:
1. Lambda → Monitor → View logs in CloudWatch
2. Look for error messages in the latest log stream
3. Common causes: wrong bucket name, syntax errors, timeout

### Issue: Predictions seem wrong
**Solution**: Verify your bucket name and region are correctly set in the Lambda code

### Issue: API Gateway returns 403 Forbidden
**Solution**: Make sure you deployed the API (Part 3, Step 4)

### Issue: Lambda timeout
**Solution**: Increase timeout in Configuration → General configuration → Edit → Set to 30 seconds

---

## Next Steps

Now that you have a working API, try:

1. **Add input validation** to check price ranges
2. **Add caching** to avoid retraining the model on every request
3. **Store the trained model** in S3 instead of raw data
4. **Add authentication** using API Gateway API keys
5. **Monitor usage** with CloudWatch metrics
6. **Add multiple endpoints** for different prediction types

---

## Key Takeaways

✅ **S3** stores files in the cloud  
✅ **Lambda** runs code without servers  
✅ **API Gateway** creates HTTP endpoints  
✅ **IAM roles** control permissions between services  
✅ **Serverless** means you pay only for what you use  

Congratulations! You've deployed a machine learning API on AWS! 🎉
