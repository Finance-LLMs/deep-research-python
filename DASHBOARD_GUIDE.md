# Deep Research UI Dashboard - Quick Start Guide

## What's New? 🎉

You now have a beautiful web-based UI dashboard for the Deep Research tool! No more command-line interfaces - just point and click.

## Features ✨

### 1. **Interactive Web Interface**
- Clean, modern design with real-time updates
- Easy-to-use form for research parameters
- No terminal commands needed!

### 2. **Live Progress Tracking**
- Visual progress bar showing research completion
- Real-time statistics (depth, breadth, queries completed)
- Activity log showing what's happening
- Current query display

### 3. **Organized Results Display**
Four organized tabs:
- **Output**: Your research report or answer (clean, without sources cluttering the text)
- **Learnings**: All key findings extracted during research
- **Sources**: All URLs visited (separate from the output for better readability)
- **Feedback**: Follow-up questions for further research

### 4. **Export Functionality**
- Download button to save results as Markdown files
- Downloaded files include sources automatically
- Preserves formatting and structure

### 5. **Flexible Parameters**
- Breadth: 1-20 queries per iteration
- Depth: 1-10 research iterations
- Mode: Choose between detailed report or concise answer

## How to Use 🚀

### Quick Start

**Option 1: Using the Batch File (Windows)**
```
Double-click: start_dashboard.bat
```

**Option 2: Using PowerShell**
```powershell
.\start_dashboard.ps1
```

**Option 3: Using Python directly**
```bash
python run_dashboard.py
```

Then open your browser to: **http://localhost:5000**

### Step-by-Step Usage

1. **Enter Your Research Query**
   - Type what you want to research in the text area
   - Be as specific or broad as you like

2. **Adjust Parameters** (optional)
   - **Breadth**: How many search queries per iteration (default: 4)
   - **Depth**: How many iterations to go deeper (default: 2)
   - **Mode**: Report (detailed) or Answer (concise)

3. **Click "Start Research"**
   - Watch the progress in real-time
   - See the activity log for details
   - Monitor which queries are being executed

4. **Review Results**
   - Switch between tabs to explore different aspects
   - Read the clean output without sources mixed in
   - Check learnings and sources separately
   - Review feedback questions for follow-up

5. **Download if Needed**
   - Click "Download as Markdown" to save
   - File includes both output and sources
   - Ready to share or archive

## Configuration

The dashboard uses the same `.env.local` configuration as the CLI:

```bash
FIRECRAWL_KEY="your_firecrawl_key"
OPEN_ROUTER_KEY="your_openrouter_key"
# ... other API keys
```

### Optional Settings

```bash
PORT=5000                    # Change dashboard port
FLASK_DEBUG=false           # Enable debug mode
FIRECRAWL_CONCURRENCY=2     # Concurrent requests
```

## Key Improvements

### Before (CLI)
- Terminal-based interaction
- Hard to track progress
- Sources mixed with output
- No visual indicators
- Difficult for non-technical users

### After (Dashboard)
- Beautiful web interface
- Real-time progress tracking
- Organized tabs for different data
- Visual progress bars and stats
- User-friendly for everyone

## Technical Details

### Architecture
- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript + HTML/CSS
- **Communication**: Server-Sent Events (SSE) for real-time updates
- **Async**: Background processing with threading + asyncio

### Files Added
```
src/
  ├── app.py              # Flask application
  ├── templates/
  │   └── index.html      # Dashboard UI
  └── static/
      ├── style.css       # Styling
      └── script.js       # Frontend logic

run_dashboard.py          # Launcher script
start_dashboard.bat       # Windows batch file
start_dashboard.ps1       # PowerShell script
```

## Troubleshooting

### Dashboard won't start
```bash
# Install/update dependencies
pip install -r requirements.txt
```

### Port already in use
Change the port in `.env.local`:
```bash
PORT=5001
```

Or specify when running:
```bash
PORT=5001 python run_dashboard.py
```

### Can't access from other devices
The dashboard binds to `0.0.0.0`, so you can access it from other devices on your network:
```
http://YOUR_IP:5000
```

## Next Steps

1. **Try it out**: Start with a simple query to test
2. **Experiment**: Adjust breadth and depth to see how it affects results
3. **Share**: The UI makes it easy to share with non-technical team members
4. **Integrate**: The same codebase still supports CLI and API modes

## Tips for Best Results

- **Start small**: Use breadth=2, depth=1 for testing
- **Be specific**: More specific queries yield better results
- **Watch the logs**: Activity log shows what's happening
- **Use feedback**: Follow-up questions help refine research
- **Download results**: Save interesting findings for later

Enjoy your new research dashboard! 🔬✨
