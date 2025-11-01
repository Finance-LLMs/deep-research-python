"""
Flask web application for Deep Research UI Dashboard
"""
import os
import asyncio
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import json
from queue import Queue
import threading

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / ".env.local"
load_dotenv(env_path)

from .ai.providers import get_model
from .deep_research import deep_research, write_final_answer, write_final_report
from .feedback import generate_feedback

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Store active research sessions
active_sessions = {}


def log_to_queue(session_id, message_type, message):
    """Helper to send messages to the session queue"""
    if session_id in active_sessions:
        active_sessions[session_id]['queue'].put({
            'type': message_type,
            'data': message
        })


async def run_research(session_id, query, breadth, depth, is_report):
    """Run the research in the background"""
    try:
        # Initialize model
        client, model_name = get_model()
        log_to_queue(session_id, 'info', f'Using model: {model_name}')
        
        log_to_queue(session_id, 'info', f'Starting research with breadth={breadth}, depth={depth}')
        
        # Custom progress callback
        def progress_callback(progress):
            log_to_queue(session_id, 'progress', {
                'current_depth': progress['current_depth'],
                'total_depth': progress['total_depth'],
                'current_breadth': progress['current_breadth'],
                'total_breadth': progress['total_breadth'],
                'current_query': progress['current_query'] or 'Processing...',
                'total_queries': progress['total_queries'],
                'completed_queries': progress['completed_queries']
            })
        
        # Run the research
        research_result = await deep_research(
            query=query,
            breadth=breadth,
            depth=depth,
            on_progress=progress_callback
        )
        
        log_to_queue(session_id, 'info', 'Research complete! Generating final output...')
        
        # Generate final output without sources (they'll be shown separately)
        if is_report:
            # Generate report without sources appended
            learnings_string = "\n".join([f"<learning>\n{learning}\n</learning>" for learning in research_result.learnings])
            from .ai.providers import generate_object, parse_response, trim_prompt
            from .prompt import system_prompt
            
            report_prompt = trim_prompt(
                f"Given the following prompt from the user, write a final report on the topic using the learnings from research. Make it as as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:\n\n<prompt>{query}</prompt>\n\nHere are all the learnings from previous research:\n\n<learnings>\n{learnings_string}\n</learnings>"
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
                final_output = result.get("report_markdown", "")
            except Exception as e:
                log_to_queue(session_id, 'error', f'Error generating report: {str(e)}')
                final_output = "Error generating report"
        else:
            final_output = await write_final_answer(query, research_result.learnings)
        
        # Generate feedback
        try:
            feedback = await generate_feedback(query=query)
            log_to_queue(session_id, 'feedback', feedback)
        except Exception as e:
            log_to_queue(session_id, 'warning', f'Could not generate feedback: {str(e)}')
        
        # Send final result (sources separate from output)
        log_to_queue(session_id, 'complete', {
            'output': final_output,
            'learnings': research_result.learnings,
            'visited_urls': research_result.visited_urls
        })
        
    except Exception as e:
        log_to_queue(session_id, 'error', str(e))
    finally:
        # Mark session as complete
        if session_id in active_sessions:
            active_sessions[session_id]['complete'] = True


@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_research():
    """Start a new research session"""
    data = request.json
    
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    breadth = int(data.get('breadth', 4))
    depth = int(data.get('depth', 2))
    mode = data.get('mode', 'report')
    is_report = mode == 'report'
    
    # Create session
    session_id = os.urandom(16).hex()
    active_sessions[session_id] = {
        'queue': Queue(),
        'complete': False
    }
    
    # Start research in background thread
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_research(session_id, query, breadth, depth, is_report))
        loop.close()
    
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
    
    return jsonify({'session_id': session_id})


@app.route('/api/stream/<session_id>')
def stream_progress(session_id):
    """Stream progress updates using Server-Sent Events"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    def generate():
        session = active_sessions[session_id]
        queue = session['queue']
        
        while True:
            # Get message from queue
            try:
                message = queue.get(timeout=1)
                yield f"data: {json.dumps(message)}\n\n"
                
                # If complete message, break after sending
                if message['type'] == 'complete' or message['type'] == 'error':
                    break
                    
            except:
                # Check if session is complete
                if session.get('complete', False):
                    break
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        # Clean up session
        if session_id in active_sessions:
            del active_sessions[session_id]
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


def main():
    """Run the Flask application"""
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n🚀 Deep Research Dashboard starting...")
    print(f"📊 Dashboard URL: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
