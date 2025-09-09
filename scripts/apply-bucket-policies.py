#!/usr/bin/env python3

import json
import boto3
import argparse
import sys
from typing import Dict, Any

def load_policy_template(template_path: str) -> Dict[str, Any]:
    """Load S3 bucket policy template."""
    with open(template_path, 'r') as f:
        return json.load(f)

def apply_bucket_policy(bucket_name: str, policy: Dict[str, Any], s3_client) -> bool:
    """Apply policy to S3 bucket."""
    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(policy)
        )
        print(f"✓ Applied policy to bucket: {bucket_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to apply policy to bucket {bucket_name}: {str(e)}")
        return False

def get_stack_outputs(stack_name: str, region: str) -> Dict[str, str]:
    """Get CloudFormation stack outputs."""
    cf_client = boto3.client('cloudformation', region_name=region)
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0].get('Outputs', [])
        
        result = {}
        for output in outputs:
            result[output['OutputKey']] = output['OutputValue']
        
        return result
    except Exception as e:
        print(f"Error getting stack outputs: {str(e)}")
        sys.exit(1)

def substitute_policy_placeholders(
    policy: Dict[str, Any], 
    bucket_name: str, 
    account_id: str, 
    role_name: str
) -> Dict[str, Any]:
    """Replace placeholders in policy template."""
    policy_str = json.dumps(policy)
    policy_str = policy_str.replace('BUCKET_NAME', bucket_name)
    policy_str = policy_str.replace('ACCOUNT_ID', account_id)
    policy_str = policy_str.replace('ROLE_NAME', role_name)
    
    return json.loads(policy_str)

def main():
    parser = argparse.ArgumentParser(description='Apply S3 bucket policies')
    parser.add_argument('--environment', '-e', required=True, help='Environment (dev/staging/prod)')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region')
    parser.add_argument('--project-name', '-p', default='media-processing-pipeline', help='Project name')
    
    args = parser.parse_args()
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=args.region)
    sts_client = boto3.client('sts', region_name=args.region)
    
    # Get account ID
    account_id = sts_client.get_caller_identity()['Account']
    
    # Get stack outputs
    stack_name = f"{args.project_name}-{args.environment}"
    outputs = get_stack_outputs(stack_name, args.region)
    
    if 'MediaBucketName' not in outputs:
        print("Error: Could not find MediaBucketName in stack outputs")
        sys.exit(1)
    
    # Load policy template
    policy_template = load_policy_template('policies/s3-bucket-policy-template.json')
    
    # Apply policies to buckets
    buckets_to_secure = [
        {
            'name': outputs['MediaBucketName'],
            'role': f"{args.project_name}-{args.environment}-lambda-role"
        }
    ]
    
    if 'ProcessedBucketName' in outputs:
        buckets_to_secure.append({
            'name': outputs['ProcessedBucketName'],
            'role': f"{args.project_name}-{args.environment}-lambda-role"
        })
    
    print(f"Applying bucket policies for {len(buckets_to_secure)} buckets...")
    
    success_count = 0
    for bucket_config in buckets_to_secure:
        bucket_name = bucket_config['name']
        role_name = bucket_config['role']
        
        # Substitute placeholders in policy
        policy = substitute_policy_placeholders(
            policy_template.copy(),
            bucket_name,
            account_id,
            role_name
        )
        
        # Apply the policy
        if apply_bucket_policy(bucket_name, policy, s3_client):
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(buckets_to_secure)} bucket policies applied successfully")
    
    if success_count == len(buckets_to_secure):
        print("✓ All bucket policies applied successfully!")
        sys.exit(0)
    else:
        print("✗ Some bucket policies failed to apply")
        sys.exit(1)

if __name__ == '__main__':
    main()