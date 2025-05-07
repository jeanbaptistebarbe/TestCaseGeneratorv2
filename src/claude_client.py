# Claude API client for the Test Case Generator
import json
import logging
import os
import re
from datetime import datetime
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import settings
from utils import make_request
from knowledge_base.prompt_enhancer import enhance_prompt_with_knowledge_base

logger = logging.getLogger(__name__)

def clean_jira_formatting(text):
    """
    Nettoie le formatage Jira du texte
    
    Args:
        text (str): Le texte à nettoyer
    
    Returns:
        str: Le texte nettoyé
    """
    # Supprime les balises de couleur Jira
    text = re.sub(r'\{color:[^\}]*\}', '', text)
    text = re.sub(r'\{color\}', '', text)
    
    # Nettoyage des doubles sauts de ligne créés
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text

def sanitize_json_string(json_string):
    """
    Nettoyer une chaîne JSON pour corriger les problèmes courants
    
    Args:
        json_string (str): La chaîne JSON à nettoyer
    
    Returns:
        str: La chaîne JSON nettoyée
    """
    # Remplacer les caractères de contrôle et les caractères d'échappement problématiques
    cleaned = json_string
    # Échapper les guillemets non échappés dans les chaînes
    cleaned = re.sub(r'(?<!\\)\\(?!["\\\/bfnrtu])', r'\\\\', cleaned)
    # Remplacer les guillemets simples par des guillemets doubles
    cleaned = re.sub(r'(?<!")\'', '"', cleaned)
    cleaned = re.sub(r'\'(?!")', '"', cleaned)
    # Gérer les retours à la ligne dans les chaînes
    cleaned = re.sub(r'(?<!")\n(?!")', r'\\n', cleaned)
    
    return cleaned

def complete_incomplete_json(incomplete_json):
    """
    Tente de compléter un JSON incomplet
    
    Args:
        incomplete_json (str): JSON incomplet
    
    Returns:
        str: JSON complété ou le même JSON si déjà complet
    """
    # Compter les crochets ouvrants et fermants
    open_brackets = len(re.findall(r'\[', incomplete_json) or [])
    close_brackets = len(re.findall(r'\]', incomplete_json) or [])
    
    # Compter les accolades ouvrantes et fermantes
    open_braces = len(re.findall(r'\{', incomplete_json) or [])
    close_braces = len(re.findall(r'\}', incomplete_json) or [])
    
    # Compter les guillemets (ils devraient être en nombre pair)
    quotes = len(re.findall(r'"', incomplete_json) or [])
    
    logger.info(f"JSON structure analysis: [{open_brackets}:{close_brackets}], {{{open_braces}:{close_braces}}}, \"{quotes % 2 == 0 and 'balanced' or 'unbalanced'}\" quotes")
    
    completed = incomplete_json
    
    # Détecter les guillemets non fermés à la fin et tenter de les fermer
    if quotes % 2 != 0:
        completed += '"'
    
    # Équilibrer les accolades
    for i in range(open_braces - close_braces):
        completed += '}'
    
    # Équilibrer les crochets
    for i in range(open_brackets - close_brackets):
        completed += ']'
    
    return completed

def extract_json_from_text(text):
    """
    Extrait un tableau JSON d'une chaîne de texte
    
    Args:
        text (str): Le texte contenant du JSON
    
    Returns:
        dict or None: Le JSON extrait ou None si aucun JSON valide n'est trouvé
    """
    try:
        # Essayer de parser le texte entier d'abord
        return json.loads(text)
    except json.JSONDecodeError:
        logger.info('Could not parse full text as JSON, trying to extract JSON...')
        
        # Essayer d'extraire un objet JSON seul (sans délimiteurs)
        if text.strip().startswith('{') and text.strip().endswith('}'): 
            logger.info('Detected standalone JSON object, attempting to parse...')
            try:
                return json.loads(text.strip())
            except json.JSONDecodeError:
                logger.info('Failed to parse standalone JSON object, continuing...')
        
        # Chercher un array JSON
        first_bracket = text.find('[')
        last_bracket = text.rfind(']')
        
        if first_bracket != -1 and last_bracket > first_bracket:
            try:
                json_str = text[first_bracket:last_bracket + 1]
                # Essayer de nettoyer et parser le JSON extrait
                sanitized = sanitize_json_string(json_str)
                
                try:
                    return json.loads(sanitized)
                except json.JSONDecodeError as parse_error:
                    logger.warning(f"Failed to parse JSON array: {str(parse_error)}")
            except Exception as inner_error:
                logger.warning(f'Failed to extract JSON array: {str(inner_error)}')
        
        # Chercher le JSON entre tripple backticks
        json_pattern = r'```json\s*(.+?)\s*```'
        json_matches = re.findall(json_pattern, text, re.DOTALL)
        
        if json_matches:
            for json_match in json_matches:
                try:
                    # Essayer de parser le JSON extrait
                    return json.loads(json_match)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON between backticks")
        
        logger.warning('Could not extract valid JSON from text')
        return None

def extract_test_cases_manually(text):
    """
    Extrait manuellement les test cases d'une réponse textuelle
    
    Args:
        text (str): Le texte à analyser
    
    Returns:
        list: Un tableau de test cases
    """
    logger.info('Extracting test cases manually from text...')
    
    # Enregistrer la réponse brute pour diagnostic
    logs_dir = os.path.join(settings.generator["outputBaseDir"], 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, f'claude_response_{datetime.now().timestamp()}.txt')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Raw response saved to {log_file} for diagnosis")
    
    # Chercher les modèles qui indiquent des test cases
    test_cases = []
    
    # Essayer d'extraire le JSON entre tripple backticks
    json_pattern = r'```json\s*(.+?)\s*```'
    json_matches = re.findall(json_pattern, text, re.DOTALL)
    
    if json_matches:
        for json_match in json_matches:
            try:
                # Essayer de parser le JSON extrait
                json_data = json.loads(json_match)
                if isinstance(json_data, list):
                    test_cases = json_data
                    logger.info(f"Successfully extracted {len(test_cases)} test cases from JSON between backticks")
                    return test_cases
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON between backticks")
    
    # Si l'extraction de JSON complet a échoué, essayer d'extraire manuellement les composants
    summary_pattern = r'"summary":\s*"([^"]+)"'
    description_pattern = r'"description":\s*"([^"]+)"'
    
    # Modèle pour extraire les étapes - recherche les tableaux d'étapes complets
    steps_pattern = r'"steps"\s*:\s*(\[\s*\{[^\]]*\}\s*\])'
    
    # Pattern pour extraire des étapes individuelles
    action_pattern = r'"action"\s*:\s*"([^"]+)"'
    data_pattern = r'"data"\s*:\s*"([^"]+)"'
    result_pattern = r'"result"\s*:\s*"([^"]+)"'
    
    summaries = re.findall(summary_pattern, text)
    descriptions = re.findall(description_pattern, text)
    steps_matches = re.findall(steps_pattern, text, re.DOTALL)
    
    # Construire des test cases basiques à partir des données extraites
    for i in range(min(len(summaries), len(descriptions))):
        # Tenter d'extraire les étapes pour ce test case
        steps = []
        
        # Si nous avons un matching steps section, essayer de l'analyser
        if i < len(steps_matches):
            try:
                extracted_steps = json.loads(steps_matches[i])
                if isinstance(extracted_steps, list) and extracted_steps:
                    steps = extracted_steps
            except json.JSONDecodeError:
                # Si le parsing JSON a échoué, chercher les étapes manuellement
                actions = re.findall(action_pattern, steps_matches[i])
                datas = re.findall(data_pattern, steps_matches[i])
                results = re.findall(result_pattern, steps_matches[i])
                
                # Créer les étapes à partir des éléments extraits
                for j in range(max(len(actions), len(datas), len(results))):
                    step = {
                        "action": actions[j] if j < len(actions) else "User performs an action",
                        "data": datas[j] if j < len(datas) else "Test data",
                        "result": results[j] if j < len(results) else "Expected result"
                    }
                    steps.append(step)
        
        # Si aucune étape n'a été extraite, ajouter une étape par défaut
        if not steps:
            steps = [
                {
                    "action": "User performs the action required by this test case",
                    "data": "Test data specific to this scenario",
                    "result": "Expected outcome based on the test description"
                }
            ]
        
        test_cases.append({
            "summary": summaries[i],
            "description": descriptions[i],
            "steps": steps
        })
    
    # Si aucun test case n'a été trouvé, créer un test case par défaut
    if not test_cases:
        logger.warning('Could not extract test cases from Claude response, creating default test case')
        test_cases.append({
            "summary": "Default Test Case",
            "description": "This is a default test case created because the Claude response could not be parsed correctly.",
            "steps": [
                {
                    "action": "User performs the action required by the scenario",
                    "data": "Test data specific to this scenario",
                    "result": "Expected outcome based on the scenario"
                }
            ]
        })
    
    return test_cases

def analyze_with_claude(user_story):
    """
    Analyze a user story using Claude API
    
    Args:
        user_story (dict): The user story to analyze
    
    Returns:
        list: Generated test cases
    """
    logger.info('Calling Claude API to analyze the user story and generate test cases...')
    
    # Préparer le prompt pour Claude
    # Nettoyer le formatage Jira avant de l'envoyer à Claude
    cleaned_summary = clean_jira_formatting(user_story['fields']['summary'])
    cleaned_description = clean_jira_formatting(user_story['fields']['description'])
    
    base_prompt = settings.claude["promptTemplate"] \
        .replace('{USER_STORY_SUMMARY}', cleaned_summary) \
        .replace('{USER_STORY_DESCRIPTION}', cleaned_description) \
        .replace('{USER_STORY_TITLE}', cleaned_summary)
    
    # Enrichir le prompt avec la base de connaissances Concord si approprié
    prompt = enhance_prompt_with_knowledge_base(base_prompt, user_story)
    
    # Enregistrer le prompt pour diagnostic
    logs_dir = os.path.join(settings.generator["outputBaseDir"], 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    prompt_file = os.path.join(logs_dir, f'claude_prompt_{datetime.now().timestamp()}.txt')
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    logger.info(f"Prompt saved to {prompt_file} for reference")
    
    # Configuration de la requête à l'API Claude
    claude_request_data = {
        "model": settings.claude["apiModel"],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 8000,  # Augmenté pour éviter la troncature
        "temperature": 0.2
    }
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': settings.claude["apiKey"],
        'anthropic-version': '2023-06-01'
    }
    
    try:
        # Appeler l'API Claude
        claude_response = make_request(url, method='POST', headers=headers, json_data=claude_request_data)
        
        # Enregistrer la réponse de Claude pour diagnostic
        logs_dir = os.path.join(settings.generator["outputBaseDir"], 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, f'claude_response_object_{datetime.now().timestamp()}.json')
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(claude_response, f, indent=2)
        
        # Vérifier si la réponse a été tronquée
        if claude_response.get('stop_reason') == "max_tokens":
            logger.warning("⚠️ WARNING: Claude response was truncated (max_tokens reached). Some content may be missing.")
            logger.warning(f"Used {claude_response.get('usage', {}).get('output_tokens', '?')} of {settings.claude.get('maxTokens', 8000)} available tokens.")
        
        # Extraire la réponse de Claude
        response_content = claude_response['content'][0]['text']
        
        # Extraire le JSON de la réponse avec notre fonction robuste
        test_cases = extract_json_from_text(response_content)
        
        if test_cases and isinstance(test_cases, list) and len(test_cases) > 0:
            logger.info(f"Successfully extracted {len(test_cases)} test cases from Claude response")
            return test_cases
        else:
            logger.warning('Failed to extract valid test cases using JSON parsing, trying manual extraction...')
            manually_extracted_test_cases = extract_test_cases_manually(response_content)
            if len(manually_extracted_test_cases) > 0:
                logger.info(f"Manually extracted {len(manually_extracted_test_cases)} test cases")
                return manually_extracted_test_cases
            raise Exception('Failed to extract valid test cases from Claude response')
    except Exception as error:
        logger.error(f'Error calling Claude API: {str(error)}')
        
        # Fallback - génération basique de test cases en cas d'échec de l'API
        logger.info('Using fallback test case generation since Claude API call failed')
        
        # Extraction simplifiée des scénarios d'acceptation
        scenario_regex = r'\*Scenario \d+\*\s*([\s\S]*?)(?=\*Scenario \d+\*|$)'
        scenarios = re.findall(scenario_regex, user_story['fields']['description'])
        
        # Génération de test cases basiques pour chaque scénario
        fallback_test_cases = []
        for i, scenario in enumerate(scenarios):
            test_case = {
                "summary": f"{user_story['fields']['summary']}: Scenario {i + 1} Test",
                "description": f"Test case to verify the scenario: {scenario.strip()}",
                "steps": []
            }
            
            # Extraire Given/When/Then si présent
            given_match = re.search(r'Given (.*?)(?=,|When|Then|$)', scenario, re.IGNORECASE)
            when_match = re.search(r'When (.*?)(?=,|Then|$)', scenario, re.IGNORECASE)
            then_match = re.search(r'Then (.*?)(?=,|$)', scenario, re.IGNORECASE)
            
            if given_match:
                test_case["steps"].append({
                    "action": f"User ensures {given_match.group(1)}",
                    "data": "N/A",
                    "result": "Precondition is established"
                })
            
            if when_match:
                test_case["steps"].append({
                    "action": f"User {when_match.group(1)}",
                    "data": "Appropriate test data",
                    "result": "Action is performed"
                })
            
            if then_match:
                test_case["steps"].append({
                    "action": "User verifies the result",
                    "data": "N/A",
                    "result": f"{then_match.group(1)}"
                })
            
            fallback_test_cases.append(test_case)
        
        return fallback_test_cases