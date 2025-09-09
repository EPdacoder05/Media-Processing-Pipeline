import json
import boto3
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
ssm_client = boto3.client('ssm')
s3_client = boto3.client('s3')
macie_client = boto3.client('macie2')
events_client = boto3.client('events')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing PII detection events from Amazon Macie.
    
    Args:
        event: EventBridge event containing Macie findings
        context: Lambda context object
        
    Returns:
        Response dictionary with status and message
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Get configuration from Parameter Store
        config = get_configuration()
        
        # Process the event
        if event.get('source') == 'aws.macie2':
            result = process_macie_finding(event, config)
        else:
            logger.warning(f"Unexpected event source: {event.get('source')}")
            result = {"processed": False, "reason": "Unknown event source"}
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Event processed successfully',
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Event processing failed',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def get_configuration() -> Dict[str, str]:
    """
    Retrieve configuration from Parameter Store.
    
    Returns:
        Dictionary containing configuration parameters
    """
    project_name = os.environ.get('PROJECT_NAME', 'media-processing-pipeline')
    environment = os.environ.get('ENVIRONMENT', 'dev')
    
    parameter_prefix = f'/{project_name}/{environment}'
    
    try:
        response = ssm_client.get_parameters_by_path(
            Path=parameter_prefix,
            Recursive=True,
            WithDecryption=True
        )
        
        config = {}
        for param in response['Parameters']:
            key = param['Name'].replace(parameter_prefix + '/', '')
            config[key] = param['Value']
            
        logger.info(f"Retrieved {len(config)} configuration parameters")
        return config
        
    except Exception as e:
        logger.error(f"Failed to retrieve configuration: {str(e)}")
        raise

def process_macie_finding(event: Dict[str, Any], config: Dict[str, str]) -> Dict[str, Any]:
    """
    Process a Macie finding event.
    
    Args:
        event: EventBridge event from Macie
        config: Configuration dictionary from Parameter Store
        
    Returns:
        Processing result dictionary
    """
    detail = event.get('detail', {})
    finding_id = detail.get('id')
    severity = detail.get('severity', {}).get('description', 'UNKNOWN')
    finding_type = detail.get('type')
    
    logger.info(f"Processing Macie finding {finding_id} with severity {severity}")
    
    # Extract affected resources
    affected_resources = detail.get('resources', [])
    
    result = {
        'finding_id': finding_id,
        'severity': severity,
        'type': finding_type,
        'actions_taken': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    for resource in affected_resources:
        if resource.get('resourceType') == 'S3Object':
            s3_resource = resource.get('s3Object', {})
            bucket_name = s3_resource.get('bucketName')
            object_key = s3_resource.get('key')
            
            if bucket_name and object_key:
                action_result = handle_pii_in_s3_object(
                    bucket_name, 
                    object_key, 
                    severity, 
                    config
                )
                result['actions_taken'].append(action_result)
    
    # Send custom event for high severity findings
    if severity in ['HIGH', 'CRITICAL']:
        send_high_severity_alert(result, config)
    
    return result

def handle_pii_in_s3_object(
    bucket_name: str, 
    object_key: str, 
    severity: str, 
    config: Dict[str, str]
) -> Dict[str, Any]:
    """
    Handle PII detected in an S3 object.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        severity: Severity level of the finding
        config: Configuration dictionary
        
    Returns:
        Action result dictionary
    """
    action_result = {
        'bucket': bucket_name,
        'key': object_key,
        'severity': severity,
        'actions': []
    }
    
    try:
        # For high severity findings, quarantine the object
        if severity in ['HIGH', 'CRITICAL']:
            quarantine_result = quarantine_object(bucket_name, object_key, config)
            action_result['actions'].append(quarantine_result)
        
        # Tag the object for tracking
        tag_result = tag_object_with_pii_info(bucket_name, object_key, severity)
        action_result['actions'].append(tag_result)
        
        # Log the finding details
        logger.info(f"Handled PII in {bucket_name}/{object_key} with severity {severity}")
        
    except Exception as e:
        logger.error(f"Error handling PII in {bucket_name}/{object_key}: {str(e)}")
        action_result['error'] = str(e)
    
    return action_result

def quarantine_object(bucket_name: str, object_key: str, config: Dict[str, str]) -> Dict[str, Any]:
    """
    Quarantine an object by moving it to a secure location or applying restrictions.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        config: Configuration dictionary
        
    Returns:
        Quarantine action result
    """
    try:
        # Get the quarantine bucket from config or use a quarantine prefix
        quarantine_prefix = 'quarantine/'
        quarantine_key = f"{quarantine_prefix}{object_key}"
        
        # Copy object to quarantine location
        copy_source = {'Bucket': bucket_name, 'Key': object_key}
        s3_client.copy_object(
            CopySource=copy_source,
            Bucket=bucket_name,
            Key=quarantine_key,
            ServerSideEncryption='AES256',
            Metadata={
                'quarantine-reason': 'PII-detected',
                'quarantine-timestamp': datetime.utcnow().isoformat(),
                'original-key': object_key
            },
            MetadataDirective='REPLACE'
        )
        
        # Remove public access by applying restrictive ACL
        s3_client.put_object_acl(
            Bucket=bucket_name,
            Key=quarantine_key,
            ACL='private'
        )
        
        logger.info(f"Quarantined object: {bucket_name}/{object_key} -> {bucket_name}/{quarantine_key}")
        
        return {
            'action': 'quarantine',
            'status': 'success',
            'quarantine_location': f"{bucket_name}/{quarantine_key}"
        }
        
    except Exception as e:
        logger.error(f"Failed to quarantine object {bucket_name}/{object_key}: {str(e)}")
        return {
            'action': 'quarantine',
            'status': 'failed',
            'error': str(e)
        }

def tag_object_with_pii_info(bucket_name: str, object_key: str, severity: str) -> Dict[str, Any]:
    """
    Tag an S3 object with PII detection information.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        severity: Severity level
        
    Returns:
        Tagging action result
    """
    try:
        tags = {
            'pii-detected': 'true',
            'pii-severity': severity.lower(),
            'pii-detection-date': datetime.utcnow().strftime('%Y-%m-%d'),
            'security-status': 'flagged'
        }
        
        # Convert tags to the format expected by S3
        tag_set = [{'Key': k, 'Value': v} for k, v in tags.items()]
        
        s3_client.put_object_tagging(
            Bucket=bucket_name,
            Key=object_key,
            Tagging={'TagSet': tag_set}
        )
        
        logger.info(f"Tagged object {bucket_name}/{object_key} with PII information")
        
        return {
            'action': 'tag',
            'status': 'success',
            'tags_applied': tags
        }
        
    except Exception as e:
        logger.error(f"Failed to tag object {bucket_name}/{object_key}: {str(e)}")
        return {
            'action': 'tag',
            'status': 'failed',
            'error': str(e)
        }

def send_high_severity_alert(result: Dict[str, Any], config: Dict[str, str]) -> None:
    """
    Send an alert for high severity PII findings.
    
    Args:
        result: Processing result dictionary
        config: Configuration dictionary
    """
    try:
        # Create a custom event for high severity findings
        event_detail = {
            'finding_id': result['finding_id'],
            'severity': result['severity'],
            'type': result['type'],
            'actions_taken': result['actions_taken'],
            'alert_level': 'HIGH',
            'timestamp': result['timestamp']
        }
        
        events_client.put_events(
            Entries=[
                {
                    'Source': 'media-processing-pipeline.security',
                    'DetailType': 'High Severity PII Detection',
                    'Detail': json.dumps(event_detail),
                    'Time': datetime.utcnow()
                }
            ]
        )
        
        logger.info(f"Sent high severity alert for finding {result['finding_id']}")
        
    except Exception as e:
        logger.error(f"Failed to send high severity alert: {str(e)}")