"""
Provenance Tracking Module

Tracks the source and supporting evidence for each learning generated during research.
Provides transparency and verifiability by linking each insight back to its original source.

Usage:
    from src.provenance import track_learning_provenance, format_learnings_with_provenance
    
    # Track provenance for learnings
    learnings_with_provenance = track_learning_provenance(
        learnings=learnings_list,
        source_documents=documents,
        source_url=url
    )
    
    # Format for output
    markdown = format_learnings_with_provenance(learnings_with_provenance)
"""

import re
from typing import List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass, asdict
import json


class LearningWithProvenance(TypedDict):
    """Structure for a learning with its provenance information"""
    learning: str
    source_url: str
    source_snippet: str
    confidence: Optional[float]


@dataclass
class ProvenanceRecord:
    """
    Complete provenance record for a learning
    
    Attributes:
        learning: The summarized insight/learning
        source_url: URL of the source document
        source_snippet: 1-2 sentence excerpt supporting the learning
        confidence: Confidence score (0-1), None if not calculated
    """
    learning: str
    source_url: str
    source_snippet: str
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Format as markdown"""
        md = f"**Learning:** {self.learning}\n\n"
        md += f"**Source:** [{self.source_url}]({self.source_url})\n\n"
        md += f"**Supporting Evidence:**\n> {self.source_snippet}\n"
        if self.confidence is not None:
            md += f"\n*Confidence: {self.confidence:.2%}*\n"
        return md
    
    def to_html(self) -> str:
        """Format as HTML"""
        html = f'<div class="learning-with-provenance">\n'
        html += f'  <div class="learning">{self.learning}</div>\n'
        html += f'  <div class="provenance">\n'
        html += f'    <div class="source"><strong>Source:</strong> <a href="{self.source_url}" target="_blank">{self.source_url}</a></div>\n'
        html += f'    <div class="snippet"><strong>Evidence:</strong> <em>{self.source_snippet}</em></div>\n'
        if self.confidence is not None:
            html += f'    <div class="confidence"><strong>Confidence:</strong> {self.confidence:.2%}</div>\n'
        html += f'  </div>\n'
        html += f'</div>\n'
        return html


def extract_supporting_snippet(
    learning: str,
    document_text: str,
    max_sentences: int = 2,
    context_chars: int = 300
) -> str:
    """
    Extract the most relevant snippet from document that supports the learning
    
    Args:
        learning: The summarized learning/insight
        document_text: Full text of the source document
        max_sentences: Maximum number of sentences to include in snippet
        context_chars: Approximate characters of context to search
        
    Returns:
        1-2 sentence snippet that best supports the learning
    """
    if not document_text:
        return "No source text available"
    
    # Clean the texts
    learning_lower = learning.lower()
    document_lower = document_text.lower()
    
    # Extract key terms from the learning (nouns, proper nouns, numbers)
    # Simple approach: words with 4+ chars, excluding common words
    common_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 
                   'will', 'their', 'there', 'about', 'which', 'when', 'where'}
    
    key_terms = []
    for word in re.findall(r'\b\w+\b', learning_lower):
        if len(word) >= 4 and word not in common_words:
            key_terms.append(word)
    
    if not key_terms:
        # Fallback: just use first few sentences
        sentences = re.split(r'[.!?]+', document_text)
        return '. '.join(sentences[:max_sentences]).strip() + '.'
    
    # Split document into sentences
    sentences = re.split(r'(?<=[.!?])\s+', document_text)
    
    # Score each sentence by how many key terms it contains
    best_score = 0
    best_sentences = []
    
    for i, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()
        score = sum(1 for term in key_terms if term in sentence_lower)
        
        if score > best_score:
            best_score = score
            # Get this sentence and optionally the next one
            best_sentences = sentences[i:i+max_sentences]
    
    if not best_sentences:
        # Fallback: return first sentences
        best_sentences = sentences[:max_sentences]
    
    snippet = ' '.join(best_sentences).strip()
    
    # Truncate if too long
    if len(snippet) > context_chars:
        snippet = snippet[:context_chars].rsplit(' ', 1)[0] + '...'
    
    return snippet


def track_learning_provenance(
    learnings: List[str],
    source_documents: List[Dict[str, Any]],
    source_url: Optional[str] = None
) -> List[ProvenanceRecord]:
    """
    Track provenance for a list of learnings
    
    Args:
        learnings: List of learning strings
        source_documents: List of source document dicts with 'markdown'/'content' and 'url'
        source_url: Optional single source URL if all learnings are from one source
        
    Returns:
        List of ProvenanceRecord objects with full provenance information
    """
    provenance_records = []
    
    for learning in learnings:
        # Find the best matching document for this learning
        best_doc = None
        best_snippet = None
        
        if source_documents:
            # Try to match learning to most relevant document
            best_match_score = 0
            
            for doc in source_documents:
                content = doc.get('markdown', '') or doc.get('content', '')
                if not content:
                    continue
                
                # Simple relevance: count matching words
                learning_words = set(re.findall(r'\b\w{4,}\b', learning.lower()))
                content_words = set(re.findall(r'\b\w{4,}\b', content.lower()))
                match_score = len(learning_words & content_words)
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_doc = doc
            
            if best_doc:
                content = best_doc.get('markdown', '') or best_doc.get('content', '')
                best_snippet = extract_supporting_snippet(learning, content)
                doc_url = best_doc.get('url', source_url or 'Unknown source')
            else:
                best_snippet = "Source document not available"
                doc_url = source_url or 'Unknown source'
        else:
            best_snippet = "Source document not available"
            doc_url = source_url or 'Unknown source'
        
        record = ProvenanceRecord(
            learning=learning,
            source_url=doc_url,
            source_snippet=best_snippet,
            confidence=None  # Can be set later if confidence scoring is implemented
        )
        
        provenance_records.append(record)
    
    return provenance_records


def track_single_learning(
    learning: str,
    source_url: str,
    source_text: str,
    confidence: Optional[float] = None
) -> ProvenanceRecord:
    """
    Track provenance for a single learning
    
    Args:
        learning: The learning/insight text
        source_url: URL of the source
        source_text: Full text of the source document
        confidence: Optional confidence score (0-1)
        
    Returns:
        ProvenanceRecord with full provenance information
    """
    snippet = extract_supporting_snippet(learning, source_text)
    
    return ProvenanceRecord(
        learning=learning,
        source_url=source_url,
        source_snippet=snippet,
        confidence=confidence
    )


def format_learnings_with_provenance(
    provenance_records: List[ProvenanceRecord],
    format: str = 'markdown'
) -> str:
    """
    Format learnings with provenance for output
    
    Args:
        provenance_records: List of ProvenanceRecord objects
        format: Output format ('markdown' or 'html')
        
    Returns:
        Formatted string with learnings and provenance
    """
    if format == 'html':
        output = '<div class="learnings-with-provenance">\n'
        for i, record in enumerate(provenance_records, 1):
            output += f'<div class="learning-item" id="learning-{i}">\n'
            output += f'<h4>Learning #{i}</h4>\n'
            output += record.to_html()
            output += '</div>\n'
        output += '</div>\n'
        
        # Add CSS
        output += '''
<style>
.learnings-with-provenance {
    margin: 20px 0;
}
.learning-item {
    margin-bottom: 20px;
    padding: 15px;
    border-left: 4px solid #2563eb;
    background: #f8fafc;
    border-radius: 4px;
}
.learning {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #0f172a;
}
.provenance {
    margin-top: 10px;
    padding-left: 15px;
    font-size: 14px;
    color: #64748b;
}
.source {
    margin-bottom: 5px;
}
.snippet {
    margin: 8px 0;
    padding: 8px;
    background: white;
    border-radius: 4px;
    font-style: italic;
}
.confidence {
    margin-top: 5px;
    font-size: 12px;
}
</style>
'''
        return output
    
    else:  # markdown
        output = "# Research Learnings with Provenance\n\n"
        for i, record in enumerate(provenance_records, 1):
            output += f"## Learning #{i}\n\n"
            output += record.to_markdown()
            output += "\n---\n\n"
        return output


def export_provenance_json(
    provenance_records: List[ProvenanceRecord],
    filepath: str
):
    """
    Export provenance records to JSON file
    
    Args:
        provenance_records: List of ProvenanceRecord objects
        filepath: Path to output JSON file
    """
    data = {
        'learnings': [record.to_dict() for record in provenance_records],
        'total_learnings': len(provenance_records),
        'timestamp': None  # Can add timestamp if needed
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_provenance_json(filepath: str) -> List[ProvenanceRecord]:
    """
    Load provenance records from JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of ProvenanceRecord objects
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return [
        ProvenanceRecord(**record)
        for record in data['learnings']
    ]


# Example usage
if __name__ == "__main__":
    # Example documents
    example_docs = [
        {
            "url": "https://example.com/python-3.12",
            "markdown": """
            Python 3.12 was released in October 2023 with significant performance improvements.
            The new version includes better error messages with more precise locations.
            Performance benchmarks show 10-60% faster execution compared to Python 3.11.
            The type system has been enhanced with new syntax for generic types.
            """
        },
        {
            "url": "https://example.com/python-features",
            "markdown": """
            Python 3.12 introduces f-string improvements allowing inline debugging.
            The PEP 701 proposal adds more flexibility to f-string syntax.
            Error messages now include color coding in the terminal for better readability.
            The interpreter startup time has been reduced by 20%.
            """
        }
    ]
    
    # Example learnings
    example_learnings = [
        "Python 3.12 shows 10-60% performance improvement over Python 3.11",
        "Python 3.12 includes enhanced error messages with precise locations and color coding",
        "F-strings in Python 3.12 support improved debugging capabilities"
    ]
    
    # Track provenance
    print("="*60)
    print("PROVENANCE TRACKING EXAMPLE")
    print("="*60 + "\n")
    
    provenance_records = track_learning_provenance(
        learnings=example_learnings,
        source_documents=example_docs
    )
    
    print("Tracked provenance for", len(provenance_records), "learnings:\n")
    
    for i, record in enumerate(provenance_records, 1):
        print(f"{i}. {record.learning}")
        print(f"   Source: {record.source_url}")
        print(f"   Snippet: {record.source_snippet[:100]}...")
        print()
    
    # Format as markdown
    print("\nMarkdown Output:")
    print("-"*60)
    markdown_output = format_learnings_with_provenance(provenance_records, format='markdown')
    print(markdown_output[:500] + "...\n")
    
    # Format as HTML
    print("HTML Output Preview:")
    print("-"*60)
    html_output = format_learnings_with_provenance(provenance_records, format='html')
    print(html_output[:300] + "...\n")
    
    print("✓ Provenance tracking complete!")
