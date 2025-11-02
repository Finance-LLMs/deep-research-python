# Provenance Tracking

## Overview

The deep-research-python tool now includes **provenance tracking** functionality that provides transparency and verifiability for research findings. For every generated learning, the system tracks:

1. **Source URL** - The original document where the information was found
2. **Supporting Snippet** - The exact 1-2 sentence excerpt that supports the learning
3. **Confidence Score** - A similarity score indicating how well the learning matches the source

## Why Provenance Tracking?

Provenance tracking addresses key challenges in AI-powered research:

- **Transparency**: Users can see exactly where each learning came from
- **Verifiability**: Anyone can click through to verify the original source
- **Trust**: Supporting snippets show the AI didn't hallucinate facts
- **Accountability**: Clear attribution to source materials

## How It Works

### 1. Document Collection

During research, the system:
- Scrapes web pages using Firecrawl API
- Stores the full text content of each document
- Maintains URL references for all sources

### 2. Learning Generation

The AI analyzes collected documents and generates learnings using LLMs (Large Language Models).

### 3. Provenance Extraction

For each generated learning, the system:

```python
from src.provenance import track_learning_provenance

# Track provenance for all learnings
provenance_records = track_learning_provenance(
    learnings=["Learning 1", "Learning 2", ...],
    source_documents=[
        {"url": "https://...", "markdown": "content..."},
        ...
    ]
)
```

The algorithm:
1. **Key Term Extraction**: Identifies important words/phrases from each learning
2. **Snippet Matching**: Searches source documents for sentences containing those terms
3. **Scoring**: Ranks snippets by term overlap and proximity
4. **Selection**: Chooses the best 1-2 sentence excerpt as supporting evidence

### 4. Display in Results

Provenance information appears in multiple formats:

**CLI/Report Output:**
```markdown
## Research Findings with Provenance

### Learning #1
**Finding:** Python 3.12 introduces improved error messages

**Source:** "Python 3.12 now provides more detailed error messages..."
**From:** https://docs.python.org/3.12/whatsnew
**Confidence:** 95%
```

**Dashboard UI:**
Each learning displays with:
- Main learning text
- Collapsible provenance section showing:
  - Supporting snippet (quoted text)
  - "View Source" link to original document
  - Confidence score badge

## Using Provenance Tracking

### Enabling/Disabling

Provenance tracking is **enabled by default** for all research operations.

To disable (not recommended):
```python
# In deep_research.py
processed = await process_serp_result(
    query,
    result,
    track_provenance=False  # Disable provenance
)
```

### Accessing Provenance Data

**From Python Code:**
```python
from src.deep_research import deep_research

result = await deep_research(
    query="Your research query",
    breadth=4,
    depth=2
)

# Access provenance records
if result.learnings_with_provenance:
    for provenance in result.learnings_with_provenance:
        print(f"Learning: {provenance.learning}")
        print(f"Source: {provenance.source_url}")
        print(f"Snippet: {provenance.supporting_snippet}")
        print(f"Confidence: {provenance.confidence_score}")
```

**From Dashboard:**

Learnings are automatically displayed with provenance in the "Learnings" tab.

**From Report File:**

When you generate a report, provenance is automatically included:
```bash
python -m src.run "Your query" --report
# Check report.md for provenance section
```

## Provenance Data Structure

Each provenance record contains:

```python
@dataclass
class ProvenanceRecord:
    learning: str                    # The generated learning
    source_url: str                  # URL of the source document
    supporting_snippet: Optional[str] # 1-2 sentence excerpt
    confidence_score: float          # 0.0 to 1.0 similarity score
    matched_terms: Optional[List[str]] # Key terms found in snippet
```

## Configuration

The provenance extraction algorithm can be tuned in `src/provenance.py`:

```python
def extract_supporting_snippet(
    learning: str,
    document_text: str,
    max_snippet_length: int = 200,  # Max characters in snippet
    context_sentences: int = 2       # Number of sentences to include
) -> Tuple[Optional[str], float, List[str]]:
```

**Parameters:**
- `max_snippet_length`: Maximum characters in extracted snippet (default: 200)
- `context_sentences`: Number of sentences to include around matched terms (default: 2)

## Advanced Usage

### Export Provenance Data

```python
from src.provenance import export_provenance_to_json

# Export to JSON file
export_provenance_to_json(
    provenance_records,
    filename="research_provenance.json"
)
```

### Import and Analyze

```python
from src.provenance import import_provenance_from_json

# Load previously saved provenance
records = import_provenance_from_json("research_provenance.json")

# Analyze confidence scores
avg_confidence = sum(r.confidence_score for r in records) / len(records)
print(f"Average confidence: {avg_confidence:.2%}")
```

### Custom Formatting

```python
from src.provenance import format_learnings_with_provenance

# Generate HTML output
html_output = format_learnings_with_provenance(
    provenance_records,
    format='html'
)

# Or Markdown
markdown_output = format_learnings_with_provenance(
    provenance_records,
    format='markdown'
)
```

## Troubleshooting

### No Provenance Data Available

If `learnings_with_provenance` is empty:

1. **Check that provenance is enabled:**
   - Ensure `track_provenance=True` in `process_serp_result()`
   
2. **Verify source documents were collected:**
   - Check logs for "Tracked provenance for X learnings"
   - Ensure Firecrawl API is working correctly

3. **Check for errors:**
   - Look for "Warning: Could not track provenance" in logs
   - Review error messages for import or processing issues

### Low Confidence Scores

If confidence scores are consistently low (< 0.3):

1. **Learnings may be too abstract** - The AI generated high-level summaries that don't match exact source text
2. **Source documents may be unrelated** - The scraped content doesn't support the learnings
3. **Algorithm tuning needed** - Adjust `context_sentences` or matching strategy in `provenance.py`

### Missing Supporting Snippets

Some learnings may have `supporting_snippet=None`:

- This occurs when no matching text is found in source documents
- The learning may be an inference or synthesis from multiple sources
- Consider this a signal to review the learning's validity

## Best Practices

1. **Always review provenance** - Click through to source URLs to verify information
2. **Check confidence scores** - Higher scores (>0.5) indicate stronger evidence
3. **Look for missing snippets** - Learnings without snippets may need additional verification
4. **Export provenance data** - Save provenance records for reproducibility and auditing

## API Integration

If you're building on top of deep-research-python:

```python
# Include provenance in your API responses
@app.route('/api/research', methods=['POST'])
async def research_endpoint():
    result = await deep_research(...)
    
    return jsonify({
        'learnings': result.learnings,
        'sources': result.visited_urls,
        'provenance': [
            p.to_dict() for p in result.learnings_with_provenance
        ] if result.learnings_with_provenance else []
    })
```

## Future Enhancements

Potential improvements to provenance tracking:

- **Semantic similarity** using embeddings instead of keyword matching
- **Citation styles** (APA, MLA, Chicago) for academic use
- **Multi-source attribution** when learnings synthesize multiple documents
- **Timestamp tracking** to show when information was retrieved
- **Version tracking** for documents that change over time

## Contributing

To improve provenance tracking, see `src/provenance.py` and submit pull requests for:
- Better snippet extraction algorithms
- Alternative similarity scoring methods
- Additional output formats
- Performance optimizations

---

For questions or issues, please open a GitHub issue or refer to the main [README.md](README.md).
