# Quick Start: Retrieval Post-Processing

## Installation

### 1. Install Dependencies

```bash
pip install sentence-transformers torch
```

Or install all project requirements:

```bash
pip install -r requirements.txt
```

### 2. Enable in Configuration

Add to your `.env.local` file:

```bash
# Enable retrieval post-processing
USE_RERANKING=true

# Optional: Customize settings
DEDUP_THRESHOLD=0.9    # Similarity threshold for duplicates (0-1)
MIN_YEAR=2020         # Minimum year for freshness filtering
```

### 3. Verify Installation

```bash
python example_retrieval_processor.py
```

You should see output like:
```
✓ Retrieval processor loaded successfully

📊 Processing 5 search results...
  → Ranked 5 documents by semantic similarity
  → Removed 1 near-duplicates (threshold: 0.9)
  → Filtered by freshness: kept 3 docs, removed 1 outdated

✓ Processing complete: 5 → 3 documents
```

## Usage

### Automatic (with Deep Research)

The post-processing is automatically applied when you run research:

```bash
# CLI
python -m src.run

# Dashboard
python run_dashboard.py

# API
python -m src.api
```

The pipeline will:
1. Search with Firecrawl
2. Scrape content
3. **→ Apply post-processing** (re-rank, deduplicate, filter)
4. Extract learnings
5. Generate report

### Manual (standalone)

Use the module directly:

```python
from src.retrieval_processor import process_search_results

# Your documents
documents = [
    {"url": "...", "markdown": "...", "title": "..."},
    # ... more documents
]

# Process
processed, stats = process_search_results(
    results=documents,
    query="your search query",
    dedup_threshold=0.9,
    min_year=2020
)

print(f"Processed {stats.initial_count} → {stats.after_freshness} documents")
```

## Testing

Run the test suite:

```bash
python test_retrieval_processor.py
```

Expected output:
```
============================================================
RETRIEVAL POST-PROCESSOR TEST SUITE
============================================================

============================================================
TEST 1: Semantic Re-ranking
============================================================
...
✓ Test passed: Documents correctly ranked by relevance

============================================================
TEST 2: Deduplication
============================================================
...
✓ Test passed: Duplicates successfully removed

...

============================================================
✓ ALL TESTS PASSED
============================================================
```

## Configuration Options

### Environment Variables

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `USE_RERANKING` | Enable post-processing | `true` | true/false |
| `DEDUP_THRESHOLD` | Deduplication threshold | `0.9` | 0.0-1.0 |
| `MIN_YEAR` | Minimum document year | `2020` | 2000-2025 |

### Programmatic Configuration

```python
from src.retrieval_processor import process_search_results

# Custom settings
processed, stats = process_search_results(
    results=documents,
    query="your query",
    dedup_threshold=0.95,      # Stricter deduplication
    min_year=2023,             # Only very recent docs
    model_name="all-mpnet-base-v2"  # Better model
)

# Skip specific steps
processed, stats = process_search_results(
    results=documents,
    query="your query",
    skip_ranking=False,        # Enable ranking
    skip_dedup=True,          # Skip deduplication
    skip_freshness=False      # Enable freshness
)
```

## Troubleshooting

### "sentence-transformers not found"

```bash
pip install sentence-transformers torch
```

### "CUDA out of memory"

Use CPU instead:

```python
from src.retrieval_processor import RetrievalProcessor

processor = RetrievalProcessor(device="cpu")
```

Or in environment:
```bash
export CUDA_VISIBLE_DEVICES=""  # Force CPU
```

### Slow processing

Use a faster model:

```python
processor = RetrievalProcessor(model_name="all-MiniLM-L6-v2")
```

### Module not working

Check if dependencies are installed:

```bash
python -c "from src.retrieval_processor import process_search_results; print('✓ Working')"
```

If it fails, reinstall:

```bash
pip install --upgrade sentence-transformers torch
```

## Performance Tips

### 1. Use GPU if available
- 5-10x faster than CPU
- Automatically detected

### 2. Reuse processor instance
```python
from src.retrieval_processor import get_processor

# Get cached instance
processor = get_processor()

# Use multiple times
for query in queries:
    result = processor.semantic_rerank(docs, query)
```

### 3. Adjust thresholds
```python
# More aggressive deduplication = faster
processed, _ = process_search_results(
    results=docs,
    query=query,
    dedup_threshold=0.85  # Lower threshold
)
```

### 4. Skip unnecessary steps
```python
# Only re-rank, skip others
processed, _ = process_search_results(
    results=docs,
    query=query,
    skip_dedup=True,
    skip_freshness=True
)
```

## Next Steps

1. **Read the full documentation**: [RETRIEVAL_PROCESSOR.md](RETRIEVAL_PROCESSOR.md)
2. **Run examples**: `python example_retrieval_processor.py`
3. **Run tests**: `python test_retrieval_processor.py`
4. **Try with research**: `python run_dashboard.py`
5. **Customize settings**: Edit `.env.local`

## Support

- **Documentation**: See [RETRIEVAL_PROCESSOR.md](RETRIEVAL_PROCESSOR.md)
- **Examples**: See [example_retrieval_processor.py](example_retrieval_processor.py)
- **Tests**: See [test_retrieval_processor.py](test_retrieval_processor.py)
- **Issues**: Check existing issues or open a new one

## Summary

✅ **Installed** - Dependencies in place
✅ **Configured** - Settings in .env.local
✅ **Integrated** - Works with existing pipeline
✅ **Tested** - All tests passing
✅ **Ready** - Start using now!

Enjoy better search results! 🚀
