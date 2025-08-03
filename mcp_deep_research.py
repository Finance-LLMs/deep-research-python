#!/usr/bin/env python3
"""
MCP Deep Research Tool
Provides web research capabilities through Model Context Protocol
"""

import os
import json
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Load environment variables
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent
    env_path = project_root / ".env.local"
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed")

# Import the deep research functionality
from src.deep_research import deep_research, write_final_answer, write_final_report
from src.feedback import generate_feedback

# Import MCP with proper error handling
try:
    import mcp
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError as e:
    print(f"Error importing MCP: {e}")
    print("Please install MCP with: pip install mcp")
    sys.exit(1)


# Create the MCP server instance
server = Server("deep-research")


@server.call_tool()
async def deep_web_research(_name: str, arguments: dict) -> Sequence[TextContent]:
    """
    Perform deep web research on any topic using iterative search and analysis.
    
    This tool conducts comprehensive research by:
    1. Generating targeted search queries
    2. Scraping and analyzing web content  
    3. Iteratively diving deeper based on findings
    4. Producing detailed reports or specific answers
    """
    
    # Extract arguments with defaults
    query = arguments.get("query", "")
    breadth = arguments.get("breadth", 3)
    depth = arguments.get("depth", 2)
    output_type = arguments.get("output_type", "report")
    generate_followup = arguments.get("generate_followup", True)
    
    # Validate arguments
    if not query:
        return [TextContent(
            type="text",
            text="Error: Query parameter is required for research."
        )]
    
    # Validate numeric parameters
    breadth = max(1, min(10, int(breadth)))
    depth = max(1, min(5, int(depth)))
    
    if output_type not in ["report", "answer"]:
        output_type = "report"
    
    try:
        combined_query = query
        
        # Generate follow-up questions if requested
        if generate_followup and output_type == "report":
            try:
                follow_up_questions = await generate_feedback(query)
                if follow_up_questions:
                    questions_text = "\n".join([f"- {q}" for q in follow_up_questions])
                    combined_query = f"{query}\n\nAdditional research directions:\n{questions_text}"
            except Exception as e:
                # Continue without follow-up questions if there's an error
                pass
        
        # Perform deep research
        result = await deep_research(
            query=combined_query,
            breadth=breadth,
            depth=depth
        )
        
        # Generate appropriate output
        if output_type == "answer":
            # Generate concise answer
            answer = await write_final_answer(
                prompt=query,
                learnings=result.learnings
            )
            
            response_text = f"**Research Answer:**\n\n{answer}\n\n"
            
            # Add key findings
            if result.learnings:
                response_text += "**Key Findings:**\n"
                for i, learning in enumerate(result.learnings[:5], 1):
                    response_text += f"{i}. {learning}\n"
                response_text += "\n"
            
            # Add sources
            if result.visited_urls:
                response_text += f"**Sources:** {len(result.visited_urls)} URLs researched\n"
                for url in result.visited_urls[:5]:
                    response_text += f"- {url}\n"
                if len(result.visited_urls) > 5:
                    response_text += f"... and {len(result.visited_urls) - 5} more sources\n"
        
        else:
            # Generate detailed report
            report = await write_final_report(
                prompt=query,
                learnings=result.learnings,
                visited_urls=result.visited_urls
            )
            
            response_text = f"**Deep Research Report**\n\n{report}\n\n"
            response_text += f"**Research Statistics:**\n"
            response_text += f"- Breadth: {breadth} queries per iteration\n"
            response_text += f"- Depth: {depth} research iterations\n" 
            response_text += f"- Total findings: {len(result.learnings)}\n"
            response_text += f"- Sources analyzed: {len(result.visited_urls)}\n"
        
        return [TextContent(
            type="text",
            text=response_text
        )]
        
    except Exception as e:
        error_msg = f"Error during research: {str(e)}"
        return [TextContent(
            type="text", 
            text=error_msg
        )]


@server.call_tool()
async def generate_research_questions(_name: str, arguments: dict) -> Sequence[TextContent]:
    """
    Generate clarifying follow-up questions for a research topic.
    
    This tool helps refine research direction by generating relevant
    follow-up questions that can help narrow down or expand the research scope.
    """
    
    query = arguments.get("query", "")
    num_questions = arguments.get("num_questions", 3)
    
    if not query:
        return [TextContent(
            type="text",
            text="Error: Query parameter is required."
        )]
    
    # Validate num_questions
    num_questions = max(1, min(10, int(num_questions)))
    
    try:
        questions = await generate_feedback(query, num_questions)
        
        if questions:
            response_text = f"**Follow-up Research Questions for:** {query}\n\n"
            for i, question in enumerate(questions, 1):
                response_text += f"{i}. {question}\n"
            
            response_text += f"\n*These questions can help refine your research direction and ensure comprehensive coverage of the topic.*"
        else:
            response_text = f"The research query '{query}' appears to be sufficiently clear and specific. No additional clarifying questions are needed."
        
        return [TextContent(
            type="text",
            text=response_text
        )]
        
    except Exception as e:
        error_msg = f"Error generating follow-up questions: {str(e)}"
        return [TextContent(
            type="text",
            text=error_msg
        )]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="deep_web_research",
            description="Perform comprehensive web research on any topic using iterative search and analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The research question or topic to investigate"
                    },
                    "breadth": {
                        "type": "integer",
                        "description": "Number of parallel search queries per iteration (1-10, default: 3)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 3
                    },
                    "depth": {
                        "type": "integer", 
                        "description": "Number of research iterations to perform (1-5, default: 2)",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 2
                    },
                    "output_type": {
                        "type": "string",
                        "description": "Type of output - 'report' for detailed analysis or 'answer' for concise response",
                        "enum": ["report", "answer"],
                        "default": "report"
                    },
                    "generate_followup": {
                        "type": "boolean",
                        "description": "Whether to generate clarifying follow-up questions (default: True)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="generate_research_questions", 
            description="Generate clarifying follow-up questions for a research topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The initial research question or topic"
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions to generate (1-10, default: 3)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        )
    ]


async def main():
    """Main entry point for the MCP server"""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"Error starting MCP server: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
