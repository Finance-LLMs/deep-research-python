import os
import tiktoken
from pathlib import Path
from openai import OpenAI
from typing import Optional, Union
from .text_splitter import RecursiveCharacterTextSplitter

# Ensure environment variables are loaded
if not os.getenv("OPENAI_KEY") and not os.getenv("FIRECRAWL_KEY"):
    try:
        from dotenv import load_dotenv
        # Load environment variables from .env.local in the project root
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env.local"
        load_dotenv(env_path)
    except ImportError:
        pass


class AIProvider:
    def __init__(self):
        # Initialize OpenAI clients for different providers
        self.openai_client = None
        self.nvidia_client = None
        self.fireworks_client = None
        self.custom_client = None
        
        # Initialize providers based on available API keys
        if os.getenv("OPENAI_KEY"):
            self.openai_client = OpenAI(
                api_key=os.getenv("OPENAI_KEY"),
                base_url=os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
            )
        
        if os.getenv("NVIDIA_API_KEY"):
            self.nvidia_client = OpenAI(
                api_key=os.getenv("NVIDIA_API_KEY"),
                base_url="https://integrate.api.nvidia.com/v1"
            )
        
        if os.getenv("FIREWORKS_KEY"):
            self.fireworks_client = OpenAI(
                api_key=os.getenv("FIREWORKS_KEY"),
                base_url="https://api.fireworks.ai/inference/v1"
            )
        
        if os.getenv("CUSTOM_MODEL") and self.openai_client:
            self.custom_client = self.openai_client

    def get_model(self) -> tuple[OpenAI, str]:
        """Get the best available model and client"""
        # Priority order based on the TypeScript version
        if self.custom_client and os.getenv("CUSTOM_MODEL"):
            return self.custom_client, os.getenv("CUSTOM_MODEL")
        
        # NVIDIA models (start with smaller, more stable models)
        if self.nvidia_client:
            return self.nvidia_client, "meta/llama-3.1-70b-instruct"
        
        # Fireworks DeepSeek R1
        if self.fireworks_client:
            return self.fireworks_client, "accounts/fireworks/models/deepseek-r1"
        
        # OpenAI fallback
        if self.openai_client:
            return self.openai_client, "gpt-4o-mini"
        
        raise ValueError("No model found. Please set at least one API key.")

    def generate_object(self, system_prompt: str, user_prompt: str, schema: dict, timeout: int = 60):
        """Generate structured output using the best available model"""
        client, model_name = self.get_model()
        
        # For OpenAI models, use structured outputs
        if "gpt-" in model_name:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                timeout=timeout
            )
        else:
            # For other models, use tool calling to get structured output
            tools = [{
                "type": "function",
                "function": {
                    "name": "respond_with_structure",
                    "description": "Respond with the requested structured data",
                    "parameters": schema
                }
            }]
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "respond_with_structure"}},
                timeout=timeout
            )
        
        return response

def parse_structured_response(response):
    """Parse structured response from either tool calls or function calls"""
    import json
    
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        
        # Check for tool calls (new format)
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            return json.loads(choice.message.tool_calls[0].function.arguments)
        
        # Check for function call (deprecated format)
        elif hasattr(choice, 'function_call'):
            return json.loads(choice.function_call.arguments)
        
        # Fallback to message content
        else:
            return json.loads(choice.message.content)
    
    raise ValueError("Unable to parse response")


# Initialize global provider
_ai_provider = AIProvider()

def get_model() -> tuple[OpenAI, str]:
    """Get the current model client and name"""
    return _ai_provider.get_model()

def generate_object(system_prompt: str, user_prompt: str, schema: dict, timeout: int = 60):
    """Generate structured output"""
    return _ai_provider.generate_object(system_prompt, user_prompt, schema, timeout)

def parse_response(response):
    """Parse structured response from API"""
    return parse_structured_response(response)


MIN_CHUNK_SIZE = 140

def trim_prompt(prompt: str, context_size: int = None) -> str:
    """Trim prompt to maximum context size"""
    if context_size is None:
        context_size = int(os.getenv("CONTEXT_SIZE", "128000"))
    
    if not prompt:
        return ""
    
    try:
        encoder = tiktoken.get_encoding("o200k_base")
        length = len(encoder.encode(prompt))
        
        if length <= context_size:
            return prompt
        
        overflow_tokens = length - context_size
        # On average it's 3 characters per token, so multiply by 3 to get a rough estimate
        chunk_size = len(prompt) - overflow_tokens * 3
        
        if chunk_size < MIN_CHUNK_SIZE:
            return prompt[:MIN_CHUNK_SIZE]
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=0
        )
        
        chunks = splitter.split_text(prompt)
        trimmed_prompt = chunks[0] if chunks else ""
        
        # Last catch, recursively trim if needed
        if len(trimmed_prompt) == len(prompt):
            return trim_prompt(prompt[:chunk_size], context_size)
        
        # Recursively trim until the prompt is within the context size
        return trim_prompt(trimmed_prompt, context_size)
    
    except Exception as e:
        print(f"Error trimming prompt: {e}")
        # Fallback to simple truncation
        return prompt[:context_size * 3]  # Rough estimate
