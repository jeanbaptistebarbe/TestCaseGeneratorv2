# Main test case generator module
import json
import os
import logging
import re
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import settings
from jira_client import get_jira_issue, create_xray_test_case, create_issue_link
from xray_client import import_test_cases_to_xray
from claude_client import analyze_with_claude

logger = logging.getLogger(__name__)

def generate_test_cases_from_user_story(user_story_key):
    """
    Generate test cases for a user story
    
    Args:
        user_story_key (str): The key of the user story
    
    Returns:
        dict: Generation results
    """
    try:
        logger.info(f"Generating test cases for user story: {user_story_key}")
        
        # Get user story details from Jira
        user_story = get_jira_issue(user_story_key)
        logger.info(f"Retrieved user story: {user_story['fields']['summary']}")
        
        # Create output directory based on user story title
        folder_name = re.sub(r'[^\w\s-]', '', user_story['fields']['summary']).replace(' ', '_')
        output_dir = os.path.join(settings.generator["outputBaseDir"], folder_name)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use Claude to analyze the user story and generate test cases
        test_cases = analyze_with_claude(user_story)
        logger.info(f"Generated {len(test_cases)} test cases")
        
        # Save test cases to files
        results = []
        for test_case in test_cases:
            # Vérifier et ajuster le format du titre si nécessaire
            if not test_case["summary"].startswith(user_story['fields']['summary']):
                test_case["summary"] = f"{user_story['fields']['summary']}: {test_case['summary']}"
            
            # Create a valid filename
            file_name = re.sub(r'[^\w\s-]', '', test_case["summary"]).replace(' ', '_')[:100] + '.json'
            file_path = os.path.join(output_dir, file_name)
            
            # Formater correctement la description pour Xray
            if "description" in test_case:
                # Nettoyer le formatage de la description
                description = test_case["description"]
                
                # Corriger les problèmes d'astérisques dans la description
                # Normaliser les doubles astérisques pour la mise en forme du texte en gras
                # Problème avec le format '* *Text**' -> correction en '**Text**'
                description = re.sub(r'\*\s*\*(.*?)\*\*', r'**\1**', description)
                
                # Corriger les astérisques à la fin des titres sans * en début
                # Problème avec le format 'Text*' qui devrait être '**Text**'
                description = re.sub(r'([^\*])\*([\s\n])', r'\1\2', description)
                
                # Corriger les astérisques en trop dans les titres
                description = description.replace("***Prerequisites and Test Data", "**Prerequisites and Test Data**")
                description = description.replace("Test Data:***", "**Test Data:**")
                description = description.replace("* *Prerequisites:**", "**Prerequisites:**")
                description = description.replace("* *Test Data:**", "**Test Data:**")
                
                # S'assurer que les retours à la ligne sont correctement interprétés
                # Remplacer explicitement les séquences \n par des sauts de ligne réels
                description = description.replace("\\n", "\n")
                
                # Détecter si nous avons des tables dans le texte
                if '|' in description and '-|' in description:
                    # Extraction des lignes du tableau
                    table_lines = []
                    in_table = False
                    new_description_lines = []
                    
                    for line in description.split('\n'):
                        if '|' in line and not in_table:
                            # Début potentiel du tableau
                            in_table = True
                            table_lines.append(line)
                        elif '|' in line and in_table:
                            # Continuation du tableau
                            table_lines.append(line)
                        elif in_table:
                            # Fin du tableau
                            in_table = False
                            
                            # Formatter le tableau en liste à puces
                            if len(table_lines) >= 3:  # Un tableau valide a au moins l'en-tête, le séparateur et une ligne
                                # Ignorer les lignes d'en-tête et de séparation
                                formatted_list = "\n"
                                
                                # Formatter chaque ligne de données en puce
                                for data_line in table_lines[2:]:  # Ignorer l'en-tête et la ligne de séparation
                                    cells = [c.strip() for c in data_line.split('|') if c.strip()]
                                    if len(cells) >= 2:  # Assurez-vous qu'il y a au moins deux cellules
                                        formatted_list += f"\u2022 {cells[0]}: {cells[1]}\n"
                                
                                new_description_lines.append(formatted_list)
                            else:
                                # Si le tableau n'est pas valide, le conserver tel quel
                                new_description_lines.extend(table_lines)
                            
                            table_lines = []
                            new_description_lines.append(line)
                        else:
                            new_description_lines.append(line)
                    
                    # Ajouter les dernières lignes de tableau si la boucle se termine dans un tableau
                    if in_table and table_lines:
                        formatted_list = "\n"
                        for data_line in table_lines[2:]:  # Ignorer l'en-tête et la ligne de séparation si possible
                            cells = [c.strip() for c in data_line.split('|') if c.strip()]
                            if len(cells) >= 2:
                                formatted_list += f"\u2022 {cells[0]}: {cells[1]}\n"
                        new_description_lines.append(formatted_list)
                    
                    # Mettre à jour la description
                    description = '\n'.join(new_description_lines)
                
                # Assurer des espaces consistants après les puces et numéros
                description = re.sub(r'(^|\n)\s*([\*\-])\s*', r'\1\2 ', description)
                description = re.sub(r'(^|\n)\s*(\d+\.)\s*', r'\1\2 ', description)
                
                # Mettre à jour la description formatée
                test_case["description"] = description
            
            # Save test case to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(test_case, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved test case to: {file_path}")
            
            results.append({
                "testCase": test_case["summary"],
                "filePath": file_path,
                "success": False,  # Sera mis à jour après l'import en masse
                "key": None        # Sera mis à jour après l'import en masse
            })
            
        # Import all test cases in bulk
        try:
            if settings.xray.get("use_bulk_import", False):
                logger.info(f"Importing {len(test_cases)} test cases in bulk to Xray")
                # Utiliser le mode avec wait_for_completion pour attendre la fin du job
                # Définir un temps d'attente suffisant pour le traitement (30 tentatives avec 5 secondes = 2.5 minutes)
                bulk_import_result = import_test_cases_to_xray(test_cases, user_story_key, wait_for_completion=True, max_polling_attempts=30, polling_interval=5)
                
                if bulk_import_result["success"]:
                    # Vérifier si nous avons un résultat asynchrone avec jobId ou un résultat direct
                    if "jobId" in bulk_import_result:
                        logger.info(f"Processing import job results with ID: {bulk_import_result['jobId']}")
                        # Pour un job asynchrone terminé, les clés sont dans importedTests
                        if "importedTests" in bulk_import_result and bulk_import_result["importedTests"]:
                            imported_keys = bulk_import_result["importedTests"]
                            for i, key in enumerate(imported_keys):
                                if i < len(results):
                                    results[i]["key"] = key
                                    results[i]["success"] = True
                            
                            logger.info(f"Successfully imported {len(imported_keys)} test cases")
                        else:
                            # Si pas de clés trouvées, marquer comme échoué
                            logger.warning(f"No imported tests found in job result. Status: {bulk_import_result.get('status')}")
                            for result in results:
                                result["error"] = f"No test keys found in import job result. Status: {bulk_import_result.get('status')}"
                    else:
                        # Pour un résultat direct
                        imported_keys = bulk_import_result.get("importedTests", [])
                        for i, key in enumerate(imported_keys):
                            if i < len(results):
                                results[i]["key"] = key
                                results[i]["success"] = True
                        
                        logger.info(f"Successfully imported {len(imported_keys)} test cases")
                    
                    # Log any errors
                    if bulk_import_result.get("errors"):
                        logger.warning(f"Encountered {len(bulk_import_result['errors'])} errors during import: {bulk_import_result['errors']}")
                else:
                    error_message = bulk_import_result.get('message', 'Unknown error during bulk import')
                    logger.error(f"Bulk import failed: {error_message}")
                    
                    # Journal des erreurs spécifiques
                    if "errors" in bulk_import_result and bulk_import_result["errors"]:
                        for i, error in enumerate(bulk_import_result["errors"]):
                            element_num = error.get("elementNumber", i)
                            error_details = error.get("errors", {})
                            logger.error(f"  Test {element_num}: {error_details}")
                    
                    # Mark all test cases as failed
                    for i, result in enumerate(results):
                        if "errors" in bulk_import_result and bulk_import_result["errors"] and i < len(bulk_import_result["errors"]):
                            error = bulk_import_result["errors"][i]
                            element_num = error.get("elementNumber", i)
                            error_details = error.get("errors", {})
                            result["error"] = f"Import error: {error_details}"
                        else:
                            result["error"] = error_message
            else:
                # Fallback to individual import if bulk import is disabled
                logger.info("Bulk import disabled, falling back to individual import")
                for i, test_case in enumerate(test_cases):
                    try:
                        logger.info(f"Importing test case: {test_case['summary']}")
                        import_result = create_xray_test_case(test_case)
                        
                        # Create link to user story
                        if import_result and import_result.get('key'):
                            logger.info(f"Creating link between {import_result['key']} and {user_story_key}")
                            link_result = create_issue_link(import_result['key'], user_story_key)
                            logger.info(f"Link creation result: {link_result}")
                        
                        results[i]["key"] = import_result['key']
                        results[i]["success"] = True
                    except Exception as error:
                        logger.error(f"Error importing test case: {str(error)}")
                        results[i]["error"] = str(error)
        except Exception as error:
            error_message = str(error)
            logger.error(f"Error during test case import: {error_message}")
            # Mark all test cases as failed
            for result in results:
                if not result.get("success"):
                    result["error"] = error_message
        
        # Préparer les données de retour
        return_data = {
            "userStory": user_story_key,
            "title": user_story['fields']['summary'],
            "testCases": results
        }
        
        # Ajouter les informations du job si disponibles
        if 'bulk_import_result' in locals() and isinstance(bulk_import_result, dict):
            if "jobId" in bulk_import_result:
                return_data["jobId"] = bulk_import_result["jobId"]
                return_data["status"] = bulk_import_result.get("status")
                
                # Ajouter les informations d'erreur
                if "errors" in bulk_import_result:
                    return_data["errors"] = bulk_import_result["errors"]
        
        return return_data
    except Exception as error:
        logger.error(f"Error generating test cases: {str(error)}")
        raise