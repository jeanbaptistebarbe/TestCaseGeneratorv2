# Utility functions for the Test Case Generator
import json
import requests
import os
import logging
import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import settings

def setup_logging():
    """Configure basic logging for the application"""
    logs_dir = os.path.join(settings.generator["outputBaseDir"], 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(logs_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'))
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def make_request(url, method='GET', headers=None, data=None, json_data=None):
    """
    Make an HTTP request
    
    Args:
        url (str): Request URL
        method (str): HTTP method (GET, POST, etc.)
        headers (dict): Request headers
        data (str): Raw data to send
        json_data (dict): JSON data to send
    
    Returns:
        dict or str: Response data
    """
    logger.info(f"Making {method} request to: {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            if json_data:
                response = requests.post(url, headers=headers, json=json_data)
            else:
                response = requests.post(url, headers=headers, data=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            # Save raw response for diagnostic if it's the Claude API
            if 'api.anthropic.com' in url:
                logs_dir = os.path.join(settings.generator["outputBaseDir"], 'logs')
                if not os.path.exists(logs_dir):
                    os.makedirs(logs_dir, exist_ok=True)
                log_file = os.path.join(logs_dir, f'raw_response_{datetime.now().timestamp()}.txt')
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"Raw response saved to {log_file} for diagnosis")
            
            try:
                return response.json() if response.text else {}
            except json.JSONDecodeError as e:
                logger.warning(f"Response is not JSON or contains invalid JSON: {e}")
                logger.info("Returning raw response...")
                return response.text
        else:
            # Log a shorter version of the error
            error_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
            error_msg = f"HTTP Error {response.status_code}: {error_preview}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise