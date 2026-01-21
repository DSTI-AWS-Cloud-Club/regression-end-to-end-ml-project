# Phase 0 - Deploy a **simple** ML model in the cloud
Integrate a ML artifact into S3 and using Lambda call through an API

## Steps

### 0.Clone the repository
Create a folder in your local system and clone the repository:

`git clone https://github.com/DSTI-AWS-Cloud-Club/regression-end-to-end-ml-project.git`

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

### 2. Get the data
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

## The AWS services involved

- **S3 Integration**: Data and model storage in `??????????` bucket
- **Lambda** :  Functions that can run a python script
- **API Gateway**: REST API endpoint service
