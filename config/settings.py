# Configuration settings for the Test Case Generator

# Jira API configuration
jira = {
    "baseUrl": "your-jira-instance.atlassian.net",
    "apiEndpoint": "/rest/api/2",
    "authToken": "Basic YOUR_BASE64_ENCODED_TOKEN",  # Use "Bearer YOUR_TOKEN" for OAuth token
    "testProjectKey": "TEST",  # Project key for test cases
    "projectKey": "PROJ"  # Default project key for user stories
}

# Xray API configuration
xray = {
    "client_id": "YOUR_XRAY_CLIENT_ID",
    "client_secret": "YOUR_XRAY_CLIENT_SECRET",
    "use_bulk_import": True,  # Use bulk import for multiple test cases
    "defaultTestType": "Manual",  # Default test type (Manual, Automated, etc.)
    "debug_mode": False  # Enable for more detailed logging
}

# Generator configuration
generator = {
    "outputBaseDir": "output",  # Base directory for generated test cases
    "knowledgeBaseDir": "knowledge_base"  # Directory containing knowledge base files
}

# Claude API configuration
claude = {
    "apiKey": "sk-ant-api03-YOUR-API-KEY",
    "apiModel": "claude-3-opus-20240229",  # Use the appropriate Claude model
    "promptTemplate": """You are a quality assurance expert specialized in analyzing user stories and generating comprehensive test cases. Focus on both functional tests (verifying behavior) and edge cases (validating handling of unexpected inputs or situations).

User Story Title: {USER_STORY_SUMMARY}

User Story Description:
{USER_STORY_DESCRIPTION}

Create a set of detailed test cases for this user story, considering different scenarios, edge cases, and validation requirements. Each test case should include:

1. A specific, descriptive title starting with the user story title
2. A clear description of what the test is verifying
3. Detailed test steps including:
   - Action (what the user does)
   - Test data (specific inputs to use)
   - Expected result (what should happen)

Format your response as a JSON array of test case objects with the following structure:
```json
[
  {
    "summary": "Title of the test case",
    "description": "Detailed description of what this test verifies",
    "steps": [
      {
        "action": "Specific user action",
        "data": "Test data to use",
        "result": "Expected outcome"
      },
      // Additional steps...
    ]
  },
  // Additional test cases...
]
```

Important guidelines:
- Cover all functional requirements mentioned in the user story
- Include boundary conditions and edge cases
- Add validation tests (data validation, error handling)
- Include at least one negative test scenario
- Keep test steps clear, specific and actionable

Return ONLY the valid JSON array of test cases, with no additional explanation.
"""
}

# Knowledge Base configuration
knowledge_base = {
    "use_knowledge_base": True,  # Enable or disable knowledge base enhancement
    "similarity_threshold": 0.65  # Threshold for considering content relevant (0.0 to 1.0)
}