#!/usr/bin/env python
# Script to synchronize and validate the knowledge base
import os
import sys
import json
import logging
import glob
from datetime import datetime

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import project modules
try:
    from config import settings
except ImportError as e:
    print(f"Error importing project modules: {str(e)}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, "output", "logs", f"sync_kb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_knowledge_base_file(file_path):
    """
    Validate a knowledge base file
    
    Args:
        file_path (str): Path to the knowledge base file
    
    Returns:
        tuple: (valid, warnings) - Boolean indicating if file is valid and list of warnings
    """
    warnings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Check required fields
        required_fields = ['domain', 'description', 'keywords', 'sample_tests']
        for field in required_fields:
            if field not in content:
                warnings.append(f"Missing required field: {field}")
        
        # Check sample tests
        if 'sample_tests' in content:
            tests = content['sample_tests']
            if not isinstance(tests, list) or len(tests) == 0:
                warnings.append("sample_tests must be a non-empty array")
            else:
                for i, test in enumerate(tests):
                    test_warnings = validate_test_case(test, i)
                    warnings.extend(test_warnings)
        
        # Check keywords
        if 'keywords' in content:
            keywords = content['keywords']
            if not isinstance(keywords, list) or len(keywords) == 0:
                warnings.append("keywords must be a non-empty array")
            else:
                for keyword in keywords:
                    if not isinstance(keyword, str) or len(keyword.strip()) == 0:
                        warnings.append(f"Invalid keyword: {keyword}")
        
        return len(warnings) == 0, warnings
    except json.JSONDecodeError as e:
        warnings.append(f"Invalid JSON format: {str(e)}")
        return False, warnings
    except Exception as e:
        warnings.append(f"Error validating file: {str(e)}")
        return False, warnings

def validate_test_case(test_case, index):
    """
    Validate a test case
    
    Args:
        test_case (dict): The test case to validate
        index (int): Index of the test case in the file
    
    Returns:
        list: Warnings found during validation
    """
    warnings = []
    
    # Check required fields
    required_fields = ['summary', 'description', 'steps']
    for field in required_fields:
        if field not in test_case:
            warnings.append(f"Test case {index}: Missing required field: {field}")
    
    # Check steps
    if 'steps' in test_case:
        steps = test_case['steps']
        if not isinstance(steps, list) or len(steps) == 0:
            warnings.append(f"Test case {index}: steps must be a non-empty array")
        else:
            for j, step in enumerate(steps):
                step_warnings = validate_step(step, index, j)
                warnings.extend(step_warnings)
    
    return warnings

def validate_step(step, test_index, step_index):
    """
    Validate a test step
    
    Args:
        step (dict): The step to validate
        test_index (int): Index of the parent test case
        step_index (int): Index of the step
    
    Returns:
        list: Warnings found during validation
    """
    warnings = []
    
    # Check required fields
    required_fields = ['action', 'data', 'result']
    for field in required_fields:
        if field not in step:
            warnings.append(f"Test case {test_index}, Step {step_index}: Missing required field: {field}")
    
    return warnings

def main():
    """
    Main function to synchronize and validate knowledge base
    """
    logger.info("Starting knowledge base synchronization")
    
    # Get knowledge base directory
    kb_dir = os.path.join(parent_dir, settings.generator["knowledgeBaseDir"])
    if not os.path.exists(kb_dir):
        logger.error(f"Knowledge base directory not found: {kb_dir}")
        print(f"Error: Knowledge base directory not found: {kb_dir}")
        sys.exit(1)
    
    logger.info(f"Validating knowledge base files in: {kb_dir}")
    
    # Find and validate all JSON files
    files = glob.glob(os.path.join(kb_dir, "*.json"))
    logger.info(f"Found {len(files)} knowledge base files")
    
    valid_count = 0
    warning_count = 0
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        logger.info(f"Validating: {file_name}")
        
        valid, warnings = validate_knowledge_base_file(file_path)
        
        if valid:
            logger.info(f"✅ {file_name} is valid")
            valid_count += 1
        else:
            logger.warning(f"⚠️ {file_name} has warnings/errors")
            warning_count += 1
        
        # Print warnings if any
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    # Summary
    logger.info("Knowledge base validation completed")
    logger.info(f"Total files: {len(files)}, Valid: {valid_count}, With warnings/errors: {warning_count}")
    
    # Print summary to console
    print("\nKnowledge base validation completed:")
    print(f"Total files: {len(files)}")
    print(f"Valid files: {valid_count}")
    print(f"Files with warnings/errors: {warning_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error in knowledge base synchronization: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1)
