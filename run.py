#!/usr/bin/env python
# Script d'exécution principal pour le générateur de cas de test
# Ce script permet d'exécuter le générateur en ligne de commande

import sys
import os
import logging
import argparse

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configurer le logging
log_dir = os.path.join(current_dir, "output", "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"app_{os.path.basename(__file__).split('.')[0]}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Point d'entrée principal pour le générateur de cas de test
    """
    parser = argparse.ArgumentParser(description='Test Case Generator')
    parser.add_argument('jira_id', nargs='?', help='ID de l\'User Story Jira (ex: PT-28)')
    parser.add_argument('--gui', action='store_true', help='Lancer l\'interface graphique')
    args = parser.parse_args()
    
    try:
        if args.gui or not args.jira_id:
            # Lancer l'interface graphique si demandé ou si aucun ID Jira n'est fourni
            logger.info("Lancement de l'interface graphique...")
            from interface.app_jira import main as launch_gui
            launch_gui()
        else:
            # Exécuter avec l'ID Jira fourni
            logger.info(f"Traitement de l'User Story Jira: {args.jira_id}")
            from src.generator import generate_test_cases_from_user_story
            results = generate_test_cases_from_user_story(args.jira_id)
            
            # Afficher un résumé des résultats
            print('\n======== RÉSUMÉ ========')
            print(f"User Story: {results['title']} ({results['userStory']})")
            print(f"Cas de test générés: {len(results['testCases'])}")
            print(f"Importés avec succès: {sum(1 for tc in results['testCases'] if tc['success'])}")
            
            print('\n======== CAS DE TEST ========')
            for i, tc in enumerate(results['testCases']):
                if tc['success']:
                    print(f"{i + 1}. {tc['testCase']} -> {tc['key']}")
                else:
                    print(f"{i + 1}. {tc['testCase']} -> Échec de l'import: {tc.get('error', 'Erreur inconnue')}")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        print(f"Une erreur s'est produite: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interruption par l'utilisateur")
        print("\nOpération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Erreur fatale: {str(e)}", exc_info=True)
        print(f"Erreur fatale: {str(e)}")
        sys.exit(1)