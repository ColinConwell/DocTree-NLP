"""
Example of text summarization and grammatical correction using LLMs.

This example demonstrates how to use Language Models (LLMs) to improve text
by summarizing content or correcting spelling and grammar.
"""
from typing import Dict, Any, Optional

from doctree_nlp import TextProcessor, Block, get_api_key

try:
    import anthropic
except ImportError:
    raise ImportError("anthropic is not installed. Please install it with 'pip install anthropic'.")

class LLMTextImprover:
    """Handle text improvement using LLMs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM text improver.
        
        Args:
            api_key: API key for the LLM service (defaults to environment variable)
        """
        self.api_key = api_key or get_api_key("anthropic")
        if not self.api_key:
            raise ValueError("API key not provided and not found in environment variables")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def summarize_text(self, text: str, max_length: int = 150) -> str:
        """
        Summarize text using an LLM.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary in words
            
        Returns:
            str: Summarized text
        """
        prompt = f"""
        Please summarize the following text in a concise way, keeping the most important information.
        Keep the summary under {max_length} words.
        
        Text to summarize:
        {text}
        
        Summary:
        """
        
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0.3,
            system="You are a helpful assistant that summarizes text accurately and concisely.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    def correct_text(self, text: str) -> Dict[str, Any]:
        """
        Correct spelling and grammar in text using an LLM.
        
        Args:
            text: Text to correct
            
        Returns:
            Dict[str, Any]: Corrected text with metadata
        """
        prompt = f"""
        Please correct any spelling or grammatical errors in the following text.
        Return the corrected version only, without explanations.
        
        Text to correct:
        {text}
        
        Corrected text:
        """
        
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0.0,
            system="You are a helpful assistant that corrects spelling and grammar accurately.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        corrected_text = response.content[0].text
        
        # Calculate simple diff statistics
        original_words = text.split()
        corrected_words = corrected_text.split()
        
        return {
            "original": text,
            "corrected": corrected_text,
            "original_length": len(original_words),
            "corrected_length": len(corrected_words),
            "difference": abs(len(original_words) - len(corrected_words))
        }

def main():
    """Main example function."""
    try:
        # Initialize improver with API key from environment
        try:
            improver = LLMTextImprover()
        except ValueError as e:
            print(f"Error: {e}")
            return
        
        # Sample text with errors
        sample_text = """
        The DocTree-NLP library is desined to help developers work with Notion documents.
        It provides various NLP capabilites such as entity extraction, text summarization,
        and document tagging. The libary can be used to build powerfull applications
        that leverage both Notion's API and modern NLP techniques.
        """
        
        print("Sample text:")
        print(sample_text)
        
        # Correct text
        print("\nCorrecting text...")
        correction_result = improver.correct_text(sample_text)
        
        print("\nCorrected text:")
        print(correction_result["corrected"])
        print(f"\nDifference: {correction_result['difference']} words")
        
        # Longer text for summarization
        longer_text = """
        The Notion NLP library provides a comprehensive set of tools for processing and analyzing
        Notion documents using natural language processing techniques. It allows developers to
        extract structured data from unstructured text, identify entities and relationships,
        generate tags based on content, and organize documents hierarchically.
        
        Key features include document retrieval from the Notion API, content extraction with
        enhanced handling of different block types, entity recognition using spaCy models,
        keyword extraction based on part-of-speech tagging, and hierarchical document structure
        analysis. The library also supports custom tagging and basic sentiment analysis.
        
        Developers can use the library to build applications that automatically organize and
        categorize Notion documents, extract insights from document collections, generate
        metadata for better searchability, and create knowledge graphs from document relationships.
        The library is designed to be extensible, allowing integration with other NLP tools and
        custom processing pipelines.
        """
        
        print("\nLonger text for summarization:")
        print(longer_text)
        
        # Summarize text
        print("\nSummarizing text...")
        summary = improver.summarize_text(longer_text)
        
        print("\nSummary:")
        print(summary)
        
        # Integration with NotionNLP
        print("\nIntegration with NotionNLP:")
        processor = TextProcessor()
        block = Block(
            id="example",
            type="paragraph",
            content=longer_text,
            has_children=False
        )
        
        # Process the block with NLP
        processed = processor.process_blocks([block])[0]
        
        # Compare built-in summarization with LLM summarization
        built_in_summary = processor.extract_summary(processed["content"], sentences=3)
        
        print("\nBuilt-in extractive summary:")
        print(built_in_summary)
        
        print("\nLLM-based abstractive summary:")
        print(summary)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
