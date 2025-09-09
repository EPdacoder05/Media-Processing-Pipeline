# Media Processing Pipeline

A secure, cost-optimized AWS-based media processing pipeline with automated PII detection, event-driven security responses, and comprehensive access controls.

## 🚀 Features

- **🔒 Security-First Design**: Comprehensive data protection with encryption at rest and in transit
- **🤖 Automated PII Detection**: Amazon Macie integration for sensitive data identification
- **⚡ Event-Driven Architecture**: Real-time response to security events using EventBridge and Lambda
- **🛡️ Access Controls**: Strict S3 bucket policies and IAM role-based access
- **📊 Cost Optimization**: Intelligent storage tiering and resource optimization
- **📋 Compliance Ready**: Audit trails, retention policies, and governance controls

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   S3 Media  │────│   Amazon    │────│ EventBridge │────│   Lambda    │
│   Buckets   │    │   Macie     │    │    Rules    │    │ Functions   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                                       │                 │
       │            ┌─────────────┐            │                 │
       └────────────│ Parameter   │            │                 │
                    │   Store     │            │                 │
                    └─────────────┘            │                 │
                                              │                 │
                    ┌─────────────┐            │                 │
                    │ CloudWatch  │←───────────┼─────────────────┘
                    │    Logs     │            │
                    └─────────────┘            │
                                              │
                    ┌─────────────┐            │
                    │   Custom    │←───────────┘
                    │   Events    │
                    └─────────────┘
```

## 📁 Project Structure

```
├── cloudformation/          # Infrastructure as Code
│   └── main-infrastructure.yaml
├── lambda/                  # Lambda function source code
│   └── pii_processor.py
├── policies/               # IAM and S3 bucket policies
│   ├── s3-bucket-policy-template.json
│   └── lambda-execution-policy.json
├── scripts/                # Deployment and utility scripts
│   ├── deploy.sh
│   └── apply-bucket-policies.py
├── docs/                   # Documentation
│   ├── security-controls.md
│   └── cost-controls.md
├── requirements.txt        # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.9 or later
- Bash shell (for deployment scripts)

### Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/EPdacoder05/Media-Processing-Pipeline.git
   cd Media-Processing-Pipeline
   ```

2. **Deploy the infrastructure**
   ```bash
   ./scripts/deploy.sh dev us-east-1
   ```

3. **Verify deployment**
   ```bash
   aws cloudformation describe-stacks --stack-name media-processing-pipeline-dev
   ```

### Configuration

The pipeline uses AWS Parameter Store for configuration management:

```
/media-processing-pipeline/dev/
├── s3/media-bucket-name          # Main media storage bucket
├── s3/processed-bucket-name      # Processed media bucket
└── s3/media-key-prefix          # S3 key prefix for organization
```

## 🔐 Security Features

### Data Protection
- **Encryption**: AES-256 encryption for all S3 objects
- **Access Control**: Principle of least privilege IAM policies
- **Secure Transport**: HTTPS/TLS required for all communications
- **Public Access**: Blocked at bucket level

### PII Detection & Response
- **Automated Scanning**: Daily Macie classification jobs
- **Real-time Response**: EventBridge triggers for immediate action
- **Quarantine Process**: Automatic isolation of sensitive files
- **Audit Trail**: Comprehensive logging of all security events

### Event-Driven Security

When Macie detects PII:
1. **High/Critical Severity**: Immediate quarantine + alert
2. **Medium Severity**: File tagging + monitoring
3. **Low Severity**: Logging for audit purposes

## 💰 Cost Optimization

### Storage Optimization
- **Intelligent Tiering**: Automatic transition to cheaper storage classes
- **Lifecycle Policies**: Automated deletion based on retention requirements
- **Cross-Region Strategy**: Optimized for lowest transfer costs

### Processing Optimization
- **Lambda Rightsizing**: Memory and timeout optimization
- **Batch Processing**: Efficient event handling
- **Scheduled Jobs**: Cost-effective Macie classification timing

### Monitoring & Alerts
- **Budget Controls**: Automated spending alerts and limits
- **Resource Utilization**: Continuous optimization recommendations
- **Cost Anomaly Detection**: Automated spike detection and response

## 📊 Monitoring

### CloudWatch Integration
- **Application Logs**: Lambda function execution logs
- **Access Logs**: S3 bucket access patterns
- **Security Events**: PII detection and response actions
- **Performance Metrics**: Processing latency and throughput

### Custom Dashboards
- **Security Overview**: PII detection trends and response times
- **Cost Analytics**: Spending patterns and optimization opportunities
- **Operational Health**: System performance and availability

## 🔧 Customization

### Adding Custom Data Types
Update the Macie configuration to detect domain-specific sensitive data:

```python
# In lambda/pii_processor.py
CUSTOM_DATA_IDENTIFIERS = [
    'employee-id-pattern',
    'customer-reference-format',
    'internal-document-codes'
]
```

### Modifying Response Actions
Customize the automated response based on your requirements:

```python
def handle_pii_in_s3_object(bucket_name, object_key, severity, config):
    if severity == 'HIGH':
        # Custom high-severity actions
        quarantine_object(bucket_name, object_key, config)
        notify_security_team(bucket_name, object_key)
        create_incident_ticket(bucket_name, object_key)
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/test_pii_processor.py -v
```

### Integration Tests
```bash
python -m pytest tests/test_s3_integration.py -v
```

### Security Tests
```bash
python scripts/security-validation.py --environment dev
```

## 📚 Documentation

- **[Security Controls](docs/security-controls.md)**: Comprehensive security implementation details
- **[Cost Controls](docs/cost-controls.md)**: Cost optimization strategies and monitoring
- **[API Documentation](docs/api.md)**: Lambda function APIs and event schemas
- **[Troubleshooting Guide](docs/troubleshooting.md)**: Common issues and solutions

## 🚨 Incident Response

### High-Severity PII Detection
1. **Automatic Response**: File quarantined immediately
2. **Notification**: Security team alerted via EventBridge
3. **Investigation**: Review Macie findings and access logs
4. **Remediation**: Clean file validation and restoration

### Cost Anomalies
1. **Detection**: Automated budget alerts trigger
2. **Investigation**: Cost breakdown analysis
3. **Mitigation**: Resource scaling or emergency shutdown
4. **Root Cause**: Analysis and prevention measures

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow AWS security best practices
- Include unit tests for new features
- Update documentation for significant changes
- Test in development environment before production

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community support
- **Security**: Email security@company.com for security-related concerns

### Emergency Contacts
- **Security Incidents**: security-oncall@company.com
- **Production Issues**: ops-oncall@company.com
- **Cost Alerts**: finops@company.com

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-01  
**Maintainer**: Security Engineering Team