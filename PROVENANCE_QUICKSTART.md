# Provenance Tracking - Quick Reference

## TL;DR

Every research learning now includes:
- 📄 **Source URL** - Where it came from
- 💬 **Supporting Snippet** - Exact quote from source
- ✅ **Confidence Score** - How well it matches (0-100%)

## Quick Start

```python
from src.deep_research import deep_research

# Run research (provenance enabled by default)
result = await deep_research("Your query", breadth=4, depth=2)

# Access provenance
for p in result.learnings_with_provenance:
    print(f"Learning: {p['learning']}")
    print(f"Source: {p['source_url']}")
    print(f"Evidence: {p['supporting_snippet']}")
    print(f"Confidence: {p['confidence_score']:.0%}")
```

## Dashboard Usage

1. **Start dashboard:** `python run_dashboard.py`
2. **Run research** - Enter query and parameters
3. **View learnings tab** - Each learning shows:
   - Main text
   - Supporting evidence (quoted)
   - "View Source" link
   - Confidence badge

## CLI Usage

```bash
python -m src.run

# Enter your query
# Report will include provenance section at the end
# Check report.md for full details
```

## Key Functions

```python
# Track provenance for learnings
from src.provenance import track_learning_provenance

records = track_learning_provenance(
    learnings=["learning 1", "learning 2"],
    source_documents=[
        {"url": "https://...", "markdown": "content"},
        ...
    ]
)

# Export to JSON
from src.provenance import export_provenance_to_json
export_provenance_to_json(records, "output.json")

# Format for display
from src.provenance import format_learnings_with_provenance
markdown = format_learnings_with_provenance(records, format='markdown')
```

## Understanding Confidence Scores

| Score | Meaning | Action |
|-------|---------|--------|
| **>80%** | 🟢 Strong match | Trust the learning |
| **50-80%** | 🟡 Good match | Verify if important |
| **<50%** | 🔴 Weak match | Manual verification needed |

## Troubleshooting

**No provenance showing?**
- Check logs for "Tracked provenance for X learnings"
- Ensure Firecrawl is working (check source URLs)
- Verify `track_provenance=True` in code

**Low confidence scores?**
- Learning may be abstract/high-level
- Source documents may be unrelated
- AI may have synthesized multiple sources

**Missing snippets?**
- No matching text found in sources
- Learning may be an inference
- Consider manual verification

## Example Output

### Dashboard
```
Learning #1
Deep Research performs iterative web searches and content analysis.

[Expandable section]
Source: "Deep Research uses an iterative approach to search..."
📄 View Source
✓ Confidence: 85%
```

### Report (Markdown)
```markdown
## Research Findings with Provenance

### Learning #1
**Finding:** Deep Research performs iterative web searches

**Source:** "Deep Research uses an iterative approach to search..."
**From:** https://example.com/article
**Confidence:** 85%
```

## Configuration

Provenance is **enabled by default**. No setup needed!

To disable (not recommended):
```python
# In deep_research.py, modify process_serp_result call
processed = await process_serp_result(
    query, result,
    track_provenance=False  # Disable
)
```

## Files to Check

- 📖 **PROVENANCE_TRACKING.md** - Full documentation
- 💻 **example_provenance.py** - Usage examples
- 🔧 **src/provenance.py** - Core implementation
- 📋 **PROVENANCE_IMPLEMENTATION.md** - Technical details

## Common Patterns

### Analyze Quality
```python
records = [ProvenanceRecord(**p) for p in result.learnings_with_provenance]

# Calculate average confidence
avg = sum(r.confidence_score for r in records) / len(records)
print(f"Average confidence: {avg:.0%}")

# Find low-confidence learnings
low = [r for r in records if r.confidence_score < 0.5]
print(f"Review needed: {len(low)} learnings")
```

### Custom Formatting
```python
for record in records:
    if record.supporting_snippet:
        print(f"✓ {record.learning}")
        print(f"  └─ {record.supporting_snippet}")
        print(f"     {record.source_url}")
    else:
        print(f"⚠ {record.learning} (no source found)")
```

### Export and Share
```python
# Export provenance data
export_provenance_to_json(records, "research_sources.json")

# Load later
from src.provenance import import_provenance_from_json
loaded = import_provenance_from_json("research_sources.json")
```

## Quick Tips

✅ **DO:**
- Check confidence scores before trusting learnings
- Click through to verify important facts
- Review learnings with missing snippets
- Export provenance for reproducibility

❌ **DON'T:**
- Ignore low confidence warnings
- Assume all learnings are equally reliable
- Skip verification for critical decisions
- Disable provenance without good reason

## Support

- 📚 Full docs: [PROVENANCE_TRACKING.md](PROVENANCE_TRACKING.md)
- 🐛 Issues: GitHub Issues
- 💡 Examples: `python example_provenance.py`

---

**Remember:** Provenance tracking makes research transparent and verifiable. Always review sources for critical information!
