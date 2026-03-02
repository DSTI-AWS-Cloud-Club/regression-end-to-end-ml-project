# AWS Labs - Prerequisites Installation Guide

This guide explains, step by step, how to prepare your machine and AWS account before starting any lab.

## What you need before starting

You must have:

1. An **AWS Free Tier account**
2. An **IAM admin user** (do not use root for daily work)
3. **AWS CLI** installed and configured
4. An IDE (**VS Code** or **PyCharm**) with **Colab** extension
5. **uv** installed
6. **Git** installed

---

## Step 1 - Create and secure your AWS account

### 1.1 Create AWS Free Tier account

1. Go to: https://aws.amazon.com/free/
2. Create your account and complete billing/identity verification.
3. Sign in to the **AWS Management Console**.

### 1.2 Secure the root account (one-time)

Use root only for account-level operations.

1. Sign in as root user.
2. Enable MFA for root account:
     - Go to **IAM** -> **Dashboard** -> **Security recommendations**.
     - Enable multi-factor authentication (MFA).
3. Sign out from root.

### 1.3 Create an admin IAM user (recommended for labs)

Follow AWS setup reference:
https://docs.aws.amazon.com/streams/latest/dev/setting-up.html#setting-up-next-step-2

1. Sign in to AWS Console (as root only for this setup step).
2. Open **IAM** -> **Users** -> **Create user**.
3. Username suggestion: `admin`.
4. Enable access type for console and/or programmatic access as needed.
5. Attach policy **AdministratorAccess**.
6. Create user and save credentials securely.
7. Sign out and sign in with the new admin user.

> ✅ For labs, ensure the IAM user has **AdministratorAccess**.

---

## Step 2 - Install AWS CLI

Official docs:
https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

### Windows

1. Download the AWS CLI MSI installer from the official AWS docs.
2. Run the installer and finish setup.
3. Open a **new** terminal (PowerShell or CMD).
4. Verify installation:

```powershell
aws --version
```

You should see output similar to:

```text
aws-cli/2.x.x Python/3.x.x Windows/...
```

---

## Step 3 - Configure AWS CLI credentials

You need an access key from your IAM admin user.

### 3.1 Create Access Key

1. Go to **IAM** -> **Users** -> select your `admin` user.
2. Open **Security credentials** tab.
3. Under **Access keys**, click **Create access key**.
4. Choose use case (CLI).
5. Save:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`

### 3.2 Configure locally

Run:

```bash
aws configure
```

When prompted, enter:

- AWS Access Key ID
- AWS Secret Access Key
- Default region name (example: `us-east-1`)
- Default output format (`json`)

### 3.3 Validate configuration

```bash
aws sts get-caller-identity
```

Expected result: JSON with your AWS account/user identity.

---

## Step 4 - Install an IDE and Colab extension

Install one of the following:

- VS Code: https://code.visualstudio.com/
- PyCharm: https://www.jetbrains.com/pycharm/

Then install the **Colab** extension/plugin in your IDE.

Verification:

1. Open your IDE.
2. Open Extensions/Plugins.
3. Confirm **Colab** appears as installed.

---

## Step 5 - Install `uv`

Official docs:
https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen terminal, then verify:

```powershell
uv --version
```

If the command is not recognized, restart terminal/IDE and check that `uv` was added to PATH.

---

## Step 6 - Install Git

1. Download and install Git:
     https://git-scm.com/downloads
2. Use default options unless your team specifies different settings.
3. Open a new terminal and verify:

```bash
git --version
```

Optional first-time identity setup:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## Step 7 - Final pre-lab checklist

Run these commands in a terminal:

```bash
aws --version
aws sts get-caller-identity
uv --version
git --version
```

All commands must execute without errors before starting the lab.

---

## Quick troubleshooting

- `aws: command not found` or not recognized:
    - Reopen terminal and verify AWS CLI installation.
- `Unable to locate credentials`:
    - Re-run `aws configure` and ensure keys are valid.
- `AccessDenied` in AWS CLI:
    - Verify IAM user has `AdministratorAccess`.
- `uv` not recognized:
    - Reopen terminal or reinstall `uv` from official docs.
- `git` not recognized:
    - Reinstall Git and ensure PATH option is enabled during setup.
