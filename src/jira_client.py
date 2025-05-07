# Jira API client for the Test Case Generator
import logging
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import settings
from utils import make_request

logger = logging.getLogger(__name__)

def get_jira_issue(issue_key):
    """
    Get details of a Jira issue
    
    Args:
        issue_key (str): The key of the Jira issue
    
    Returns:
        dict: Issue details
    """
    url = f"https://{settings.jira['baseUrl']}{settings.jira['apiEndpoint']}/issue/{issue_key}?expand=renderedFields"
    headers = {
        'Authorization': settings.jira['authToken']
    }
    
    return make_request(url, method='GET', headers=headers)

def create_xray_test_case(test_case_data):
    """
    Create a test case in Jira using standard API
    
    Args:
        test_case_data (dict): Test case data
    
    Returns:
        dict: Created issue
    """
    # Convertir les étapes de test en format texte pour la description
    steps_formatted = []
    for i, step in enumerate(test_case_data['steps']):
        steps_formatted.append(
            f"**Step {i+1}:**\n* **Action:** {step['action']}\n* **Data:** {step['data']}\n* **Expected Result:** {step['result']}"
        )
    
    steps_text = '\n\n'.join(steps_formatted)
    
    # Créer le test case avec les champs Jira standards
    create_data = {
        "fields": {
            "project": {
                "key": settings.jira["testProjectKey"]
            },
            "summary": test_case_data["summary"],
            "description": f"{test_case_data['description']}\n\n## Test Steps\n\n{steps_text}",
            "issuetype": {
                "name": "Test"
            }
        }
    }
    
    url = f"https://{settings.jira['baseUrl']}{settings.jira['apiEndpoint']}/issue"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': settings.jira['authToken']
    }
    
    try:
        # Créer le test case
        create_result = make_request(url, method='POST', headers=headers, json_data=create_data)
        logger.info(f"Test case created: {create_result['key']}")
        
        return create_result
    except Exception as error:
        logger.error(f'Error creating test case: {str(error)}')
        raise

def create_issue_link(test_case_key, user_story_key):
    """
    Create a link between a test case and user story
    
    Args:
        test_case_key (str): The key of the test case
        user_story_key (str): The key of the user story
    
    Returns:
        dict: Link result
    """
    link_data = {
        "type": {
            "name": "Test"
        },
        "inwardIssue": {
            "key": test_case_key
        },
        "outwardIssue": {
            "key": user_story_key
        }
    }
    
    url = f"https://{settings.jira['baseUrl']}{settings.jira['apiEndpoint']}/issueLink"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': settings.jira['authToken']
    }
    
    try:
        make_request(url, method='POST', headers=headers, json_data=link_data)
        return {
            "success": True,
            "message": f"Link created between {test_case_key} and {user_story_key}"
        }
    except Exception as error:
        logger.error(f"Error creating link: {str(error)}")
        return {
            "success": False,
            "error": str(error)
        }