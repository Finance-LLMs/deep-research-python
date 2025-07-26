# Deep Research Python

An AI-powered research assistant that performs iterative, deep research on any topic by combining search engines, web scraping, and large language models.

## Python Version Features

This Python version maintains all the functionality of the TypeScript version:

- **Iterative Research**: Performs deep research by iteratively generating search queries, processing results, and diving deeper based on findings
- **Intelligent Query Generation**: Uses LLMs to generate targeted search queries based on research goals and previous findings
- **Depth & Breadth Control**: Configurable parameters to control how wide (breadth) and deep (depth) the research goes
- **Smart Follow-up**: Generates follow-up questions to better understand research needs
- **Comprehensive Reports**: Produces detailed markdown reports with findings and sources
- **Concurrent Processing**: Handles multiple searches and result processing in parallel for efficiency

## Requirements

- Python 3.8+
- API keys for:
  - Firecrawl API (for web search and content extraction)

## Setup

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env.local` file:

```bash
FIRECRAWL_KEY="your_firecrawl_key"
# If you want to use your self-hosted Firecrawl, add the following below:
# FIRECRAWL_BASE_URL="http://localhost:3002"

# NVIDIA API (build.nvidia.com) - Recommended
NVIDIA_API_KEY="your_nvidia_api_key"

# Alternative: OpenAI API (fallback)
OPENAI_KEY="your_openai_key"

# Alternative: Fireworks AI (for DeepSeek R1)
# FIREWORKS_KEY="your_fireworks_key"
```

## Usage

Run the research assistant:

```bash
python -m src.run
```

Or run the API server:

```bash
python -m src.api
```

### API Endpoints

- `POST /api/research` - Perform research and get a concise answer
- `POST /api/generate-report` - Perform research and generate a detailed report

Both endpoints accept:
```json
{
  "query": "Your research question",
  "breadth": 4,  // optional, default 3
  "depth": 2     // optional, default 3
}
```

## Model Priority

The system automatically selects the best available model in this order:

1. **Custom Model** - if `CUSTOM_MODEL` and `OPENAI_ENDPOINT` are set
2. **NVIDIA Llama 3.1 70B** - if `NVIDIA_API_KEY` is set ⭐ **Recommended**
3. **DeepSeek R1** (Fireworks) - if `FIREWORKS_KEY` is set
4. **GPT-4o-mini** (OpenAI) - Fallback option

## Environment Variables

- `FIRECRAWL_KEY` - Your Firecrawl API key
- `FIRECRAWL_BASE_URL` - Optional custom Firecrawl endpoint
- `FIRECRAWL_CONCURRENCY` - Concurrency limit (default: 2)
- `NVIDIA_API_KEY` - NVIDIA API key for their models
- `OPENAI_KEY` - OpenAI API key
- `FIREWORKS_KEY` - Fireworks AI API key
- `CUSTOM_MODEL` - Custom model name for local/custom endpoints
- `OPENAI_ENDPOINT` - Custom OpenAI-compatible endpoint
- `CONTEXT_SIZE` - Maximum context size (default: 128000)

## Docker

The Python version can also be run with Docker:

1. Build the image:
```bash
docker build -t deep-research-python .
```

2. Run the container:
```bash
docker run -p 3051:3051 --env-file .env.local deep-research-python
```

## License

MIT License - feel free to use and modify as needed.
