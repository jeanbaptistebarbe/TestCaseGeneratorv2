# Test Case Generator v2

An automated application that generates comprehensive test cases from Jira User Stories using Claude API and imports them directly into Xray.

## Features

- Automatic retrieval of User Stories from Jira
- Test case generation via Anthropic's Claude API
- Automatic import of test cases into Xray
- Simple and intuitive user interface
- Knowledge base enhancement for domain-specific test cases

## Installation

1. Make sure you have Python 3.8 or higher installed
2. Run the `Install.bat` script to install required dependencies
3. The application will automatically create the `output` directory to store generated test cases

## Configuration

All configuration is stored in the `config/settings.py` file:

- **Jira**: Base URL, authentication token, and project key
- **Xray**: Client ID and secret for Xray API
- **Generator**: Output paths and knowledge base configuration
- **Claude**: API key, model, and prompt template

You'll need to update these settings with your own credentials before using the application.

## Usage

1. Launch the application by running `TestCaseGenerator.bat`
2. Enter the Jira User Story ID (e.g., PT-28)
3. Click "Submit" to generate test cases
4. Results will be displayed in the interface and saved to the `output` directory

### Command Line Usage

You can also run the application from the command line:

```
GenerateTests.bat JIRA-ID
```

For example:
```
GenerateTests.bat PT-28
```

## Project Structure

- `config/`: Application configuration
- `docs/`: Documentation
- `interface/`: User interface
- `knowledge_base/`: Knowledge base used for context enhancement
- `output/`: Output directory for generated test cases
- `src/`: Main source code
  - `claude_client.py`: Claude API client
  - `generator.py`: Test case generator
  - `jira_client.py`: Jira API client
  - `main.py`: Main entry point
  - `xray_client.py`: Xray API client

## Knowledge Base Enhancement

The application includes a knowledge base system that enhances test case generation with domain-specific knowledge. The system:

1. Analyzes the user story to identify relevant domains
2. Searches the knowledge base for matching content
3. Enhances the prompt to Claude with relevant testing patterns
4. Produces higher-quality, domain-appropriate test cases

To update or verify the knowledge base, run:
```
SyncKnowledgeBase.bat
```

## Troubleshooting

If you encounter issues:

1. Verify that Python is correctly installed
2. Ensure the API keys in `config/settings.py` are valid
3. Check the logs in the `output/logs/` directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is distributed under the MIT License. See `LICENSE` file for more information.

## Acknowledgments

- [Anthropic's Claude](https://www.anthropic.com/) for the AI-powered test case generation
- [Jira](https://www.atlassian.com/software/jira) and [Xray](https://www.getxray.app/) for test management integration