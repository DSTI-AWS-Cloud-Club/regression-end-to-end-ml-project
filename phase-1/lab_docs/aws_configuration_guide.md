# AWS Configuration Guide

## 1. Package the Lambda code
- From the project root, run `uv pip install --target build/python . --link-mode=copy` so uv reads `pyproject.toml` directly and installs every dependency into `build/python/` without creating a `requirements.txt` file (omit `--link-mode=copy` on Linux/Unix).
- Copy the contents of `phase-1/src/` (and any local assets you need at cold start) into `build/python/`.
- Zip everything inside `build/python/` so the archive contains the package roots, not the parent directory.
- Optional: move larger shared dependencies into a Lambda layer if the ZIP approaches the uncompressed 250 MB limit.

### Moving dependencies into a Lambda layer
1. Create a parallel folder just for the layer, e.g. `build/layer/python/`.
2. Install only the dependencies into that folder: `uv pip install --target build/layer/python .` (omit your app code).
3. Zip the contents of `build/layer/` (not the folder itself) into `ml-deps-layer.zip` and publish it:
   ```bash
   aws lambda publish-layer-version --layer-name housing-regression-deps --zip-file ml-deps-layer.zip --compatible-runtimes python3.11
   ```
4. Record the returned LayerVersionArn and attach it to the Lambda function (console → Layers → Add a layer).
5. When you ship the actual Lambda code package, include only `src/` and other light assets—leave dependencies in the layer so the handler ZIP stays well below the 250 MB uncompressed limit.

### When the layer still exceeds 250 MB
If your dependency layer is larger than the 250 MB uncompressed ceiling, you have three realistic options:
1. **Prune the install**
  - Delete build artifacts that are not required at runtime: `__pycache__`, `tests/`, `*.dist-info/RECORD` files, and compiled sources specific to other platforms.
  - Keep only the packages you truly call: `uv pip install --target build/layer/python pandas==... scikit-learn==... lightgbm==...` (omit helper libraries you never import).
  - Consider replacing heavy libraries with lighter alternatives (for example, `lightgbm` or a distilled model) when feasible.
2. **Split across multiple layers**
  - Group bulky libs (like `pandas` + `numpy`) into one layer, ML frameworks (such as `lightgbm`, `scikit-learn`) into a second, etc. A function can attach up to five layers, each subject to the same 250 MB uncompressed limit.
  - **Example: two-layer split**
   1. Create folders `build/layers/core/python/` and `build/layers/ml/python/`.
   2. Install base data tooling into the first layer:
     ```bash
     uv pip install --target build/layers/core/python pandas numpy pyarrow --link-mode=copy
     ```
   3. Install modeling libraries into the second layer:
     ```bash
     uv pip install --target build/layers/ml/python scikit-learn lightgbm joblib --link-mode=copy
     ```
   4. Zip each layer directory separately (zip the contents of `build/layers/core/` into `core-layer.zip`, same for `ml-layer.zip`).
   5. Publish both via `aws lambda publish-layer-version`, capturing the two ARNs.
   6. Attach both layers to the Lambda function (order does not matter).
3. **Switch to a Lambda container image**
  - Create a `Dockerfile` based on `public.ecr.aws/lambda/python:3.11`, copy your project and run `uv pip install` inside the image.
  - Build and push it to Amazon ECR (max image size 10 GB), then create the Lambda from “Container image” instead of ZIP.
  - This route removes the ZIP/Layers size limit altogether while keeping the same event model.

## 2. Upload model artifacts to S3
- Store the trained model at `bucket_name/models/model.pkl` (matching the `MODEL_KEY`).
- If you rely on encoders or the training-feature schema, upload them as well (e.g., `bucket_name/models/freq_encoder.pkl`, `bucket_name/models/target_encoder.pkl`, `bucket_name/processed/feature_engineered_train.csv`).
- Turn on bucket versioning so you can roll back to a prior artifact quickly.

## 3. Create/Update the Lambda execution role
- Start from `AWSLambdaBasicExecutionRole` for CloudWatch logging.
- Add an inline policy granting `s3:GetObject` on every key the function downloads, such as `arn:aws:s3:::bucket_name/models/*` and `arn:aws:s3:::bucket_name/processed/*`.
- If the Lambda sits inside a VPC, attach the appropriate ENI permissions and subnets; otherwise leave it public for lower cold-start latency.

## 4. Configure the Lambda function
- Create Function
- Runtime: Python 3.11.
- Handler: `src.lambda.lambda_handler`.
- Memory + timeout: start with 1024 MB and 30 seconds; fine-tune after observing metrics.
- Environment variables:
  - `S3_BUCKET=bucket_name`
  - `MODEL_KEY=models/model.pkl`
  - Optional: `FREQ_ENCODER_KEY=models/freq_encoder.pkl`, `TARGET_ENCODER_KEY=models/target_encoder.pkl`, `TRAIN_FEATURES_KEY=processed/feature_engineered_train.csv`, `ARTIFACT_DIR=/tmp/ml_artifacts`
- Upload the ZIP or point to the S3 object containing it.
- (Optional) Add a Lambda layer ARN if you split dependencies.

## 5. Build the API Gateway front door
- Create an **HTTP API** (lighter latency) or **REST API** (legacy) depending on your needs.
- Define a `POST /predict` route.
- Integration type: Lambda proxy → select the Lambda function created above.
- Enable CORS if browsers will call the endpoint directly.
- Deploy the API to a stage (e.g., `prod`) and note the invoke URL.

## 6. Test the end-to-end flow
- In the API Gateway console, send a sample body:
  ```json
  {
    "records": [
      {
        "feature_a": 123,
        "...": "..."
      },
      {
        "feature_a": 456,
        "...": "..."
      }
    ]
  }
  ```
- Alternatively, issue a `curl` request: `curl -X POST "$INVOKE_URL/predict" -H "Content-Type: application/json" -d '{"records": [...]}'.`
- Expect a JSON response containing `predictions`, `count`, and optionally `actuals` when you submit truth labels.

## 7. Observe and operate
- Watch CloudWatch Logs (`/aws/lambda/<function-name>`) to confirm artifacts download once per cold start and to capture stack traces.
- Enable Provisioned Concurrency if cold-start latency is unacceptable.
- Update model versions by uploading the new artifact to S3, then flipping the Lambda env vars (or alias) to the new key after validation.
