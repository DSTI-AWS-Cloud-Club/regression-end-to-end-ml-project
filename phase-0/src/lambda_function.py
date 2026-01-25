"""
AWS Lambda Function for Demand Prediction
==========================================

This function predicts product demand based on pricing using a log-log regression model.
It uses boto3 (pre-installed in Lambda) for S3 access and implements regression from scratch.

Input: JSON with 'prices' array [Price_Milk, Price_Chocolate, Price_Soup, Price_Ramen]
Output: JSON with predicted demands for each product
"""

import json
import math
import boto3
from typing import List, Dict, Any


# ===========================
# CONFIGURATION
# ===========================
BUCKET_NAME = "your-bucket-name-here"  # UPDATE THIS
DATA_KEY = "demand_data.csv"
REGION = "us-east-1"  # UPDATE THIS


# ===========================
# CORE FUNCTIONS
# ===========================

def download_data_from_s3(bucket: str, key: str, region: str) -> str:
    """
    Downloads CSV data from S3 using boto3 with IAM role authentication.
    
    Args:
        bucket: S3 bucket name
        key: Object key (file name)
        region: AWS region
        
    Returns:
        CSV content as string
    """
    try:
        # Initialize S3 client (boto3 is pre-installed in Lambda runtime)
        s3_client = boto3.client('s3', region_name=region)
        
        # Get object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        # Read and decode content
        csv_content = response['Body'].read().decode('utf-8')
        
        return csv_content
    except Exception as e:
        # Provide detailed error message for debugging
        error_msg = (
            f"Failed to download from S3. "
            f"Bucket: '{bucket}', Key: '{key}', Region: '{region}'. "
            f"Error: {str(e)}. "
            f"Check: 1) Bucket name is correct, 2) Region matches bucket location, "
            f"3) IAM role has s3:GetObject permission for this bucket"
        )
        raise Exception(error_msg)


def parse_csv(csv_content: str) -> Dict[str, List[float]]:
    """
    Parses CSV content into a dictionary of columns.
    
    Args:
        csv_content: CSV string with header
        
    Returns:
        Dictionary mapping column names to lists of values
    """
    lines = csv_content.strip().split('\n')
    
    if len(lines) < 2:
        raise ValueError("CSV must have at least header and one data row")
    
    # Parse header - strip whitespace from column names
    header = [col.strip() for col in lines[0].split(',')]
    
    # Initialize data dictionary
    data = {col: [] for col in header}
    
    # Parse data rows
    for line in lines[1:]:
        values = line.split(',')
        if len(values) != len(header):
            continue  # Skip malformed rows
        
        for col, val in zip(header, values):
            try:
                data[col].append(float(val.strip()))
            except ValueError:
                continue  # Skip non-numeric values
    
    return data


def calculate_mean(values: List[float]) -> float:
    """Calculate arithmetic mean."""
    return sum(values) / len(values) if values else 0.0


def calculate_covariance(x: List[float], y: List[float]) -> float:
    """Calculate covariance between two lists."""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    
    mean_x = calculate_mean(x)
    mean_y = calculate_mean(y)
    
    return sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / len(x)


def fit_linear_regression(X: List[List[float]], y: List[float]) -> List[float]:
    """
    Fits simple linear regression using ordinary least squares.
    Returns coefficients [intercept, coef1, coef2, ...]
    
    This uses the closed-form solution: beta = (X'X)^-1 X'y
    Simplified implementation for small matrices.
    """
    n = len(y)
    p = len(X[0])  # Number of features
    
    # Add intercept column (all ones) to X
    X_with_intercept = [[1.0] + row for row in X]
    p_with_intercept = p + 1
    
    # Compute X'X (transpose of X times X)
    XtX = [[0.0] * p_with_intercept for _ in range(p_with_intercept)]
    for i in range(p_with_intercept):
        for j in range(p_with_intercept):
            XtX[i][j] = sum(X_with_intercept[k][i] * X_with_intercept[k][j] for k in range(n))
    
    # Compute X'y (transpose of X times y)
    Xty = [sum(X_with_intercept[k][i] * y[k] for k in range(n)) for i in range(p_with_intercept)]
    
    # Solve XtX * beta = Xty using Gaussian elimination
    beta = solve_linear_system(XtX, Xty)
    
    return beta


def solve_linear_system(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Solves Ax = b using Gaussian elimination with partial pivoting.
    Returns solution vector x.
    """
    n = len(b)
    
    # Create augmented matrix [A|b]
    augmented = [A[i][:] + [b[i]] for i in range(n)]
    
    # Forward elimination
    for i in range(n):
        # Partial pivoting
        max_row = i
        for k in range(i + 1, n):
            if abs(augmented[k][i]) > abs(augmented[max_row][i]):
                max_row = k
        augmented[i], augmented[max_row] = augmented[max_row], augmented[i]
        
        # Check for singular matrix
        if abs(augmented[i][i]) < 1e-10:
            augmented[i][i] = 1e-10  # Regularization
        
        # Eliminate column
        for k in range(i + 1, n):
            factor = augmented[k][i] / augmented[i][i]
            for j in range(i, n + 1):
                augmented[k][j] -= factor * augmented[i][j]
    
    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = augmented[i][n]
        for j in range(i + 1, n):
            x[i] -= augmented[i][j] * x[j]
        x[i] /= augmented[i][i]
    
    return x


def train_demand_model(data: Dict[str, List[float]]) -> Dict[str, List[float]]:
    """
    Trains log-log regression models for each product.
    
    Returns:
        Dictionary mapping product names to regression coefficients
    """
    price_cols = ['Price_Milk', 'Price_Chocolate', 'Price_Soup', 'Price_Ramen']
    demand_cols = ['Demand_Milk', 'Demand_Chocolate', 'Demand_Soup', 'Demand_Ramen']
    
    # Apply log transformation to prices
    log_prices = []
    n_samples = len(data[price_cols[0]])
    
    for i in range(n_samples):
        log_price_row = []
        for col in price_cols:
            price = data[col][i]
            if price > 0:
                log_price_row.append(math.log(price))
            else:
                log_price_row.append(0.0)  # Handle edge case
        log_prices.append(log_price_row)
    
    # Train a model for each product
    models = {}
    
    for demand_col in demand_cols:
        product_name = demand_col.replace('Demand_', '')
        
        # Apply log transformation to demand
        log_demand = []
        for demand in data[demand_col]:
            if demand > 0:
                log_demand.append(math.log(demand))
            else:
                log_demand.append(0.0)  # Handle edge case
        
        # Fit regression: log(Demand) = β0 + β1*log(P1) + β2*log(P2) + β3*log(P3) + β4*log(P4)
        coefficients = fit_linear_regression(log_prices, log_demand)
        models[product_name] = coefficients
    
    return models


def predict_demand(prices: List[float], models: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Predicts demand for all products given prices.
    
    Args:
        prices: List of prices [Price_Milk, Price_Chocolate, Price_Soup, Price_Ramen]
        models: Trained model coefficients for each product
        
    Returns:
        Dictionary mapping product names to predicted demands
    """
    if len(prices) != 4:
        raise ValueError("Expected 4 prices [Milk, Chocolate, Soup, Ramen]")
    
    # Apply log transformation to input prices
    log_prices = [math.log(max(p, 0.01)) for p in prices]  # Avoid log(0)
    
    predictions = {}
    
    for product_name, coefficients in models.items():
        # Compute log(demand) = β0 + β1*log(P1) + ... + β4*log(P4)
        log_demand = coefficients[0]  # Intercept
        for i, log_price in enumerate(log_prices):
            log_demand += coefficients[i + 1] * log_price
        
        # Transform back to original scale
        demand = math.exp(log_demand)
        predictions[product_name] = round(demand, 2)
    
    return predictions


# ===========================
# LAMBDA HANDLER
# ===========================

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Expected event format:
    {
        "prices": [3.5, 4.0, 4.5, 2.5]
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "predictions": {
                "Milk": 850.23,
                "Chocolate": 120.45,
                "Soup": 180.67,
                "Ramen": 200.89
            },
            "input_prices": [3.5, 4.0, 4.5, 2.5]
        }
    }
    """
    try:
        # Parse input
        if isinstance(event, str):
            event = json.loads(event)
        
        # Handle API Gateway proxy integration
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            prices = body.get('prices', [])
        else:
            prices = event.get('prices', [])
        
        if not prices or len(prices) != 4:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid input. Expected "prices" array with 4 values [Milk, Chocolate, Soup, Ramen]',
                    'example': {'prices': [3.5, 4.0, 4.5, 2.5]}
                })
            }
        
        # Validate prices are positive
        if any(p <= 0 for p in prices):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'All prices must be positive numbers'
                })
            }
        
        # Download training data from S3
        # Note: BUCKET_NAME, DATA_KEY, and REGION are defined at the top of this file
        print(f"Attempting to download from S3: Bucket={BUCKET_NAME}, Key={DATA_KEY}, Region={REGION}")
        csv_content = download_data_from_s3(BUCKET_NAME, DATA_KEY, REGION)
        print(f"Successfully downloaded {len(csv_content)} bytes from S3")
        
        # Parse CSV
        data = parse_csv(csv_content)
        
        # Train model
        models = train_demand_model(data)
        
        # Make predictions
        predictions = predict_demand(prices, models)
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'predictions': predictions,
                'input_prices': prices
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


# ===========================
# LOCAL TESTING
# ===========================

if __name__ == "__main__":
    """
    For local testing. Run with: python lambda_function.py
    Uses local CSV file instead of S3 to avoid AWS credential requirements.
    """
    import os
    
    print("Testing Lambda function locally...")
    print("Note: Using local CSV file (not S3) for testing\n")
    
    # Mock event
    test_event = {
        'prices': [3.5, 4.0, 4.5, 2.5]
    }
    
    # Load data from local file
    local_csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'demand_data.csv')
    
    if not os.path.exists(local_csv_path):
        print(f"ERROR: CSV file not found at {local_csv_path}")
        print("Make sure demand_data.csv exists in phase-0/data/ folder")
        exit(1)
    
    print(f"Input: {json.dumps(test_event, indent=2)}")
    print("\nProcessing...\n")
    
    try:
        # Read local CSV
        with open(local_csv_path, 'r') as f:
            csv_content = f.read()
        
        # Parse and train
        data = parse_csv(csv_content)
        models = train_demand_model(data)
        
        # Make predictions
        prices = test_event['prices']
        predictions = predict_demand(prices, models)
        
        # Format response
        result = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'predictions': predictions,
                'input_prices': prices
            })
        }
        
        print(f"✅ Status Code: {result['statusCode']}")
        print(f"Response: {json.dumps(json.loads(result['body']), indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
