# AWS Deployment Lab: Housing Regression ML Application
## Deploying Streamlit UI & FastAPI Backend to AWS ECR and Fargate

## Resources
Please refer to the original Anas Riad project resources if you have any doubts.

- Here is a [link](https://theneuralmaze.substack.com/p/how-to-build-production-ready-ml) to a blog explaining the steps 
- Here is the [YouTube](https://www.youtube.com/watch?v=Y0SbCp4fUvA) video of Anas explaining the whole project
- Here is Anas' [repo](https://github.com/anesriad/Regression_ML_EndtoEnd) on Github

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
- **ECR**: First 500 MB/month free, then $0.10/GB/month
- **Estimated Lab Cost**: $1-3 (if completed in 2-4 hours and cleaned up)

> ⚠️ **Important**: Remember to clean up resources after completing the lab to avoid ongoing charges!

---

## Lab Setup

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
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

---

## Part 1: AWS Environment Setup

### 🌍 Set Environment Variables

Create a file to store your configuration:

```bash
# Windows PowerShell
$env:AWS_REGION = "us-east-1"
$env:AWS_ACCOUNT_ID = $(aws sts get-caller-identity --query Account --output text)
$env:PROJECT_NAME = "housing-regression"

# Verify
echo $env:AWS_ACCOUNT_ID
echo $env:AWS_REGION
```

```bash
# Linux/Mac/WSL
export AWS_REGION="us-east-1"
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

### 🧪 Test Docker Builds Locally (Optional but Recommended)

```bash
# Test backend build
docker build -t housing-api:test -f Dockerfile .

# Test UI build
docker build -t housing-streamlit:test -f Dockerfile.streamlit .

# Verify images were created
docker images | grep housing
```

**🎓 Why Test Locally?**
- Faster iteration (no AWS upload/download)
- Easier debugging
- Catches errors before pushing to ECR

---

## Part 3: ECR Repository Setup

### 📦 Create ECR Repositories

**What is ECR?**
Amazon ECR is a managed container registry that stores, manages, and deploys Docker images. Think of it as "Docker Hub" but private and integrated with AWS services.

```bash
# Create repository for backend API
aws ecr create-repository \
    --repository-name housing-api \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256

# Create repository for Streamlit UI
aws ecr create-repository \
    --repository-name housing-streamlit \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
```

**🔍 Command Breakdown**:
- `--repository-name`: Unique name for your repository
- `--image-scanning-configuration`: Automatically scans images for vulnerabilities
- `--encryption-configuration`: Encrypts images at rest using AES256

### ✅ Verify ECR Repositories

```bash
# List all repositories
aws ecr describe-repositories --region $AWS_REGION

# Expected output: JSON with both repositories
```

You should see both `housing-api` and `housing-streamlit` repositories.

---

## Part 4: Build and Push Docker Images

### 🔐 Step 1: Authenticate Docker to ECR

```bash
# Get login password and authenticate
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
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

```bash
# Tag backend image
docker tag housing-api:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-api:latest

# Tag UI image
docker tag housing-streamlit:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-streamlit:latest
```

**🎓 Understanding Tags**:
- Tags identify specific versions of images
- `latest`: Convention for most recent version
- ECR images require full registry path in tag

### ⬆️ Step 4: Push Images to ECR

```bash
# Push backend image
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-api:latest

# Push UI image
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/housing-streamlit:latest
```

**⏱️ Expected Push Time**: 2-10 minutes per image (depending on internet speed)

### ✅ Step 5: Verify Images in ECR

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
        "arn:aws:s3:::housing-regression-data",
        "arn:aws:s3:::housing-regression-data/*"
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

**⚠️ Important**: Update `housing-regression-data` to match your S3 bucket name!

### ✅ Step 3: Verify Roles

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

### 🚀 Create ECS Cluster

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

### ✅ Verify Cluster

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

### 📍 Step 1: Get Default VPC and Subnets

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

### 🔒 Step 2: Create Security Group for API

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

**🔍 CIDR Notation**:
- `0.0.0.0/0`: Allows traffic from any IP address (public internet)
- For production, restrict to specific IP ranges or security groups

### 🔒 Step 3: Create Security Group for UI

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

### 🔒 Step 4: Create Security Group for Load Balancers

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

### 🔗 Step 5: Update Security Groups to Allow ALB → Tasks

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

### ✅ Verify Security Groups

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

### ✅ Verify Log Groups

```bash
# List log groups
aws logs describe-log-groups \
    --log-group-name-prefix /ecs/housing \
    --region $AWS_REGION
```

---

## Part 9: Deploy FastAPI Backend to Fargate

### 📄 Step 1: Create Task Definition

Create a file `task-def-api.json`:

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
          "value": "housing-regression-data"
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

### 🔧 Step 2: Update Task Definition with Your Values

```bash
# Replace placeholders automatically
sed -i "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-def-api.json
sed -i "s/YOUR_REGION/$AWS_REGION/g" task-def-api.json

# Or manually edit the file with your favorite editor
```

### 📤 Step 3: Register Task Definition

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

### 🔗 Step 3: Create Listener for API ALB

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

```bash
# Wait for service to reach steady state (may take 3-5 minutes)
aws ecs wait services-stable \
    --cluster housing-ml-cluster \
    --services housing-api-service \
    --region $AWS_REGION

echo "✅ API Service is stable!"
```

### ✅ Step 6: Verify API Deployment

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

### 📄 Step 1: Create Task Definition for UI

Create a file `task-def-ui.json`:

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
          "value": "housing-regression-data"
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

### 🔧 Step 2: Update Task Definition with Actual Values

```bash
# Replace placeholders
sed -i "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-def-ui.json
sed -i "s/YOUR_REGION/$AWS_REGION/g" task-def-ui.json
sed -i "s|YOUR_API_ALB_DNS|$API_ALB_DNS|g" task-def-ui.json

# Verify the API_URL is correct
grep API_URL task-def-ui.json
```

### 📤 Step 3: Register UI Task Definition

```bash
# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://task-def-ui.json \
    --region $AWS_REGION
```

### 🎯 Step 4: Create Target Group for UI

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

**💡 Note**: Streamlit health check uses `/` (root path) and allows 200-399 status codes.

### 🎯 Step 5: Create Load Balancer for UI

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

### 🔗 Step 6: Create Listener for UI ALB

```bash
# Create listener
aws elbv2 create-listener \
    --load-balancer-arn $UI_ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$UI_TG_ARN \
    --region $AWS_REGION
```

### 🚀 Step 7: Create ECS Service for UI

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

**💡 Note**: Streamlit takes longer to start, so grace period is 90 seconds.

### ⏱️ Step 8: Wait for Service to Stabilize

```bash
# Wait for service stability
aws ecs wait services-stable \
    --cluster housing-ml-cluster \
    --services housing-streamlit-service \
    --region $AWS_REGION

echo "✅ UI Service is stable!"
```

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

Always cleanup resources when done with the lab!

```bash
echo "🧹 Starting cleanup process..."

# 1. Delete ECS Services (this stops and removes tasks)
echo "Deleting ECS services..."
aws ecs delete-service \
    --cluster housing-ml-cluster \
    --service housing-api-service \
    --force \
    --region $AWS_REGION

aws ecs delete-service \
    --cluster housing-ml-cluster \
    --service housing-streamlit-service \
    --force \
    --region $AWS_REGION

# Wait for services to be deleted
echo "Waiting for services to be deleted..."
sleep 30

# 2. Delete Load Balancers
echo "Deleting load balancers..."
aws elbv2 delete-load-balancer \
    --load-balancer-arn $API_ALB_ARN \
    --region $AWS_REGION

aws elbv2 delete-load-balancer \
    --load-balancer-arn $UI_ALB_ARN \
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
    --region $AWS_REGION

aws ecr delete-repository \
    --repository-name housing-streamlit \
    --force \
    --region $AWS_REGION

# 9. Delete IAM Roles (optional, might be used by other projects)
echo "Deleting IAM roles..."
# Detach policies first
aws iam detach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Delete inline policies
aws iam delete-role-policy \
    --role-name ecs_s3_access \
    --policy-name S3AccessPolicy

# Delete roles
aws iam delete-role --role-name ecsTaskExecutionRole
aws iam delete-role --role-name ecs_s3_access

echo "✅ Cleanup complete!"
echo "💰 All resources should be deleted. Verify in AWS Console to ensure no orphaned resources."
```

### ✅ Verify Cleanup

```bash
# Check no running tasks
aws ecs list-tasks --cluster housing-ml-cluster --region $AWS_REGION

# Check no load balancers
aws elbv2 describe-load-balancers --region $AWS_REGION | grep housing

# Check no ECR repositories
aws ecr describe-repositories --region $AWS_REGION | grep housing

# Check no security groups (besides default)
aws ec2 describe-security-groups --filters "Name=group-name,Values=housing-*" --region $AWS_REGION
```

**💡 Pro Tip**: Create a checklist and verify each resource is deleted to avoid surprise charges!

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
