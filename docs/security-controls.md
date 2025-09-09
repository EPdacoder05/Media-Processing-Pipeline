# Security Controls Documentation

## Overview

This document outlines the comprehensive security controls implemented in the Media Processing Pipeline to protect sensitive data and ensure compliance with security best practices.

## 1. Data Protection and Encryption

### 1.1 Encryption at Rest
- **S3 Buckets**: All S3 buckets use AES-256 server-side encryption
- **Parameter Store**: All parameters support encryption with AWS KMS
- **Lambda Environment Variables**: Sensitive configurations stored in Parameter Store, not environment variables

### 1.2 Encryption in Transit
- **HTTPS/TLS**: All communications use SSL/TLS encryption
- **S3 Bucket Policy**: Explicit denial of insecure connections (HTTP)

## 2. Access Controls

### 2.1 S3 Bucket Policies
The following access controls are enforced on all media buckets:

#### Restrictive Access
```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:GetObject",
  "Condition": {
    "StringNotEquals": {
      "aws:PrincipalServiceName": ["lambda.amazonaws.com", "macie2.amazonaws.com"]
    }
  }
}
```

#### Encryption Requirements
- All uploads must specify AES-256 encryption
- Unencrypted uploads are explicitly denied

#### Secure Transport
- HTTP connections are denied
- Only HTTPS/TLS connections allowed

### 2.2 IAM Roles and Policies

#### Lambda Execution Role
- Principle of least privilege applied
- Access limited to specific S3 buckets and actions
- Parameter Store access restricted to project-specific parameters
- Macie read-only access for findings

#### Resource-Based Policies
- S3 bucket policies restrict access to authorized roles only
- Cross-account access prevented by default

## 3. PII Detection and Response

### 3.1 Amazon Macie Configuration
- **Automated Classification**: Daily scheduled jobs scan all media buckets
- **Sensitive Data Types**: Detects credit cards, SSNs, phone numbers, emails
- **Custom Data Identifiers**: Configurable for domain-specific sensitive data

### 3.2 Automated Response System

#### Event-Driven Architecture
```
S3 Upload → Macie Scan → EventBridge → Lambda → Response Actions
```

#### Response Actions by Severity

**HIGH/CRITICAL Severity:**
1. Object quarantine (moved to secure prefix)
2. Access restriction (private ACL)
3. Immediate alert generation
4. Custom event for escalation

**MEDIUM Severity:**
1. Object tagging for tracking
2. Logging for audit trail

**LOW Severity:**
1. Logging and monitoring only

### 3.3 Quarantine Process
```python
# Objects with HIGH/CRITICAL PII findings are:
1. Copied to quarantine/ prefix
2. Tagged with detection metadata
3. Access restricted to private
4. Original location preserved in metadata
```

## 4. Monitoring and Alerting

### 4.1 CloudWatch Integration
- **Lambda Logs**: All processing events logged
- **S3 Access Logs**: Stored in dedicated logging bucket
- **Retention**: 30-day log retention for cost optimization

### 4.2 EventBridge Rules
- **Macie Findings**: Automatic Lambda triggering for medium+ severity
- **Custom Events**: High severity findings generate additional alerts
- **Integration Ready**: Can connect to SNS, SQS, or external systems

### 4.3 Audit Trail
```
Event Type: PII Detection
Timestamp: 2024-01-01T12:00:00Z
Finding ID: finding-12345
Severity: HIGH
Actions Taken: [quarantine, tag, alert]
Object: s3://media-bucket/sensitive-file.pdf
```

## 5. Configuration Management

### 5.1 Parameter Store Structure
```
/media-processing-pipeline/
├── dev/
│   ├── s3/
│   │   ├── media-bucket-name
│   │   ├── processed-bucket-name
│   │   └── media-key-prefix
│   └── security/
│       ├── macie-findings-severity-threshold
│       └── quarantine-retention-days
└── prod/
    └── ... (same structure)
```

### 5.2 Environment Separation
- **Development**: Separate AWS account or strict resource tagging
- **Production**: Enhanced monitoring and stricter access controls
- **Staging**: Production-like configuration for testing

## 6. Compliance and Governance

### 6.1 Data Classification
- **Public**: No sensitive data, minimal protection
- **Internal**: Business data, standard encryption
- **Confidential**: PII/PHI data, enhanced protection + Macie
- **Restricted**: Highly sensitive, manual approval required

### 6.2 Retention Policies
- **Media Files**: Business-defined retention (default: 7 years)
- **Logs**: 30 days for cost optimization
- **Quarantined Files**: 90 days with manual review process

### 6.3 Incident Response
1. **Detection**: Automated via Macie and EventBridge
2. **Containment**: Automatic quarantine for high-severity findings
3. **Investigation**: CloudWatch logs and Macie findings review
4. **Recovery**: Validated clean files restored from quarantine
5. **Lessons Learned**: Security control updates based on findings

## 7. Security Testing

### 7.1 Automated Tests
```bash
# Test PII detection
python3 tests/test_pii_detection.py

# Test access controls
python3 tests/test_s3_access.py

# Test quarantine process
python3 tests/test_quarantine.py
```

### 7.2 Penetration Testing
- **Quarterly**: Third-party security assessment
- **Scope**: S3 access, Lambda functions, IAM policies
- **Remediation**: 30-day SLA for critical findings

## 8. Security Metrics and KPIs

### 8.1 Detection Metrics
- **Mean Time to Detection (MTTD)**: Target < 15 minutes
- **False Positive Rate**: Target < 5%
- **Coverage**: 100% of uploaded files scanned

### 8.2 Response Metrics
- **Mean Time to Response (MTTR)**: Target < 5 minutes for HIGH severity
- **Quarantine Success Rate**: Target > 99%
- **Alert Escalation Time**: Target < 1 minute

## 9. Disaster Recovery

### 9.1 Backup Strategy
- **Cross-Region Replication**: Critical buckets replicated to secondary region
- **Parameter Store**: Backed up via CloudFormation templates
- **Lambda Code**: Stored in versioned S3 buckets

### 9.2 Recovery Procedures
1. **Infrastructure**: CloudFormation stack deployment in DR region
2. **Data**: S3 cross-region replication provides data availability
3. **Configuration**: Parameter Store recreation from backup templates
4. **Testing**: Monthly DR drills with documented procedures

## 10. Updates and Maintenance

### 10.1 Security Patching
- **Lambda Runtime**: Automatic updates to latest supported versions
- **Dependencies**: Monthly security vulnerability scans
- **Infrastructure**: Quarterly review and updates

### 10.2 Policy Reviews
- **IAM Policies**: Quarterly access review
- **S3 Bucket Policies**: Semi-annual review
- **Macie Configuration**: Monthly tuning based on false positives

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-01  
**Next Review**: 2024-04-01  
**Owner**: Security Team  
**Approver**: CISO