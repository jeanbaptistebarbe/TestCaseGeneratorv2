# Test Case Generator v2 Documentation

## Overview

Test Case Generator v2 is an application that automatically generates comprehensive test cases from Jira user stories using Claude AI from Anthropic. The generated test cases can be automatically imported into Xray for test management.

## Installation

1. Ensure you have Python 3.8 or higher installed on your system
2. Clone this repository to your local machine
3. Run the `Install.bat` script to install dependencies
4. Configure the application settings in `config/settings.py`

## Configuration

All configuration is stored in `config/settings.py`. You'll need to set the following:

### Jira Configuration

```python
jira = {
    "baseUrl": "your-instance.atlassian.net",       # Your Jira instance URL (without https://)
    "apiEndpoint": "/rest/api/2",                   # Jira API endpoint 
    "authToken": "Basic YOUR_BASE64_ENCODED_TOKEN", # Base64 encoded user:api_token
    "testProjectKey": "TEST",                       # Project key for test cases
    "projectKey": "PROJ"                            # Default project for user stories
}
```

To generate your auth token:
1. Create an API token in Atlassian account settings
2. Encode "email:token" in Base64
3. Add "Basic " prefix to the encoded string

### Xray Configuration

```python
xray = {
    "client_id": "YOUR_XRAY_CLIENT_ID",         # Xray API client ID
    "client_secret": "YOUR_XRAY_CLIENT_SECRET", # Xray API client secret
    "use_bulk_import": True,                    # Use bulk import for multiple test cases
    "defaultTestType": "Manual",                # Default test type
    "debug_mode": False                         # Enable for detailed logging
}
```

To get Xray API credentials:
1. Go to Xray API Keys in your Jira instance
2. Generate a new Client ID and Client Secret
3. Copy these values to the configuration

### Claude API Configuration

```python
claude = {
    "apiKey": "sk-ant-api03-YOUR-API-KEY",   # Claude API key
    "apiModel": "claude-3-opus-20240229",    # Claude model to use
    "promptTemplate": """..."""              # Prompt template for test generation
}
```

To get a Claude API key:
1. Sign up at [Anthropic](https://console.anthropic.com/)
2. Create an API key and copy it to the configuration
3. Select an appropriate model (recommended: claude-3-opus-20240229)

## Using the Application

### GUI Mode

1. Run `TestCaseGenerator.bat` to launch the graphical interface
2. Enter a Jira User Story ID (e.g., "PROJ-123")
3. Click "Generate Test Cases"
4. The application will:
   - Retrieve the user story details from Jira
   - Generate test cases using Claude AI
   - Import the test cases into Xray
   - Create links between the test cases and the user story
5. Results will be displayed in the interface and saved to the output directory

### Command Line Mode

1. Run `GenerateTests.bat` with a user story ID as parameter:
   ```
   GenerateTests.bat PROJ-123
   ```
2. Progress and results will be displayed in the console
3. Generated test cases will be saved to the output directory

## Knowledge Base

The application can enhance test case generation by leveraging domain-specific knowledge stored in the `knowledge_base` directory. Each knowledge base file contains:

- Domain information
- Testing guidelines for the domain
- Sample test cases

The prompt enhancer automatically finds relevant knowledge base files based on the user story content and includes this context in the prompt to Claude.

### Managing the Knowledge Base

- Add new domain knowledge by creating JSON files in the `knowledge_base` directory
- Run `SyncKnowledgeBase.bat` to validate all knowledge base files
- Follow the structure in the example files (e.g., `api_domain_tests.json`)

## Troubleshooting

If you encounter issues:

1. Check the logs in the `output/logs` directory
2. Verify your API keys and connection settings
3. Ensure your Jira permissions allow access to the user story
4. Make sure your Xray license is valid and permissions are set correctly

Common issues:
- "Authentication failed" - Check your Jira/Xray API credentials
- "User story not found" - Verify the user story ID and your permissions
- "Failed to connect" - Check your internet connection or proxy settings
- "Import failed" - Check Xray permissions and project configuration

## Advanced Usage

### Customizing the Prompt Template

The prompt template in `settings.py` can be customized to change the instructions given to Claude. Key aspects to consider:

- Be specific about the test case format and requirements
- Include special instructions for your testing methodology
- Specify formatting guidelines for test steps

### Batch Processing

For batch processing of multiple user stories, you can:

1. Create a list of user story IDs in a text file
2. Create a batch script that reads each ID and calls `run.py`
3. Process results to generate summary reports

## Support

For support and questions, please file an issue in the GitHub repository or contact the maintainers directly.
