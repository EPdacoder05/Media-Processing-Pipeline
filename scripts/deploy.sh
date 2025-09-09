#!/bin/bash

# Deploy Media Processing Pipeline Infrastructure
# Usage: ./deploy.sh [environment] [region]

set -e

# Default values
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
PROJECT_NAME="media-processing-pipeline"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

echo "Deploying Media Processing Pipeline..."
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack: $STACK_NAME"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "Error: AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Package Lambda function
echo "Packaging Lambda function..."
cd lambda
zip -r ../pii-processor.zip pii_processor.py
cd ..

# Create S3 bucket for deployment artifacts if it doesn't exist
DEPLOYMENT_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-deployment-$(aws sts get-caller-identity --query Account --output text)"
if ! aws s3 ls "s3://$DEPLOYMENT_BUCKET" 2>/dev/null; then
    echo "Creating deployment bucket: $DEPLOYMENT_BUCKET"
    aws s3 mb "s3://$DEPLOYMENT_BUCKET" --region "$REGION"
fi

# Upload Lambda code to S3
echo "Uploading Lambda code..."
aws s3 cp pii-processor.zip "s3://$DEPLOYMENT_BUCKET/lambda/pii-processor.zip"

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file cloudformation/main-infrastructure.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ProjectName="$PROJECT_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

# Get stack outputs
echo "Retrieving stack outputs..."
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output table

# Apply S3 bucket policies
echo "Applying S3 bucket policies..."
python3 scripts/apply-bucket-policies.py --environment "$ENVIRONMENT" --region "$REGION"

echo "Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review the deployed resources in the AWS Console"
echo "2. Test the PII detection by uploading a sample file with sensitive data"
echo "3. Monitor CloudWatch logs for processing events"
echo "4. Check Macie findings in the AWS Console"