# Lambda Deployment Guide

This document captures the end-to-end steps for packaging the inference code under [src](src), attaching the `housing-regression-core-deps` and `housing-regression-ml-deps` layers, wiring permissions, and exposing the function via API Gateway.

## 1. Prerequisites
- AWS CLI configured with credentials that can manage Lambda, IAM, and S3.
- Two published Lambda layers:
  - `housing-regression-core-deps`
  - `housing-regression-ml-deps`
- An S3 bucket that stores the trained model plus auxiliary artifacts (`models/model.pkl`, encoders, training features, etc.).
- Project root is `regression-end-to-end-ml-project/phase-1`.

## 2. Package the Lambda handler ZIP
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
     Compress-Archive -Path build/function/src/* -DestinationPath build/src.zip -Force
     ```
   - Linux/macOS:
     ```bash
     (cd build/function && zip -r ../src.zip .)
     ```

### 3. Layer creation
Open a terminal in the `phase-1` folder.

- Windows / Limux / MacOS (once we have the compiled dependencies in a .zip file)
```powershell / bash
# Core/data tooling layer
aws lambda publish-layer-version --layer-name housing-regression-core-deps --zip-file fileb://data/layers/core-layer.zip --compatible-runtimes python3.11

# Modeling layer
aws lambda publish-layer-version --layer-name housing-regression-ml-deps --zip-file fileb://data/layers/ml-layer.zip --compatible-runtimes python3.11
```

Save the `LayerVersionArn` outputs; you will need them when attaching layers to the function.

## 4. Create model artifacts and upload them to S3
1. Execute the `training pipeline/train.py` and `tune.py` to generate our `lgbm_model.pkl` and `lgbm_best_model.pkl` files. 
2. Execute `01_S3_push_datasets_AWS.ipynb` notebook to upload files to S3.
3. Enable bucket versioning for quick rollback.

## 5. Create or update the Lambda execution role
1. Start with the managed policy `AWSLambdaBasicExecutionRole` for CloudWatch logging.
2. Add an inline S3 read policy so the function can download the artifacts:
   - In the IAM console open the role (linked under the Lambda function's Permissions tab).
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
   - Validate, name it (e.g., `AllowModelArtifactsRead`), and save.

## 6. Create the Lambda function
1. Console → Lambda → **Create function** → "Author from scratch".
2. Runtime: **Python 3.11**.
3. Handler: `src.lambda_function.lambda_handler` (matches [src/lambda_function.py](src/lambda.py)).
4. Execution role: select the role from step 5.
5. Create the function and upload `build/src.zip` (either directly or via S3 object).
6. Go to Configuration -> Edit basic configuration. Set initial memory/timeouts (e.g., 1024 MB and 10 s). Adjust after profiling.

## 7. Attach the dependency layers
1. Lambda console → **Configuration → Layers → Add a layer**.
2. Choose "Specify an ARN".
3. Paste the ARN for `housing-regression-core-deps`. Save.
4. Repeat for `housing-regression-ml-deps`.
5. Confirm both layers appear in the list and that the combined uncompressed size shown in the console is ≤ 262 MB (core ≈ 98 MB + ml ≈ 155 MB after the shared-numpy optimization).

## 8. Configure environment variables
Navigate to **Configuration → Environment variables → Edit** and add:
- `S3_BUCKET=<bucket-name>`
(OPTIONAL):  
- `MODEL_KEY=models/model.pkl`
- `FREQ_ENCODER_KEY=models/freq_encoder.pkl`
- `TARGET_ENCODER_KEY=models/target_encoder.pkl`
- `TRAIN_FEATURES_KEY=processed/feature_engineered_train.csv`
- Overrides: `ARTIFACT_DIR=/tmp/ml_artifacts`

These map directly to the lookups performed in [src/lambda_function.py](src/lambda_function.py).

## 9. Test the function
1. (Optional sanity check before deploying) emulate Lambda locally to ensure dependency sharing works:
  ```bash
  PYTHONPATH=build/layers/core/python:build/layers/ml/python python - <<'PY'
  import pandas as pd
  from joblib import load
  import lightgbm as lgb
  import numpy as np
  print("numpy version:", np.__version__)
  print("lightgbm version:", lgb.__version__)
  PY
  ```
  The script must print the expected versions without ImportError, proving `--no-deps` installs are satisfied by the shared core layer.
2. In the Lambda console, create a test event shaped like the handler expects:
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
2. Invoke the test; watch CloudWatch Logs (`/aws/lambda/<function-name>`) for download messages. `_ensure_local_artifact` caches files under `/tmp/ml_artifacts`, so repeated invocations should skip downloads in the same container.

## 10. Expose via API Gateway (optional but typical)
1. Create an **HTTP API** (faster) or **REST API** (legacy) in API Gateway.
2. Define a `POST /predict` route with a Lambda proxy integration targeting your function.
3. Enable CORS if browsers invoke the endpoint directly.
4. Deploy to a stage (e.g., `prod`) and capture the invoke URL.
5. Test with curl:
   ```bash
   curl -X POST "$INVOKE_URL/predict_price" \
     -H "Content-Type: application/json" \
     -d "{\"records\":[{\"year\":2021,\"quarter\":3,\"month\":7,\"median_list_price\":259900.0,\"median_ppsf\":145.3961600865,\"median_list_ppsf\":140.9792442789,\"homes_sold\":104.0,\"pending_sales\":98.0,\"new_listings\":107.0,\"inventory\":66.0,\"median_dom\":48.0,\"avg_sale_to_list\":1.0160580397,\"sold_above_list\":0.4326923077,\"off_market_in_two_weeks\":0.8163265306,\"bank\":8.0,\"bus\":1.0,\"hospital\":0.0,\"mall\":2.0,\"park\":15.0,\"restaurant\":14.0,\"school\":19.0,\"station\":0.0,\"supermarket\":9.0,\"Total Population\":21501.0,\"Median Age\":40.0,\"Per Capita Income\":37886.0,\"Total Families Below Poverty\":21480.0,\"Total Housing Units\":9067.0,\"Median Rent\":943.0,\"Median Home Value\":182900.0,\"Total Labor Force\":10937.0,\"Unemployed Population\":250.0,\"Total School Age Population\":20604.0,\"Total School Enrollment\":20604.0,\"Median Commute Time\":10007.0,\"price\":255300.5620379616,\"lat\":39.0811,\"lng\":-84.4646,\"zipcode_freq\":94.0,\"city_encoded\":150644.1629528453}]}"
   ```
   

## 11. Operations checklist
- Monitor CloudWatch metrics (Duration, Errors, IteratorAge if streaming).
- Enable Provisioned Concurrency if cold-start latency is unacceptable.
- Rotate model versions by uploading new artifacts and then updating Lambda environment variables or aliases.
- Keep IAM scoped to only the S3 prefixes in use; add additional statements if new artifact paths are introduced.
