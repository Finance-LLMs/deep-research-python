import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST before importing other modules
project_root = Path(__file__).parent.parent
env_path = project_root / ".env.local"
load_dotenv(env_path)

# Now import the modules that depend on environment variables
from .ai.providers import get_model
from .deep_research import deep_research, write_final_answer, write_final_report
from .feedback import generate_feedback

def log(*args):
    """Helper function for consistent logging"""
    print(*args)


async def run():
    """Main function to run the research agent"""
    try:
        client, model_name = get_model()
        print(f"Using model: {model_name}")
    except Exception as e:
        print(f"Error initializing model: {e}")
        return
    
    # Get initial query
    initial_query = input("What would you like to research? ")
    
    # Get breadth and depth parameters
    try:
        breadth_input = input("Enter research breadth (recommended 2-10, default 4): ").strip()
        breadth = int(breadth_input) if breadth_input else 4
    except ValueError:
        breadth = 4
    
    try:
        depth_input = input("Enter research depth (recommended 1-5, default 2): ").strip()
        depth = int(depth_input) if depth_input else 2
    except ValueError:
        depth = 2
    
    mode_input = input("Do you want to generate a long report or a specific answer? (report/answer, default report): ").strip()
    is_report = mode_input != "answer"
    
    combined_query = initial_query
    
    if is_report:
        log("Creating research plan...")
        
        # Generate follow-up questions
        try:
            follow_up_questions = await generate_feedback(initial_query)
            
            if follow_up_questions:
                log("\nTo better understand your research needs, please answer these follow-up questions:")
                
                # Collect answers to follow-up questions
                answers = []
                for question in follow_up_questions:
                    answer = input(f"\n{question}\nYour answer: ")
                    answers.append(answer)
                
                # Combine all information for deep research
                qa_pairs = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(follow_up_questions, answers)])
                combined_query = f"""
Initial Query: {initial_query}
Follow-up Questions and Answers:
{qa_pairs}
"""
        except Exception as e:
            log(f"Error generating follow-up questions: {e}")
            log("Proceeding with initial query only...")
    
    log("\nStarting research...\n")
    
    try:
        # Perform deep research
        result = await deep_research(
            query=combined_query,
            breadth=breadth,
            depth=depth
        )
        
        log(f"\n\nLearnings:\n\n{chr(10).join(result.learnings)}")
        log(f"\n\nVisited URLs ({len(result.visited_urls)}):\n\n{chr(10).join(result.visited_urls)}")
        log("Writing final report...")
        
        if is_report:
            # Generate and save report
            report = await write_final_report(
                prompt=combined_query,
                learnings=result.learnings,
                visited_urls=result.visited_urls
            )
            
            with open("report.md", "w", encoding="utf-8") as f:
                f.write(report)
            
            print(f"\n\nFinal Report:\n\n{report}")
            print("\nReport has been saved to report.md")
        else:
            # Generate and save answer
            answer = await write_final_answer(
                prompt=combined_query,
                learnings=result.learnings
            )
            
            with open("answer.md", "w", encoding="utf-8") as f:
                f.write(answer)
            
            print(f"\n\nFinal Answer:\n\n{answer}")
            print("\nAnswer has been saved to answer.md")
    
    except Exception as e:
        log(f"Error during research: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run())
