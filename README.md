# Sigma Validator Service

A lightweight HTTP service that validates Sigma detection rules using the official [pySigma](https://github.com/SigmaHQ/pySigma) library. This service is used by `sigma2ppl-go` to validate Sigma rules before converting them to OpenSearch PPL queries.

## Overview

This service provides a simple REST API to validate Sigma rules, ensuring they conform to the Sigma specification before processing. It catches syntax errors, missing required fields, and structural issues early in the conversion pipeline.

**Architecture:**
```
sigma2ppl-go (Go) → HTTP POST /validate → Sigma Validator (Python/Docker) → pySigma validation
```

## Features

- **Official pySigma validation**: Uses the authoritative Sigma parser
- **Containerized**: Runs in Docker, no Python installation needed on host
- **Fast**: <50ms validation response time
- **Stateless**: Each request is independent, scales horizontally
- **Healthcheck**: Built-in health monitoring
- **Logging**: Structured logging for debugging

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+ (optional, but recommended)

## Quick Start

### 1. Start the Service

```bash
# Using docker-compose (recommended)
make up

# Or manually
docker-compose up -d
```

### 2. Verify Health

```bash
make health

# Or manually
curl http://localhost:8080/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "service": "sigma-validator",
  "version": "1.0.0"
}
```

### 3. Validate a Sigma Rule

```bash
make test

# Or manually test with a valid rule
curl -X POST http://localhost:8080/validate \
  -H "Content-Type: application/json" \
  -d '{
    "sigma_rule": "title: Suspicious PowerShell\nid: test-001\nstatus: experimental\nlogsource:\n  category: process_creation\n  product: windows\ndetection:\n  selection:\n    CommandLine|contains: \"encodedcommand\"\n  condition: selection"
  }'
```

**Expected response:**
```json
{
  "valid": true,
  "error": null,
  "metadata": {
    "title": "Suspicious PowerShell",
    "id": "test-001",
    "level": null,
    "status": "experimental"
  },
  "rule_count": 1
}
```

## API Reference

### POST /validate

Validates a Sigma rule.

**Request:**
```json
{
  "sigma_rule": "<YAML content as string>"
}
```

**Response (Success):**
```json
{
  "valid": true,
  "error": null,
  "metadata": {
    "title": "Rule Title",
    "id": "rule-id-uuid",
    "level": "high",
    "status": "experimental"
  },
  "rule_count": 1
}
```

**Response (Invalid Rule):**
```json
{
  "valid": false,
  "error": "Sigma validation error: missing required field 'detection'",
  "metadata": null,
  "rule_count": 0
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "sigma-validator",
  "version": "1.0.0"
}
```

### GET /

Service information endpoint.

**Response:**
```json
{
  "service": "Sigma Rule Validator",
  "version": "1.0.0",
  "endpoints": {
    "validate": "POST /validate",
    "health": "GET /health"
  },
  "powered_by": "pySigma"
}
```

## Makefile Commands

```bash
make help      # Show all available commands
make build     # Build Docker image
make up        # Start service (detached mode)
make down      # Stop service
make logs      # View logs (follow mode)
make restart   # Restart service
make health    # Check service health
make test      # Test validation endpoint
make status    # Show container status
make clean     # Remove container and image
make rebuild   # Clean, rebuild, and start
```

## Integration with sigma2ppl-go

This service is automatically called by `sigma2ppl-go` when processing Sigma rules. No manual integration needed - just ensure the service is running:

```bash
# Terminal 1: Start validator service
cd tools/sigma-validator-service
make up

# Terminal 2: Run sigma2ppl-go
cd tools/sigma2ppl-go
./bin/sigma2ppl --sigma rules/
```

The Go application will:
1. Check validator service health on startup
2. Validate each Sigma rule before conversion
3. Skip invalid rules and log detailed errors
4. Only send valid rules to Ollama for PPL conversion

## Configuration

### Port Binding

To change the exposed port, edit `docker-compose.yml`:

```yaml
services:
  sigma-validator:
    ports:
      - "9090:8080"  # Change left side (host port)
```

### Resource Limits

Add resource constraints in `docker-compose.yml`:

```yaml
services:
  sigma-validator:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Validation Examples

### Valid Sigma Rule

```yaml
title: Suspicious PowerShell Encoded Command
id: test-001
status: experimental
description: Detects encoded PowerShell commands
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - '-encodedcommand'
      - '-enc '
  condition: selection
level: high
```

**Result:** `valid: true`

### Invalid Sigma Rule (Missing Detection)

```yaml
title: Incomplete Rule
id: test-002
logsource:
  category: process_creation
  product: windows
```

**Result:** `valid: false, error: "missing required field 'detection'"`

### Invalid Sigma Rule (Bad YAML)

```yaml
title: Broken YAML
id: test-003
logsource:
  category: process_creation
detection:
  selection:
    - bad indent
```

**Result:** `valid: false, error: "YAML parsing error: ..."`

## Troubleshooting

### Service Not Starting

**Problem:** `docker-compose up` fails

**Solutions:**
1. Check if port 8080 is already in use:
   ```bash
   lsof -i :8080
   ```

2. View detailed logs:
   ```bash
   docker-compose logs sigma-validator
   ```

3. Rebuild from scratch:
   ```bash
   make rebuild
   ```

### Connection Refused

**Problem:** `curl: (7) Failed to connect to localhost port 8080: Connection refused`

**Solutions:**
1. Verify container is running:
   ```bash
   make status
   # or
   docker ps | grep sigma-validator
   ```

2. Check container logs:
   ```bash
   make logs
   ```

3. Restart service:
   ```bash
   make restart
   ```

### Validation Errors

**Problem:** Valid-looking Sigma rule fails validation

**Solutions:**
1. Check Sigma specification: https://github.com/SigmaHQ/sigma-specification
2. Validate manually with pySigma:
   ```bash
   # Enter container
   docker exec -it sigma-validator /bin/bash

   # Test interactively
   python3
   >>> from sigma.collection import SigmaCollection
   >>> SigmaCollection.from_yaml("your rule here")
   ```

3. Check pySigma version compatibility:
   ```bash
   docker exec sigma-validator pip list | grep pysigma
   ```

## Development

### Running Locally Without Docker

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run service
python3 validator.py
```

### Updating pySigma Version

Edit `requirements.txt`:
```txt
pysigma==0.12.0  # Update version
```

Then rebuild:
```bash
make rebuild
```

### Adding Custom Validation Rules

Edit `validator.py` and add custom checks after line 67:

```python
# Additional validation can be done here
rules = list(collection.rules)

# Custom validation example
for rule in rules:
    if not rule.level:
        return jsonify({
            'valid': False,
            'error': 'Rule must specify a severity level'
        }), 200
```

## Performance

- **Validation time:** 10-50ms per rule
- **Memory usage:** ~100MB baseline
- **Concurrent requests:** Handles 100+ req/s on standard hardware
- **Startup time:** ~3-5 seconds

## Security

- **Non-root user:** Container runs as `validator` user (UID 1000)
- **Read-only:** No file system writes required
- **No external network:** Validator doesn't make outbound connections
- **Input validation:** All requests are sanitized

## Integration with Arancia XDR Platform

This validator service integrates into the detection engineering pipeline:

```
SIGMA Rules → Validator Service → sigma2ppl-go → PPL Queries → OpenSearch → Detection
```

1. **Rule Authoring:** Write Sigma rules in `security-rules/`
2. **Validation:** Automatic validation via this service
3. **Conversion:** Valid rules converted to PPL by sigma2ppl-go
4. **Testing:** Test PPL in OpenSearch Dashboards
5. **Deployment:** Store in catalog service, activate in sight-detector

## Resources

- [pySigma Documentation](https://github.com/SigmaHQ/pySigma)
- [Sigma Specification](https://github.com/SigmaHQ/sigma-specification)
- [Sigma Rule Repository](https://github.com/SigmaHQ/sigma)
- [OpenSearch PPL](https://opensearch.org/docs/latest/search-plugins/sql/ppl/)

## License

Part of the Arancia XDR platform. Refer to the root repository for license information.
