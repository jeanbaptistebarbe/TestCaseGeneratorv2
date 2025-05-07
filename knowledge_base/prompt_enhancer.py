# Knowledge base prompt enhancement module
import os
import logging
import re
import glob
import json
import sys
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import settings

logger = logging.getLogger(__name__)

def enhance_prompt_with_knowledge_base(prompt, user_story):
    """
    Enhance a prompt with relevant content from knowledge base
    
    Args:
        prompt (str): The base prompt
        user_story (dict): User story data
    
    Returns:
        str: Enhanced prompt
    """
    if not settings.knowledge_base.get("use_knowledge_base", False):
        logger.info("Knowledge base enhancement disabled in settings")
        return prompt
    
    logger.info("Enhancing prompt with knowledge base content...")
    
    knowledge_base_dir = os.path.join(parent_dir, settings.generator["knowledgeBaseDir"])
    if not os.path.exists(knowledge_base_dir):
        logger.warning(f"Knowledge base directory {knowledge_base_dir} not found")
        return prompt
    
    # Extract keywords from user story
    title = user_story['fields']['summary'].lower()
    description = user_story['fields']['description'].lower() if user_story['fields']['description'] else ""
    
    # Simple keyword extraction (can be enhanced with NLP in the future)
    keywords = extract_keywords(title + " " + description)
    logger.info(f"Extracted keywords: {', '.join(keywords)}")
    
    # Find relevant files
    relevant_files = []
    for filename in glob.glob(os.path.join(knowledge_base_dir, "*.json")):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
                
                relevance_score = calculate_relevance(file_content, keywords)
                if relevance_score >= settings.knowledge_base.get("similarity_threshold", 0.65):
                    logger.info(f"Found relevant file: {os.path.basename(filename)} (score: {relevance_score:.2f})")
                    relevant_files.append((filename, relevance_score, file_content))
        except Exception as e:
            logger.error(f"Error reading knowledge base file {filename}: {str(e)}")
    
    # Sort by relevance score
    relevant_files.sort(key=lambda x: x[1], reverse=True)
    
    # Limit to top 3 files
    relevant_files = relevant_files[:3]
    
    if not relevant_files:
        logger.info("No relevant knowledge base files found")
        return prompt
    
    # Enhance prompt with relevant content
    enhanced_prompt = prompt + "\n\n" + "KNOWLEDGE BASE CONTEXT:\n"
    
    for filename, score, content in relevant_files:
        # Get only required fields for the context
        domain = content.get("domain", "General")
        tests = content.get("sample_tests", [])
        guidelines = content.get("guidelines", "")
        
        enhanced_prompt += f"\n## Domain: {domain}\n"
        if guidelines:
            enhanced_prompt += f"Guidelines: {guidelines}\n"
        
        # Add sample tests if available
        if tests:
            enhanced_prompt += "Sample test cases:\n"
            for i, test in enumerate(tests[:3]):  # Limit to 3 samples
                summary = test.get("summary", f"Test case {i+1}")
                enhanced_prompt += f"- {summary}\n"
        
        enhanced_prompt += "\n"
    
    enhanced_prompt += "\nPlease incorporate the relevant knowledge from above when generating test cases for this user story."
    
    return enhanced_prompt

def extract_keywords(text):
    """
    Extract important keywords from text
    
    Args:
        text (str): Text to extract keywords from
    
    Returns:
        list: List of keywords
    """
    # Remove common words and special characters
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    
    # Simple stopwords list (can be enhanced)
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 
                'at', 'from', 'by', 'for', 'with', 'about', 'against', 'between',
                'into', 'through', 'during', 'before', 'after', 'above', 'below',
                'to', 'of', 'in', 'on', 'is', 'are', 'was', 'were', 'be', 'been',
                'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
                'doing', 'can', 'could', 'should', 'would', 'ought', 'i', 'you',
                'he', 'she', 'it', 'we', 'they', 'their', 'this', 'that', 'these',
                'those', 'am', 'is', 'are', 'was', 'will', 'as', 'so', 'such'}
    
    # Filter words
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Return unique keywords
    return list(set(keywords))

def calculate_relevance(file_content, keywords):
    """
    Calculate relevance score between file content and keywords
    
    Args:
        file_content (dict): File content
        keywords (list): Keywords list
    
    Returns:
        float: Relevance score (0.0 to 1.0)
    """
    # Simple keyword matching (can be enhanced with more sophisticated NLP)
    content_text = json.dumps(file_content).lower()
    
    matches = 0
    for keyword in keywords:
        if keyword in content_text:
            matches += 1
    
    # Calculate score (normalize by number of keywords)
    if not keywords:
        return 0.0
    
    return matches / len(keywords)
