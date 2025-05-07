# Main entry point for the Test Case Generator
import sys
import logging
import os

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from generator import generate_test_cases_from_user_story

logger = logging.getLogger(__name__)

def main():
    """
    Main function
    """
    try:
        # Get user story key from command line
        if len(sys.argv) < 2:
            logger.error('Error: Please provide a user story key')
            logger.error('Usage: python main.py YOUR-PROJECT-123')
            sys.exit(1)
        
        user_story_key = sys.argv[1]
        
        logger.info(f"Starting Claude API-integrated test case generation for {user_story_key}")
        results = generate_test_cases_from_user_story(user_story_key)
        
        # Display summary
        print('\n======== SUMMARY ========')
        print(f"User Story: {results['title']} ({results['userStory']})")
        print(f"Test Cases Generated: {len(results['testCases'])}")
        print(f"Successfully Imported: {sum(1 for tc in results['testCases'] if tc['success'])}")
        
        # Afficher les informations de job si présentes
        if 'jobId' in results:
            print(f"Import Job ID: {results.get('jobId')}")
            print(f"Job Status: {results.get('status', 'Unknown')}")
            
            # Afficher les erreurs détaillées
            if 'errors' in results and results['errors']:
                print("\n======== ERROR DETAILS ========")
                for i, error in enumerate(results['errors']):
                    element_num = error.get("elementNumber", i)
                    error_details = error.get("errors", {})
                    print(f"Test {element_num + 1}: {error_details}")
        
        print('\n======== TEST CASES ========')
        for i, tc in enumerate(results['testCases']):
            if tc['success']:
                print(f"{i + 1}. {tc['testCase']} -> {tc['key']}")
            else:
                print(f"{i + 1}. {tc['testCase']} -> Import Failed: {tc['error']}")
        
        print('\nProcess completed successfully.')
        return results
    except Exception as error:
        logger.error(f'Error in main process: {str(error)}')
        sys.exit(1)

if __name__ == "__main__":
    # Initialize logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    try:
        results = main()
        print('All done!')
    except Exception as error:
        logger.error(f'Fatal error: {str(error)}')