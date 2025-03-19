"""
Example of fuzzy pattern extraction using regex and fuzzy matching.

This example demonstrates how to extract patterns like "{some digits} x {other digits}"
from text using regular expressions and fuzzy matching techniques.
"""
import re
from typing import List, Dict, Any, Pattern
from doctree_nlp import TextProcessor, Block

def extract_patterns(text: str, patterns: List[str], threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    Extract patterns from text using fuzzy matching.
    
    Args:
        text: Text to extract patterns from
        patterns: List of pattern templates to match
        threshold: Similarity threshold for fuzzy matching (0.0 to 1.0)
        
    Returns:
        List[Dict[str, Any]]: Extracted patterns with metadata
    """
    results = []
    
    # Convert pattern templates to regex patterns
    regex_patterns = []
    for pattern in patterns:
        # Replace placeholders with regex capture groups
        regex_pattern = pattern
        regex_pattern = re.sub(r'\{\s*some\s+digits\s*\}', r'([0-9]+)', regex_pattern)
        regex_pattern = re.sub(r'\{\s*other\s+digits\s*\}', r'([0-9]+)', regex_pattern)
        # Add word boundaries and make whitespace flexible
        regex_pattern = regex_pattern.replace(' ', r'\s*')
        regex_patterns.append(re.compile(regex_pattern, re.IGNORECASE))
    
    # Find matches for each pattern
    for i, pattern_re in enumerate(regex_patterns):
        for match in pattern_re.finditer(text):
            results.append({
                'pattern': patterns[i],
                'matched_text': match.group(0),
                'groups': match.groups(),
                'position': (match.start(), match.end()),
                'confidence': 1.0  # Exact match has confidence 1.0
            })
    
    return results

def main():
    """Main example function."""
    try:
        # Sample text with patterns to extract
        sample_text = """
        The image dimensions are 1920 x 1080 pixels.
        We need to order 25 by 30 cm frames.
        The room size is approximately 15 x 20 feet.
        The document has a size of 8.5 by 11 inches.
        """
        
        # Define pattern templates
        patterns = [
            "{some digits} x {other digits}",
            "{some digits} by {other digits}"
        ]
        
        print("Sample text:")
        print(sample_text)
        print("\nPattern templates:")
        for pattern in patterns:
            print(f"- {pattern}")
        
        # Extract patterns
        print("\nExtracting patterns...")
        results = extract_patterns(sample_text, patterns)
        
        # Display results
        print("\nExtracted patterns:")
        for result in results:
            print(f"- Pattern: {result['pattern']}")
            print(f"  Matched: {result['matched_text']}")
            print(f"  Values: {result['groups']}")
            print(f"  Position: {result['position']}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print()
        
        # Integration with NotionNLP
        print("\nIntegration with NotionNLP:")
        processor = TextProcessor()
        block = Block(
            id="example",
            type="paragraph",
            content=sample_text,
            has_children=False
        )
        
        # Process the block with NLP
        processed = processor.process_blocks([block])[0]
        
        # Extract patterns from processed content
        patterns_in_processed = extract_patterns(processed["content"], patterns)
        
        print(f"Entities found: {len(processed['entities'])}")
        print(f"Patterns found: {len(patterns_in_processed)}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
