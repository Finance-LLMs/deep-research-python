import asyncio
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from .deep_research import deep_research, write_final_answer, write_final_report

# Load environment variables
load_dotenv(".env.local")

app = Flask(__name__)
CORS(app)

def log(*args):
    """Helper function for consistent logging"""
    print(*args)


@app.route('/api/research', methods=['POST'])
async def research_endpoint():
    """API endpoint to run research"""
    try:
        data = request.get_json()
        query = data.get('query')
        depth = data.get('depth', 3)
        breadth = data.get('breadth', 3)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        log('\nStarting research...\n')
        
        # Perform research
        result = await deep_research(
            query=query,
            breadth=breadth,
            depth=depth
        )
        
        log(f"\n\nLearnings:\n\n{chr(10).join(result.learnings)}")
        log(f"\n\nVisited URLs ({len(result.visited_urls)}):\n\n{chr(10).join(result.visited_urls)}")
        
        # Generate final answer
        answer = await write_final_answer(
            prompt=query,
            learnings=result.learnings
        )
        
        return jsonify({
            'success': True,
            'answer': answer,
            'learnings': result.learnings,
            'visited_urls': result.visited_urls
        })
        
    except Exception as e:
        print(f'Error in research API: {e}')
        return jsonify({
            'error': 'An error occurred during research',
            'message': str(e)
        }), 500


@app.route('/api/generate-report', methods=['POST'])
async def generate_report_endpoint():
    """Generate report API"""
    try:
        data = request.get_json()
        query = data.get('query')
        depth = data.get('depth', 3)
        breadth = data.get('breadth', 3)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        log('\nStarting research...\n')
        
        # Perform research
        result = await deep_research(
            query=query,
            breadth=breadth,
            depth=depth
        )
        
        log(f"\n\nLearnings:\n\n{chr(10).join(result.learnings)}")
        log(f"\n\nVisited URLs ({len(result.visited_urls)}):\n\n{chr(10).join(result.visited_urls)}")
        
        # Generate report
        report = await write_final_report(
            prompt=query,
            learnings=result.learnings,
            visited_urls=result.visited_urls
        )
        
        return jsonify({
            'success': True,
            'report': report,
            'learnings': result.learnings,
            'visited_urls': result.visited_urls
        })
        
    except Exception as e:
        print(f'Error in generate report API: {e}')
        return jsonify({
            'error': 'An error occurred during research',
            'message': str(e)
        }), 500


def create_app():
    """Create and configure the Flask app"""
    return app


if __name__ == '__main__':
    port = int(os.getenv('PORT', 3051))
    print(f'Deep Research API running on port {port}')
    app.run(host='0.0.0.0', port=port, debug=True)
