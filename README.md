# Test Case Generator v2

Application pour générer automatiquement des cas de test à partir d'User Stories Jira et les importer dans Xray.

## Fonctionnalités

- Récupération automatique des User Stories depuis Jira
- Génération de cas de test via l'API Claude d'Anthropic
- Import automatique des cas de test dans Xray
- Interface utilisateur simple et intuitive

## Installation

1. Assurez-vous d'avoir Python 3.8 ou supérieur installé
2. Exécutez le script `Install.bat` pour installer les dépendances requises
3. Le programme créera automatiquement le dossier `output` pour stocker les cas de test générés

## Configuration

Toutes les configurations sont stockées dans le fichier `config/settings.py` :

- **Jira** : URL de base, token d'authentification et clé de projet
- **Xray** : ID client et secret pour l'API Xray
- **Generator** : Chemins de sortie et de base de connaissances
- **Claude** : Clé API Claude, modèle et template de prompt

## Utilisation

1. Lancez l'application en exécutant `TestCaseGenerator.bat`
2. Entrez l'ID de l'User Story Jira (ex: PT-28)
3. Cliquez sur "Submit" pour générer les cas de test
4. Les résultats seront affichés dans l'interface et sauvegardés dans le dossier `output`

## Structure du projet

- `config/` : Configuration de l'application
- `docs/` : Documentation
- `interface/` : Interface utilisateur
- `knowledge_base/` : Base de connaissances utilisée pour le contexte
- `output/` : Dossier de sortie des cas de test générés
- `src/` : Code source principal
  - `claude_client.py` : Client API Claude
  - `generator.py` : Générateur de cas de test
  - `jira_client.py` : Client API Jira
  - `main.py` : Point d'entrée principal
  - `xray_client.py` : Client API Xray

## Dépannage

Si vous rencontrez des problèmes :

1. Vérifiez que Python est correctement installé
2. Assurez-vous que les API keys dans `config/settings.py` sont valides
3. Vérifiez les journaux dans le dossier `output/logs/`