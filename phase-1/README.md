# Phase 1 - Deploy a **complex** ML model in the cloud
Integrate a ML artifact into S3 and using Lambda call through an API

## Steps

### 1.Initialise python env
Open your IDE and open the cloned repo. Open a terminal and run:

```
uv sync
```

#### 1.1 Activate environment

On Windows:
`.\.venv\Scripts\activate.ps1`  

On Linux:
`source .venv/bin/activate`

### 2. Get the data for the lab
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
    └── (models and any other python objects files go here, e.g. lgbm_model.pkl, freq_encoder)
```

### 3. Push the dataset to S3
- Navigate to **S3 Console**. 
- Select **Create bucket**
- Give a unique name to your bucket `aws-cc-regression-lab_<unique_id>`
- Open the notebook `phase 1\notebooks\01_S3_push_datasets_AWS.ipynb`
- change the variables `bucket = <your_bucket_name>` and `region = <your_aws_region>`. 
  You will find the name of your region on the **top-right** of the console, e.g. `Europe (Paris) eu-west-3`.
- **Select the kernel** for this notebook and execute it
- **Check** that you have all the data uploaded to your S3 bucket

#### 4. Create a Lambda function

Due to limitation of our environment (project dependencies > 250 MB), we are going to create two Lambda Layers.

##### 4.1 Creating the Lambda environment

The lambda function will use this Layers as its python environment.

Open a terminal **in the same folder where the zip files** are `data/layers`.
Run the following AWS CLI commands:

- The **Core dependencies layer**:
```
aws lambda publish-layer-version --layer-name 
housing-regression-core-deps --zip-file fileb://core-deps-layer.zip --compatible-runtimes python3.11
```
- And the **ML dependencies layer**:
```
aws lambda publish-layer-version --layer-name housing-regression-ml-deps --zip-file fileb://ml-deps-layer.zip --compatible-runtimes python3.11
```  
If you have not installed the AWS CLI, you can do it manually in the **Lambda Console**. 
- Go to **Layers**
- Create Layer
- **Layer Name:** housing-regression-ml-deps
- **Upload a zip file**: "ml-deps-layer.zip"
- **Runtime**: Python 3.11
- Do the same for the **Core** zip file.

- **Keep in mind** the **ARN** of each layer, we are going to use it later on.

##### 4.2 Creating the Lambda function

## The AWS services involved

- **S3 Integration**: Data and model storage in `housing-regression-data` bucket
- **Lambda** :  Functions that can run a python script
- **API Gateway**: REST API endpoint service

# S3 + Lambda + API Gateway approach
## Pros
- We consume only S3 storage and
- Lambda and API Gateway are Serverless (they size according to demand and they have a cost per request)

## Cons
- It is oversimplified: no data treatment, just a simple input and pkl files uploaded to S3.
- If the environment (python packages and other dependencies) grows beyond 250 MB we can't deploy as a ZIP. We mitigated this by replacing heavy dependencies (like category-encoders) with lightweight in-house code and, if needed, offloading the rest to Lambda layers. 
- It adds extra handling of the layers (remember that the compilation must be done on a Linux environment).
- No user interface, just backend integration.
- This is not a valid approach for big projects (UI, > 250 MB environments, etc). For instance, if we wanted to use the library `xgboost` in our project, it will be too big for fitting it into a layer !

# Extra resources

## Lambda Layers: Compiling the environment of a project
To create the layers zip files we have used the following scripts.  
In the **ROOT** directory, open a terminal and execute:

```
uv pip install --target build/layers/ml/python lightgbm>=3.1.3 --link-mode=copy
uv pip install --target build/layers/core/python pandas>=2.3.3 joblib>=1.4.2 boto3>=1.42.30  --link-mode=copy
```
This will compile the environment. After that, compress each folder separately in a `.zip` file ready to be uploaded to Lambda Layers.
