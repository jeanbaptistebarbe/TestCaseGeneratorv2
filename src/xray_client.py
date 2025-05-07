# Xray API client for the Test Case Generator
import logging
import requests
import json
import sys
import os
import re

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import settings
from utils import make_request

logger = logging.getLogger(__name__)

def get_xray_auth_token():
    """
    Obtenir un token d'authentification pour l'API Xray
    
    Returns:
        str: Token d'authentification
    """
    logger.info("Obtaining Xray API authentication token")
    
    auth_url = "https://xray.cloud.getxray.app/api/v2/authenticate"
    auth_data = {
        "client_id": settings.xray["client_id"],
        "client_secret": settings.xray["client_secret"]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(auth_url, json=auth_data, headers=headers)
        response.raise_for_status()
        token = response.text.strip('"')  # Le token est retourné entre guillemets
        logger.info("Successfully obtained Xray API token")
        return token
    except Exception as e:
        logger.error(f"Error obtaining Xray API token: {str(e)}")
        raise

def import_test_cases_to_xray(test_cases, user_story_key, wait_for_completion=False, max_polling_attempts=20, polling_interval=5):
    """
    Importer des test cases en masse vers Xray en utilisant l'API v2
    
    Args:
        test_cases (list): Liste de dictionnaires contenant les données des test cases
        user_story_key (str): Clé de la user story associée
        wait_for_completion (bool, optional): Si True, attendre la fin du job d'import. Par défaut False.
        max_polling_attempts (int, optional): Nombre maximum de tentatives de vérification. Par défaut 20.
        polling_interval (int, optional): Intervalle en secondes entre chaque tentative. Par défaut 5 secondes.
    
    Returns:
        dict: Résultat de l'import, avec des informations supplémentaires si wait_for_completion est True
    """
    logger.info(f"Importing {len(test_cases)} test cases to Xray for user story {user_story_key}")
    
    # Obtenir le token d'authentification
    token = get_xray_auth_token()
    
    # Préparer les données de test au format attendu par l'API Xray v2
    xray_tests = []
    for test_case in test_cases:
        # Convertir les étapes du format Claude au format attendu par Xray
        xray_steps = []
        # Vérifier si test_case contient directement des étapes ou si elles sont dans une sous-clé "steps"
        steps_data = test_case.get("steps", [])
        if not steps_data and isinstance(test_case, list):
            # Si test_case est une liste, c'est peut-être directement une liste d'étapes
            steps_data = test_case
        
        for step in steps_data:
            xray_steps.append({
                "action": step.get("action", ""),
                "data": step.get("data", ""),
                "result": step.get("result", "")
            })
        
        # Créer le test au format Xray selon la structure attendue
        # Extraire le résumé et la description en gérant le cas où ils n'existent pas
        summary = test_case.get("summary", "Test Case")
        description = test_case.get("description", "")
        
        # Si test_case est une liste d'étapes, utiliser un titre par défaut
        if isinstance(test_case, list):
            summary = "Generated Test Case"
            description = "Test case generated from steps data"
        
        # Traitement spécial pour les tableaux markdown dans la description
        if description and isinstance(description, str):
            # Assurer que les lignes de tableau sont correctement formatées
            # Vérifier si nous avons des tableaux dans la description
            if "|" in description and "\n" in description:
                # Ajouter des espaces autour du contenu des cellules pour une meilleure lisibilité
                table_pattern = r'\|([^\|]*?)\|'
                description = re.sub(table_pattern, lambda m: f"| {m.group(1).strip()} |", description)
                
                # S'assurer que les lignes de séparation des en-têtes sont correctes
                table_header_pattern = r'\|(.*?)\|\s*\n\s*\|([-\|\s]+)\|'
                description = re.sub(table_header_pattern, lambda m: f"|{m.group(1)}|\n|{m.group(2)}|\n", description)
        
        # Structure exacte du format attendu par Xray (format simple)
        xray_test = {
            "fields": {
                "summary": summary,
                "description": description,
                "project": {
                    "key": settings.jira["testProjectKey"]
                },
                "issuetype": {
                    "name": "Test"
                }
            },
            "testtype": settings.xray.get("defaultTestType", "Manual"),  # Utiliser la valeur par défaut de la configuration
            "steps": xray_steps
        }
        
        xray_tests.append(xray_test)
    
    # Préparer les en-têtes avec le token d'authentification
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Pour débogage, afficher les données envoyées à l'API
    if settings.xray.get("debug_mode", False):
        logger.debug(f"Data sent to API: {json.dumps(xray_tests, indent=2)}")
        
    try:
        # Déterminer si nous utilisons l'import individuel ou en masse
        if len(xray_tests) == 1:
            # Pour un seul test case, utiliser le format simple
            logger.info("Sending single test case import request to Xray API")
            # Utiliser l'URL standard
            import_url = "https://xray.cloud.getxray.app/api/v2/import/test"
            response = requests.post(import_url, json=xray_tests[0], headers=headers)
            is_bulk_import = False
        else:
            # Pour plusieurs test cases, utiliser l'import en masse 
            logger.info(f"Sending bulk import request to Xray API for {len(xray_tests)} test cases")
            # Utiliser l'URL standard pour l'import en masse
            import_url = "https://xray.cloud.getxray.app/api/v2/import/test/bulk"
            response = requests.post(import_url, json=xray_tests, headers=headers)
            is_bulk_import = True
        
        response.raise_for_status()
        
        # Traiter la réponse
        result = response.json()
        
        # Si c'est un import en masse, la réponse contient un job ID
        if is_bulk_import:
            # Vérifier si nous avons un job ID
            if isinstance(result, dict) and "jobId" in result:
                job_id = result.get("jobId")
                logger.info(f"Bulk import job created with ID: {job_id}")
                
                # Récupérer le statut initial du job
                job_status = get_import_job_status(job_id, token)
                
                # Si demandé, attendre la fin du job
                if wait_for_completion:
                    logger.info(f"Waiting for job {job_id} to complete...")
                    final_status = poll_import_job_status(job_id, max_polling_attempts, polling_interval)
                    
                    # Vérifier si le job s'est terminé avec succès
                    if final_status.get("status") in ["successful", "partially_successful"]:
                        # Extraire les résultats
                        result = final_status.get("result", {})
                        logger.debug(f"Final job status: {final_status}")
                        issues = result.get("issues", [])
                        logger.info(f"Found {len(issues)} successfully imported tests in result")
                        
                        # Extraire les clés des issues créées
                        test_keys = []
                        for issue in issues:
                            if "key" in issue:
                                test_keys.append(issue.get("key"))
                                logger.debug(f"Added test key: {issue.get('key')}")
                        errors = result.get("errors", [])
                        
                        # Créer les liens entre les tests créés et la user story
                        if len(test_keys) > 0 and user_story_key:
                            logger.info(f"Creating links between {len(test_keys)} tests and user story {user_story_key}")
                            for test_key in test_keys:
                                try:
                                    # Utiliser une fonction pour créer un lien après la création des tests
                                    create_test_to_story_link(test_key, user_story_key, token)
                                except Exception as link_error:
                                    logger.warning(f"Failed to create link between {test_key} and {user_story_key}: {str(link_error)}")
                        
                        return {
                            "success": True,
                            "jobId": job_id,
                            "status": final_status.get("status"),
                            "importedTests": test_keys,
                            "errors": errors,
                            "message": f"Job completed. Successfully imported: {len(test_keys)}, Failed: {len(errors)}"
                        }
                    else:
                        return {
                            "success": False,
                            "jobId": job_id,
                            "status": final_status.get("status"),
                            "errors": final_status.get("result", {}).get("errors", []),
                            "message": f"Job failed or timed out with status: {final_status.get('status')}"
                        }
                
                # Si pas d'attente demandée, retourner le statut initial
                return {
                    "success": True,
                    "jobId": job_id,
                    "status": job_status.get("status"),
                    "progress": job_status.get("progress", []),
                    "progressValue": job_status.get("progressValue", 0),
                    "message": f"Bulk import job created with ID: {job_id}"
                }
            else:
                logger.warning(f"Unexpected response format from Xray API bulk import: {result}")
        else:
            # Pour l'import simple, nous avons une réponse directe
            # Vérifier le format de la réponse qui peut avoir changé avec le nouveau format
            if isinstance(result, dict) and "testKeys" in result:
                test_keys = result.get("testKeys", [])
            elif isinstance(result, list):
                # Dans certaines versions de l'API, la réponse peut être une liste directement
                test_keys = result
            elif isinstance(result, dict) and "key" in result:
                # Réponse pour un seul test case créé
                test_keys = [result.get("key")]
            else:
                test_keys = []
                logger.warning(f"Unexpected response format from Xray API: {result}")
            
            logger.info(f"Successfully imported {len(test_keys)} test cases to Xray")
            
            # Ajouter les détails d'import au résultat
            return {
                "success": True,
                "importedTests": test_keys,
                "errors": result.get("errors", []) if isinstance(result, dict) else [],
                "message": f"Successfully imported {len(test_keys)} test cases"
            }
    except Exception as e:
        logger.error(f"Error importing test cases to Xray: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to import test cases to Xray"
        }

def get_import_job_status(job_id, token=None):
    """
    Vérifier le statut d'un job d'import de tests en masse
    
    Args:
        job_id (str): L'identifiant du job d'import
        token (str, optional): Token d'authentification. Si None, un nouveau token sera obtenu.
    
    Returns:
        dict: Statut du job d'import contenant les informations sur l'avancement
              et les résultats si le job est terminé
    """
    logger.info(f"Checking status of import job: {job_id}")
    
    # Si pas de token fourni, en obtenir un nouveau
    if token is None:
        token = get_xray_auth_token()
    
    url = f"https://xray.cloud.getxray.app/api/v2/import/test/bulk/{job_id}/status"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        status_data = response.json()
        
        # Log l'état actuel du job
        job_status = status_data.get("status", "unknown")
        logger.info(f"Import job {job_id} status: {job_status}")
        
        if job_status in ["successful", "partially_successful", "unsuccessful"]:
            # Job terminé - log les résultats
            result = status_data.get("result", {})
            errors = len(result.get("errors", []))
            issues = len(result.get("issues", []))
            logger.info(f"Import job completed. Successfully imported: {issues}, Failed: {errors}")
        elif job_status == "working":
            # Job en cours - log la progression
            progress_value = status_data.get("progressValue", 0)
            logger.info(f"Import job in progress. Completion: {progress_value}%")
        
        return status_data
    except Exception as e:
        logger.error(f"Error checking import job status: {str(e)}")
        return {"status": "error", "error": str(e)}

def poll_import_job_status(job_id, max_attempts=20, interval=5):
    """
    Interroger périodiquement le statut d'un job d'import jusqu'à ce qu'il soit terminé
    ou que le nombre maximum de tentatives soit atteint
    
    Args:
        job_id (str): L'identifiant du job d'import
        max_attempts (int, optional): Nombre maximum de tentatives. Par défaut 20.
        interval (int, optional): Intervalle en secondes entre chaque tentative. Par défaut 5.
    
    Returns:
        dict: Statut final du job d'import
    """
    import time
    
    logger.info(f"Polling import job status for job {job_id}. Max attempts: {max_attempts}, Interval: {interval}s")
    
    # Obtenir un token valide pour toutes les requêtes
    token = get_xray_auth_token()
    
    attempts = 0
    status_data = {"status": "unknown"}
    
    while attempts < max_attempts:
        # Vérifier le statut
        status_data = get_import_job_status(job_id, token)
        job_status = status_data.get("status", "")
        
        # Journaliser les progrès à chaque tentative
        progress_value = status_data.get("progressValue", 0)
        progress_messages = status_data.get("progress", [])
        if progress_messages and len(progress_messages) > 0:
            latest_progress = progress_messages[-1] if progress_messages else "No progress info"
            logger.info(f"Job progress: {progress_value}% - {latest_progress}")
        
        # Vérifier si le job est terminé
        if job_status in ["successful", "partially_successful", "unsuccessful", "failed"]:
            logger.info(f"Import job {job_id} completed with status: {job_status}")
            if "result" in status_data:
                issues = status_data.get("result", {}).get("issues", [])
                errors = status_data.get("result", {}).get("errors", [])
                logger.info(f"Job result: {len(issues)} issues created, {len(errors)} errors")
                
                # Afficher les détails des erreurs pour débogage
                if errors:
                    logger.error("Error details:")
                    for i, error in enumerate(errors):
                        element_num = error.get("elementNumber", i)
                        error_details = error.get("errors", {})
                        logger.error(f"  Test {element_num}: {error_details}")
            return status_data
        
        # Attendre avant la prochaine tentative
        attempts += 1
        if attempts < max_attempts:
            logger.info(f"Import job still in progress. Waiting {interval}s before next check. Attempt {attempts}/{max_attempts}")
            time.sleep(interval)
    
    logger.warning(f"Maximum polling attempts reached for job {job_id}. Last status: {status_data.get('status')}")
    return status_data

def create_test_to_story_link(test_key, story_key, token=None):
    """
    Créer un lien entre un test et une user story
    
    Args:
        test_key (str): La clé du test case
        story_key (str): La clé de la user story
        token (str, optional): Non utilisé, gardé pour compatibilité avec les appels existants
    
    Returns:
        bool: True si le lien a été créé avec succès, False sinon
    """
    logger.info(f"Creating link between test {test_key} and story {story_key}")
    
    # Utiliser l'API JIRA pour créer un lien
    url = f"https://{settings.jira['baseUrl']}/rest/api/2/issueLink"
    
    # Structure de base pour la requête
    link_data = {
        "type": {
            "name": "Test" # Sera rempli dans la boucle
        },
        "inwardIssue": {
            "key": test_key
        },
        "outwardIssue": {
            "key": story_key
        }
    }
    
    success = False
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': settings.jira['authToken']
    }
    
    success = False
    errors = []
        
    try:
        logger.debug(f"Sending link request to: {url}")
        logger.debug(f"Link data: {json.dumps(link_data)}")
        
        response = requests.post(url, json=link_data, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Successfully created link between {test_key} and {story_key}")
        success = True
    except Exception as e:
        logger.error(f"Failed to create link")
    
    # Vérifier si on a réussi avec au moins un type
    if success:
        return True
    else:
        return False

def get_test_case_details(test_key):
    """
    Obtenir les détails d'un test case spécifique depuis Xray
    
    Args:
        test_key (str): La clé du test case
    
    Returns:
        dict: Détails du test case
    """
    token = get_xray_auth_token()
    
    url = f"https://xray.cloud.getxray.app/api/v2/tests/{test_key}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting test case details: {str(e)}")
        return None