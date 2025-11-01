"""
Example: Using the Retrieval Post-Processor

This script demonstrates how to use the retrieval post-processing module
to enhance search results quality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.retrieval_processor import process_search_results
    print("✓ Retrieval processor loaded successfully\n")
except ImportError as e:
    print(f"❌ Error: {e}")
    print("\nInstall required packages:")
    print("  pip install sentence-transformers torch")
    sys.exit(1)


def example_basic():
    """Basic example with simple documents"""
    print("="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)
    
    # Sample documents (simulating Firecrawl results)
    documents = [
        {
            "url": "https://example.com/python-2024",
            "markdown": """
                Python 3.12 Released in October 2024
                
                Python 3.12 brings significant performance improvements and new features.
                The release includes better error messages, faster execution, and improved
                type hints. This is one of the most important updates to Python.
            """,
            "title": "Python 3.12 Features"
        },
        {
            "url": "https://example.com/python-duplicate",
            "markdown": """
                Python 3.12 Released in October 2024
                
                Python 3.12 brings significant performance improvements and new features.
                The release includes better error messages, faster execution, and improved
                type hints. This is a major update.
            """,
            "title": "Python 3.12 Overview (Duplicate)"
        },
        {
            "url": "https://example.com/javascript-2024",
            "markdown": """
                JavaScript ES2024 Features Released
                
                ECMAScript 2024 introduces new array methods and improved async handling.
                The update focuses on developer experience and performance.
            """,
            "title": "JavaScript ES2024"
        },
        {
            "url": "https://example.com/python-old",
            "markdown": """
                Python 2.7 End of Life in 2019
                
                Python 2.7 reached end of life on January 1, 2020. This version is no
                longer supported and users should migrate to Python 3.
            """,
            "title": "Python 2.7 EOL"
        },
        {
            "url": "https://example.com/python-2023",
            "markdown": """
                Python 3.11 Performance Improvements in 2023
                
                Python 3.11 introduced significant speed improvements, making it 10-60%
                faster than Python 3.10. New features include better error locations.
            """,
            "title": "Python 3.11 Speed Boost"
        }
    ]
    
    # Process with default settings
    query = "Python latest features and updates"
    
    print(f"\nQuery: '{query}'")
    print(f"Input: {len(documents)} documents\n")
    
    processed, stats = process_search_results(
        results=documents,
        query=query,
        dedup_threshold=0.9,
        min_year=2020
    )
    
    print("\n📋 Final Results:")
    print("-" * 60)
    for i, doc in enumerate(processed, 1):
        score = doc.get('_similarity_score', 0)
        year = doc.get('_extracted_year', 'N/A')
        print(f"\n{i}. {doc['title']}")
        print(f"   URL: {doc['url']}")
        print(f"   Relevance: {score:.3f}")
        print(f"   Year: {year}")
    
    print("\n" + "="*60 + "\n")


def example_custom_config():
    """Example with custom configuration"""
    print("="*60)
    print("EXAMPLE 2: Custom Configuration")
    print("="*60)
    
    documents = [
        {
            "url": "https://research.com/ai-2024",
            "markdown": "Latest AI research breakthroughs in 2024. GPT-5 and beyond.",
            "title": "AI 2024"
        },
        {
            "url": "https://research.com/ai-2023",
            "markdown": "AI developments in 2023. ChatGPT and large language models.",
            "title": "AI 2023"
        },
        {
            "url": "https://research.com/ai-2022",
            "markdown": "AI progress in 2022. Stable Diffusion and DALL-E 2.",
            "title": "AI 2022"
        },
        {
            "url": "https://research.com/ml-basics",
            "markdown": "Machine learning fundamentals and neural networks.",
            "title": "ML Basics"
        }
    ]
    
    query = "cutting edge AI research"
    
    print(f"\nQuery: '{query}'")
    print(f"Config: min_year=2023, dedup_threshold=0.95")
    print(f"Input: {len(documents)} documents\n")
    
    # More strict filtering
    processed, stats = process_search_results(
        results=documents,
        query=query,
        dedup_threshold=0.95,  # More strict deduplication
        min_year=2023         # Only very recent papers
    )
    
    print(f"\n✓ Kept {len(processed)} documents (filtered out 2022 and older)")
    for i, doc in enumerate(processed, 1):
        year = doc.get('_extracted_year', 'N/A')
        print(f"  {i}. {doc['title']} (Year: {year})")
    
    print("\n" + "="*60 + "\n")


def example_selective_processing():
    """Example showing selective step enabling"""
    print("="*60)
    print("EXAMPLE 3: Selective Processing")
    print("="*60)
    
    documents = [
        {"url": "a.com", "markdown": "AI trends in 2024", "title": "AI 2024"},
        {"url": "b.com", "markdown": "ML developments in 2023", "title": "ML 2023"},
        {"url": "c.com", "markdown": "Deep learning basics", "title": "DL Basics"}
    ]
    
    query = "artificial intelligence"
    
    # Only re-ranking, no dedup or freshness
    print("\n1️⃣ Re-ranking only (no dedup, no freshness):")
    processed, stats = process_search_results(
        results=documents,
        query=query,
        skip_dedup=True,
        skip_freshness=True
    )
    print(f"   Result: {stats.initial_count} → {stats.after_freshness} documents")
    
    # Only deduplication
    print("\n2️⃣ Deduplication only (no ranking, no freshness):")
    processed, stats = process_search_results(
        results=documents,
        query=query,
        skip_ranking=True,
        skip_freshness=True
    )
    print(f"   Result: {stats.initial_count} → {stats.after_freshness} documents")
    
    # Only freshness filtering
    print("\n3️⃣ Freshness only (no ranking, no dedup):")
    processed, stats = process_search_results(
        results=documents,
        query=query,
        skip_ranking=True,
        skip_dedup=True
    )
    print(f"   Result: {stats.initial_count} → {stats.after_freshness} documents")
    
    print("\n" + "="*60 + "\n")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("RETRIEVAL POST-PROCESSOR EXAMPLES")
    print("="*60 + "\n")
    
    try:
        example_basic()
        example_custom_config()
        example_selective_processing()
        
        print("✓ All examples completed successfully!\n")
        print("Next steps:")
        print("  • Run tests: python test_retrieval_processor.py")
        print("  • Read docs: RETRIEVAL_PROCESSOR.md")
        print("  • Integrate with your pipeline\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
