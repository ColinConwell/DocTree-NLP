"""
Text processing and NLP capabilities.
"""
import logging
import spacy
import subprocess
from typing import List, Dict, Any

from .structure import Block

# Set up logging
logger = logging.getLogger(__name__)

class TextProcessor:
    """Handle text processing and NLP tasks."""
    
    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize the text processor.
        
        Args:
            model: spaCy model to use for NLP tasks
        """
        try:
            self.nlp = spacy.load(model)
        except OSError:
            logger.info(f"Downloading spaCy model: {model}...")
            _download_spacy_model(model)
            self.nlp = spacy.load(model)

    def process_blocks(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """
        Process text blocks with NLP pipeline.
        
        Args:
            blocks: List of text blocks to process
            
        Returns:
            List[Dict[str, Any]]: Processed blocks with NLP annotations
        """
        processed_blocks = []
        
        for block in blocks:
            doc = self.nlp(block.content)
            
            processed_block = {
                "id": block.id,
                "type": block.type,
                "content": block.content,
                "entities": [
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    } for ent in doc.ents
                ],
                "sentences": [str(sent) for sent in doc.sents],
                "keywords": [
                    token.text for token in doc
                    if not token.is_stop and not token.is_punct and token.pos_ in ["NOUN", "PROPN"]
                ]
            }
            
            processed_blocks.append(processed_block)
            
        return processed_blocks

    def extract_summary(self, text: str, sentences: int = 3) -> str:
        """
        Generate a summary of the text.
        
        Args:
            text: Text to summarize
            sentences: Number of sentences in the summary
            
        Returns:
            str: Summarized text
        """
        doc = self.nlp(text)
        
        # Simple extractive summarization based on sentence importance
        sentence_scores = {}
        for sent in doc.sents:
            # Score based on the number of important words
            score = sum(1 for token in sent
                       if not token.is_stop and not token.is_punct)
            sentence_scores[sent.text] = score
            
        # Get top sentences
        summary_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:sentences]
        
        return " ".join(sent[0] for sent in summary_sentences)
    
def _download_spacy_model(model: str):
    """Download the spaCy model if it doesn't exist."""
    subprocess.run(["python", "-m", "spacy", "download", model])
