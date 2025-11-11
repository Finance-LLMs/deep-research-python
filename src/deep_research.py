import os
import json
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, TypedDict, Callable
from dataclasses import dataclass

# Load environment variables if not already loaded
if not os.getenv("OPENAI_KEY") and not os.getenv("FIRECRAWL_KEY"):
    try:
        from dotenv import load_dotenv
        # Load environment variables from .env.local in the project root
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".env.local"
        load_dotenv(env_path)
    except ImportError:
        print("Warning: python-dotenv not installed. Environment variables may not be loaded from .env.local")

try:
    from firecrawl import FirecrawlApp
except ImportError:
    # Fallback for different firecrawl package structures
    try:
        from firecrawl.firecrawl import FirecrawlApp
    except ImportError:
        print("Error: firecrawl package not found. Please install with: pip install firecrawl-py")
        raise
from .ai.providers import generate_object, trim_prompt, parse_response
from .prompt import system_prompt

# Try to import retrieval processor (optional enhancement)
try:
    from .retrieval_processor import process_search_results
    RETRIEVAL_PROCESSOR_AVAILABLE = True
except ImportError:
    RETRIEVAL_PROCESSOR_AVAILABLE = False
    print("Note: Retrieval processor not available. Install sentence-transformers for enhanced search ranking.")


def log(*args):
    """Helper function for consistent logging"""
    print(*args)


def _unescape_escapes(text: Optional[str]) -> Optional[str]:
    """Convert common escaped sequences (e.g. "\\n") into actual characters.

    Tries a unicode-escape decode first, falls back to manual replacements.
    This fixes cases where generated text contains literal backslash sequences
    that should be rendered as newlines/tabs when displayed or saved.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        return text
    try:
        # unicode_escape will convert sequences like \n, \t, etc. into actual
        # control characters. Wrap in bytes to avoid accidental changes when
        # the string already contains real unicode escapes.
        return bytes(text, "utf-8").decode("unicode_escape")
    except Exception:
        # Fallback: do manual replacements for the most common escapes
        return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\\\', '\\')


class ResearchProgress(TypedDict):
    current_depth: int
    total_depth: int
    current_breadth: int
    total_breadth: int
    current_query: Optional[str]
    total_queries: int
    completed_queries: int


@dataclass
class ResearchResult:
    learnings: List[str]
    visited_urls: List[str]
    learnings_with_provenance: Optional[List[Dict[str, Any]]] = None


@dataclass
class SerpQuery:
    query: str
    research_goal: str


# Initialize Firecrawl
CONCURRENCY_LIMIT = int(os.getenv("FIRECRAWL_CONCURRENCY", "2"))

firecrawl = FirecrawlApp(
    api_key=os.getenv("FIRECRAWL_KEY", ""),
    api_url=os.getenv("FIRECRAWL_BASE_URL")
)


async def generate_serp_queries(
    query: str, 
    num_queries: int = 3, 
    learnings: Optional[List[str]] = None
) -> List[SerpQuery]:
    """Generate SERP queries for research"""
    
    learnings_text = ""
    if learnings:
        learnings_text = f"\n\nHere are some learnings from previous research, use them to generate more specific queries: {chr(10).join(learnings)}"
    
    prompt = f"Given the following prompt from the user, generate a list of SERP queries to research the topic. Return a maximum of {num_queries} queries, but feel free to return less if the original prompt is clear. Make sure each query is unique and not similar to each other: <prompt>{query}</prompt>{learnings_text}"
    
    schema = {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SERP query"
                        },
                        "research_goal": {
                            "type": "string",
                            "description": "First talk about the goal of the research that this query is meant to accomplish, then go deeper into how to advance the research once the results are found, mention additional research directions. Be as specific as possible, especially for additional research directions."
                        }
                    },
                    "required": ["query", "research_goal"]
                },
                "description": f"List of SERP queries, max of {num_queries}"
            }
        },
        "required": ["queries"]
    }
    
    try:
        response = generate_object(system_prompt(), prompt, schema)
        
        # Parse response
        result = parse_response(response)
        
        queries_data = result.get("queries", [])
        queries = [
            SerpQuery(query=q["query"], research_goal=q["research_goal"])
            for q in queries_data
        ]
        
        log(f"Created {len(queries)} queries", [q.query for q in queries])
        return queries[:num_queries]
    
    except Exception as e:
        log(f"Error generating SERP queries: {e}")
        import traceback
        log(f"Full traceback: {traceback.format_exc()}")
        return []


async def process_serp_result(
    query: str,
    result: Dict[str, Any],
    num_learnings: int = 3,
    num_follow_up_questions: int = 3,
    track_provenance: bool = True
) -> Dict[str, Any]:
    """Process SERP search results with optional provenance tracking"""
    
    # Extract content from search results
    contents = []
    source_documents = []  # For provenance tracking
    if "data" in result:
        log(f"DEBUG: Found {len(result['data'])} items in search results")
        for i, item in enumerate(result["data"]):
            log(f"DEBUG: Item {i}: {list(item.keys())}")
            if "markdown" in item and item["markdown"]:
                content = trim_prompt(item["markdown"], 25000)
                contents.append(content)
                # Store full document for provenance
                source_documents.append(item)
                log(f"DEBUG: Added markdown content from item {i}")
            elif "content" in item and item["content"]:
                content = trim_prompt(item["content"], 25000)
                contents.append(content)
                # Store full document for provenance
                source_documents.append(item)
                log(f"DEBUG: Added content from item {i}")
    else:
        log(f"DEBUG: No 'data' key in result. Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    log(f"Ran {query}, found {len(contents)} contents")
    
    if not contents:
        return {"learnings": [], "follow_up_questions": []}
    
    contents_text = "\n".join([f"<content>\n{content}\n</content>" for content in contents])
    
    prompt = trim_prompt(
        f"Given the following contents from a SERP search for the query <query>{query}</query>, generate a list of learnings from the contents. Return a maximum of {num_learnings} learnings, but feel free to return less if the contents are clear. Make sure each learning is unique and not similar to each other. The learnings should be concise and to the point, as detailed and information dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any exact metrics, numbers, or dates. The learnings will be used to research the topic further.\n\n<contents>{contents_text}</contents>"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "learnings": {
                "type": "array",
                "items": {"type": "string"},
                "description": f"List of learnings, max of {num_learnings}"
            },
            "follow_up_questions": {
                "type": "array", 
                "items": {"type": "string"},
                "description": f"List of follow-up questions to research the topic further, max of {num_follow_up_questions}"
            }
        },
        "required": ["learnings", "follow_up_questions"]
    }
    
    try:
        response = generate_object(system_prompt(), prompt, schema, timeout=60)
        
        result = parse_response(response)
        
        learnings = result.get("learnings", [])
        follow_up_questions = result.get("follow_up_questions", [])
        
        log(f"Created {len(learnings)} learnings", learnings)
        
        # Track provenance if enabled
        learnings_with_provenance = []
        if track_provenance and learnings:
            try:
                from .provenance import track_learning_provenance
                provenance_records = track_learning_provenance(
                    learnings=learnings,
                    source_documents=source_documents
                )
                learnings_with_provenance = [rec.to_dict() for rec in provenance_records]
                log(f"Tracked provenance for {len(learnings_with_provenance)} learnings")
            except Exception as e:
                log(f"Warning: Could not track provenance: {e}")
        
        return {
            "learnings": learnings,
            "follow_up_questions": follow_up_questions,
            "learnings_with_provenance": learnings_with_provenance
        }
    
    except Exception as e:
        log(f"Error processing SERP result: {e}")
        return {"learnings": [], "follow_up_questions": [], "learnings_with_provenance": []}


async def write_final_report(
    prompt: str,
    learnings: List[str],
    visited_urls: List[str],
    learnings_with_provenance: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Write final research report"""
    
    learnings_string = "\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings])
    
    report_prompt = trim_prompt(
        f"Given the following prompt from the user, write a final report on the topic using the learnings from research. Make it as as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:\n\n<prompt>{prompt}</prompt>\n\nHere are all the learnings from previous research:\n\n<learnings>\n{learnings_string}\n</learnings>"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "report_markdown": {
                "type": "string",
                "description": "Final report on the topic in Markdown"
            }
        },
        "required": ["report_markdown"]
    }
    
    try:
        response = generate_object(system_prompt(), report_prompt, schema)
        
        result = parse_response(response)
        
        report = result.get("report_markdown", "")

        # Append sources
        urls_section = f"\n\n## Sources\n\n" + "\n".join([f"- {url}" for url in visited_urls])

        # Append provenance if available
        if learnings_with_provenance:
            try:
                from .provenance import format_learnings_with_provenance, ProvenanceRecord
                # Convert dicts back to ProvenanceRecord objects
                provenance_objs = [ProvenanceRecord(**p) for p in learnings_with_provenance]
                provenance_section = format_learnings_with_provenance(
                    provenance_objs,
                    format='markdown'
                )
                # Ensure any escaped sequences (like "\\n") are converted to real
                # newlines before returning/saving the report so PDFs and UI render
                # line breaks properly.
                provenance_section = _unescape_escapes(provenance_section) or ""
                report = _unescape_escapes(report) or ""
                urls_section = _unescape_escapes(urls_section) or ""

                report = report + "\n\n---\n\n" + provenance_section + urls_section
            except Exception as e:
                log(f"Warning: Could not format provenance: {e}")
                report = report + urls_section
        else:
            report = _unescape_escapes(report + urls_section) or ""

        return report
    
    except Exception as e:
        log(f"Error writing final report: {e}")
        return "Error generating report"


async def write_final_answer(
    prompt: str,
    learnings: List[str]
) -> str:
    """Write final answer based on research"""
    
    learnings_string = "\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings])
    
    answer_prompt = trim_prompt(
        f"Given the following prompt from the user, write a final answer on the topic using the learnings from research. Follow the format specified in the prompt. Do not yap or babble or include any other text than the answer besides the format specified in the prompt. Keep the answer as concise as possible - usually it should be just a few words or maximum a sentence. Try to follow the format specified in the prompt (for example, if the prompt is using Latex, the answer should be in Latex. If the prompt gives multiple answer choices, the answer should be one of the choices).\n\n<prompt>{prompt}</prompt>\n\nHere are all the learnings from research on the topic that you can use to help answer the prompt:\n\n<learnings>\n{learnings_string}\n</learnings>"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "exact_answer": {
                "type": "string",
                "description": "The final answer, make it short and concise, just the answer, no other text"
            }
        },
        "required": ["exact_answer"]
    }
    
    try:
        log("DEBUG: Calling generate_object for final answer...")
        response = generate_object(system_prompt(), answer_prompt, schema)
        
        log(f"DEBUG: Response received: {response}")
        result = parse_response(response)
        log(f"DEBUG: Parsed result: {result}")
        
        answer = result.get("exact_answer", "")
        log(f"DEBUG: Final answer extracted: '{answer}'")
        # Sanitize escaped sequences so the UI and saved files show proper
        # newlines instead of literal "\\n" text.
        answer = _unescape_escapes(answer) or ""
        
        return answer
    
    except Exception as e:
        log(f"Error writing final answer: {e}")
        import traceback
        log(f"Full traceback: {traceback.format_exc()}")
        return "Error generating answer"


async def deep_research(
    query: str,
    breadth: int,
    depth: int,
    learnings: Optional[List[str]] = None,
    visited_urls: Optional[List[str]] = None,
    on_progress: Optional[Callable[[ResearchProgress], None]] = None
) -> ResearchResult:
    """Perform deep research on a query"""
    
    if learnings is None:
        learnings = []
    if visited_urls is None:
        visited_urls = []
    
    progress = ResearchProgress(
        current_depth=depth,
        total_depth=depth,
        current_breadth=breadth,
        total_breadth=breadth,
        current_query=None,
        total_queries=0,
        completed_queries=0
    )
    
    def report_progress(update: Dict[str, Any]):
        progress.update(update)
        if on_progress:
            on_progress(progress)
    
    # Generate SERP queries
    serp_queries = await generate_serp_queries(query, learnings=learnings, num_queries=breadth)
    
    if not serp_queries:
        return ResearchResult(learnings=learnings, visited_urls=visited_urls)
    
    report_progress({
        "total_queries": len(serp_queries),
        "current_query": serp_queries[0].query if serp_queries else None
    })
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    async def process_query(serp_query: SerpQuery):
        async with semaphore:
            try:
                # Perform search using Firecrawl
                result = firecrawl.search(
                    query=serp_query.query,
                    limit=5
                )
                
                log(f"DEBUG: Firecrawl search result for '{serp_query.query}': success={getattr(result, 'success', False)}")
                
                # Extract URLs and scrape content
                new_urls = []
                scraped_contents = []
                
                # Handle SearchResponse object
                data_items = []
                if hasattr(result, 'data') and result.data:
                    data_items = result.data
                elif hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                    data_items = result_dict.get("data", [])
                
                for item in data_items:
                    if "url" in item and item["url"]:
                        url = item["url"]
                        new_urls.append(url)
                        
                        # Scrape the content from the URL
                        try:
                            # Add small delay to avoid rate limits
                            await asyncio.sleep(1)
                            scrape_result = firecrawl.scrape_url(url)
                            if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
                                scraped_contents.append({
                                    "url": url,
                                    "markdown": scrape_result.markdown
                                })
                            elif hasattr(scrape_result, 'model_dump'):
                                scrape_dict = scrape_result.model_dump()
                                if scrape_dict.get("markdown"):
                                    scraped_contents.append({
                                        "url": url,
                                        "markdown": scrape_dict["markdown"]
                                    })
                        except Exception as scrape_error:
                            log(f"Error scraping {url}: {scrape_error}")
                            continue
                
                log(f"Found {len(new_urls)} URLs, successfully scraped {len(scraped_contents)} pages")
                
                # Apply retrieval post-processing if available
                if RETRIEVAL_PROCESSOR_AVAILABLE and scraped_contents:
                    try:
                        # Get settings from environment or use defaults
                        use_reranking = os.getenv("USE_RERANKING", "true").lower() == "true"
                        dedup_threshold = float(os.getenv("DEDUP_THRESHOLD", "0.9"))
                        min_year = int(os.getenv("MIN_YEAR", "2020"))
                        
                        if use_reranking:
                            log(f"Applying retrieval post-processing...")
                            scraped_contents, stats = process_search_results(
                                results=scraped_contents,
                                query=serp_query.query,
                                dedup_threshold=dedup_threshold,
                                min_year=min_year
                            )
                            log(f"Post-processing: {stats.initial_count} → {stats.after_freshness} documents")
                    except Exception as e:
                        log(f"Warning: Retrieval post-processing failed: {e}")
                        # Continue with original results
                
                new_breadth = max(1, breadth // 2)
                new_depth = depth - 1
                
                # Create a result structure that matches what process_serp_result expects
                processed_result = {
                    "data": scraped_contents
                }
                
                # Process the search results
                processed = await process_serp_result(
                    serp_query.query,
                    processed_result,
                    num_follow_up_questions=new_breadth,
                    track_provenance=True
                )
                
                all_learnings = learnings + processed["learnings"]
                all_urls = visited_urls + new_urls
                all_provenance = processed.get("learnings_with_provenance", [])
                
                if new_depth > 0:
                    log(f"Researching deeper, breadth: {new_breadth}, depth: {new_depth}")
                    
                    report_progress({
                        "current_depth": new_depth,
                        "current_breadth": new_breadth,
                        "completed_queries": progress["completed_queries"] + 1,
                        "current_query": serp_query.query
                    })
                    
                    next_query = f"""
Previous research goal: {serp_query.research_goal}
Follow-up research directions: {chr(10).join(processed["follow_up_questions"])}
                    """.strip()
                    
                    deeper_result = await deep_research(
                        next_query,
                        new_breadth,
                        new_depth,
                        all_learnings,
                        all_urls,
                        on_progress
                    )
                    # Merge provenance from deeper research
                    if deeper_result.learnings_with_provenance:
                        all_provenance.extend(deeper_result.learnings_with_provenance)
                    return ResearchResult(
                        learnings=deeper_result.learnings,
                        visited_urls=deeper_result.visited_urls,
                        learnings_with_provenance=all_provenance
                    )
                else:
                    report_progress({
                        "current_depth": 0,
                        "completed_queries": progress["completed_queries"] + 1,
                        "current_query": serp_query.query
                    })
                    return ResearchResult(
                        learnings=all_learnings,
                        visited_urls=all_urls,
                        learnings_with_provenance=all_provenance
                    )
                    
            except Exception as e:
                if "timeout" in str(e).lower():
                    log(f"Timeout error running query: {serp_query.query}: {e}")
                else:
                    log(f"Error running query: {serp_query.query}: {e}")
                return ResearchResult(learnings=[], visited_urls=[], learnings_with_provenance=[])
    
    # Execute all queries concurrently
    tasks = [process_query(query) for query in serp_queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    all_learnings = set(learnings)
    all_urls = set(visited_urls)
    all_provenance = []
    
    for result in results:
        if isinstance(result, ResearchResult):
            all_learnings.update(result.learnings)
            all_urls.update(result.visited_urls)
            if result.learnings_with_provenance:
                all_provenance.extend(result.learnings_with_provenance)
        elif isinstance(result, Exception):
            log(f"Task failed with exception: {result}")
    
    return ResearchResult(
        learnings=list(all_learnings),
        visited_urls=list(all_urls),
        learnings_with_provenance=all_provenance if all_provenance else None
    )
