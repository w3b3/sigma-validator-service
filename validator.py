#!/usr/bin/env python3
"""
Sigma Rule Validator Service

A lightweight HTTP service that validates Sigma detection rules using pySigma.
Used by sigma2ppl-go to validate rules before conversion to PPL.
"""

from flask import Flask, request, jsonify
from sigma.collection import SigmaCollection
from sigma.exceptions import SigmaError
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate_sigma():
    """
    Validate a Sigma rule using pySigma.

    Request JSON:
        {
            "sigma_rule": "<YAML content as string>"
        }

    Response JSON:
        {
            "valid": true/false,
            "error": "<error message if invalid>",
            "metadata": {
                "title": "<rule title>",
                "id": "<rule id>",
                "level": "<severity level>",
                "status": "<rule status>"
            },
            "rule_count": <number of rules in collection>
        }
    """
    try:
        # Get YAML content from request
        data = request.get_json()

        if not data:
            logger.warning("Request missing JSON body")
            return jsonify({
                'valid': False,
                'error': 'Request must contain JSON body'
            }), 400

        sigma_yaml = data.get('sigma_rule', '')

        if not sigma_yaml:
            logger.warning("Request missing sigma_rule field")
            return jsonify({
                'valid': False,
                'error': 'No sigma_rule provided in request'
            }), 400

        logger.info("Validating Sigma rule...")

        # Parse and validate using pySigma
        try:
            # This validates the Sigma rule structure
            collection = SigmaCollection.from_yaml(sigma_yaml)

            # Get rules from collection
            rules = list(collection.rules)

            if len(rules) == 0:
                logger.warning("No valid rules found in YAML")
                return jsonify({
                    'valid': False,
                    'error': 'No valid Sigma rules found in provided YAML'
                }), 200

            # Extract metadata from first rule
            rule = rules[0]
            metadata = {
                'title': rule.title,
                'id': str(rule.id) if rule.id else None,
                'level': rule.level.name if rule.level else None,
                'status': rule.status.name if rule.status else None
            }

            logger.info(f"✓ Validation passed: {rule.title}")

            return jsonify({
                'valid': True,
                'error': None,
                'metadata': metadata,
                'rule_count': len(rules)
            }), 200

        except SigmaError as e:
            error_msg = f"Sigma validation error: {str(e)}"
            logger.warning(error_msg)
            return jsonify({
                'valid': False,
                'error': error_msg
            }), 200

        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {str(e)}"
            logger.warning(error_msg)
            return jsonify({
                'valid': False,
                'error': error_msg
            }), 200

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'valid': False,
            'error': error_msg
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'sigma-validator',
        'version': '1.0.0'
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information."""
    return jsonify({
        'service': 'Sigma Rule Validator',
        'version': '1.0.0',
        'endpoints': {
            'validate': 'POST /validate',
            'health': 'GET /health'
        },
        'powered_by': 'pySigma'
    }), 200

if __name__ == '__main__':
    logger.info("Starting Sigma Validator Service on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)
