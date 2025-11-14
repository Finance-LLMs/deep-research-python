// State management
let currentSession = null;
let eventSource = null;
let results = {
    output: '',
    learnings: [],
    sources: [],
    feedback: null,
    learnings_with_provenance: []
};

// DOM elements
const researchForm = document.getElementById('researchForm');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const startBtn = document.getElementById('startBtn');
const newResearchBtn = document.getElementById('newResearchBtn');
const logContent = document.getElementById('logContent');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startBtn.addEventListener('click', startResearch);
    newResearchBtn.addEventListener('click', resetForm);
    
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
});

// Start research
async function startResearch() {
    const query = document.getElementById('query').value.trim();
    const breadth = parseInt(document.getElementById('breadth').value);
    const depth = parseInt(document.getElementById('depth').value);
    const mode = document.getElementById('mode').value;

    if (!query) {
        alert('Please enter a research query');
        return;
    }

    // Validate inputs
    if (breadth < 1 || breadth > 20) {
        alert('Breadth must be between 1 and 20');
        return;
    }

    if (depth < 1 || depth > 10) {
        alert('Depth must be between 1 and 10');
        return;
    }

    // Disable form
    startBtn.disabled = true;
    startBtn.innerHTML = '<span class="spinner"></span> Starting...';

    try {
        // Start research session
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, breadth, depth, mode })
        });

        if (!response.ok) {
            throw new Error('Failed to start research');
        }

        const data = await response.json();
        currentSession = data.session_id;

        // Hide form, show progress
        researchForm.style.display = 'none';
        progressSection.style.display = 'block';
        resultsSection.style.display = 'none';

        // Clear previous logs
        logContent.innerHTML = '';

        // Connect to event stream
        connectEventStream(currentSession);

    } catch (error) {
        alert('Error starting research: ' + error.message);
        startBtn.disabled = false;
        startBtn.textContent = 'Start Research';
    }
}

// Connect to event stream
function connectEventStream(sessionId) {
    eventSource = new EventSource(`/api/stream/${sessionId}`);

    eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };

    eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
        addLog('Connection error occurred', 'error');
    };
}

// Handle incoming messages
function handleMessage(message) {
    switch (message.type) {
        case 'info':
            addLog(message.data, 'info');
            break;

        case 'progress':
            updateProgress(message.data);
            break;

        case 'warning':
            addLog(message.data, 'warning');
            break;

        case 'error':
            addLog('Error: ' + message.data, 'error');
            eventSource?.close();
            showError(message.data);
            break;

        case 'feedback':
            results.feedback = message.data;
            break;

        case 'complete':
            handleComplete(message.data);
            break;

        case 'heartbeat':
            // Ignore heartbeat messages
            break;

        default:
            console.log('Unknown message type:', message.type);
    }
}

// Update progress display
function updateProgress(progress) {
    document.getElementById('currentDepth').textContent = progress.current_depth;
    document.getElementById('totalDepth').textContent = progress.total_depth;
    document.getElementById('currentBreadth').textContent = progress.current_breadth;
    document.getElementById('totalBreadth').textContent = progress.total_breadth;
    document.getElementById('completedQueries').textContent = progress.completed_queries;
    document.getElementById('totalQueries').textContent = progress.total_queries;
    document.getElementById('currentQuery').textContent = progress.current_query || 'Processing...';

    // Update progress bar
    const percentage = progress.total_queries > 0 
        ? (progress.completed_queries / progress.total_queries) * 100 
        : 0;
    document.getElementById('progressFill').style.width = percentage + '%';
}

// Add log entry
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
}

// Handle completion
function handleComplete(data) {
    eventSource?.close();
    
    results.output = data.output;
    results.learnings = data.learnings;
    results.sources = data.visited_urls;
    results.learnings_with_provenance = data.learnings_with_provenance || [];

    addLog('Research complete!', 'success');

    // Show results
    setTimeout(() => {
        progressSection.style.display = 'none';
        resultsSection.style.display = 'block';
        displayResults();
    }, 1000);
}

// Display results
function displayResults() {
    // Output tab
    const outputContent = document.getElementById('outputContent');
    outputContent.innerHTML = marked.parse(results.output);

    // Learnings tab - now with provenance if available
    const learningsList = document.getElementById('learningsList');
    learningsList.innerHTML = '';
    
    if (results.learnings_with_provenance && results.learnings_with_provenance.length > 0) {
        // Display learnings with provenance
        results.learnings_with_provenance.forEach((provenance, index) => {
            const li = document.createElement('li');
            li.className = 'learning-with-provenance';
            
            // Convert \n to <br> tags for proper line breaks
            const learningText = provenance.learning.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
            
            let html = `
                <div class="learning-text">
                    <strong>${index + 1}.</strong> ${learningText}
                </div>
            `;
            
            if (provenance.supporting_snippet) {
                const snippetText = provenance.supporting_snippet.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
                html += `
                    <div class="provenance-info">
                        <div class="provenance-snippet">
                            <strong>📄 Supporting Evidence:</strong><br>
                            <em>"${snippetText}"</em>
                        </div>
                        <div class="provenance-metadata">
                            <a href="${provenance.source_url}" target="_blank" rel="noopener noreferrer" class="source-link">
                                🔗 View Source Document
                            </a>
                            <span class="confidence-score">✓ Confidence: ${(provenance.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                `;
            } else {
                // Show source URL even without snippet
                html += `
                    <div class="provenance-info">
                        <div class="provenance-metadata">
                            <a href="${provenance.source_url}" target="_blank" rel="noopener noreferrer" class="source-link">
                                🔗 View Source Document
                            </a>
                        </div>
                    </div>
                `;
            }
            
            li.innerHTML = html;
            learningsList.appendChild(li);
        });
    } else {
        // Fallback to regular learnings display
        results.learnings.forEach((learning, index) => {
            const li = document.createElement('li');
            // Convert \n to <br> for proper line breaks
            const learningText = learning.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
            li.innerHTML = `<strong>${index + 1}.</strong> ${learningText}`;
            learningsList.appendChild(li);
        });
    }

    // Sources tab
    const sourcesList = document.getElementById('sourcesList');
    sourcesList.innerHTML = '';
    results.sources.forEach((url, index) => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${index + 1}.</strong> <a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
        sourcesList.appendChild(li);
    });

    // Feedback tab
    const feedbackContent = document.getElementById('feedbackContent');
    if (results.feedback && results.feedback.length > 0) {
        feedbackContent.innerHTML = '<h4>Follow-up Questions:</h4><ul></ul>';
        const ul = feedbackContent.querySelector('ul');
        results.feedback.forEach(question => {
            const li = document.createElement('li');
            li.textContent = question;
            ul.appendChild(li);
        });
    } else {
        feedbackContent.innerHTML = '<p class="muted">No feedback available</p>';
    }
}

// Switch tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
}

// Show error
function showError(message) {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    
    const outputContent = document.getElementById('outputContent');
    outputContent.innerHTML = `
        <div style="color: var(--danger-color); padding: 2rem; text-align: center;">
            <h3>❌ Research Failed</h3>
            <p>${message}</p>
        </div>
    `;
}

// Reset form
function resetForm() {
    researchForm.style.display = 'block';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    startBtn.disabled = false;
    startBtn.textContent = 'Start Research';
    
    // Reset results
    results = {
        output: '',
        learnings: [],
        sources: [],
        feedback: null,
        learnings_with_provenance: []
    };
    
    // Clear session
    currentSession = null;
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

// Download markdown
function downloadMarkdown() {
    const mode = document.getElementById('mode').value;
    const query = document.getElementById('query').value;
    const filename = mode === 'report' ? 'research_report.md' : 'research_answer.md';
    
    let content = `# ${query}\n\n`;
    content += results.output;
    
    // Add sources section when downloading
    if (results.sources && results.sources.length > 0) {
        content += '\n\n## Sources\n\n';
        results.sources.forEach((url, index) => {
            content += `${index + 1}. ${url}\n`;
        });
    }
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Simple markdown parser (basic implementation)
const marked = {
    parse: (markdown) => {
        return markdown
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Links
            .replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // Lists
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // Wrap in paragraphs
            .replace(/^(.+)$/gm, '<p>$1</p>')
            // Clean up
            .replace(/<p><h/g, '<h')
            .replace(/<\/h([1-6])><\/p>/g, '</h$1>')
            .replace(/<p><ul>/g, '<ul>')
            .replace(/<\/ul><\/p>/g, '</ul>');
    }
};
