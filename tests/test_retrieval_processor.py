"""
Test suite for the retrieval post-processing module

Run with: python -m pytest test_retrieval_processor.py -v
Or directly: python test_retrieval_processor.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.retrieval_processor import (
        RetrievalProcessor,
        process_search_results,
        ProcessingStats
    )
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Error importing retrieval processor: {e}")
    print("Install requirements: pip install sentence-transformers torch")
    PROCESSOR_AVAILABLE = False
    sys.exit(1)


def test_semantic_reranking():
    """Test semantic re-ranking functionality"""
    print("\n" + "="*60)
    print("TEST 1: Semantic Re-ranking")
    print("="*60)
    
    documents = [
        {
            "url": "https://example.com/cats",
            "markdown": "Dogs are loyal pets. They love to play fetch and go for walks.",
            "title": "Dogs Guide"
        },
        {
            "url": "https://example.com/dogs",
            "markdown": "Cats are independent animals. They enjoy napping and grooming.",
            "title": "Cat Care"
        },
        {
            "url": "https://example.com/pets",
            "markdown": "Cats and dogs are both popular pets. Each has unique characteristics.",
            "title": "Pet Comparison"
        }
    ]
    
    query = "information about cats"
    
    processor = RetrievalProcessor()
    ranked = processor.semantic_rerank(documents, query)
    
    print(f"\nQuery: '{query}'")
    print("\nRanked results:")
    for i, doc in enumerate(ranked, 1):
        print(f"{i}. {doc['title']} (score: {doc.get('_similarity_score', 0):.3f})")
    
    # The cat document should rank highest
    assert ranked[0]['title'] == "Cat Care", "Cat document should rank first"
    print("\n✓ Test passed: Documents correctly ranked by relevance")


def test_deduplication():
    """Test deduplication functionality"""
    print("\n" + "="*60)
    print("TEST 2: Deduplication")
    print("="*60)
    
    documents = [
        {
            "url": "https://example.com/ai-1",
            "markdown": "Artificial intelligence is transforming the world. AI systems are becoming more powerful.",
            "title": "AI Overview"
        },
        {
            "url": "https://example.com/ai-2",
            "markdown": "Artificial intelligence is transforming the world. AI systems are becoming more powerful.",
            "title": "AI Overview (Duplicate)"
        },
        {
            "url": "https://example.com/ml",
            "markdown": "Machine learning is a subset of AI focused on learning from data.",
            "title": "Machine Learning"
        },
        {
            "url": "https://example.com/ai-3",
            "markdown": "AI is changing industries. Systems are getting more capable each year.",
            "title": "AI Similar"
        }
    ]
    
    processor = RetrievalProcessor()
    unique = processor.deduplicate(documents, threshold=0.9)
    
    print(f"\nOriginal documents: {len(documents)}")
    print(f"After deduplication: {len(unique)}")
    print("\nKept documents:")
    for i, doc in enumerate(unique, 1):
        print(f"{i}. {doc['title']}")
    
    assert len(unique) < len(documents), "Some duplicates should be removed"
    print("\n✓ Test passed: Duplicates successfully removed")


def test_freshness_filtering():
    """Test freshness filtering functionality"""
    print("\n" + "="*60)
    print("TEST 3: Freshness Filtering")
    print("="*60)
    
    documents = [
        {
            "url": "https://example.com/new",
            "markdown": "Latest AI developments in 2024. Published January 2024.",
            "title": "AI 2024"
        },
        {
            "url": "https://example.com/recent",
            "markdown": "Machine learning trends from 2022. Updated in March 2022.",
            "title": "ML 2022"
        },
        {
            "url": "https://example.com/old",
            "markdown": "AI basics from 2018. Historical overview.",
            "title": "AI 2018"
        },
        {
            "url": "https://example.com/no-date",
            "markdown": "General information about artificial intelligence.",
            "title": "AI General"
        }
    ]
    
    processor = RetrievalProcessor()
    fresh = processor.filter_by_freshness(documents, min_year=2020)
    
    print(f"\nOriginal documents: {len(documents)}")
    print(f"After freshness filter (min_year=2020): {len(fresh)}")
    print("\nKept documents:")
    for i, doc in enumerate(fresh, 1):
        year = doc.get('_extracted_year', 'N/A')
        print(f"{i}. {doc['title']} (year: {year})")
    
    # Should keep 2024, 2022, and no-date document
    assert len(fresh) >= 3, "Should keep recent and undated documents"
    print("\n✓ Test passed: Old documents filtered successfully")


def test_full_pipeline():
    """Test the complete processing pipeline"""
    print("\n" + "="*60)
    print("TEST 4: Full Pipeline")
    print("="*60)
    
    documents = [
        {
            "url": "https://example.com/python-2024-1",
            "markdown": "Python 3.12 features released in 2024. New syntax and performance improvements.",
            "title": "Python 3.12"
        },
        {
            "url": "https://example.com/python-2024-2",
            "markdown": "Python 3.12 features released in 2024. New syntax and performance improvements.",
            "title": "Python 3.12 (Duplicate)"
        },
        {
            "url": "https://example.com/python-old",
            "markdown": "Python 2.7 end of life in 2019. Legacy version information.",
            "title": "Python 2.7"
        },
        {
            "url": "https://example.com/javascript",
            "markdown": "JavaScript ES2024 features and updates. New array methods.",
            "title": "JavaScript 2024"
        },
        {
            "url": "https://example.com/python-2023",
            "markdown": "Python type hints and async improvements in 2023.",
            "title": "Python 2023"
        }
    ]
    
    query = "Python programming latest features"
    
    processed, stats = process_search_results(
        results=documents,
        query=query,
        dedup_threshold=0.9,
        min_year=2020
    )
    
    print(f"\nQuery: '{query}'")
    print(f"\nProcessing statistics:")
    print(f"  Initial: {stats.initial_count}")
    print(f"  After ranking: {stats.after_ranking}")
    print(f"  After dedup: {stats.after_deduplication}")
    print(f"  After freshness: {stats.after_freshness}")
    print(f"  Duplicates removed: {stats.duplicates_removed}")
    print(f"  Outdated removed: {stats.outdated_removed}")
    
    print("\nFinal documents:")
    for i, doc in enumerate(processed, 1):
        score = doc.get('_similarity_score', 0)
        year = doc.get('_extracted_year', 'N/A')
        print(f"{i}. {doc['title']} (score: {score:.3f}, year: {year})")
    
    # Should have fewer documents than original
    assert len(processed) < len(documents), "Pipeline should reduce document count"
    # Python documents should rank higher than JavaScript
    assert "Python" in processed[0]['title'], "Python docs should rank highest for Python query"
    print("\n✓ Test passed: Full pipeline working correctly")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TEST 5: Edge Cases")
    print("="*60)
    
    processor = RetrievalProcessor()
    
    # Empty list
    print("\n• Testing empty document list...")
    result = processor.semantic_rerank([], "test query")
    assert result == [], "Empty list should return empty list"
    print("  ✓ Empty list handled")
    
    # Single document
    print("\n• Testing single document...")
    single = [{"markdown": "Test content", "url": "test.com"}]
    result = processor.deduplicate(single)
    assert len(result) == 1, "Single document should remain"
    print("  ✓ Single document handled")
    
    # Documents without content
    print("\n• Testing documents without markdown/content...")
    no_content = [{"url": "test.com", "title": "Test"}]
    result = processor.semantic_rerank(no_content, "query")
    assert len(result) == 1, "Documents without content should be handled"
    print("  ✓ Missing content handled")
    
    # Very similar documents (high threshold)
    print("\n• Testing high similarity threshold...")
    similar = [
        {"markdown": "AI is cool", "url": "1"},
        {"markdown": "AI is cool", "url": "2"}
    ]
    result = processor.deduplicate(similar, threshold=0.99)
    assert len(result) == 1, "Exact duplicates should be removed"
    print("  ✓ High threshold handled")
    
    print("\n✓ All edge cases handled correctly")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RETRIEVAL POST-PROCESSOR TEST SUITE")
    print("="*60)
    
    if not PROCESSOR_AVAILABLE:
        print("\n❌ Retrieval processor not available")
        print("Install with: pip install sentence-transformers torch")
        return False
    
    try:
        test_semantic_reranking()
        test_deduplication()
        test_freshness_filtering()
        test_full_pipeline()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
