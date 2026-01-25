The following lab is divided in two main parts:
- phase-0: a simple Lambda deployment using S3, Lambda and API Gateway AWS Services.
- phase-1 to phase-3: a lab inspired on the great work made by [Anes Riad](https://github.com/anesriad/Regression_ML_EndtoEnd).

# First lambda function lab (phase-0)
This lab is a first touch on S3, Lambda and API Gateway. The lab prepares the installation and the deployment of a simple python script in AWS Lambda that will be accessed through an API.

Go to `phase-0/README.md` to get started ! :grin:

# Regression End to End ML project (phase-1 to phase-3)
This project uses a House TS Data set to create a regression model.

We are going through the steps from loading and treating the data to deploy and serve the model into the cloud.

This lab is inspired on the great work made by [Anes Riad](https://github.com/anesriad/Regression_ML_EndtoEnd).

The codebase is organized into distinct pipelines following the flow:
`Load → Preprocess → Feature Engineering → Train → Tune → Evaluate → Inference → Batch → Serve`

Here a description of the steps of our end-to-end pipeline:

- **Preprocessing**: Data Split / Data Cleaning / Data quality check (*Great expectations*)
- **Feature Engineering**: Transform features / Encoding / tests
- **Train, Tune, Evaluation & Model Tracking**: Model optimization (*Optuna* for hyper parameter tuning), Performance metrics and model tracking (*MLFlow* for experience tracking)
- **Set pipelines**: Feature, training and inference pipelines
- **Containerize & CI / CD** : Reproducibility (*Docker*), run, test and push to AWS (*Github Actions* to automate deployment)
- **Deploy & Serve** : Production API (*FastAPI* / *AWS ECS* )
- **Frontend**: Streamlit

The **cost** of this lab is less than **$5** (Free on your Free Tier credits)

![End-To-End-Schema](/assets/ml-end-to-end-schema.png)

## Pre-requisites
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

## Project 
To ease understanding, since we could have different levels of knowledge between the members of the Club, we are going to divide the project increasing its complexity.  
The division is as follows:

1. *Phase1*: Integrate a model into S3 and using Lambda call through an API
2. *Phase2*: Code our ML pipeline into an application and integrate it in an EC2 instance.
3. *Phase3*: Full integration (original Anes Riad project) -> Integrate the whole End to End pipeline.

## The AWS services involved

- **AWS S3 Integration**: Data and model storage in `housing-regression-lab` bucket
- **Amazon ECR**: Container registry for Docker images
- **Amazon ECS**: Container orchestration with Fargate
- **Application Load Balancer**: Traffic distribution and routing
- **CI/CD Pipeline**: Automated deployment via GitHub Actions




