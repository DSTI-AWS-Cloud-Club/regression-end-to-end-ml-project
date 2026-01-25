# AWS Deployment Lab: Housing Regression ML Application
## Deploying Streamlit UI & FastAPI Backend to AWS ECR and Fargate

## Resources
Please refer to the original Anes Riad project resources if you have any doubts.

- Here is a [link](https://theneuralmaze.substack.com/p/how-to-build-production-ready-ml) to a blog explaining the steps 
- Here is the [YouTube](https://www.youtube.com/watch?v=Y0SbCp4fUvA) video of Anes explaining the whole project
- Here is Anes' [repo](https://github.com/anesriad/Regression_ML_EndtoEnd) on Github


:warning: For this lab we are going to clone and work on **Anes' repo** and follow up the instructions on this README file.
---

## 📚 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Lab Setup](#lab-setup)
5. [Part 1: AWS Environment Setup](#part-1-aws-environment-setup)
6. [Part 2: Docker Image Preparation](#part-2-docker-image-preparation)
7. [Part 3: ECR Repository Setup](#part-3-ecr-repository-setup)
8. [Part 4: Build and Push Docker Images](#part-4-build-and-push-docker-images)
9. [Part 5: IAM Roles and Permissions](#part-5-iam-roles-and-permissions)
10. [Part 6: ECS Cluster Setup](#part-6-ecs-cluster-setup)
11. [Part 7: Network Configuration (VPC, Security Groups)](#part-7-network-configuration-vpc-security-groups)
12. [Part 8: CloudWatch Logs Setup](#part-8-cloudwatch-logs-setup)
13. [Part 9: Deploy FastAPI Backend to Fargate](#part-9-deploy-fastapi-backend-to-fargate)
14. [Part 10: Load Balancer Configuration](#part-10-load-balancer-configuration)
15. [Part 11: Deploy Streamlit UI to Fargate](#part-11-deploy-streamlit-ui-to-fargate)
16. [Part 12: Testing and Verification](#part-12-testing-and-verification)
17. [Part 13: Monitoring and Troubleshooting](#part-13-monitoring-and-troubleshooting)
18. [Part 14: Cleanup](#part-14-cleanup)
19. [Additional Resources](#additional-resources)

---

## Overview

### 🎯 Learning Objectives
By completing this lab, you will:
- Understand containerized application deployment using Docker
- Learn AWS ECR (Elastic Container Registry) for storing Docker images
- Deploy applications using AWS Fargate (serverless container orchestration)
- Configure networking for public internet access
- Set up Application Load Balancers for distributing traffic
- Implement CloudWatch logging and monitoring
- Test and validate deployed services

### 🏗️ Project Components
This ML project consists of two microservices:

1. **FastAPI Backend** (`/src/api/main.py`)
   - Serves ML predictions via REST API
   - Loads trained XGBoost model from S3
   - Exposes `/predict` endpoint for inference
   - Port: 8000

2. **Streamlit UI** (`app.py`)
   - Interactive web dashboard
   - Calls FastAPI backend for predictions
   - Visualizes results
   - Port: 8501

---

## Architecture

### 🔍 High-Level Architecture Diagram

!["phase3-ecs-fargate-docker"](/assets/phase3-ecs-fargate-docker.png)

### 📊 Key Architectural Concepts

**Microservices Architecture**
- Separation of concerns: UI and API are independent
- Each service can scale independently
- Failure in one service doesn't crash the other

**AWS Fargate**
- Serverless compute for containers
- No EC2 instance management required
- AWS manages the underlying infrastructure
- You pay only for resources used by your containers

**Elastic Container Registry (ECR)**
- Private Docker registry
- Integrated with ECS/Fargate
- Secure image storage with encryption
- Image vulnerability scanning available

**Application Load Balancer (ALB)**
- Distributes incoming traffic
- Health checks ensure traffic goes to healthy containers
- Provides public DNS endpoint
- Enables HTTPS (optional)

---

## Prerequisites

### 💻 Required Software
- [x] **AWS Account** with appropriate permissions
- [x] **AWS CLI v2** installed ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html))
- [x] **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
- [x] **Python 3.11+** installed
- [x] **Git** installed
- [x] **Text Editor** (VS Code recommended)

### 📋 AWS Service Limits
Ensure your AWS account has capacity for:
- 2 ECR repositories
- 1 ECS cluster
- 2 Fargate services (4 vCPU, 4 GB memory combined)
- 2 Application Load Balancers
- 1 S3 bucket (for model and data storage)

### 💰 Cost Estimate
- **Fargate**: ~$0.04/hour per task (approximate)
- **ALB**: ~$0.02/hour + data processing
- **ECR**: First 500 MB/month free, then $0.10/GB/month ($0.35 / month for the two images of this lab)
- **Estimated Lab Cost**: $1-3 (if completed in 2-4 hours and cleaned up)

> ⚠️ **Important**: Remember to clean up resources after completing the lab to avoid ongoing charges!

---

## Lab Setup

### Step 1: Clone the Repository

On your local machine open a terminal and type: 

```bash
git clone https://github.com/zBotta/Regression_ML_EndtoEnd.git
cd Regression_ML_EndtoEnd
```

### Step 2: Configure AWS CLI
```bash
# Configure AWS credentials
aws configure

# Enter your credentials:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1 (or your preferred region)
# Default output format: json
```

**🔍 Understanding AWS Credentials**
- **Access Key ID**: Public identifier for your AWS account
- **Secret Access Key**: Password for programmatic access (keep secure!)
- **Region**: Geographic location where resources will be created (affects latency and cost)

### Step 3: Verify Prerequisites

**These commands work in both PowerShell and Bash:**

```bash
# Verify AWS CLI
aws --version
# Expected: aws-cli/2.x.x ...

# Verify Docker
docker --version
# Expected: Docker version 20.x.x or higher

# Verify Docker is running
docker ps
# Should show container list (may be empty)

# Verify AWS credentials
aws sts get-caller-identity
# Should display your account information
```

**💡 Tip**: Commands without environment variables (like the ones above) work the same in PowerShell and Bash.

---

## Part 1: AWS Environment Setup

### ⚠️ Important: PowerShell vs Bash Syntax

Throughout this lab, you'll see commands using environment variables. **The syntax differs between shells:**

**PowerShell (Windows):**
- Set variables: `$env:VARIABLE_NAME = "value"`
- Use variables: `$env:VARIABLE_NAME`
- Example: `$env:AWS_REGION`

**Bash (Linux/Mac/WSL):**
- Set variables: `export VARIABLE_NAME="value"`
- Use variables: `$VARIABLE_NAME`
- Example: `$AWS_REGION`

**💡 Quick Reference:**
- If you see `$AWS_REGION` in a bash block, use `$env:AWS_REGION` in PowerShell
- If you see `$AWS_ACCOUNT_ID`, use `$env:AWS_ACCOUNT_ID` in PowerShell
- Commands labeled "Linux/Mac/WSL" use bash syntax
- Commands labeled "Windows PowerShell" use PowerShell syntax

---

### 🌍 Set Environment Variables

Create a file to store your configuration:

**Windows PowerShell:**
```powershell
$env:AWS_REGION = "eu-west-3"
$env:AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$env:PROJECT_NAME = "housing-regression"

# Verify
echo $env:AWS_ACCOUNT_ID
echo $env:AWS_REGION
```

**Linux/Mac/WSL:**
```bash
export AWS_REGION="eu-west-3"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export PROJECT_NAME="housing-regression"

# Verify
echo $AWS_ACCOUNT_ID
echo $AWS_REGION
```

**📝 Note**: Replace `us-east-1` with your preferred region (e.g., `eu-west-2`, `ap-south-1`)

---

## Part 2: Docker Image Preparation

### 🔍 Understanding the Dockerfiles

#### Backend Dockerfile (`Dockerfile`)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install uv
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Concepts**:
- `FROM`: Base image (Python 3.11 lightweight version)
- `WORKDIR`: Sets working directory inside container
- `COPY`: Copies files from host to container
- `RUN`: Executes commands during image build
- `EXPOSE`: Documents which port the app uses
- `CMD`: Command to run when container starts

#### UI Dockerfile (`Dockerfile.streamlit`)
```dockerfile
FROM --platform=$BUILDPLATFORM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv && uv pip install --system .
COPY . .
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    API_URL=http://localhost:8000/predict
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py"]
```

**Key Differences**:
- Uses environment variables for Streamlit configuration
- `API_URL` will be updated to point to actual backend service
- Different port (8501 vs 8000)

**🎓 Why Test Locally?**
- Faster iteration (no AWS upload/download)
- Easier debugging
- Catches errors before pushing to ECR

---

## Part 3: ECR Repository Setup

### 📦 Create ECR Repositories

**What is ECR?**
Amazon ECR is a managed container registry that stores, manages, and deploys Docker images. Think of it as "Docker Hub" but private and integrated with AWS services.

#### Option A: AWS Console (Beginner-Friendly)

**Create Repository for Backend API:**

1. Navigate to **Amazon ECR** in the AWS Console
2. In the left sidebar, click **Repositories**
3. Click **Create repository**
4. Configure the repository:
   - **Visibility settings**: Private
   - **Repository name**: `housing-api`
   - **Tag immutability**: Disabled (default)
   - **Scan on push**: ✅ Enable
   - **KMS encryption**: Disabled (uses AES-256 by default)
5. Click **Create repository**

**Create Repository for Streamlit UI:**

Repeat the above steps with these changes:
- **Repository name**: `housing-streamlit`

**💡 Console Tip**: After creation, note the repository URI displayed (e.g., `123456789.dkr.ecr.us-east-1.amazonaws.com/housing-api`). You'll need this later.

---

#### Option B: AWS CLI (Advanced)

```bash
# Create repository for backend API
aws ecr create-repository 
    --repository-name housing-api 
    --region $AWS_REGION 
    --image-scanning-configuration scanOnPush=true 
    --encryption-configuration encryptionType=AES256

# Create repository for Streamlit UI
aws ecr create-repository
    --repository-name housing-streamlit
    --region $AWS_REGION
    --image-scanning-configuration scanOnPush=true
    --encryption-configuration encryptionType=AES256
```

**🔍 Command Breakdown**:
- `--repository-name`: Unique name for your repository
- `--image-scanning-configuration`: Automatically scans images for vulnerabilities
- `--encryption-configuration`: Encrypts images at rest using AES256

---

### ✅ Verify ECR Repositories

#### AWS Console
1. Go to **ECR** → **Repositories**
2. Verify both `housing-api` and `housing-streamlit` are listed
3. Check that **Scan on push** shows "Enabled"

#### AWS CLI

**PowerShell:**
```powershell
aws ecr describe-repositories --region $env:AWS_REGION
```

**Linux/Mac/WSL:**
```bash
# List all repositories
aws ecr describe-repositories --region $AWS_REGION

# Expected output: JSON with both repositories
```

You should see both `housing-api` and `housing-streamlit` repositories.

---

## Part 4: Build and Push Docker Images

### 🔐 Step 1: Authenticate Docker to ECR

**Windows PowerShell:**
```powershell
# Get login password and authenticate
aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
```

**Linux/Mac/WSL:**
```bash
# Get login password and authenticate
aws ecr get-login-password --region $AWS_REGION |
    docker login --username AWS --password-stdin
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

**📚 What's Happening?**
- `get-login-password`: Generates a temporary authentication token
- `docker login`: Authenticates Docker CLI with ECR
- Token is valid for 12 hours

### 🏗️ Step 2: Build Docker Images

```bash
# Build backend API image
docker build -t housing-api:latest -f Dockerfile .

# Build Streamlit UI image
docker build -t housing-streamlit:latest -f Dockerfile.streamlit .

# Verify builds
docker images | grep housing
```

**⏱️ Expected Build Time**: 3-10 minutes per image (depending on your machine)

### 🏷️ Step 3: Tag Images for ECR

**Windows PowerShell:**
```powershell
# Tag backend image
docker tag housing-api:latest "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/housing-api:latest"

# Tag UI image
docker tag housing-streamlit:latest "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/housing-streamlit:latest"
```

**Linux/Mac/WSL:**
```bash
# Tag backend image
docker tag housing-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-api:latest

# Tag UI image
docker tag housing-streamlit:latest 
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-streamlit:latest
```

**🎓 Understanding Tags**:
- Tags identify specific versions of images
- `latest`: Convention for most recent version
- ECR images require full registry path in tag

### ⬆️ Step 4: Push Images to ECR

**Windows PowerShell:**
```powershell
# Build image names as variables first (workaround for PowerShell/Docker issue)
$apiImageName = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/housing-api:latest"
$uiImageName = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/housing-streamlit:latest"

# Push backend image
docker push $apiImageName

# Push UI image
docker push $uiImageName
```

**Linux/Mac/WSL:**
```bash
# Push backend image
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-api:latest

# Push UI image

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-streamlit:latest
```

# Push UI image
```
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-streamlit:latest
```

**⏱️ Expected Push Time**: 2-10 minutes per image (depending on internet speed)

### ✅ Step 5: Verify Images in ECR

**PowerShell:**
```powershell
# List images in backend repository
aws ecr list-images --repository-name housing-api --region $env:AWS_REGION

# List images in UI repository
aws ecr list-images --repository-name housing-streamlit --region $env:AWS_REGION

# Get image details (including size and digest)
aws ecr describe-images --repository-name housing-api --region $env:AWS_REGION
```

**Linux/Mac/WSL:**
```bash
# List images in backend repository
aws ecr list-images --repository-name housing-api --region $AWS_REGION

# List images in UI repository
aws ecr list-images --repository-name housing-streamlit --region $AWS_REGION

# Get image details (including size and digest)
aws ecr describe-images --repository-name housing-api --region $AWS_REGION
```

**Expected Output**: JSON showing image tags, digests, and metadata.

---

**:warning: 📝 Note for the Rest of the Lab:**

From this point forward, most commands will be shown in **bash syntax** (using `$VARIABLE_NAME`). 

**If you're using PowerShell**, remember to:
1. Replace `$VARIABLE_NAME` with `$env:VARIABLE_NAME`
2. Remove backslashes `\` at line ends (PowerShell doesn't need them)
3. When setting variables with command output, use: `$env:VAR = (command)` instead of `export VAR=$(command)`

**Example conversion:**
```bash
# Bash
export API_ALB_DNS=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[0].DNSName' --output text)
```
```powershell
# PowerShell
$env:API_ALB_DNS = (aws elbv2 describe-load-balancers --query 'LoadBalancers[0].DNSName' --output text)
```

For read-only commands (like `aws ecr describe-repositories`), you can usually copy them as-is to PowerShell.

---

## Part 5: IAM Roles and Permissions

### 🔑 Understanding IAM Roles for ECS

**Two Required Roles**:

1. **Task Execution Role** (`ecsTaskExecutionRole`)
   - Used by ECS agent to pull images and write logs
   - Required permissions: ECR pull, CloudWatch logs write

2. **Task Role** (`ecs_s3_access`)
   - Used by your application code
   - Required permissions: S3 read (for model/data access)

### 📋 Step 1: Create Task Execution Role

#### Option A: AWS Console (Beginner-Friendly)

1. Navigate to **IAM** in the AWS Console
2. In the left sidebar, click **Roles**
3. Click **Create role**
4. **Select trusted entity**:
   - **Trusted entity type**: AWS service
   - **Use case**: Elastic Container Service → **Elastic Container Service Task**
5. Click **Next**
6. **Add permissions**:
   - Search for and select: `AmazonECSTaskExecutionRolePolicy`
   - ✅ Check the box next to it
7. Click **Next**
8. **Name, review, and create**:
   - **Role name**: `ecsTaskExecutionRole`
   - **Description**: "Allows ECS tasks to call AWS services on your behalf"
9. Click **Create role**

**💡 Console Tip**: The `AmazonECSTaskExecutionRolePolicy` allows ECS to pull images from ECR and write logs to CloudWatch.

---

#### Option B: AWS CLI (Advanced)

```bash
# Create trust policy document
cat > ecs-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://ecs-trust-policy.json

# Attach AWS managed policy for ECS task execution
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

**🔍 Trust Policy Explained**:
- Allows ECS service to "assume" this role
- Without this, ECS cannot act on your behalf

### 📋 Step 2: Create Task Role (S3 Access)

#### Option A: AWS Console (Beginner-Friendly)

1. In **IAM** → **Roles**, click **Create role**
2. **Select trusted entity**:
   - **Trusted entity type**: AWS service
   - **Use case**: Elastic Container Service → **Elastic Container Service Task**
3. Click **Next**
4. **Add permissions**: Skip for now (we'll add inline policy next)
5. Click **Next**
6. **Name, review, and create**:
   - **Role name**: `ecs_s3_access`
   - **Description**: "Allows ECS tasks to access S3 buckets for model and data"
7. Click **Create role**

**Add S3 Access Policy:**

8. Find and click on the newly created `ecs_s3_access` role
9. Under **Permissions** tab, click **Add permissions** → **Create inline policy**
10. Click the **JSON** tab
11. Paste the following policy:

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
        "arn:aws:s3:::housing-regression-lab",
        "arn:aws:s3:::housing-regression-lab/*"
      ]
    }
  ]
}
```

12. Click **Review policy**
13. **Policy name**: `S3AccessPolicy`
14. Click **Create policy**

**⚠️ Important**: Update `housing-regression-lab` to match your actual S3 bucket name!

---

#### Option B: AWS CLI (Advanced)

```bash
# Create S3 access policy
cat > s3-access-policy.json << 'EOF'
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
        "arn:aws:s3:::housing-regression-lab",
        "arn:aws:s3:::housing-regression-lab/*"
      ]
    }
  ]
}
EOF

# Create the role
aws iam create-role \
    --role-name ecs_s3_access \
    --assume-role-policy-document file://ecs-trust-policy.json

# Create and attach the policy
aws iam put-role-policy \
    --role-name ecs_s3_access \
    --policy-name S3AccessPolicy \
    --policy-document file://s3-access-policy.json
```

**⚠️ Important**: Update `housing-regression-lab` to match your S3 bucket name!

### ✅ Step 3: Verify Roles

#### AWS Console
1. Go to **IAM** → **Roles**
2. Search for `ecsTaskExecutionRole` and `ecs_s3_access`
3. Click each role to verify:
   - **Trust relationships** shows `ecs-tasks.amazonaws.com`
   - **Permissions** tab shows attached policies

#### AWS CLI
```bash
# List roles
aws iam list-roles | grep -E "ecsTaskExecutionRole|ecs_s3_access"

# Get specific role details
aws iam get-role --role-name ecsTaskExecutionRole
aws iam get-role --role-name ecs_s3_access
```

---

## Part 6: ECS Cluster Setup

### 🎯 What is an ECS Cluster?

An **ECS Cluster** is a logical grouping of tasks or services. Think of it as a "virtual data center" where your containers run.

**Key Concepts**:
- **Task**: A single running instance of your container
- **Service**: Manages running a specified number of tasks continuously
- **Cluster**: Groups services and tasks together

### Prerequisites: Create ECS Service-Linked Role

**⚠️ Important First Step**: Before creating a cluster, ensure the ECS service-linked role exists. This role allows ECS to manage resources on your behalf.

#### Check if the role exists:

**PowerShell:**
```powershell
aws iam get-role --role-name AWSServiceRoleForECS
```

**Linux/Mac/WSL:**
```bash
aws iam get-role --role-name AWSServiceRoleForECS
```

If you get an error "NoSuchEntity", create the role:

**PowerShell/Linux/Mac/WSL (same command):**
```bash
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com
```

**Expected output**: JSON confirming role creation, or a message saying it already exists.

**💡 Tip**: This role is automatically created when you first use ECS in the AWS Console, but CLI users must create it manually.

---

### 🚀 Create ECS Cluster

#### Option A: AWS Console (Beginner-Friendly)

1. Navigate to **Amazon ECS** in the AWS Console
2. In the left sidebar, click **Clusters**
3. Click **Create cluster**
4. **Cluster configuration**:
   - **Cluster name**: `housing-ml-cluster`
   - **Namespace** (optional): Leave empty or use `housing-ml`
5. **Infrastructure**:
   - **AWS Fargate only (serverless)**: ✅ Keep checked
   - Do NOT select EC2 instances
6. **Monitoring** (optional):
   - **Use Container Insights**: ✅ Enable (helps with monitoring, but adds cost)
7. **Tags** (optional): Add if needed for cost tracking
8. Click **Create**

**💡 Console Tip**: Container Insights provides detailed metrics but costs ~$0.30/month per task. For a lab, you can disable it to save costs.

---

#### Option B: AWS CLI (Advanced)

```bash
# Create Fargate cluster
aws ecs create-cluster \
    --cluster-name housing-ml-cluster \
    --region $AWS_REGION \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy \
        capacityProvider=FARGATE,weight=1,base=1 \
        capacityProvider=FARGATE_SPOT,weight=4

# Alternative: Simple cluster without spot instances
# aws ecs create-cluster --cluster-name housing-ml-cluster --region $AWS_REGION
```

**🔍 Capacity Provider Strategies**:
- **FARGATE**: Standard, always-available compute
- **FARGATE_SPOT**: Up to 70% cheaper, can be interrupted
- **Weight**: Distributes tasks (4:1 ratio favors Spot)
- **Base**: Minimum number of tasks on standard Fargate

---

### ✅ Verify Cluster

#### AWS Console
1. Go to **ECS** → **Clusters**
2. Verify `housing-ml-cluster` appears with status **Active**
3. Click on the cluster name to see details

#### AWS CLI
```bash
# Describe cluster
aws ecs describe-clusters \
    --clusters housing-ml-cluster \
    --region $AWS_REGION

# Expected output: Status should be "ACTIVE"
```

---

## Part 7: Network Configuration (VPC, Security Groups)

### 🌐 Understanding AWS Networking

**Virtual Private Cloud (VPC)**:
- Isolated network in AWS cloud
- Contains subnets, route tables, internet gateways
- Required for Fargate tasks

**Security Groups**:
- Virtual firewalls controlling inbound/outbound traffic
- Stateful: Return traffic automatically allowed

### 📍 Step 1: Get Housing ML VPC and Subnets
:warning: If you have not created a VPC with two subnets yet, go to **Part 1** on the ["phase-2 LAB"](/phase-2/README.md) lab.

#### Option A: AWS Console (Beginner-Friendly)

**Identify Housing ML VPC:**

1. Navigate to **VPC** in the AWS Console
2. In the left sidebar, click **Your VPCs**
3. Find the VPC with **Housing ML VPC** = **Yes**
4. **Note the VPC ID** (e.g., `vpc-12345abcd`) - you'll need this

**Identify Subnets:**

1. In the left sidebar, click **Subnets**
2. Filter by your  Housing ML ID
3. **Note at least 2 Subnet IDs** in **different Availability Zones**:
   - Example: `subnet-abc123` (us-east-1a) and `subnet-def456` (us-east-1b)
4. Write these down - needed for Load Balancer creation

**💡 Console Tip**: Load Balancers require subnets in at least 2 different Availability Zones for high availability.

---

#### Option B: AWS CLI (Advanced)

```bash
# Get default VPC ID
export VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" \
    --output text \
    --region $AWS_REGION)

echo "VPC ID: $VPC_ID"

# Get subnet IDs (need at least 2 for ALB)
aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "Subnets[*].[SubnetId,AvailabilityZone]" \
    --output table \
    --region $AWS_REGION

# Save subnet IDs
export SUBNET_1=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "Subnets[0].SubnetId" \
    --output text \
    --region $AWS_REGION)

export SUBNET_2=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "Subnets[1].SubnetId" \
    --output text \
    --region $AWS_REGION)

echo "Subnet 1: $SUBNET_1"
echo "Subnet 2: $SUBNET_2"
```

**🎓 Why Multiple Subnets?**
- High availability: Services run across multiple availability zones
- Load balancers require at least 2 subnets in different AZs

---

### 🔒 Step 2: Create Security Groups

We need to create 3 security groups for our application:
1. **API Security Group** - Controls access to FastAPI backend (port 8000)
2. **UI Security Group** - Controls access to Streamlit UI (port 8501)
3. **ALB Security Group** - Controls access to Load Balancers (ports 80, 443)

#### Option A: AWS Console (Beginner-Friendly)

**Create API Security Group:**

1. Navigate to **EC2** → **Security Groups** (under Network & Security)
2. Click **Create security group**
3. Configure:
   - **Security group name**: `housing-api-sg`
   - **Description**: `Security group for Housing API`
   - **VPC**: Select your Housing ML VPC
4. **Inbound rules** - Click **Add rule**:
   - **Type**: Custom TCP
   - **Port range**: 8000
   - **Source**: Anywhere-IPv4 (`0.0.0.0/0`)
   - **Description**: `API port`
5. **Outbound rules**: Leave default (All traffic)
6. Click **Create security group**

**Create UI Security Group:**

Repeat steps 1-6 with these changes:
- **Security group name**: `housing-ui-sg`
- **Description**: `Security group for Housing Streamlit UI`
- **Port range**: 8501
- **Description**: `Streamlit UI port`

**Create ALB Security Group:**

Repeat steps 1-6 with these changes:
- **Security group name**: `housing-alb-sg`
- **Description**: `Security group for Housing ALB`
- Add **two** inbound rules:
  - Rule 1: **Type** = HTTP, **Port** = 80, **Source** = `0.0.0.0/0`
  - Rule 2: **Type** = HTTPS, **Port** = 443, **Source** = `0.0.0.0/0` (optional)

**Update Security Groups for Inter-Service Communication:**

After creating all three security groups:

1. Go back to **Security Groups** and select `housing-api-sg`
2. **Inbound rules** tab → **Edit inbound rules** → **Add rule**:
   - **Type**: Custom TCP
   - **Port range**: 8000
   - **Source**: Custom → Select `housing-alb-sg` (type "housing" to search)
   - **Description**: `Allow ALB to API`
3. **Save rules**

4. Select `housing-ui-sg`
5. **Inbound rules** tab → **Edit inbound rules** → **Add rule**:
   - **Type**: Custom TCP
   - **Port range**: 8501
   - **Source**: Custom → Select `housing-alb-sg`
   - **Description**: `Allow ALB to UI`
6. **Save rules**

7. Go back to `housing-api-sg`
8. **Inbound rules** tab → **Edit inbound rules** → **Add rule**:
   - **Type**: Custom TCP
   - **Port range**: 8000
   - **Source**: Custom → Select `housing-ui-sg`
   - **Description**: `Allow UI to API`
9. **Save rules**

**💡 Console Tip**: Using security groups as sources (instead of IP addresses) automatically allows communication between services, even if IPs change.

---

#### Option B: AWS CLI (Advanced)

**Create API Security Group:**

```bash
# Create security group for backend API
export API_SG_ID=$(aws ec2 create-security-group \
    --group-name housing-api-sg \
    --description "Security group for Housing API" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' \
    --output text)

echo "API Security Group ID: $API_SG_ID"

# Allow inbound traffic on port 8000
aws ec2 authorize-security-group-ingress \
    --group-id $API_SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

# Allow all outbound traffic (default, but explicit)
aws ec2 authorize-security-group-egress \
    --group-id $API_SG_ID \
    --protocol all \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION 2>/dev/null || true
```

**Create UI Security Group:**

```bash
# Create security group for Streamlit UI
export UI_SG_ID=$(aws ec2 create-security-group \
    --group-name housing-ui-sg \
    --description "Security group for Housing Streamlit UI" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' \
    --output text)

echo "UI Security Group ID: $UI_SG_ID"

# Allow inbound traffic on port 8501
aws ec2 authorize-security-group-ingress \
    --group-id $UI_SG_ID \
    --protocol tcp \
    --port 8501 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

# Allow outbound traffic
aws ec2 authorize-security-group-egress \
    --group-id $UI_SG_ID \
    --protocol all \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION 2>/dev/null || true
```

**Create ALB Security Group:**

```bash
# Create security group for ALB
export ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name housing-alb-sg \
    --description "Security group for Housing ALB" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' \
    --output text)

echo "ALB Security Group ID: $ALB_SG_ID"

# Allow HTTP traffic (port 80) from internet
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

# Optional: Allow HTTPS (port 443)
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION 2>/dev/null || true
```

**Update Security Groups for Inter-Service Communication:**

```bash
# Allow ALB to reach API tasks
aws ec2 authorize-security-group-ingress \
    --group-id $API_SG_ID \
    --protocol tcp \
    --port 8000 \
    --source-group $ALB_SG_ID \
    --region $AWS_REGION

# Allow ALB to reach UI tasks
aws ec2 authorize-security-group-ingress \
    --group-id $UI_SG_ID \
    --protocol tcp \
    --port 8501 \
    --source-group $ALB_SG_ID \
    --region $AWS_REGION

# Allow UI to reach API (for internal communication)
aws ec2 authorize-security-group-ingress \
    --group-id $API_SG_ID \
    --protocol tcp \
    --port 8000 \
    --source-group $UI_SG_ID \
    --region $AWS_REGION
```

**🔍 CIDR Notation**:
- `0.0.0.0/0`: Allows traffic from any IP address (public internet)
- For production, restrict to specific IP ranges or security groups

---

### ✅ Verify Security Groups

#### AWS Console
1. Go to **EC2** → **Security Groups**
2. Search for "housing" to find all three groups
3. Click each one to verify:
   - **Inbound rules** match expected ports
   - **Outbound rules** allow all traffic
   - **VPC** matches your Housing ML VPC

#### AWS CLI

```bash
# List security groups
aws ec2 describe-security-groups \
    --group-ids $API_SG_ID $UI_SG_ID $ALB_SG_ID \
    --region $AWS_REGION \
    --query "SecurityGroups[*].[GroupId,GroupName,Description]" \
    --output table
```

---

## Part 8: CloudWatch Logs Setup

### 📊 What are CloudWatch Logs?

**CloudWatch Logs** collect, monitor, and analyze logs from your applications. Essential for:
- Debugging container issues
- Monitoring application health
- Tracking errors and performance

### 📝 Create Log Groups

#### Option A: AWS Console (Beginner-Friendly)

**Create Log Group for API:**

1. Navigate to **CloudWatch** in the AWS Console
2. In the left sidebar, expand **Logs** and click **Log management**
3. Click **Create log group**
4. **Log group name**: `/ecs/housing-api-task-ecs`
5. **Retention setting**: Select **1 week** (to save costs)
6. **KMS key**: Leave as default (no encryption)
7. Click **Create**

**Create Log Group for UI:**

Repeat the above steps with:
- **Log group name**: `/ecs/housing-streamlit`
- **Retention setting**: **1 week**

**💡 Console Tip**: The `/ecs/` prefix is a naming convention for ECS-related logs. The retention setting automatically deletes logs older than the specified period.

---

#### Option B: AWS CLI (Advanced)

```bash
# Create log group for API
aws logs create-log-group \
    --log-group-name /ecs/housing-api-task-ecs \
    --region $AWS_REGION

# Create log group for UI
aws logs create-log-group \
    --log-group-name /ecs/housing-streamlit \
    --region $AWS_REGION

# Set retention period (optional, saves costs)
aws logs put-retention-policy \
    --log-group-name /ecs/housing-api-task-ecs \
    --retention-in-days 7 \
    --region $AWS_REGION

aws logs put-retention-policy \
    --log-group-name /ecs/housing-streamlit \
    --retention-in-days 7 \
    --region $AWS_REGION
```

**🎓 Retention Policies**:
- Default: Logs kept forever (costs accumulate)
- 7 days: Good for labs/testing
- Production: 30-90 days typical

---

### ✅ Verify Log Groups

#### AWS Console
1. Go to **CloudWatch** → **Logs** → **Log groups**
2. Verify both `/ecs/housing-api-task-ecs` and `/ecs/housing-streamlit` are listed
3. Check **Retention** column shows "1 week"

#### AWS CLI
```bash
# List log groups
aws logs describe-log-groups \
    --log-group-name-prefix /ecs/housing \
    --region $AWS_REGION
```

---

## Part 9: Deploy FastAPI Backend to Fargate

### 📄 Step 1: Create Task Definition

#### AWS Console (Beginner-Friendly)

1. Navigate to **Amazon ECS** in AWS Console
2. In the left sidebar, click **Task Definitions**
3. Click **Create new task definition** → **Create new task definition with JSON**
4. Clear the default JSON and paste the following (replace `YOUR_ACCOUNT_ID` and `YOUR_REGION` with your actual values):

**Task Definition JSON**:

```json
{
  "family": "housing-api-task-ecs",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecs_s3_access",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "3072",
  "containerDefinitions": [
    {
      "name": "housing-api",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/housing-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "S3_BUCKET",
          "value": "housing-regression-lab"
        },
        {
          "name": "AWS_REGION",
          "value": "YOUR_REGION"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/housing-api-task-ecs",
          "awslogs-region": "YOUR_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**🔍 Task Definition Components**:
- **family**: Logical name for task versions
- **cpu/memory**: Resources allocated (1 vCPU = 1024, min 3GB for ML model)
- **networkMode**: `awsvpc` gives each task its own ENI (network interface)
- **requiresCompatibilities**: FARGATE for serverless

**💡 CPU/Memory Combinations** (Fargate restrictions):
- 1024 CPU (1 vCPU): 2GB - 8GB memory
- 2048 CPU (2 vCPU): 4GB - 16GB memory
- 4096 CPU (4 vCPU): 8GB - 30GB memory

5. Make sure to replace:
   - `YOUR_ACCOUNT_ID` with your AWS account ID
   - `YOUR_REGION` with your AWS region (e.g., `us-east-1`)
   - Verify the `executionRoleArn` uses your `ecsTaskExecutionRole` ARN
   - Verify the `taskRoleArn` uses your `ecs_s3_access` ARN

6. Click **Create**

**Expected Result**: Task definition `housing-api-task-ecs:1` is created successfully.

#### AWS CLI (Advanced)

Create a file `task-def-api.json` with the same JSON content as above.

### 🔧 Step 2: Update Task Definition with Your Values

#### AWS Console

If you already created it via console, skip to Step 3.

#### AWS CLI

```bash
# Replace placeholders automatically
sed -i "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-def-api.json
sed -i "s/YOUR_REGION/$AWS_REGION/g" task-def-api.json

# Or manually edit the file with your favorite editor
```

### 📤 Step 3: Verify Task Definition

#### AWS Console

1. Navigate to **ECS** → **Task Definitions**
2. Click on **housing-api-task-ecs**
3. Verify the task definition shows:
   - **Status**: ACTIVE
   - **Revision**: 1
   - **CPU**: 1024 (1 vCPU)
   - **Memory**: 3072 (3 GB)
   - **Container**: housing-api with port 8000

#### AWS CLI

```bash
# Register the task definition
aws ecs register-task-definition \
    --cli-input-json file://task-def-api.json \
    --region $AWS_REGION

# Verify registration
aws ecs describe-task-definition \
    --task-definition housing-api-task-ecs \
    --region $AWS_REGION
```

---

## Part 10: Load Balancer Configuration

### 🌐 Understanding Load Balancers

**Application Load Balancer (ALB)**:
- Distributes traffic across multiple tasks
- Provides health checks (removes unhealthy tasks from rotation)
- Gives you a stable DNS endpoint
- Handles SSL/TLS termination (if configured)

### 🎯 Step 1: Create Target Group for API

#### AWS Console (Beginner-Friendly)

1. Navigate to **EC2** → **Target Groups** (under Load Balancing in left sidebar)
2. Click **Create target group**
3. Configure target group:
   - **Choose a target type**: IP addresses

4. **Basic configuration**:
   - **Target group name**: `housing-api-tg`
   - **Protocol**: HTTP
   - **Port**: 80
   - **VPC**: Select your `housing-ml-vpc`
   - **Protocol version**: HTTP1

5. **Health checks**:
   - **Health check protocol**: HTTP
   - **Health check path**: `/health`
   - **Advanced health check settings**:
     - **Healthy threshold**: 2
     - **Unhealthy threshold**: 3
     - **Timeout**: 5 seconds
     - **Interval**: 30 seconds
     - **Success codes**: 200

6. Click **Next**
7. Skip registering targets (Fargate will auto-register)
8. Click **Create target group**

**Expected Result**: Target group `housing-api-tg` created successfully.

**📝 Note**: Copy the **Target group ARN** - you'll need it later!

:warning: **Repeat 1-8 to also create Target Group for the Streamlit UI**:
- **Choose a target type**: IP addresses
- **Target group name**: `housing-ui-tg`
- **Port**: 80
- **VPC**: Select your `housing-ml-vpc`
- **Health check path**: `/health`
     - **Healthy threshold**: 2
     - **Unhealthy threshold**: 3

#### AWS CLI (Advanced)

```bash
# Create target group
export API_TG_ARN=$(aws elbv2 create-target-group \
    --name housing-api-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-enabled \
    --health-check-protocol HTTP \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --region $AWS_REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

echo "API Target Group ARN: $API_TG_ARN"
```

**🔍 Health Check Parameters**:
- **path**: `/health` endpoint in your API
- **interval**: Check every 30 seconds
- **timeout**: Wait 5 seconds for response
- **healthy-threshold**: 2 consecutive successes = healthy
- **unhealthy-threshold**: 3 consecutive failures = unhealthy

### 🎯 Step 2: Create Application Load Balancer for API

#### AWS Console (Beginner-Friendly)

1. Navigate to **EC2** → **Load Balancers** (under Load Balancing)
2. Click **Create load balancer**
3. Select **Application Load Balancer** → Click **Create**

4. **Basic configuration**:
   - **Load balancer name**: `housing-api-alb`
   - **Scheme**: Internet-facing
   - **IP address type**: IPv4

5. **Network mapping**:
   - **VPC**: Select your `housing-ml-vpc`
   - **Mappings**: Select at least 2 availability zones
     - Check boxes for 2 AZs if you want high availability. If not you can just select one.
     - For each, select the public subnet

6. **Security groups**:
   - Remove the default security group
   - Select your `housing-alb-sg` (the one allowing port 80/443 from internet)

7. **Listeners and routing**:
   - **Protocol**: HTTP
   - **Port**: 80
   - **Default action**: Forward to `housing-api-tg` 
   - **Security groups**: 
    - Select your `housing-alb-sg`
8. Review settings and click **Create load balancer**
9. Click **View load balancer**

**Expected Result**: Load balancer status shows "Provisioning" then "Active" (takes 2-3 minutes).

**📝 Important**: Copy the **DNS name** (e.g., `housing-api-alb-1234567890.us-east-1.elb.amazonaws.com`) - you'll need this for the UI!

:warning: **Repeat steps 1-9 to create an ALB for the Streamlit UI**
- **Load balancer name**: `housing-ui-alb`
- **Security groups**: `housing-ui-sg`
- **Target group**: `housing-ui-tg` 

#### AWS CLI (Advanced)

```bash
# Create ALB
export API_ALB_ARN=$(aws elbv2 create-load-balancer \
    --name housing-api-alb \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $ALB_SG_ID \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

echo "API ALB ARN: $API_ALB_ARN"

# Get ALB DNS name
export API_ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $API_ALB_ARN \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "API ALB DNS: $API_ALB_DNS"
```

**📝 Important**: Save the `API_ALB_DNS` value! You'll need it for the UI configuration.

### 🔗 Step 3: Verify Listener Configuration

#### AWS Console

The listener was automatically created when you set up the load balancer routing in Step 2. To verify:

1. Navigate to **EC2** → **Load Balancers**
2. Select `housing-api-alb`
3. Click the **Listeners and rules** tab
4. Verify you see:
   - **Protocol**: HTTP
   - **Port**: 80
   - **Default action**: Forward to `housing-api-tg`

**Expected Result**: Listener is configured and active.

#### AWS CLI

```bash
# Create listener (routes traffic from ALB to target group)
aws elbv2 create-listener \
    --load-balancer-arn $API_ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$API_TG_ARN \
    --region $AWS_REGION
```

**🔍 Listener Explained**:
- Listens on port 80 (HTTP)
- Forwards all traffic to the target group
- Target group routes to healthy Fargate tasks

### 🚀 Step 4: Create ECS Service for API

#### AWS Console (Beginner-Friendly)

1. Navigate to **Amazon ECS** → **Clusters**
2. Click on your cluster `housing-ml-cluster`
3. In the **Services** tab, click **Create**


4. **Deployment configuration**:
   - **Application type**: Service
   - **Task definition**:
     - **Family**: housing-api-task-ecs
     - **Revision**: Select latest (should be 1)
   - **Service name**: `housing-api-service`
   - **Desired tasks**: 1

5. **Environment**:
   - **Compute options**: Launch type
   - **Launch type**: FARGATE
   - **Platform version**: LATEST

6. **Networking**:
   - **VPC**: Select `housing-ml-vpc`
   - **Subnets**: Select at least 2 subnets (same ones used for ALB)
   - **Security group**: Select `housing-api-sg` (the one allowing port 8000)
   - **Public IP**: ENABLED (turn on)

7. **Load balancing**:
   - **Load balancer type**: Application Load Balancer
   - **Application Load Balancer**: Select `Use an existing load balancer` and select `housing-api-alb`
   - **Listener**: Selecte `Use an existing listener` and select existing listener (HTTP:80)
   - **Target group**: Selecte `Use an existing target group` and select `housing-api-tg`
   - **Health check grace period**: 60 seconds

8. **Service auto scaling**: Optional (Leave as default for now)

9. Click **Create**

**Expected Result**: Service creation begins. Status shows "Service created successfully".

:warning: **Repeat steps 1-9 to deploy the Streamlit UI service**:
- **Task definition family**: `housing-streamlit`
- **Service name**: `housing-ui-service`
*Networking*:
- **Security group**: Select `housing-ui-sg` (the one allowing port 8501)
*Load Balancing*:
   - **Application Load Balancer**: Select `Use an existing load balancer` and select `housing-ui-alb`
   - **Listener**: Selecte `Use an existing listener` and select existing listener (HTTP:80)
   - **Target group**: Selecte `Use an existing target group` and select `housing-ui-tg`
   
#### AWS CLI (Advanced)

```bash
# Create ECS service
aws ecs create-service \
    --cluster housing-ml-cluster \
    --service-name housing-api-service \
    --task-definition housing-api-task-ecs \
    --desired-count 1 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={
        subnets=[$SUBNET_1,$SUBNET_2],
        securityGroups=[$API_SG_ID],
        assignPublicIp=ENABLED
    }" \
    --load-balancers "targetGroupArn=$API_TG_ARN,containerName=housing-api,containerPort=8000" \
    --health-check-grace-period-seconds 60 \
    --region $AWS_REGION
```

**🔍 Service Configuration**:
- **desired-count**: Number of tasks to run (1 for lab, scale higher for production)
- **assignPublicIp**: ENABLED allows tasks to reach internet (for S3 access)
- **health-check-grace-period**: Time before health checks start (container startup time)

### ⏱️ Step 5: Wait for Service to Stabilize

#### AWS Console

1. In the ECS cluster view, click on the **Services** tab
2. Click on `housing-api-service`
3. Monitor the **Deployments and events** section:
   - Wait for **Status** to show "Steady state" or "Active"
   - **Running count** should equal **Desired count** (both = 1)
   - Look for event: "service housing-api-service has reached a steady state"

4. Click on the **Health and metrics** tab
5. Verify:
   - **Target health**: Should show 1 healthy target
   - May take 2-5 minutes for health checks to pass

**📘 Troubleshooting**: If the service doesn't stabilize:
- Check **Logs** tab for container errors
- Verify security groups allow traffic
- Check task execution role has permissions

#### AWS CLI

```bash
# Wait for service to reach steady state (may take 3-5 minutes)
aws ecs wait services-stable \
    --cluster housing-ml-cluster \
    --services housing-api-service \
    --region $AWS_REGION

echo "✅ API Service is stable!"
```

### ✅ Step 6: Verify API Deployment

#### AWS Console (Beginner-Friendly)

**Check ECS Service**:
1. Navigate to **ECS** → **Clusters** → `housing-ml-cluster`
2. Click **Services** tab → `housing-api-service`
3. Verify:
   - **Status**: Active
   - **Desired tasks**: 1
   - **Running tasks**: 1
   - **Deployment status**: Completed

**Check Load Balancer Health**:
1. Navigate to **EC2** → **Target Groups**
2. Select `housing-api-tg`
3. Click **Targets** tab
4. Verify target status is **healthy**

**Test API Endpoint**:
1. Navigate to **EC2** → **Load Balancers**
2. Select `housing-api-alb`
3. Copy the **DNS name** (e.g., `housing-api-alb-123456.us-east-1.elb.amazonaws.com`)
4. Open a web browser or terminal and test:

```bash
# Test root endpoint (replace with your ALB DNS)
curl http://YOUR_ALB_DNS/
# Expected: {"message":"Housing Regression API is running 🚀"}

# Test health endpoint
curl http://YOUR_ALB_DNS/health
# Expected: {"status":"healthy","model_path":"...","n_features_expected":...}
```


**✅ Success Indicators**:
- Service status is Active
- Running count = Desired count = 1
- Target health is Healthy
- API endpoints return expected responses

#### AWS CLI (Advanced)

```bash
# Check service status
aws ecs describe-services \
    --cluster housing-ml-cluster \
    --services housing-api-service \
    --region $AWS_REGION \
    --query 'services[0].[serviceName,status,runningCount,desiredCount]' \
    --output table

# Check task status
aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --service-name housing-api-service \
    --region $AWS_REGION

# Test the API endpoint
curl http://$API_ALB_DNS/
# Expected: {"message":"Housing Regression API is running 🚀"}

curl http://$API_ALB_DNS/health
# Expected: {"status":"healthy","model_path":"...","n_features_expected":...}
```

---

## Part 11: Deploy Streamlit UI to Fargate

This part follows similar steps to [Part 9: Deploy FastAPI Backend](#part-9-deploy-fastapi-backend-to-fargate), but deploys the Streamlit UI service.

### 📄 Step 1: Create Task Definition for UI

#### AWS Console (Beginner-Friendly)

1. Navigate to **Amazon ECS** in AWS Console
2. In the left sidebar, click **Task Definitions**
3. Click **Create new task definition** → **Create new task definition with JSON**
4. Clear the default JSON and paste the following (replace `YOUR_ACCOUNT_ID`, `YOUR_REGION`, and `YOUR_API_ALB_DNS` with your actual values):

**Task Definition JSON**:

```json
{
  "family": "housing-streamlit",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecs_s3_access",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "housing-streamlit",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/housing-streamlit:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "STREAMLIT_SERVER_PORT",
          "value": "8501"
        },
        {
          "name": "STREAMLIT_SERVER_ADDRESS",
          "value": "0.0.0.0"
        },
        {
          "name": "API_URL",
          "value": "http://YOUR_API_ALB_DNS/predict"
        },
        {
          "name": "S3_BUCKET",
          "value": "housing-regression-lab"
        },
        {
          "name": "AWS_REGION",
          "value": "YOUR_REGION"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/housing-streamlit",
          "awslogs-region": "YOUR_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**🔍 Task Definition Components**:
- **family**: Logical name for task versions (housing-streamlit)
- **cpu/memory**: 512 CPU (0.5 vCPU), 1GB memory (lighter than API since no ML model)
- **networkMode**: `awsvpc` gives each task its own ENI (network interface)
- **requiresCompatibilities**: FARGATE for serverless
- **API_URL**: **Critical** - Points to your FastAPI backend ALB DNS

**💡 Important**: 
- Streamlit needs less resources than the API (no ML model loading)
- The API_URL must point to your **FastAPI ALB DNS** from Part 9
- Health check uses root path `/` instead of `/health`

5. Make sure to replace:
   - `YOUR_ACCOUNT_ID` with your AWS account ID
   - `YOUR_REGION` with your AWS region (e.g., `us-east-1`)
   - `YOUR_API_ALB_DNS` with your **API ALB DNS** from Part 10 (e.g., `housing-api-alb-123456.us-east-1.elb.amazonaws.com`)
   - Verify the `executionRoleArn` uses your `ecsTaskExecutionRole` ARN
   - Verify the `taskRoleArn` uses your `ecs_s3_access` ARN

6. Click **Create**

**Expected Result**: Task definition `housing-streamlit:1` is created successfully.

#### AWS CLI (Advanced)

Create a file `task-def-ui.json` with the same JSON content as above.

### 🔧 Step 2: Update Task Definition with Your Values

#### AWS Console

If you already created it via console, skip to Step 3.

#### AWS CLI

```bash
# Replace placeholders
sed -i "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-def-ui.json
sed -i "s/YOUR_REGION/$AWS_REGION/g" task-def-ui.json
sed -i "s|YOUR_API_ALB_DNS|$API_ALB_DNS|g" task-def-ui.json

# Verify the API_URL is correct (should point to your FastAPI ALB)
grep API_URL task-def-ui.json
```

**🔍 Verify**: The API_URL should show your FastAPI load balancer DNS, not localhost!

### 📤 Step 3: Verify Task Definition

#### AWS Console

1. Navigate to **ECS** → **Task Definitions**
2. Click on **housing-streamlit**
3. Verify the task definition shows:
   - **Status**: ACTIVE
   - **Revision**: 1
   - **CPU**: 512 (0.5 vCPU)
   - **Memory**: 1024 (1 GB)
   - **Container**: housing-streamlit with port 8501
   - **Environment variable API_URL**: Points to your FastAPI ALB

#### AWS CLI

```bash
# Register the task definition
aws ecs register-task-definition \
    --cli-input-json file://task-def-ui.json \
    --region $AWS_REGION

# Verify registration
aws ecs describe-task-definition \
    --task-definition housing-streamlit \
    --region $AWS_REGION
```

---

### 🎯 Step 4: Create Target Group for UI

#### AWS Console (Beginner-Friendly)

1. Navigate to **EC2** → **Target Groups** (under Load Balancing in left sidebar)
2. Click **Create target group**
3. Configure target group:
   - **Choose a target type**: IP addresses
   - Click **Next**

4. **Basic configuration**:
   - **Target group name**: `housing-ui-tg`
   - **Protocol**: HTTP
   - **Port**: 8501
   - **VPC**: Select your `housing-ml-vpc`
   - **Protocol version**: HTTP1

5. **Health checks**:
   - **Health check protocol**: HTTP
   - **Health check path**: `/`  ⚠️ **(Note: Different from API - uses root path)**
   - **Advanced health check settings**:
     - **Healthy threshold**: 2
     - **Unhealthy threshold**: 3
     - **Timeout**: 10 seconds ⚠️ **(Longer than API - Streamlit is slower)**
     - **Interval**: 30 seconds
     - **Success codes**: 200-399 ⚠️ **(Wider range than API)**

6. Click **Next**
7. Skip registering targets (Fargate will auto-register)
8. Click **Create target group**

**Expected Result**: Target group `housing-ui-tg` created successfully.

**📝 Note**: Copy the **Target group ARN** - you'll need it later!

**💡 Key Differences from API Target Group**:
- Health check path is `/` (root) instead of `/health`
- Timeout is 10 seconds (Streamlit takes longer to respond)
- Success codes allow 200-399 range (Streamlit may return 301/302 redirects)

#### AWS CLI (Advanced)

```bash
# Create target group for Streamlit
export UI_TG_ARN=$(aws elbv2 create-target-group \
    --name housing-ui-tg \
    --protocol HTTP \
    --port 8501 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-enabled \
    --health-check-protocol HTTP \
    --health-check-path / \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 10 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --matcher HttpCode=200-399 \
    --region $AWS_REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

echo "UI Target Group ARN: $UI_TG_ARN"
```

---

### 🎯 Step 5: Create Application Load Balancer for UI

#### AWS Console (Beginner-Friendly)

1. Navigate to **EC2** → **Load Balancers** (under Load Balancing)
2. Click **Create load balancer**
3. Select **Application Load Balancer** → Click **Create**

4. **Basic configuration**:
   - **Load balancer name**: `housing-ui-alb`
   - **Scheme**: Internet-facing
   - **IP address type**: IPv4

5. **Network mapping**:
   - **VPC**: Select your `housing-ml-vpc`
   - **Mappings**: Select at least 2 availability zones
     - Check boxes for 2 AZs (same ones used for API ALB)
     - For each, select the public subnet

6. **Security groups**:
   - Remove the default security group
   - Select your `housing-alb-sg` (the one allowing port 80/443 from internet)

7. **Listeners and routing**:
   - **Protocol**: HTTP
   - **Port**: 80
   - **Default action**: Forward to `housing-ui-tg`

8. Review settings and click **Create load balancer**
9. Click **View load balancer**

**Expected Result**: Load balancer status shows "Provisioning" then "Active" (takes 2-3 minutes).

**📝 Important**: Copy the **DNS name** (e.g., `housing-ui-alb-1234567890.us-east-1.elb.amazonaws.com`) - this is your **public UI URL**!

#### AWS CLI (Advanced)

```bash
# Create ALB for Streamlit
export UI_ALB_ARN=$(aws elbv2 create-load-balancer \
    --name housing-ui-alb \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $ALB_SG_ID \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

echo "UI ALB ARN: $UI_ALB_ARN"

# Get ALB DNS name
export UI_ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $UI_ALB_ARN \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "UI ALB DNS: $UI_ALB_DNS"
echo "🌐 Access your UI at: http://$UI_ALB_DNS"
```

---

### 🔗 Step 6: Verify Listener Configuration

#### AWS Console

The listener was automatically created when you set up the load balancer routing in Step 5. To verify:

1. Navigate to **EC2** → **Load Balancers**
2. Select `housing-ui-alb`
3. Click the **Listeners and rules** tab
4. Verify you see:
   - **Protocol**: HTTP
   - **Port**: 80
   - **Default action**: Forward to `housing-ui-tg`

**Expected Result**: Listener is configured and active.

#### AWS CLI

```bash
# Create listener (routes traffic from ALB to target group)
aws elbv2 create-listener \
    --load-balancer-arn $UI_ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$UI_TG_ARN \
    --region $AWS_REGION
```

**🔍 Listener Explained**:
- Listens on port 80 (HTTP)
- Forwards all traffic to the UI target group
- Target group routes to healthy Streamlit Fargate tasks

---

### 🚀 Step 7: Create ECS Service for UI

#### AWS Console (Beginner-Friendly)

1. Navigate to **Amazon ECS** → **Clusters**
2. Click on your cluster `housing-ml-cluster`
3. In the **Services** tab, click **Create**

4. **Environment**:
   - **Compute options**: Launch type
   - **Launch type**: FARGATE
   - **Platform version**: LATEST

5. **Deployment configuration**:
   - **Application type**: Service
   - **Task definition**:
     - **Family**: housing-streamlit
     - **Revision**: Select latest (should be 1)
   - **Service name**: `housing-streamlit-service`
   - **Desired tasks**: 1

6. **Networking**:
   - **VPC**: Select `housing-ml-vpc`
   - **Subnets**: Select at least 2 subnets (same ones used for API service)
   - **Security group**: Select `housing-ui-sg` (the one allowing port 8501)
   - **Public IP**: ENABLED (turn on)

7. **Load balancing**:
   - **Load balancer type**: Application Load Balancer
   - **Application Load Balancer**: Select `housing-ui-alb`
   - **Listener**: Select existing listener (HTTP:80)
   - **Target group**: Select `housing-ui-tg`
   - **Health check grace period**: 90 seconds ⚠️ **(Longer than API - Streamlit is slower to start)**

8. **Service auto scaling**: Optional (Leave as default for now)

9. Click **Create**

**Expected Result**: Service creation begins. Status shows "Service created successfully".

**💡 Note**: The 90-second grace period is important because Streamlit takes longer to initialize than the FastAPI backend.

#### AWS CLI (Advanced)

```bash
# Create ECS service for Streamlit
aws ecs create-service \
    --cluster housing-ml-cluster \
    --service-name housing-streamlit-service \
    --task-definition housing-streamlit \
    --desired-count 1 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={
        subnets=[$SUBNET_1,$SUBNET_2],
        securityGroups=[$UI_SG_ID],
        assignPublicIp=ENABLED
    }" \
    --load-balancers "targetGroupArn=$UI_TG_ARN,containerName=housing-streamlit,containerPort=8501" \
    --health-check-grace-period-seconds 90 \
    --region $AWS_REGION
```

**🔍 Service Configuration**:
- **desired-count**: Number of tasks to run (1 for lab, scale higher for production)
- **assignPublicIp**: ENABLED allows tasks to reach internet (for S3 access and calling API)
- **health-check-grace-period**: 90 seconds (Streamlit startup time is longer than FastAPI)

---

### ⏱️ Step 8: Wait for Service to Stabilize

#### AWS Console

1. In the ECS cluster view, click on the **Services** tab
2. Click on `housing-streamlit-service`
3. Monitor the **Deployments and events** section:
   - Wait for **Status** to show "Steady state" or "Active"
   - **Running count** should equal **Desired count** (both = 1)
   - Look for event: "service housing-streamlit-service has reached a steady state"

4. Click on the **Health and metrics** tab
5. Verify:
   - **Target health**: Should show 1 healthy target
   - May take 3-7 minutes for health checks to pass (longer than API)

**📘 Troubleshooting**: If the service doesn't stabilize:
- Check **Logs** tab for container errors
- Verify API_URL environment variable points to correct FastAPI ALB
- Check security groups allow UI → API traffic
- Verify task execution role has permissions

#### AWS CLI

```bash
# Wait for service to reach steady state (may take 5-7 minutes)
aws ecs wait services-stable \
    --cluster housing-ml-cluster \
    --services housing-streamlit-service \
    --region $AWS_REGION

echo "✅ UI Service is stable!"
```

**💡 Note**: Streamlit service typically takes 2-3 minutes longer than the API service to reach steady state.

---

### ✅ Step 9: Verify UI Deployment

#### AWS Console (Beginner-Friendly)

**Check ECS Service**:
1. Navigate to **ECS** → **Clusters** → `housing-ml-cluster`
2. Click **Services** tab → `housing-streamlit-service`
3. Verify:
   - **Status**: Active
   - **Desired tasks**: 1
   - **Running tasks**: 1
   - **Deployment status**: Completed

**Check Load Balancer Health**:
1. Navigate to **EC2** → **Target Groups**
2. Select `housing-ui-tg`
3. Click **Targets** tab
4. Verify target status is **healthy**

**Test UI Endpoint**:
1. Navigate to **EC2** → **Load Balancers**
2. Select `housing-ui-alb`
3. Copy the **DNS name** (e.g., `housing-ui-alb-123456.us-east-1.elb.amazonaws.com`)
4. **Open in web browser**: `http://YOUR_UI_ALB_DNS`

**✅ Success Indicators**:
- Service status is Active
- Running count = Desired count = 1
- Target health is Healthy
- **Streamlit UI loads in browser with visualizations**
- Can select filters and make predictions
- Predictions successfully call the FastAPI backend

**🎉 If all checks pass**: You've successfully deployed both the FastAPI backend and Streamlit UI to AWS Fargate!

#### AWS CLI (Advanced)

```bash
# Check service status
aws ecs describe-services \
    --cluster housing-ml-cluster \
    --services housing-streamlit-service \
    --region $AWS_REGION \
    --query 'services[0].[serviceName,status,runningCount,desiredCount]' \
    --output table

# Check task status
aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --service-name housing-streamlit-service \
    --region $AWS_REGION

# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $UI_TG_ARN \
    --region $AWS_REGION

# Test the UI endpoint (should return HTML)
curl -s -o /dev/null -w "%{http_code}\n" http://$UI_ALB_DNS/
# Expected: 200

echo ""
echo "🌐 Access your Streamlit UI at: http://$UI_ALB_DNS"
```

**💡 Manual Browser Test**:
Open your browser and navigate to: `http://$UI_ALB_DNS`

You should see:
- Streamlit interface with Housing Prediction title
- Dropdowns for Year, Month, Region filters
- "Show Predictions 🚀" button
- Data visualizations and metrics
- Ability to make predictions that call your FastAPI backend

---

## Part 12: Testing and Verification

### 🧪 Test Suite 1: Container Health

```bash
# 1. Check if containers are running
echo "=== Checking Running Tasks ==="
aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --region $AWS_REGION

# 2. Get detailed task information
echo "=== API Task Details ==="
API_TASK_ARN=$(aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --service-name housing-api-service \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text)

aws ecs describe-tasks \
    --cluster housing-ml-cluster \
    --tasks $API_TASK_ARN \
    --region $AWS_REGION \
    --query 'tasks[0].[lastStatus,healthStatus,containers[0].healthStatus]'

echo "=== UI Task Details ==="
UI_TASK_ARN=$(aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --service-name housing-streamlit-service \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text)

aws ecs describe-tasks \
    --cluster housing-ml-cluster \
    --tasks $UI_TASK_ARN \
    --region $AWS_REGION \
    --query 'tasks[0].[lastStatus,healthStatus,containers[0].healthStatus]'
```

**✅ Expected Results**:
- `lastStatus`: RUNNING
- `healthStatus`: HEALTHY

### 🧪 Test Suite 2: ECR Images

```bash
echo "=== Verifying ECR Images ==="

# Check API image
aws ecr describe-images \
    --repository-name housing-api \
    --region $AWS_REGION \
    --query 'imageDetails[0].[imageTags[0],imageSizeInBytes,imagePushedAt]' \
    --output table

# Check UI image
aws ecr describe-images \
    --repository-name housing-streamlit \
    --region $AWS_REGION \
    --query 'imageDetails[0].[imageTags[0],imageSizeInBytes,imagePushedAt]' \
    --output table
```

**✅ Expected Results**: Both images should show `latest` tag with recent push date.

### 🧪 Test Suite 3: Fargate Services

```bash
echo "=== Checking Fargate Services ==="

# API Service
aws ecs describe-services \
    --cluster housing-ml-cluster \
    --services housing-api-service \
    --region $AWS_REGION \
    --query 'services[0].[serviceName,status,runningCount,desiredCount,deployments[0].status]' \
    --output table

# UI Service
aws ecs describe-services \
    --cluster housing-ml-cluster \
    --services housing-streamlit-service \
    --region $AWS_REGION \
    --query 'services[0].[serviceName,status,runningCount,desiredCount,deployments[0].status]' \
    --output table
```

**✅ Expected Results**:
- Status: ACTIVE
- runningCount = desiredCount
- deployment status: PRIMARY

### 🧪 Test Suite 4: Load Balancer Health

```bash
echo "=== Checking Load Balancer Target Health ==="

# API Target Health
aws elbv2 describe-target-health \
    --target-group-arn $API_TG_ARN \
    --region $AWS_REGION \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
    --output table

# UI Target Health
aws elbv2 describe-target-health \
    --target-group-arn $UI_TG_ARN \
    --region $AWS_REGION \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
    --output table
```

**✅ Expected Results**: State should be `healthy` for all targets.

### 🧪 Test Suite 5: API Endpoint Testing

```bash
echo "=== Testing API Endpoints ==="

# Test root endpoint
echo "Testing root endpoint..."
curl -s http://$API_ALB_DNS/ | jq '.'

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://$API_ALB_DNS/health | jq '.'

# Test prediction endpoint with sample data
echo "Testing prediction endpoint..."
curl -s -X POST http://$API_ALB_DNS/predict \
    -H "Content-Type: application/json" \
    -d '[
        {
            "bedrooms": 3,
            "bathrooms": 2.0,
            "sqft_living": 1500,
            "sqft_lot": 5000,
            "floors": 1,
            "waterfront": 0,
            "view": 0,
            "condition": 3,
            "grade": 7,
            "sqft_above": 1500,
            "sqft_basement": 0,
            "yr_built": 1990,
            "yr_renovated": 0,
            "zipcode": 98001,
            "lat": 47.5,
            "long": -122.0,
            "sqft_living15": 1500,
            "sqft_lot15": 5000
        }
    ]' | jq '.'
```

**✅ Expected Results**:
- Root: `{"message":"Housing Regression API is running 🚀"}`
- Health: `{"status":"healthy",...}`
- Predict: `{"predictions":[...predicted_price...]}`

### 🧪 Test Suite 6: Streamlit UI Access

```bash
echo "=== Testing Streamlit UI ==="
echo "🌐 Open your browser and navigate to:"
echo "   http://$UI_ALB_DNS"
echo ""
echo "Expected behavior:"
echo "  ✅ Page loads with Streamlit interface"
echo "  ✅ Data visualizations appear"
echo "  ✅ Can interact with UI elements"
echo "  ✅ Predictions work when requested"
```

**Manual Testing Checklist**:
1. Open browser to `http://$UI_ALB_DNS`
2. Verify page loads without errors
3. Check that data visualizations render
4. Test making predictions
5. Verify predictions return successfully

### 🧪 Test Suite 7: CloudWatch Logs

```bash
echo "=== Checking CloudWatch Logs ==="

# Get latest log stream for API
echo "API Logs (last 20 lines):"
API_LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name /ecs/housing-api-task-ecs \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --region $AWS_REGION \
    --query 'logStreams[0].logStreamName' \
    --output text)

aws logs get-log-events \
    --log-group-name /ecs/housing-api-task-ecs \
    --log-stream-name "$API_LOG_STREAM" \
    --limit 20 \
    --region $AWS_REGION \
    --query 'events[*].message' \
    --output text

# Get latest log stream for UI
echo "UI Logs (last 20 lines):"
UI_LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name /ecs/housing-streamlit \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --region $AWS_REGION \
    --query 'logStreams[0].logStreamName' \
    --output text)

aws logs get-log-events \
    --log-group-name /ecs/housing-streamlit \
    --log-stream-name "$UI_LOG_STREAM" \
    --limit 20 \
    --region $AWS_REGION \
    --query 'events[*].message' \
    --output text
```

### 🧪 Test Suite 8: End-to-End Integration Test

Create a test script `test_e2e.sh`:

```bash
#!/bin/bash

echo "🧪 Running End-to-End Integration Test..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_passed=0
test_failed=0

# Test 1: API Root Endpoint
echo -n "Test 1: API Root Endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" http://$API_ALB_DNS/)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} (HTTP $response)"
    ((test_failed++))
fi

# Test 2: API Health Endpoint
echo -n "Test 2: API Health Endpoint... "
response=$(curl -s http://$API_ALB_DNS/health | jq -r '.status')
if [ "$response" = "healthy" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} (Status: $response)"
    ((test_failed++))
fi

# Test 3: API Prediction Endpoint
echo -n "Test 3: API Prediction Endpoint... "
response=$(curl -s -X POST http://$API_ALB_DNS/predict \
    -H "Content-Type: application/json" \
    -d '[{"bedrooms":3,"bathrooms":2.0,"sqft_living":1500,"sqft_lot":5000,"floors":1,"waterfront":0,"view":0,"condition":3,"grade":7,"sqft_above":1500,"sqft_basement":0,"yr_built":1990,"yr_renovated":0,"zipcode":98001,"lat":47.5,"long":-122.0,"sqft_living15":1500,"sqft_lot15":5000}]' \
    | jq -r '.predictions[0]')
if [ ! -z "$response" ] && [ "$response" != "null" ]; then
    echo -e "${GREEN}✅ PASSED${NC} (Prediction: $response)"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC}"
    ((test_failed++))
fi

# Test 4: UI Accessibility
echo -n "Test 4: UI Accessibility... "
response=$(curl -s -o /dev/null -w "%{http_code}" http://$UI_ALB_DNS/)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} (HTTP $response)"
    ((test_failed++))
fi

# Test 5: ECS Service Running Count
echo -n "Test 5: ECS Services Running... "
api_running=$(aws ecs describe-services \
    --cluster housing-ml-cluster \
    --services housing-api-service \
    --region $AWS_REGION \
    --query 'services[0].runningCount' \
    --output text)
ui_running=$(aws ecs describe-services \
    --cluster housing-ml-cluster \
    --services housing-streamlit-service \
    --region $AWS_REGION \
    --query 'services[0].runningCount' \
    --output text)
if [ "$api_running" -ge 1 ] && [ "$ui_running" -ge 1 ]; then
    echo -e "${GREEN}✅ PASSED${NC} (API: $api_running, UI: $ui_running)"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} (API: $api_running, UI: $ui_running)"
    ((test_failed++))
fi

# Summary
echo ""
echo "========================================"
echo "Test Summary:"
echo -e "Passed: ${GREEN}$test_passed${NC}"
echo -e "Failed: ${RED}$test_failed${NC}"
echo "========================================"

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Check logs for details.${NC}"
    exit 1
fi
```

Run the test:
```bash
chmod +x test_e2e.sh
./test_e2e.sh
```

---

## Part 13: Monitoring and Troubleshooting

### 📊 View CloudWatch Metrics

```bash
# View CPU utilization for API service
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=housing-api-service Name=ClusterName,Value=housing-ml-cluster \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --region $AWS_REGION

# View memory utilization
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name MemoryUtilization \
    --dimensions Name=ServiceName,Value=housing-api-service Name=ClusterName,Value=housing-ml-cluster \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --region $AWS_REGION
```

### 🔍 Common Issues and Solutions

#### Issue 1: Tasks Keep Restarting
**Symptoms**: Tasks show STOPPED status repeatedly

**Debugging Steps**:
```bash
# Get stopped task ARNs
aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --desired-status STOPPED \
    --region $AWS_REGION

# Describe stopped task to see failure reason
STOPPED_TASK_ARN=$(aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --desired-status STOPPED \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text)

aws ecs describe-tasks \
    --cluster housing-ml-cluster \
    --tasks $STOPPED_TASK_ARN \
    --region $AWS_REGION \
    --query 'tasks[0].[stoppedReason,containers[0].reason]'
```

**Common Causes**:
- Insufficient memory (increase in task definition)
- Image pull errors (check ECR permissions)
- Application crashes (check logs)

#### Issue 2: Cannot Access API/UI
**Symptoms**: Connection timeout or refused

**Debugging Steps**:
```bash
# Check security group rules
aws ec2 describe-security-groups \
    --group-ids $ALB_SG_ID $API_SG_ID $UI_SG_ID \
    --region $AWS_REGION \
    --query 'SecurityGroups[*].[GroupId,GroupName,IpPermissions]' \
    --output json

# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $API_TG_ARN \
    --region $AWS_REGION

# Verify public IP assignment
aws ecs describe-tasks \
    --cluster housing-ml-cluster \
    --tasks $API_TASK_ARN \
    --region $AWS_REGION \
    --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
    --output text
```

**Common Fixes**:
- Add inbound rules to security groups
- Ensure `assignPublicIp=ENABLED`
- Check subnet route table has internet gateway

#### Issue 3: Health Checks Failing
**Symptoms**: Targets show unhealthy in target group

**Debugging Steps**:
```bash
# Check health check configuration
aws elbv2 describe-target-groups \
    --target-group-arns $API_TG_ARN \
    --region $AWS_REGION \
    --query 'TargetGroups[0].[HealthCheckPath,HealthCheckIntervalSeconds,HealthCheckTimeoutSeconds]'

# View application logs
aws logs tail /ecs/housing-api-task-ecs --follow --region $AWS_REGION
```

**Common Fixes**:
- Verify health check path exists (`/health`)
- Increase timeout or grace period
- Check application is binding to `0.0.0.0` not `localhost`

#### Issue 4: Streamlit Cannot Reach API
**Symptoms**: UI loads but predictions fail

**Debugging Steps**:
```bash
# Verify API_URL environment variable
aws ecs describe-task-definition \
    --task-definition housing-streamlit \
    --region $AWS_REGION \
    --query 'taskDefinition.containerDefinitions[0].environment[?name==`API_URL`].value'

# Test API from UI task
UI_TASK_ID=$(aws ecs list-tasks \
    --cluster housing-ml-cluster \
    --service-name housing-streamlit-service \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text | awk -F/ '{print $NF}')

# Use ECS Exec to run commands in container (requires enableExecuteCommand)
# aws ecs execute-command \
#     --cluster housing-ml-cluster \
#     --task $UI_TASK_ID \
#     --container housing-streamlit \
#     --interactive \
#     --command "curl http://$API_ALB_DNS/health"
```

**Common Fixes**:
- Update API_URL in task definition
- Redeploy UI service after updating
- Check security group allows UI → API traffic

### 📝 View Detailed Logs

```bash
# Stream API logs in real-time
aws logs tail /ecs/housing-api-task-ecs --follow --region $AWS_REGION

# Stream UI logs in real-time
aws logs tail /ecs/housing-streamlit --follow --region $AWS_REGION

# Filter logs for errors
aws logs filter-log-events \
    --log-group-name /ecs/housing-api-task-ecs \
    --filter-pattern "ERROR" \
    --region $AWS_REGION
```

### 🔄 Force New Deployment

```bash
# Useful for pulling updated images
aws ecs update-service \
    --cluster housing-ml-cluster \
    --service housing-api-service \
    --force-new-deployment \
    --region $AWS_REGION

aws ecs update-service \
    --cluster housing-ml-cluster \
    --service housing-streamlit-service \
    --force-new-deployment \
    --region $AWS_REGION
```

---

## Part 14: Cleanup

### 🧹 Important: Cleanup to Avoid Charges

:warning: **Always cleanup resources when done with the lab to avoid unexpected AWS charges!**

Follow these steps **in order** to ensure all dependencies are removed properly.

---

### Step 1: Delete ECS Services

#### AWS Console (Beginner-Friendly)

1. Navigate to **Amazon ECS** → **Clusters**
2. Click on `housing-ml-cluster`
3. Click the **Services** tab

**Delete API Service**:
1. Select `housing-api-service` (check the box)
2. Click **Delete**
3. Type `delete` to confirm
4. Click **Delete**

**Delete UI Service**:
1. Select `housing-streamlit-service` (check the box)
2. Click **Delete**
3. Type `delete` to confirm
4. Click **Delete**

**Wait**: Services will drain connections and stop tasks (~1-2 minutes). You'll see status change to "DRAINING" then disappear.

#### AWS CLI (Advanced)

```bash
echo "🧹 Step 1: Deleting ECS services..."

# Delete API service
aws ecs delete-service \
    --cluster housing-ml-cluster \
    --service housing-api-service \
    --force \
    --region $AWS_REGION

# Delete UI service
aws ecs delete-service \
    --cluster housing-ml-cluster \
    --service housing-streamlit-service \
    --force \
    --region $AWS_REGION

# Wait for services to be deleted
echo "Waiting for services to be deleted..."
sleep 30
```

---

### Step 2: Delete Load Balancers

#### AWS Console

1. Navigate to **EC2** → **Load Balancers**

**Delete API Load Balancer**:
1. Select `housing-api-alb` (check the box)
2. Click **Actions** → **Delete load balancer**
3. Type `confirm` in the box
4. Click **Delete**

**Delete UI Load Balancer**:
1. Select `housing-ui-alb` (check the box)
2. Click **Actions** → **Delete load balancer**
3. Type `confirm` in the box
4. Click **Delete**

**Wait**: Load balancers take ~2 minutes to delete. Wait before proceeding to target groups.

#### AWS CLI

```bash
echo "🧹 Step 2: Deleting load balancers..."

aws elbv2 delete-load-balancer \
    --load-balancer-arn $API_ALB_ARN \
    --region $AWS_REGION

aws elbv2 delete-load-balancer \
    --load-balancer-arn $UI_ALB_ARN \
    --region $AWS_REGION

# Wait for ALBs to be deleted
echo "Waiting for load balancers to be deleted..."
sleep 60
```

---

### Step 3: Delete Target Groups

#### AWS Console

1. Navigate to **EC2** → **Target Groups**

**Delete API Target Group**:
1. Select `housing-api-tg` (check the box)
2. Click **Actions** → **Delete**
3. Click **Yes, delete**

**Delete UI Target Group**:
1. Select `housing-ui-tg` (check the box)
2. Click **Actions** → **Delete**
3. Click **Yes, delete**

#### AWS CLI

```bash
echo "🧹 Step 3: Deleting target groups..."

aws elbv2 delete-target-group \
    --target-group-arn $API_TG_ARN \
    --region $AWS_REGION

aws elbv2 delete-target-group \
    --target-group-arn $UI_TG_ARN \
    --region $AWS_REGION
```

---

### Step 4: Delete ECS Cluster

#### AWS Console

1. Navigate to **Amazon ECS** → **Clusters**
2. Select `housing-ml-cluster` (check the box)
3. Click **Delete**
4. Type `delete housing-ml-cluster` to confirm
5. Click **Delete**

**Expected Result**: Cluster is deleted immediately (since all services and tasks are already removed).

#### AWS CLI

```bash
echo "🧹 Step 4: Deleting ECS cluster..."

aws ecs delete-cluster \
    --cluster housing-ml-cluster \
    --region $AWS_REGION
```

---

### Step 5: Deregister Task Definitions (Optional)

:information_source: **Note**: Task definitions don't incur charges, so this is optional. They can only be deregistered, not deleted.

#### AWS Console

1. Navigate to **Amazon ECS** → **Task Definitions**

**Deregister API Task Definition**:
1. Click on `housing-api-task-ecs`
2. Select all revisions (check boxes)
3. Click **Actions** → **Deregister**
4. Click **Deregister**

**Deregister UI Task Definition**:
1. Click on `housing-streamlit`
2. Select all revisions (check boxes)
3. Click **Actions** → **Deregister**
4. Click **Deregister**

#### AWS CLI

```bash
echo "🧹 Step 5: Deregistering task definitions..."

# Deregister API task definitions
API_TASK_REVISIONS=$(aws ecs list-task-definitions \
    --family-prefix housing-api-task-ecs \
    --region $AWS_REGION \
    --query 'taskDefinitionArns' \
    --output text)

for revision in $API_TASK_REVISIONS; do
    aws ecs deregister-task-definition \
        --task-definition $revision \
        --region $AWS_REGION
done

# Deregister UI task definitions
UI_TASK_REVISIONS=$(aws ecs list-task-definitions \
    --family-prefix housing-streamlit \
    --region $AWS_REGION \
    --query 'taskDefinitionArns' \
    --output text)

for revision in $UI_TASK_REVISIONS; do
    aws ecs deregister-task-definition \
        --task-definition $revision \
        --region $AWS_REGION
done
```

---

### Step 6: Delete CloudWatch Log Groups

#### AWS Console

1. Navigate to **CloudWatch** → **Logs** → **Log groups**

**Delete API Log Group**:
1. Find `/ecs/housing-api-task-ecs`
2. Select it (check the box)
3. Click **Actions** → **Delete log group(s)**
4. Click **Delete**

**Delete UI Log Group**:
1. Find `/ecs/housing-streamlit`
2. Select it (check the box)
3. Click **Actions** → **Delete log group(s)**
4. Click **Delete**

#### AWS CLI

```bash
echo "🧹 Step 6: Deleting CloudWatch log groups..."

aws logs delete-log-group \
    --log-group-name /ecs/housing-api-task-ecs \
    --region $AWS_REGION

aws logs delete-log-group \
    --log-group-name /ecs/housing-streamlit \
    --region $AWS_REGION
```

---

### Step 7: Delete Security Groups

#### AWS Console

1. Navigate to **EC2** → **Security Groups**

**Wait ~30 seconds** after deleting load balancers before deleting security groups (to ensure no dependencies).

**Delete Security Groups** (in this order):
1. Select `housing-alb-sg`
2. Click **Actions** → **Delete security groups**
3. Click **Delete**
4. Repeat for `housing-api-sg`
5. Repeat for `housing-ui-sg`

:warning: **Note**: If you get "dependency violation" error, wait another minute and try again.

#### AWS CLI

```bash
echo "🧹 Step 7: Deleting security groups..."
sleep 30  # Wait to ensure no more dependencies

aws ec2 delete-security-group \
    --group-id $ALB_SG_ID \
    --region $AWS_REGION

aws ec2 delete-security-group \
    --group-id $API_SG_ID \
    --region $AWS_REGION

aws ec2 delete-security-group \
    --group-id $UI_SG_ID \
    --region $AWS_REGION
```

---

### Step 8: Delete ECR Repositories

#### AWS Console

1. Navigate to **Amazon ECR** → **Repositories**

**Delete API Repository**:
1. Select `housing-api` (check the box)
2. Click **Delete**
3. Type `delete` to confirm
4. Click **Delete**

**Delete UI Repository**:
1. Select `housing-streamlit` (check the box)
2. Click **Delete**
3. Type `delete` to confirm
4. Click **Delete**

:information_source: **Note**: This deletes all images in the repositories.

#### AWS CLI

```bash
echo "🧹 Step 8: Deleting ECR repositories..."

aws ecr delete-repository \
    --repository-name housing-api \
    --force \
    --region $AWS_REGION

aws ecr delete-repository \
    --repository-name housing-streamlit \
    --force \
    --region $AWS_REGION
```

---

### Step 9: Delete IAM Roles (Optional)

:warning: **Caution**: Only delete these if you're not using them for other projects.

#### AWS Console

1. Navigate to **IAM** → **Roles**

**Delete ecs_s3_access Role**:
1. Search for `ecs_s3_access`
2. Select the role
3. Click **Delete**
4. Type the role name to confirm
5. Click **Delete**

**Delete ecsTaskExecutionRole** (if you created a custom one):
1. Search for `ecsTaskExecutionRole`
2. Select the role (only if you created it custom, don't delete AWS-managed)
3. Click **Delete**
4. Type the role name to confirm
5. Click **Delete**

#### AWS CLI

```bash
echo "🧹 Step 9: Deleting IAM roles..."

# Detach policies from ecsTaskExecutionRole
aws iam detach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Delete inline policy from ecs_s3_access
aws iam delete-role-policy \
    --role-name ecs_s3_access \
    --policy-name S3AccessPolicy

# Delete roles
aws iam delete-role --role-name ecsTaskExecutionRole
aws iam delete-role --role-name ecs_s3_access

echo "✅ Cleanup complete!"
```

---

### ✅ Step 10: Verify Cleanup

It's important to verify all resources are deleted to avoid unexpected charges.

#### AWS Console (Beginner-Friendly)

**Check ECS**:
1. Navigate to **Amazon ECS** → **Clusters**
2. Verify `housing-ml-cluster` is NOT in the list

**Check Load Balancers**:
1. Navigate to **EC2** → **Load Balancers**
2. Verify no load balancers with "housing" in the name

**Check Target Groups**:
1. Navigate to **EC2** → **Target Groups**
2. Verify no target groups with "housing" in the name

**Check Security Groups**:
1. Navigate to **EC2** → **Security Groups**
2. Verify no security groups with "housing" in the name

**Check ECR**:
1. Navigate to **Amazon ECR** → **Repositories**
2. Verify no repositories named `housing-api` or `housing-streamlit`

**Check CloudWatch Logs**:
1. Navigate to **CloudWatch** → **Logs** → **Log groups**
2. Verify no log groups starting with `/ecs/housing`

✅ **Success**: If all checks pass, you've successfully cleaned up all resources!

#### AWS CLI (Advanced)

```bash
echo "🔍 Verifying cleanup..."

# Check no running tasks
echo "Checking ECS tasks..."
TASKS=$(aws ecs list-tasks --cluster housing-ml-cluster --region $AWS_REGION 2>&1)
if echo "$TASKS" | grep -q "ClusterNotFoundException"; then
    echo "✅ ECS cluster deleted"
else
    echo "⚠️  ECS cluster still exists"
fi

# Check no load balancers
echo "Checking load balancers..."
ALBS=$(aws elbv2 describe-load-balancers --region $AWS_REGION 2>&1 | grep housing || true)
if [ -z "$ALBS" ]; then
    echo "✅ No housing load balancers found"
else
    echo "⚠️  Load balancers still exist: $ALBS"
fi

# Check no ECR repositories
echo "Checking ECR repositories..."
REPOS=$(aws ecr describe-repositories --region $AWS_REGION 2>&1 | grep housing || true)
if [ -z "$REPOS" ]; then
    echo "✅ No housing ECR repositories found"
else
    echo "⚠️  ECR repositories still exist: $REPOS"
fi

# Check no security groups (besides default)
echo "Checking security groups..."
SGS=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=housing-*" --region $AWS_REGION --query 'SecurityGroups[*].GroupName' --output text)
if [ -z "$SGS" ]; then
    echo "✅ No housing security groups found"
else
    echo "⚠️  Security groups still exist: $SGS"
fi

echo ""
echo "💰 Cleanup verification complete!"
echo "Check your AWS billing dashboard in 24 hours to confirm no charges."
```

---

### 🤖 Complete Automated Cleanup Script (Advanced)

For convenience, here's a complete script that performs all cleanup steps automatically:

```bash
#!/bin/bash
# cleanup-all.sh - Complete cleanup script for Housing ML Lab

set -e

echo "🧹 Starting complete cleanup of Housing ML infrastructure..."
echo "=================================================="

# Load environment variables if available
if [ -f .env ]; then
    source .env
fi

# Set region if not set
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Using region: $AWS_REGION"
echo ""

# Get resource ARNs/IDs
echo "🔍 Discovering resources..."
API_SERVICE=$(aws ecs describe-services --cluster housing-ml-cluster --services housing-api-service --region $AWS_REGION --query 'services[0].serviceArn' --output text 2>/dev/null || echo "")
UI_SERVICE=$(aws ecs describe-services --cluster housing-ml-cluster --services housing-streamlit-service --region $AWS_REGION --query 'services[0].serviceArn' --output text 2>/dev/null || echo "")

# Step 1: Delete ECS Services
if [ ! -z "$API_SERVICE" ] && [ "$API_SERVICE" != "None" ]; then
    echo "🗑️  Deleting API service..."
    aws ecs delete-service --cluster housing-ml-cluster --service housing-api-service --force --region $AWS_REGION
fi

if [ ! -z "$UI_SERVICE" ] && [ "$UI_SERVICE" != "None" ]; then
    echo "🗑️  Deleting UI service..."
    aws ecs delete-service --cluster housing-ml-cluster --service housing-streamlit-service --force --region $AWS_REGION
fi

if [ ! -z "$API_SERVICE" ] || [ ! -z "$UI_SERVICE" ]; then
    echo "⏳ Waiting for services to drain..."
    sleep 30
fi

# Step 2: Delete Load Balancers
echo "🗑️  Deleting load balancers..."
API_ALB=$(aws elbv2 describe-load-balancers --region $AWS_REGION --query "LoadBalancers[?LoadBalancerName=='housing-api-alb'].LoadBalancerArn" --output text 2>/dev/null || echo "")
UI_ALB=$(aws elbv2 describe-load-balancers --region $AWS_REGION --query "LoadBalancers[?LoadBalancerName=='housing-ui-alb'].LoadBalancerArn" --output text 2>/dev/null || echo "")

if [ ! -z "$API_ALB" ]; then
    aws elbv2 delete-load-balancer --load-balancer-arn $API_ALB --region $AWS_REGION
    echo "  ✅ API ALB deleted"
fi

if [ ! -z "$UI_ALB" ]; then
    aws elbv2 delete-load-balancer --load-balancer-arn $UI_ALB --region $AWS_REGION
    echo "  ✅ UI ALB deleted"
fi

if [ ! -z "$API_ALB" ] || [ ! -z "$UI_ALB" ]; then
    echo "⏳ Waiting for load balancers to delete..."
    sleep 60
fi

# Step 3: Delete Target Groups
echo "🗑️  Deleting target groups..."
API_TG=$(aws elbv2 describe-target-groups --region $AWS_REGION --query "TargetGroups[?TargetGroupName=='housing-api-tg'].TargetGroupArn" --output text 2>/dev/null || echo "")
UI_TG=$(aws elbv2 describe-target-groups --region $AWS_REGION --query "TargetGroups[?TargetGroupName=='housing-ui-tg'].TargetGroupArn" --output text 2>/dev/null || echo "")

if [ ! -z "$API_TG" ]; then
    aws elbv2 delete-target-group --target-group-arn $API_TG --region $AWS_REGION
    echo "  ✅ API target group deleted"
fi

if [ ! -z "$UI_TG" ]; then
    aws elbv2 delete-target-group --target-group-arn $UI_TG --region $AWS_REGION
    echo "  ✅ UI target group deleted"
fi

# Step 4: Delete ECS Cluster
echo "🗑️  Deleting ECS cluster..."
aws ecs delete-cluster --cluster housing-ml-cluster --region $AWS_REGION 2>/dev/null && echo "  ✅ Cluster deleted" || echo "  ℹ️  Cluster already deleted"

# Step 5: Delete CloudWatch Log Groups
echo "🗑️  Deleting CloudWatch log groups..."
aws logs delete-log-group --log-group-name /ecs/housing-api-task-ecs --region $AWS_REGION 2>/dev/null && echo "  ✅ API logs deleted" || echo "  ℹ️  API logs already deleted"
aws logs delete-log-group --log-group-name /ecs/housing-streamlit --region $AWS_REGION 2>/dev/null && echo "  ✅ UI logs deleted" || echo "  ℹ️  UI logs already deleted"

# Step 6: Delete Security Groups
echo "🗑️  Deleting security groups..."
sleep 30  # Wait for dependencies

ALB_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=housing-alb-sg" --region $AWS_REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")
API_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=housing-api-sg" --region $AWS_REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")
UI_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=housing-ui-sg" --region $AWS_REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")

if [ ! -z "$ALB_SG" ] && [ "$ALB_SG" != "None" ]; then
    aws ec2 delete-security-group --group-id $ALB_SG --region $AWS_REGION && echo "  ✅ ALB SG deleted"
fi

if [ ! -z "$API_SG" ] && [ "$API_SG" != "None" ]; then
    aws ec2 delete-security-group --group-id $API_SG --region $AWS_REGION && echo "  ✅ API SG deleted"
fi

if [ ! -z "$UI_SG" ] && [ "$UI_SG" != "None" ]; then
    aws ec2 delete-security-group --group-id $UI_SG --region $AWS_REGION && echo "  ✅ UI SG deleted"
fi

# Step 7: Delete ECR Repositories
echo "🗑️  Deleting ECR repositories..."
aws ecr delete-repository --repository-name housing-api --force --region $AWS_REGION 2>/dev/null && echo "  ✅ API repo deleted" || echo "  ℹ️  API repo already deleted"
aws ecr delete-repository --repository-name housing-streamlit --force --region $AWS_REGION 2>/dev/null && echo "  ✅ UI repo deleted" || echo "  ℹ️  UI repo already deleted"

echo ""
echo "=================================================="
echo "🎉 Cleanup complete!"
echo "💰 All resources should be deleted."
echo "📊 Verify in AWS Console and check billing in 24 hours."
echo "=================================================="
```

**To use this script**:

```bash
# Save the script
nano cleanup-all.sh
# Paste the script above, save and exit

# Make it executable
chmod +x cleanup-all.sh

# Run it
./cleanup-all.sh
```

---

### 💡 Cleanup Best Practices

1. **Verify deletion**: Always check the AWS Console after cleanup
2. **Monitor billing**: Check your AWS billing dashboard 24 hours after cleanup
3. **Set billing alerts**: Configure CloudWatch billing alerts to catch unexpected charges
4. **Take screenshots**: Document your cleanup for proof if needed
5. **Delete S3 buckets**: If you created test S3 buckets, delete them separately
6. **Check all regions**: Ensure you deleted resources in the correct region

---

### 💰 Cost Summary

After complete cleanup, you should have **$0 ongoing charges** for this lab.

**Typical lab costs** (if run for 2 hours):
- Fargate tasks: ~$0.15
- Application Load Balancers: ~$0.06
- Data transfer: ~$0.01
- **Total**: ~$0.22

**Resources that continue to charge if not deleted**:
- ❌ Running Fargate tasks (~$0.075/hour)
- ❌ Application Load Balancers (~$0.025/hour)
- ❌ Elastic IPs not attached to instances (~$0.005/hour)
- ✅ ECR images (first 500MB free, then $0.10/GB/month)
- ✅ CloudWatch Logs (first 5GB free, then $0.50/GB)
- ✅ Task definitions (free)
- ✅ Security groups (free)

---
    --region $AWS_REGION

# Wait for ALBs to be deleted
echo "Waiting for load balancers to be deleted..."
sleep 60

# 3. Delete Target Groups
echo "Deleting target groups..."
aws elbv2 delete-target-group \
    --target-group-arn $API_TG_ARN \
    --region $AWS_REGION

aws elbv2 delete-target-group \
    --target-group-arn $UI_TG_ARN \
    --region $AWS_REGION

# 4. Delete ECS Cluster
echo "Deleting ECS cluster..."
aws ecs delete-cluster \
    --cluster housing-ml-cluster \
    --region $AWS_REGION

# 5. Deregister Task Definitions (optional, doesn't incur costs)
echo "Deregistering task definitions..."
# Note: Task definitions cannot be deleted, only deregistered
API_TASK_REVISIONS=$(aws ecs list-task-definitions \
    --family-prefix housing-api-task-ecs \
    --region $AWS_REGION \
    --query 'taskDefinitionArns' \
    --output text)

for revision in $API_TASK_REVISIONS; do
    aws ecs deregister-task-definition \
        --task-definition $revision \
        --region $AWS_REGION
done

UI_TASK_REVISIONS=$(aws ecs list-task-definitions \
    --family-prefix housing-streamlit \
    --region $AWS_REGION \
    --query 'taskDefinitionArns' \
    --output text)

for revision in $UI_TASK_REVISIONS; do
    aws ecs deregister-task-definition \
        --task-definition $revision \
        --region $AWS_REGION
done

# 6. Delete CloudWatch Log Groups
echo "Deleting CloudWatch log groups..."
aws logs delete-log-group \
    --log-group-name /ecs/housing-api-task-ecs \
    --region $AWS_REGION

aws logs delete-log-group \
    --log-group-name /ecs/housing-streamlit \
    --region $AWS_REGION

# 7. Delete Security Groups
echo "Deleting security groups..."
sleep 30  # Wait to ensure no more dependencies
aws ec2 delete-security-group \
    --group-id $ALB_SG_ID \
    --region $AWS_REGION

aws ec2 delete-security-group \
    --group-id $API_SG_ID \
    --region $AWS_REGION

aws ec2 delete-security-group \
    --group-id $UI_SG_ID \
    --region $AWS_REGION

# 8. Delete ECR Repositories (including all images)
echo "Deleting ECR repositories..."
aws ecr delete-repository \
    --repository-name housing-api \
    --force \
---

## Additional Resources

### 📚 AWS Documentation
- [Amazon ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Amazon ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)

### 🎓 Learning Resources
- [AWS Free Tier](https://aws.amazon.com/free/)
- [ECS Workshop](https://ecsworkshop.com/)
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### 🛠️ Tools
- [AWS Cost Calculator](https://calculator.aws/)
- [Docker Hub](https://hub.docker.com/)
- [Postman](https://www.postman.com/) (for API testing)

### 💡 Next Steps
- **Add HTTPS**: Configure SSL/TLS certificates using AWS Certificate Manager
- **Set up CI/CD**: Automate deployments with GitHub Actions or AWS CodePipeline
- **Implement Auto-scaling**: Scale tasks based on CPU/memory metrics
- **Add Monitoring**: Set up CloudWatch dashboards and alarms
- **Database Integration**: Add RDS for persistent storage
- **CDN**: Use CloudFront for faster global access
- **Cost Optimization**: Implement Fargate Spot for non-critical workloads

---

## 🎉 Congratulations!

You've successfully:
- ✅ Containerized a machine learning application
- ✅ Deployed to AWS ECR and Fargate
- ✅ Configured networking and security
- ✅ Set up load balancers for public access
- ✅ Implemented monitoring and logging
- ✅ Tested and verified your deployment

### 📸 Lab Evidence
Take screenshots of:
1. ECR repositories with images
2. ECS cluster with running services
3. Load balancer DNS endpoints
4. Streamlit UI in browser
5. API response from `/predict` endpoint
6. CloudWatch logs showing requests

### 📝 Lab Report Template

**Student Name**: ________________  
**Date**: ________________  
**Lab Duration**: ________________

**Summary**:
- API Endpoint: `http://____________________`
- UI Endpoint: `http://____________________`
- Docker Images: ____________________
- Challenges Faced: ____________________
- Key Learnings: ____________________

**Resources Used**:
- Fargate Tasks: _____ (API) + _____ (UI)
- Total Cost: $________
- Region: ___________

---

## Appendix: Quick Reference Commands

### Environment Setup
```bash
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

### Build and Push
```bash
docker build -t housing-api:latest -f Dockerfile .
docker tag housing-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-api:latest
```

### Service Status
```bash
aws ecs describe-services --cluster housing-ml-cluster --services housing-api-service --region $AWS_REGION
```

### View Logs
```bash
aws logs tail /ecs/housing-api-task-ecs --follow --region $AWS_REGION
```

### Force Redeploy
```bash
aws ecs update-service --cluster housing-ml-cluster --service housing-api-service --force-new-deployment --region $AWS_REGION
```

---

**Last Updated**: January 2026  
**Version**: 1.0  
**Maintainer**: ML Engineering Team

---
