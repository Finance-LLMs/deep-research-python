"""
Example: Using Provenance Tracking in Deep Research

This script demonstrates how to use the provenance tracking feature
to verify research findings with source attribution.
"""

import asyncio
from src.deep_research import deep_research
from src.provenance import (
    export_provenance_to_json,
    format_learnings_with_provenance,
    ProvenanceRecord
)


async def example_research_with_provenance():
    """Run a simple research query and display provenance"""
    
    query = "What are the key features of Python 3.12?"
    
    print(f"🔍 Researching: {query}")
    print("=" * 80)
    
    # Run research with default settings (provenance enabled)
    result = await deep_research(
        query=query,
        breadth=3,  # 3 queries per iteration
        depth=1     # 1 iteration (for quick demo)
    )
    
    print(f"\n✅ Research complete!")
    print(f"   - Found {len(result.learnings)} learnings")
    print(f"   - Visited {len(result.visited_urls)} sources")
    
    # Display provenance if available
    if result.learnings_with_provenance:
        print(f"   - Tracked provenance for {len(result.learnings_with_provenance)} learnings")
        print("\n" + "=" * 80)
        print("\n📚 LEARNINGS WITH PROVENANCE:\n")
        
        # Convert dicts to ProvenanceRecord objects
        provenance_records = [
            ProvenanceRecord(**p) for p in result.learnings_with_provenance
        ]
        
        # Display each learning with its provenance
        for i, record in enumerate(provenance_records, 1):
            print(f"\n🔹 Learning #{i}")
            print(f"   {record.learning}")
            
            if record.supporting_snippet:
                print(f"\n   📄 Supporting Evidence:")
                print(f"      \"{record.supporting_snippet}\"")
                print(f"\n   🔗 Source: {record.source_url}")
                print(f"   ✓ Confidence: {record.confidence_score:.1%}")
                
                if record.matched_terms:
                    print(f"   🔑 Key Terms: {', '.join(record.matched_terms[:5])}")
            else:
                print(f"\n   ⚠️  No supporting snippet found")
                print(f"   🔗 Source: {record.source_url}")
            
            print("\n" + "-" * 80)
        
        # Export provenance to JSON
        print("\n💾 Exporting provenance data...")
        export_provenance_to_json(
            provenance_records,
            filename="provenance_example.json"
        )
        print("   ✓ Saved to provenance_example.json")
        
        # Generate formatted output
        print("\n📝 Generating formatted report...")
        markdown_report = format_learnings_with_provenance(
            provenance_records,
            format='markdown'
        )
        
        with open("provenance_report.md", "w", encoding="utf-8") as f:
            f.write(f"# Research Report: {query}\n\n")
            f.write(markdown_report)
        
        print("   ✓ Saved to provenance_report.md")
        
    else:
        print("\n   ⚠️  No provenance data available")
        print("      This may happen if:")
        print("      - Provenance tracking was disabled")
        print("      - No source documents were collected")
        print("      - An error occurred during tracking")
    
    print("\n" + "=" * 80)
    print("\n✨ Example complete!")


async def analyze_provenance_quality():
    """Analyze the quality of provenance data"""
    
    query = "What are the benefits of async programming in Python?"
    
    print(f"🔍 Analyzing provenance quality for: {query}")
    print("=" * 80)
    
    result = await deep_research(query=query, breadth=2, depth=1)
    
    if not result.learnings_with_provenance:
        print("❌ No provenance data to analyze")
        return
    
    provenance_records = [
        ProvenanceRecord(**p) for p in result.learnings_with_provenance
    ]
    
    # Calculate statistics
    total = len(provenance_records)
    with_snippets = sum(1 for r in provenance_records if r.supporting_snippet)
    avg_confidence = sum(r.confidence_score for r in provenance_records) / total
    high_confidence = sum(1 for r in provenance_records if r.confidence_score > 0.5)
    
    print(f"\n📊 PROVENANCE QUALITY ANALYSIS:\n")
    print(f"   Total Learnings: {total}")
    print(f"   With Supporting Snippets: {with_snippets} ({with_snippets/total:.1%})")
    print(f"   Average Confidence: {avg_confidence:.1%}")
    print(f"   High Confidence (>50%): {high_confidence} ({high_confidence/total:.1%})")
    
    # Show confidence distribution
    print(f"\n   Confidence Distribution:")
    for record in provenance_records:
        bar_length = int(record.confidence_score * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"      {bar} {record.confidence_score:.1%}")
    
    # Flag low confidence learnings
    low_confidence = [r for r in provenance_records if r.confidence_score < 0.3]
    if low_confidence:
        print(f"\n   ⚠️  {len(low_confidence)} learning(s) with low confidence:")
        for record in low_confidence:
            print(f"      - {record.learning[:80]}...")
            print(f"        (confidence: {record.confidence_score:.1%})")


async def compare_with_and_without_provenance():
    """Compare research output with and without provenance tracking"""
    
    query = "What is FastAPI and why is it popular?"
    
    print(f"🔍 Comparing research with/without provenance")
    print("=" * 80)
    
    # Note: This is a conceptual example since provenance is now always enabled
    # In practice, you'd need to modify deep_research.py to disable it
    
    print("\n1️⃣  Standard Research (with provenance):")
    result = await deep_research(query=query, breadth=2, depth=1)
    
    print(f"   - Learnings: {len(result.learnings)}")
    print(f"   - Provenance Records: {len(result.learnings_with_provenance or [])}")
    
    if result.learnings_with_provenance:
        verified_count = sum(
            1 for p in result.learnings_with_provenance
            if ProvenanceRecord(**p).confidence_score > 0.5
        )
        print(f"   - Verified Learnings (>50% confidence): {verified_count}")
    
    print("\n💡 Benefits of Provenance:")
    print("   ✓ Can verify each learning against original source")
    print("   ✓ See exact supporting evidence")
    print("   ✓ Build trust through transparency")
    print("   ✓ Identify potential hallucinations")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  PROVENANCE TRACKING EXAMPLES")
    print("=" * 80 + "\n")
    
    # Run examples
    print("📌 Example 1: Basic Provenance Usage\n")
    asyncio.run(example_research_with_provenance())
    
    print("\n\n" + "=" * 80)
    print("📌 Example 2: Provenance Quality Analysis\n")
    asyncio.run(analyze_provenance_quality())
    
    print("\n\n" + "=" * 80)
    print("📌 Example 3: With vs Without Provenance\n")
    asyncio.run(compare_with_and_without_provenance())
    
    print("\n\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80 + "\n")
