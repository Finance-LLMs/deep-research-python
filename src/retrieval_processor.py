"""
Retrieval Post-Processing Module

This module provides three key functions for cleaning and ranking search results:
1. Semantic re-ranking using sentence transformers
2. Deduplication based on content similarity
3. Freshness filtering based on document dates

Usage:
    from src.retrieval_processor import process_search_results
    
    processed_results = process_search_results(
        results=firecrawl_results,
        query="your search query",
        dedup_threshold=0.9,
        min_year=2020
    )
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError:
    print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")
    SentenceTransformer = None


@dataclass
class ProcessingStats:
    """Statistics from the processing pipeline"""
    initial_count: int
    after_ranking: int
    after_deduplication: int
    after_freshness: int
    duplicates_removed: int
    outdated_removed: int


class RetrievalProcessor:
    """
    Post-processes search results with semantic ranking, deduplication, and freshness filtering
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None
    ):
        """
        Initialize the retrieval processor
        
        Args:
            model_name: Name of the SentenceTransformer model to use
            device: Device to run the model on ('cuda', 'cpu', or None for auto-detect)
        """
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )
        
        # Initialize the model
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = SentenceTransformer(model_name, device=device)
        self.device = device
        print(f"✓ Retrieval processor initialized with model '{model_name}' on {device}")
    
    def semantic_rerank(
        self,
        documents: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents by semantic similarity to the query
        
        Args:
            documents: List of document dictionaries with 'markdown' or 'content' fields
            query: Search query string
            
        Returns:
            Documents sorted by relevance (highest to lowest)
        """
        if not documents:
            return []
        
        # Extract text content from documents
        texts = []
        for doc in documents:
            content = doc.get('markdown', '') or doc.get('content', '')
            # Truncate to first 1000 characters for efficiency
            texts.append(content[:1000] if content else "")
        
        # Encode query and documents
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        doc_embeddings = self.model.encode(texts, convert_to_tensor=True)
        
        # Compute cosine similarities
        similarities = torch.nn.functional.cosine_similarity(
            query_embedding.unsqueeze(0),
            doc_embeddings
        )
        
        # Sort documents by similarity (descending)
        sorted_indices = torch.argsort(similarities, descending=True).cpu().numpy()
        
        # Add similarity scores and reorder
        ranked_docs = []
        for idx in sorted_indices:
            doc = documents[idx].copy()
            doc['_similarity_score'] = float(similarities[idx])
            ranked_docs.append(doc)
        
        print(f"  → Ranked {len(ranked_docs)} documents by semantic similarity")
        return ranked_docs
    
    def deduplicate(
        self,
        documents: List[Dict[str, Any]],
        threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Remove near-duplicate documents based on content similarity
        
        Args:
            documents: List of document dictionaries
            threshold: Cosine similarity threshold for considering duplicates (0-1)
            
        Returns:
            Deduplicated list of documents
        """
        if not documents or len(documents) <= 1:
            return documents
        
        # Extract text content
        texts = []
        for doc in documents:
            content = doc.get('markdown', '') or doc.get('content', '')
            texts.append(content if content else "")
        
        # Encode all documents
        embeddings = self.model.encode(texts, convert_to_tensor=True)
        
        # Compute pairwise similarities
        similarities = torch.nn.functional.cosine_similarity(
            embeddings.unsqueeze(1),
            embeddings.unsqueeze(0),
            dim=2
        )
        
        # Find duplicates
        keep_indices = []
        removed_indices = set()
        
        for i in range(len(documents)):
            if i in removed_indices:
                continue
            
            keep_indices.append(i)
            
            # Mark similar documents as duplicates
            for j in range(i + 1, len(documents)):
                if j not in removed_indices and similarities[i][j] > threshold:
                    removed_indices.add(j)
        
        # Keep only unique documents
        unique_docs = [documents[i] for i in keep_indices]
        
        duplicates_removed = len(documents) - len(unique_docs)
        print(f"  → Removed {duplicates_removed} near-duplicates (threshold: {threshold})")
        
        return unique_docs
    
    def filter_by_freshness(
        self,
        documents: List[Dict[str, Any]],
        min_year: int = 2020
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by publication date or content freshness
        
        Args:
            documents: List of document dictionaries
            min_year: Minimum year for documents to be considered fresh
            
        Returns:
            Filtered list of documents published after min_year
        """
        if not documents:
            return []
        
        # Common date patterns to search for
        date_patterns = [
            # ISO format: 2023-12-31, 2023/12/31
            r'(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])',
            # Month Day, Year: December 31, 2023
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(20\d{2})',
            # Month Year: December 2023
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(20\d{2})',
            # Year only: 2023
            r'\b(20\d{2})\b'
        ]
        
        fresh_docs = []
        outdated_count = 0
        no_date_count = 0
        
        for doc in documents:
            # Check metadata first
            doc_year = None
            
            # Look for date in metadata
            if 'published_date' in doc or 'date' in doc or 'publishedTime' in doc:
                date_str = doc.get('published_date') or doc.get('date') or doc.get('publishedTime')
                if date_str:
                    try:
                        # Try to parse various date formats
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y', '%Y']:
                            try:
                                date_obj = datetime.strptime(str(date_str)[:10], fmt)
                                doc_year = date_obj.year
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
            
            # If no metadata date, search content
            if doc_year is None:
                content = doc.get('markdown', '') or doc.get('content', '')
                if content:
                    # Search first 2000 characters for dates
                    search_text = content[:2000]
                    
                    years_found = []
                    for pattern in date_patterns:
                        matches = re.findall(pattern, search_text)
                        for match in matches:
                            year_str = match if isinstance(match, str) else match[0]
                            try:
                                year = int(re.search(r'20\d{2}', year_str).group())
                                if 2000 <= year <= datetime.now().year:
                                    years_found.append(year)
                            except (AttributeError, ValueError):
                                continue
                    
                    # Use the most recent year found
                    if years_found:
                        doc_year = max(years_found)
            
            # Decision: keep or filter
            if doc_year is None:
                # No date found - keep it (benefit of the doubt)
                fresh_docs.append(doc)
                no_date_count += 1
            elif doc_year >= min_year:
                doc['_extracted_year'] = doc_year
                fresh_docs.append(doc)
            else:
                outdated_count += 1
        
        print(f"  → Filtered by freshness: kept {len(fresh_docs)} docs, removed {outdated_count} outdated")
        if no_date_count > 0:
            print(f"    (Note: {no_date_count} documents had no detectable date - kept by default)")
        
        return fresh_docs
    
    def process(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        dedup_threshold: float = 0.9,
        min_year: int = 2020,
        skip_ranking: bool = False,
        skip_dedup: bool = False,
        skip_freshness: bool = False
    ) -> tuple[List[Dict[str, Any]], ProcessingStats]:
        """
        Run the full processing pipeline
        
        Args:
            documents: List of document dictionaries
            query: Search query for semantic ranking
            dedup_threshold: Similarity threshold for deduplication (0-1)
            min_year: Minimum year for freshness filtering
            skip_ranking: Skip semantic re-ranking
            skip_dedup: Skip deduplication
            skip_freshness: Skip freshness filtering
            
        Returns:
            Tuple of (processed_documents, processing_stats)
        """
        initial_count = len(documents)
        print(f"\n📊 Processing {initial_count} search results...")
        
        # Step 1: Semantic Re-ranking
        if not skip_ranking and documents:
            documents = self.semantic_rerank(documents, query)
        after_ranking = len(documents)
        
        # Step 2: Deduplication
        if not skip_dedup and documents:
            documents = self.deduplicate(documents, threshold=dedup_threshold)
        after_dedup = len(documents)
        
        # Step 3: Freshness Filtering
        if not skip_freshness and documents:
            documents = self.filter_by_freshness(documents, min_year=min_year)
        after_freshness = len(documents)
        
        # Calculate statistics
        stats = ProcessingStats(
            initial_count=initial_count,
            after_ranking=after_ranking,
            after_deduplication=after_dedup,
            after_freshness=after_freshness,
            duplicates_removed=after_ranking - after_dedup,
            outdated_removed=after_dedup - after_freshness
        )
        
        print(f"\n✓ Processing complete: {initial_count} → {after_freshness} documents")
        print(f"  • Duplicates removed: {stats.duplicates_removed}")
        print(f"  • Outdated removed: {stats.outdated_removed}")
        print(f"  • Final retention rate: {(after_freshness/initial_count*100):.1f}%\n")
        
        return documents, stats


# Singleton instance for reuse
_processor_instance = None


def get_processor(
    model_name: str = "all-MiniLM-L6-v2",
    device: Optional[str] = None,
    force_new: bool = False
) -> RetrievalProcessor:
    """
    Get or create a singleton RetrievalProcessor instance
    
    Args:
        model_name: Name of the SentenceTransformer model
        device: Device to run on ('cuda', 'cpu', or None for auto)
        force_new: Force creation of a new instance
        
    Returns:
        RetrievalProcessor instance
    """
    global _processor_instance
    
    if _processor_instance is None or force_new:
        _processor_instance = RetrievalProcessor(model_name=model_name, device=device)
    
    return _processor_instance


def process_search_results(
    results: List[Dict[str, Any]],
    query: str,
    dedup_threshold: float = 0.9,
    min_year: int = 2020,
    model_name: str = "all-MiniLM-L6-v2",
    skip_ranking: bool = False,
    skip_dedup: bool = False,
    skip_freshness: bool = False
) -> tuple[List[Dict[str, Any]], ProcessingStats]:
    """
    Convenience function to process search results with default settings
    
    Args:
        results: List of document dictionaries from Firecrawl
        query: Original search query
        dedup_threshold: Cosine similarity threshold for duplicates (default: 0.9)
        min_year: Minimum year for freshness filter (default: 2020)
        model_name: SentenceTransformer model to use
        skip_ranking: Skip semantic re-ranking step
        skip_dedup: Skip deduplication step
        skip_freshness: Skip freshness filtering step
        
    Returns:
        Tuple of (processed_documents, processing_stats)
    """
    processor = get_processor(model_name=model_name)
    return processor.process(
        documents=results,
        query=query,
        dedup_threshold=dedup_threshold,
        min_year=min_year,
        skip_ranking=skip_ranking,
        skip_dedup=skip_dedup,
        skip_freshness=skip_freshness
    )


# Example usage
if __name__ == "__main__":
    # Example documents
    example_docs = [
        {
            "url": "https://example.com/ai-2024",
            "markdown": "Artificial Intelligence trends in 2024. Published on January 15, 2024.",
            "title": "AI Trends 2024"
        },
        {
            "url": "https://example.com/ai-trends",
            "markdown": "Artificial Intelligence trends in 2024. Latest developments.",
            "title": "AI Trends"
        },
        {
            "url": "https://example.com/old-ai",
            "markdown": "AI overview from 2018. Outdated information.",
            "title": "Old AI Article"
        },
        {
            "url": "https://example.com/ml",
            "markdown": "Machine Learning fundamentals explained in 2023.",
            "title": "ML Basics"
        }
    ]
    
    # Process the results
    processed, stats = process_search_results(
        results=example_docs,
        query="artificial intelligence trends",
        dedup_threshold=0.9,
        min_year=2020
    )
    
    print("\nProcessed Documents:")
    for i, doc in enumerate(processed, 1):
        print(f"{i}. {doc.get('title', 'Untitled')} - {doc.get('url', 'No URL')}")
        if '_similarity_score' in doc:
            print(f"   Similarity: {doc['_similarity_score']:.3f}")
        if '_extracted_year' in doc:
            print(f"   Year: {doc['_extracted_year']}")
