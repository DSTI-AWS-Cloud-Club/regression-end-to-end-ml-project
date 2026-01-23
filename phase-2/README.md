# AWS EC2 Deployment Lab: Housing Price Prediction ML Application

## 🎯 Lab Overview

This hands-on lab guides you through deploying a complete machine learning application on AWS EC2. You'll deploy a **FastAPI backend** (port 8000) and a **Streamlit web interface** (port 8501) on a single EC2 instance with proper networking configuration.

### Learning Objectives
- Create and configure an EC2 instance with public internet access
- Set up VPC networking with Internet Gateway and Security Groups
- Deploy Python applications on Linux (Amazon Linux 2023)
- Configure multiple services to run simultaneously
- Test API endpoints and web interfaces
- Understand AWS networking fundamentals

### 🏗️ Project Components
1. **FastAPI backend** (`src/api/main.py`) served on port 8000, loading the trained model from S3 and exposing `/predict`.
2. **Streamlit dashboard** (`app.py`) on port 8501 that visualizes metrics and forwards user actions to the API.
3. **Shared assets** – `.env` configuration plus S3-hosted datasets and model artifacts downloaded on boot.
4. **EC2 networking stack** – VPC, subnet, IGW, and security group that keep both services reachable from the internet.

### Architecture

![phase-2-ec2-schema](/assets/phase2-vpc-ec2-architecture.png)

## 📚 Table of Contents
1. [Lab Overview](#-lab-overview)
2. [Project Components](#-project-components)
3. [Architecture](#architecture)
4. [Prerequisites](#-prerequisites)
5. [Part 1: Network Infrastructure Setup](#part-1-network-infrastructure-setup)
6. [Part 2: EC2 Instance Creation](#part-2-ec2-instance-creation)
7. [Part 3: Connect to Your EC2 Instance](#part-3-connect-to-your-ec2-instance)
8. [Part 4: Instance Configuration](#part-4-instance-configuration)
9. [Part 5: Application Deployment](#part-5-application-deployment)
10. [Part 6: Start Services](#part-6-start-services)
11. [Part 7: (OPTIONAL) Testing and Verification](#part-7-optional-testing-and-verification)
12. [Part 8: Monitoring and Logs](#part-8-monitoring-and-logs)
13. [Part 9: Cost Optimization](#part-9-cost-optimization)
14. [Part 10: Cleanup (When Done)](#part-10-cleanup-when-done)
15. [Key Learnings Summary](#-key-learnings-summary)
16. [Troubleshooting Guide](#-troubleshooting-guide)
17. [Additional Resources](#-additional-resources)
18. [Congratulations](#-congratulations)

---

## 📋 Prerequisites

- **AWS Account** with administrative access
- **AWS CLI** configured locally (optional, for verification)
- **Git** knowledge for cloning repositories
- **Basic Linux** command-line familiarity
- **AWS Credentials** configured with S3 access (for model/data downloads)

---

**Estimated Completion Time**: 1-2 hours  
**AWS Cost**: ~$0.02-0.05/hour (EC2 t2.small on-demand pricing)

## Part 1: Network Infrastructure Setup

### 1.1 Create a VPC (Virtual Private Cloud)

A VPC is your isolated network in AWS where all resources will reside.

1. Navigate to **VPC Dashboard** in AWS Console
2. Click **Create VPC**
3. Configure:
   - **Resources to create**: :warning: VPC only (VPC and more will create subnets and IGW straight away)
   - **Name**: `housing-ml-vpc`
   - **IPv4 CIDR block**: `10.0.0.0/16` (provides 65,536 IP addresses)
   - **IPv6 CIDR block**: No IPv6
   - **Tenancy**: Default

4. Click **Create VPC**

**💡 Insight**: The CIDR block `/16` means the first 16 bits are fixed (10.0), leaving 16 bits for subnets and hosts. This allows you to create multiple subnets within this VPC.

---

### 1.2 Create a Public Subnet

Subnets divide your VPC into smaller networks. A public subnet can communicate with the internet.

1. In **VPC Dashboard**, go to **Subnets** → **Create subnet**
2. Configure:
   - **VPC ID**: Select `housing-ml-vpc`
   - **Subnet name**: `housing-ml-public-subnet`
   - **Availability Zone**: Choose any (e.g., `us-east-1a`)
   - **IPv4 CIDR block**: `10.0.1.0/24` (256 IP addresses)

3. Click **Create subnet**
4. Select the created subnet → **Actions** → **Edit subnet settings**
5. ✅ Check **Enable auto-assign public IPv4 address**
6. Click **Save**

**💡 Insight**: Auto-assigning public IPs ensures instances in this subnet get a public IP automatically, making them accessible from the internet.

---

### 1.3 Create and Attach an Internet Gateway

An Internet Gateway (IGW) allows communication between your VPC and the internet.

1. In **VPC Dashboard**, go to **Internet Gateways** → **Create internet gateway**
2. Configure:
   - **Name tag**: `housing-ml-igw`

3. Click **Create internet gateway**
4. Select the created IGW → **Actions** → **Attach to VPC**
5. Select `housing-ml-vpc`
6. Click **Attach internet gateway**

**💡 Insight**: Without an IGW, your VPC is completely isolated. The IGW acts as a bridge between your private network and the public internet.

---

### 1.4 Configure Route Table

Route tables control where network traffic is directed.

1. Go to **Route Tables** in VPC Dashboard
2. Find the main route table for `housing-ml-vpc` 
3. When you find it, click on the :pen: in the **Name** column and name it: `housing-ml-public-rt`
4. Click **Edit routes** → **Add route**:
   - **Destination**: `0.0.0.0/0` (all internet traffic)
   - **Target**: Select the Internet Gateway `housing-ml-igw`

5. Click **Save changes**
6. Go to **Subnet associations** tab → **Edit subnet associations**
7. ✅ Check `housing-ml-public-subnet`
8. Click **Save associations**

**💡 Insight**: The `0.0.0.0/0` route means "any destination not in my VPC should go through the IGW." This makes the subnet truly public.

---

### 1.5 Create Security Group

Security Groups act as virtual firewalls controlling inbound and outbound traffic.

1. Go to **Security Groups** → **Create security group**
2. Configure:
   - **Security group name**: `housing-ml-sg`
   - **Description**: `Allow SSH, FastAPI (8000), Streamlit (8501)`
   - **VPC**: Select `housing-ml-vpc`

3. **Inbound rules** (click **Add rule** for each):

   | Type        | Protocol | Port Range | Source       | Description                |
   |-------------|----------|------------|--------------|----------------------------|
   | SSH         | TCP      | 22         | My IP        | SSH access (your IP only)  |
   | Custom TCP  | TCP      | 8000       | 0.0.0.0/0    | FastAPI backend            |
   | Custom TCP  | TCP      | 8501       | 0.0.0.0/0    | Streamlit UI               |

4. **Outbound rules**: Keep default (allow all outbound traffic)
5. Click **Create security group**

**⚠️ Security Note**: 
- **SSH (22)**: Restrict to "My IP" for security. Never use `0.0.0.0/0` for SSH in production.
- **Ports 8000 & 8501**: Open to the world (`0.0.0.0/0`) so users can access your services.
- In production, consider using a load balancer and restricting direct instance access.

**💡 Insight**: Security Groups are stateful - if you allow inbound traffic, the response is automatically allowed outbound, regardless of outbound rules.

---

## Part 2: EC2 Instance Creation

### 2.1 Launch EC2 Instance

1. Navigate to **EC2 Dashboard** → **Instances** → **Launch instances**

2. **Name and tags**:
   - **Name**: `housing-ml-server`

3. **Application and OS Images (AMI)**:
   - **Quick Start**: Amazon Linux
   - **AMI**: Amazon Linux 2023 AMI (free tier eligible)
   - **Architecture**: 64-bit (x86)

4. **Instance type**:
   - Select **t2.small** (1 vCPU, 2 GB RAM). This instance type depends on our project demands, for our case, this is enough.

**💡 Insight**: Amazon Linux 2023 is optimized for AWS, includes python3 pre-installed, and receives regular security updates.

5. **Key pair (login)**:
   - Click **Create new key pair**
   - **Name**: `housing-ml-key`
   - **Key pair type**: RSA
   - **Private key file format**: `.pem` (for SSH on Mac/Linux) or `.ppk` (for PuTTY on Windows)
   - Click **Create key pair** (downloads automatically)
   - **⚠️ SAVE THIS FILE SECURELY** - you cannot download it again

6. **Network settings**:
   - Click **Edit**
   - **VPC**: Select `housing-ml-vpc`
   - **Subnet**: Select `housing-ml-public-subnet`
   - **Auto-assign public IP**: Enable
   - **Firewall (security groups)**: Select existing security group
   - Choose `housing-ml-sg`

7. **Configure storage**:
   - **Size**: 8 GB gp3
   - **Volume type**: gp3

8. Review and click **Launch instance**

9. Wait 2-3 minutes for instance to reach **Running** state with **2/2 status checks passed**

**💡 Insight**: The instance profile (IAM role) allows the EC2 instance to access AWS services like S3 without storing credentials on the instance - a security best practice.

---

#### 2.2. Update the EC2 execution role
The base role of an EC2 instance has limited permissions. 
We need to give it permissions to read and get objects from S3 (our pickle objects and csv files to be able to make predictions !).

- Navigate to **IAM Service Dashboard -> Click Roles**

1. Select **Create Role**
2. AWS Service -> *Use Case: EC2*
3. Click **Next**
4. Click **Next**
5. On **Role name**:  `EC2-ml-housing`
6. Cick on **Create Role**

7. Go to the **Roles** list and Click on the Role we have created.
8. Choose **Add permissions → Create inline policy**.
9. Add an inline S3 read policy so the function can download the artifacts. Switch to the **JSON editor** and paste:
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
:warning: remember to use your own **Bucket name!**
10. Validate, name it (e.g., `AllowEC2ModelArtifactsRead`), and save.

### 2.3 Note Your Instance Details

Once running, note these values (you'll need them):
- **Public IPv4 address**: e.g., `54.123.45.67`
- **Public IPv4 DNS**: e.g., `ec2-54-123-45-67.compute-1.amazonaws.com`

---

## Part 3: Connect to Your EC2 Instance

### 3.1 Set Key Permissions (Mac/Linux)

```bash
chmod 400 housing-ml-key.pem
```

### 3.2 SSH into Instance

```bash
ssh -i housing-ml-key.pem ec2-user@<YOUR_PUBLIC_IP>
```

Replace `<YOUR_PUBLIC_IP>` with your instance's public IP.

**Example**:
```bash
ssh -i housing-ml-key.pem ec2-user@54.123.45.67
```
If after the `chmod` you still can not have access to the instance, try with `sudo shh ...`

**💡 Windows Users**: Use PuTTY or Windows Subsystem for Linux (WSL) with the steps above.

### 3.3 Verify Connection

You should see:
```
   ,     #_
   ~\_  ####_        Amazon Linux 2023
  ~~  \_#####\
  ~~     \###|
  ~~       \#/ ___
   ~~       V~' '->
    ~~~         /
      ~~._.   _/
         _/ _/
       _/m/'

[ec2-user@ip-10-0-1-123 ~]$
```

---

## Part 4: Instance Configuration

### 4.1 Update System Packages

Always update packages for security patches:

```bash
sudo dnf update -y
```

**💡 Insight**: `dnf` is the package manager for Amazon Linux 2023 (replacement for `yum`). The `-y` flag auto-confirms all prompts.

---

### 4.2 Install Python 3.11 and Development Tools

```bash
# Install Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Install Git
sudo dnf install -y git

# Verify installations
python3.11 --version
git --version
```

Expected output:
```
Python 3.11.x
git version 2.x.x
```

---

### 4.3 Install System Dependencies

Some Python packages require compilation tools:

```bash
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y gcc gcc-c++ make
```

---

### 4.4 Configure AWS Credentials (If No IAM Role)

If you didn't attach an IAM role in step 2.1:

```bash
# Install AWS CLI (usually pre-installed on Amazon Linux)
aws --version

# Configure credentials
aws configure
```

Enter when prompted:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region name**: e.g., `us-east-1` (match your S3 bucket region)
- **Default output format**: `json`

**⚠️ Security Warning**: Storing credentials on an instance is less secure than using IAM roles. In production, always use IAM instance profiles.

**💡 Insight**: The application uses boto3 to download models and data from S3 bucket `housing-regression-lab`. Ensure your credentials have `s3:GetObject` permissions.

---

## Part 5: Application Deployment

### 5.1 Clone the Repository
We are going to clone a fork of the original **Anas Riad repo**.

```bash
cd ~
# add bash variable with repo name
repo_name=https://github.com/zBotta/Regression_ML_EndtoEnd.git
git clone $repo_name housing-ml
cd housing-ml
```

**Alternative** (if repo is private, copy files manually):
```bash
mkdir -p ~/housing-ml
# Then use scp from your local machine:
# scp -i housing-ml-key.pem -r ./src ./app.py ./pyproject.toml ec2-user@<PUBLIC_IP>:~/housing-ml/
```

---

### 5.2 Create Python Virtual Environment

Virtual environments isolate Python dependencies:

```bash
cd ~/housing-ml
python3.11 -m venv venv
source venv/bin/activate
```

Your prompt should now show `(venv)`:
```
(venv) [ec2-user@ip-10-0-1-123 housing-ml]$
```

**💡 Insight**: Virtual environments prevent dependency conflicts between projects and make it easier to manage package versions.

---

### 5.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

This installs all dependencies from `pyproject.toml`.

**Expected output**: Installation of fastapi, streamlit, xgboost, pandas, boto3, etc.

**⏱️ Time**: ~5-10 minutes depending on instance type.

**💡 Insight**: The `-e .` flag installs the project in "editable" mode, making the `src/` modules importable as `from src.api.main import app`.

---

### 5.4 Verify Installation

```bash
python -c "import fastapi; import streamlit; import xgboost; print('✅ All packages installed')"
```

Expected output:
```
✅ All packages installed
```

---

### 5.5 Set Environment Variables

Create a configuration file for environment variables:

```bash
# change region or bucket name if needed
cat > ~/housing-ml/.env << 'EOF'
export S3_BUCKET=housing-regression-lab
export AWS_REGION=eu-west-3 
export API_URL=http://localhost:8000/predict
EOF
```

**Adjust values** if your S3 bucket name or region differs.

Load the environment:
```bash
source ~/housing-ml/.env
```

Add to `.bashrc` for persistence:
```bash
echo "source ~/housing-ml/.env" >> ~/.bashrc
```

**💡 Insight**: Environment variables allow configuration without hardcoding values. The API_URL tells Streamlit where to find the FastAPI backend.

---

## Part 6: Start Services

You'll run two services simultaneously using separate terminal sessions.

### 6.1 Start FastAPI Backend (Session 1)

In your SSH session:

```bash
cd ~/housing-ml
source venv/bin/activate
source .env

# Start FastAPI with uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**💡 Insight**: 
- `--host 0.0.0.0` binds to all network interfaces (allows external access)
- `--port 8000` specifies the port
- `--reload` auto-restarts on code changes (useful for development)

**⚠️ Keep this terminal open** - the service is now running.

---

### 6.2 Start Streamlit UI (Session 2)

Open another terminal and a **second SSH session** to the same instance:

```bash
ssh -i housing-ml-key.pem ec2-user@<YOUR_PUBLIC_IP>
```

Then run:

```bash
cd ~/housing-ml
source venv/bin/activate
source .env

# Start Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**Expected output**:
```
  You can now view your Streamlit app in your browser.

  Network URL: http://10.0.1.123:8501
  External URL: http://<INSTANCE_PUBLIC_IP>:8501
```

**💡 Insight**: Streamlit's `--server.address 0.0.0.0` makes it accessible externally. By default, Streamlit only listens on localhost.

**⚠️ Keep both terminals open** - both services must run simultaneously.

---

### 6.3 Run Services in Background (Production Method)

For production deployment, use process managers instead of keeping terminals open:

#### Option A: Using `screen` (simpler)

**Terminal 1 - FastAPI**:
```bash
screen -S fastapi
cd ~/housing-ml && source venv/bin/activate && source .env
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+A then D to detach
```

**Terminal 2 - Streamlit**:
```bash
screen -S streamlit
cd ~/housing-ml && source venv/bin/activate && source .env
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
# Press Ctrl+A then D to detach
```

**Reattach to screens**:
```bash
screen -r fastapi    # Reattach to FastAPI
screen -r streamlit  # Reattach to Streamlit
screen -ls           # List all screens
```

However, if we restart the instance or there is an error on the server, the FastAPI and the Streamlit apps won't restart automatically. This is not prepared for production, so down below there is the option `systemd` that deploys a service per process.

#### Option B: Using `systemd` (better for production)

Create service files:

**FastAPI service**:
```bash
sudo tee /etc/systemd/system/housing-api.service > /dev/null << EOF
[Unit]
Description=Housing ML FastAPI Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/housing-ml
Environment="PATH=/home/ec2-user/housing-ml/venv/bin"
Environment="S3_BUCKET=housing-regression-lab"
Environment="AWS_REGION=eu-west-3"
ExecStart=/home/ec2-user/housing-ml/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```
:warning: **Careful** if your terminal adds `~` at the end of the pasted code, **delete it** !

**Streamlit service**:
```bash
sudo tee /etc/systemd/system/housing-streamlit.service > /dev/null << EOF 
[Unit]
Description=Housing ML Streamlit Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/housing-ml
Environment="PATH=/home/ec2-user/housing-ml/venv/bin"
Environment="S3_BUCKET=housing-regression-lab"
Environment="AWS_REGION=eu-west-3"
Environment="API_URL=http://localhost:8000/predict"
ExecStart=/home/ec2-user/housing-ml/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

**Enable and start services**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable housing-api housing-streamlit
sudo systemctl start housing-api housing-streamlit

# Check status
sudo systemctl status housing-api
sudo systemctl status housing-streamlit

# press "q" to exit the status interface

# View logs
sudo journalctl -u housing-api -f
sudo journalctl -u housing-streamlit -f

# press "control + C" to exit the journal log interface
```


**💡 Insight**: `systemd` services automatically restart on failure and survive server reboots. This is the production-grade approach.

You can test that the services will be deployed when reinitializing the instances.

To do that type:
```bash
sudo reboot
```
Reload the webpage. The instance after restarting has launched the services ! :grin:

---

## Part 7: (OPTIONAL) Testing and Verification

### 7.1 Test from EC2 Instance (Local Testing)

SSH into your instance and run:

#### Test 1: FastAPI Health Check
```bash
curl http://localhost:8000/health
```

**Expected output**:
```json
{
  "model_path": "models/xgb_best_model.pkl",
  "status": "healthy",
  "n_features_expected": 42
}
```

✅ **Pass Criteria**: Status is "healthy" and model path exists.

#### Test 2: FastAPI Root Endpoint
```bash
curl http://localhost:8000/
```

**Expected output**:
```json
{
  "message": "Housing Regression API is running 🚀"
}
```

#### Test 3: Prediction Endpoint
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '[
    {
      "date": "2022-01-15",
      "city_full": "New York",
      "zipcode": 10001,
      "sqft": 1200,
      "beds": 2,
      "baths": 1
    }
  ]'
```

**Expected output**:
```json
{
  "predictions": [450000.25]
}
```

✅ **Pass Criteria**: Returns numeric prediction(s).

**💡 Insight**: This tests the entire pipeline: data preprocessing, feature engineering, and model inference.

---

### 7.2 Test from Your Local Machine (External Access)

#### Test 1: FastAPI Health Check
```bash
curl http://<YOUR_PUBLIC_IP>:8000/health
```

Replace `<YOUR_PUBLIC_IP>` with your instance's public IP.

**Example**:
```bash
curl http://54.123.45.67:8000/health
```

✅ **Pass Criteria**: Same JSON response as local test.

❌ **If it fails**:
- Verify Security Group allows port 8000 from `0.0.0.0/0`
- Verify service is running: `sudo systemctl status housing-api` or check `screen -ls`
- Verify firewall: `sudo systemctl status firewalld` (should be inactive on Amazon Linux 2023)

#### Test 2: FastAPI Prediction

In your **local machine**, make an API call to the app.

Open a terminal.

- On linux :
```bash
curl -X POST "http://15.237.126.234:8000/predict" -H "Content-Type: application/json" -d "[{\"year\":2021,\"quarter\":3,\"month\":7,\"median_list_price\":259900.0,\"median_ppsf\":145.3961600865,\"median_list_ppsf\":140.9792442789,\"homes_sold\":104.0,\"pending_sales\":98.0,\"new_listings\":107.0,\"inventory\":66.0,\"median_dom\":48.0,\"avg_sale_to_list\":1.0160580397,\"sold_above_list\":0.4326923077,\"off_market_in_two_weeks\":0.8163265306,\"bank\":8.0,\"bus\":1.0,\"hospital\":0.0,\"mall\":2.0,\"park\":15.0,\"restaurant\":14.0,\"school\":19.0,\"station\":0.0,\"supermarket\":9.0,\"Total Population\":21501.0,\"Median Age\":40.0,\"Per Capita Income\":37886.0,\"Total Families Below Poverty\":21480.0,\"Total Housing Units\":9067.0,\"Median Rent\":943.0,\"Median Home Value\":182900.0,\"Total Labor Force\":10937.0,\"Unemployed Population\":250.0,\"Total School Age Population\":20604.0,\"Total School Enrollment\":20604.0,\"Median Commute Time\":10007.0,\"price\":255300.5620379616,\"lat\":39.0811,\"lng\":-84.4646,\"zipcode_freq\":94.0,\"city_encoded\":150644.1629528453}]"
  ```
- On windows:
```powershell
$body='[{"year":2021,"quarter":3,"month":7,"median_list_price":259900.0,"median_ppsf":145.3961600865,"median_list_ppsf":140.9792442789,"homes_sold":104.0,"pending_sales":98.0,"new_listings":107.0,"inventory":66.0,"median_dom":48.0,"avg_sale_to_list":1.0160580397,"sold_above_list":0.4326923077,"off_market_in_two_weeks":0.8163265306,"bank":8.0,"bus":1.0,"hospital":0.0,"mall":2.0,"park":15.0,"restaurant":14.0,"school":19.0,"station":0.0,"supermarket":9.0,"Total Population":21501.0,"Median Age":40.0,"Per Capita Income":37886.0,"Total Families Below Poverty":21480.0,"Total Housing Units":9067.0,"Median Rent":943.0,"Median Home Value":182900.0,"Total Labor Force":10937.0,"Unemployed Population":250.0,"Total School Age Population":20604.0,"Total School Enrollment":20604.0,"Median Commute Time":10007.0,"price":255300.5620379616,"lat":39.0811,"lng":-84.4646,"zipcode_freq":94.0,"city_encoded":150644.1629528453}]'; Invoke-RestMethod -Method Post -Uri "http://15.237.126.234:8000/predict" -ContentType "application/json" -Body $body

```
**Nota**: paste it as a one-liner

✅ **Pass Criteria**: Returns predictions array.

#### Test 3: Streamlit UI
Open your web browser and navigate to:
```
http://<YOUR_PUBLIC_IP>:8501
```

**Example**: `http://54.123.45.67:8501`

✅ **Pass Criteria**: 
- Streamlit dashboard loads successfully
- You can see dropdowns for Year, Month, Region
- "Show Predictions 🚀" button is visible

**💡 Insight**: If the page doesn't load, check:
1. Security Group allows port 8501
2. Service is running: `sudo systemctl status housing-streamlit`
3. Browser isn't blocking HTTP (some browsers prefer HTTPS)

---

### 7.3 End-to-End Integration Test

This tests the full stack: Streamlit → FastAPI → Model → Response.

1. Open Streamlit UI: `http://<YOUR_PUBLIC_IP>:8501`
2. Select any **Year**, **Month**, and **Region** from dropdowns
3. Click **"Show Predictions 🚀"**

✅ **Pass Criteria**:
- Table shows predictions vs actual prices
- Metrics display (MAE, RMSE, Avg % Error)
- Plotly chart renders showing predictions vs actuals over time
- No error messages

**Common Issues**:
- **"Connection refused"**: API_URL environment variable may be wrong. Should be `http://localhost:8000/predict` (NOT the public IP)
- **"Model not found"**: S3 download failed. Check AWS credentials and S3 bucket access
- **"No data found"**: Your filters returned no results. Try a different combination

**💡 Insight**: The Streamlit app calls the FastAPI backend internally using `localhost` because both services run on the same instance. Users access Streamlit via the public IP, but Streamlit's backend code accesses FastAPI locally.

---

### 7.4 Load Testing (Optional - Advanced)

Test API performance under concurrent requests:

```bash
# Install Apache Bench
sudo dnf install -y httpd-tools


**Create payload.json**:
```bash
cat > payload.json << 'EOF'
[{"date":"2022-01-15","city_full":"New York","zipcode":10001,"sqft":1200,"beds":2,"baths":1}]
EOF


# Send 100 requests with 10 concurrent connections
ab -n 100 -c 10 -T application/json -p payload.json http://localhost:8000/predict
```


**💡 Insight**: Load testing helps identify performance bottlenecks. A t2.small can typically handle 10-15 requests/second for ML inference.

---

## Part 8: Monitoring and Logs

### 8.1 View Application Logs

**FastAPI logs**:
```bash
# If using systemd
sudo journalctl -u housing-api -f

# If using screen
screen -r fastapi
```

**Streamlit logs**:
```bash
# If using systemd
sudo journalctl -u housing-streamlit -f

# If using screen
screen -r streamlit
```

**💡 Insight**: Logs are critical for debugging. The `-f` flag follows logs in real-time (like `tail -f`).

---

### 8.2 Monitor Instance Resources

```bash
# CPU and memory usage
top

# Disk usage
df -h

# Check running processes
ps aux | grep python
```

**💡 Insight**: Watch for memory usage approaching 4 GB (t2.medium limit). ML models can be memory-intensive.

---

### 8.3 CloudWatch Monitoring (AWS Native)

AWS automatically collects basic metrics:

1. Go to **EC2 Dashboard** → Select your instance
2. Click **Monitoring** tab
3. View metrics:
   - CPU utilization
   - Network in/out
   - Disk read/write

**💡 Insight**: For detailed application metrics, consider installing CloudWatch Agent or using Prometheus + Grafana.

---

## Part 9: Cost Optimization

### 9.1 Stop Instance When Not in Use

```bash
# From AWS Console: Select instance → Instance state → Stop
# Or from AWS CLI:
aws ec2 stop-instances --instance-ids <INSTANCE_ID>
```

**💡 Cost Insight**: Stopped instances don't incur compute charges, only EBS storage (~$0.10/GB/month).

### 9.2 Use Elastic IP (Optional)

By default, EC2 public IPs change when you stop/start instances.

1. Go to **EC2** → **Elastic IPs** → **Allocate Elastic IP address**
2. Select the allocated IP → **Actions** → **Associate Elastic IP address**
3. Choose your instance

**💡 Warning**: Elastic IPs incur charges if not associated with a running instance.

---

## Part 10: Cleanup (When Done)

To avoid ongoing charges:

### 10.1 Terminate EC2 Instance
1. **EC2 Dashboard** → Select instance → **Instance state** → **Terminate instance**
2. Confirm termination

### 10.2 Delete Resources
- **Elastic IP**: Release if allocated
- **Security Group**: Can delete `housing-ml-sg`
- **Internet Gateway**: Detach and delete `housing-ml-igw`
- **Subnet**: Delete `housing-ml-public-subnet`
- **VPC**: Delete `housing-ml-vpc` (deletes all associated resources)

**💡 Warning**: Deleting a VPC is irreversible. Make sure you've backed up any important data.

---

## 🎓 Key Learnings Summary

### Networking Concepts
- **VPC**: Isolated cloud network
- **Subnet**: Segment within VPC (public = internet-accessible)
- **Internet Gateway**: Bridge between VPC and internet
- **Route Table**: Defines traffic routing rules
- **Security Group**: Stateful firewall for instances

### AWS Best Practices
- ✅ Use IAM roles instead of storing credentials
- ✅ Restrict SSH to your IP only
- ✅ Use Security Groups as the first line of defense
- ✅ Monitor costs and stop instances when idle
- ✅ Use systemd for production services

### Application Deployment
- Virtual environments isolate dependencies
- Environment variables separate config from code
- Process managers (systemd/screen) keep services running
- Health checks verify service status
- Logs are essential for debugging

---

## 🔧 Troubleshooting Guide

| Issue | Solution |
|-------|----------|
| **Cannot SSH to instance** | • Check Security Group allows port 22 from your IP<br>• Verify instance is in "Running" state<br>• Confirm you're using correct key file and IP |
| **Pip install fails** | • Run `sudo dnf install python3.11-devel gcc`<br>• Upgrade pip: `pip install --upgrade pip` |
| **"Model not found" error** | • Check AWS credentials: `aws s3 ls s3://housing-regression-lab/`<br>• Verify S3 bucket name in .env file<br>• Check IAM permissions for S3 access |
| **Port 8000/8501 not accessible** | • Verify Security Group inbound rules<br>• Check services are running: `sudo systemctl status housing-api`<br>• Verify binding to `0.0.0.0`, not `127.0.0.1` |
| **Streamlit can't reach API** | • Check API_URL in .env: should be `http://localhost:8000/predict`<br>• Verify FastAPI is running on port 8000<br>• Check firewall: `sudo systemctl status firewalld` |
| **Out of memory errors** | • Upgrade to t2.large (8 GB RAM)<br>• Add swap space: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile` |

---

## 📚 Additional Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy)
- [systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## 🎉 Congratulations!

You've successfully deployed a production ML application on AWS EC2 with:
- ✅ Proper VPC networking with Internet Gateway
- ✅ Secure Security Group configuration
- ✅ FastAPI backend serving ML predictions
- ✅ Interactive Streamlit dashboard
- ✅ Comprehensive testing and monitoring

**Next Steps**:
- Set up HTTPS with Let's Encrypt SSL certificates
- Add a load balancer for high availability
- Implement CI/CD with GitHub Actions
- Deploy to ECS/Kubernetes for containerized orchestration
- Add authentication (OAuth/JWT) for secure access

---

**Lab Version**: 1.0  
**Last Updated**: January 2026  
**Estimated Completion Time**: 1-2 hours  
**AWS Cost**: ~$0.02-0.03/hour (t2.small on-demand pricing)
