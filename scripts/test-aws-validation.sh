#!/bin/bash

# AWS CloudFormation Template Validation Test
# This script validates the template syntax without deploying

echo "🔍 Validating CloudFormation template with AWS CLI..."

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI to run this test."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "⚠️  AWS credentials not configured. Skipping AWS validation."
    echo "ℹ️  To run AWS validation, configure credentials with: aws configure"
    exit 0
fi

# Validate the CloudFormation template
echo "Validating cloudformation/main-infrastructure.yaml..."
if aws cloudformation validate-template --template-body file://cloudformation/main-infrastructure.yaml &>/dev/null; then
    echo "✅ CloudFormation template is valid!"
else
    echo "❌ CloudFormation template validation failed:"
    aws cloudformation validate-template --template-body file://cloudformation/main-infrastructure.yaml
    exit 1
fi

echo "🎉 All AWS validations passed!"