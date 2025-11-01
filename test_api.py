"""
API Test Script
Tests if your API keys are working correctly
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent
env_path = project_root / ".env.local"
load_dotenv(env_path)

print("="*60)
print("API CONFIGURATION TEST")
print("="*60)

# Check which keys are present
print("\n1. Checking API Keys:")
print("-" * 60)

firecrawl_key = os.getenv("FIRECRAWL_KEY")
nvidia_key = os.getenv("NVIDIA_API_KEY")
openai_key = os.getenv("OPENAI_KEY")
openrouter_key = os.getenv("OPEN_ROUTER_KEY")
fireworks_key = os.getenv("FIREWORKS_KEY")

if firecrawl_key:
    print(f"✓ FIRECRAWL_KEY: {firecrawl_key[:15]}...")
else:
    print("✗ FIRECRAWL_KEY: Not set")

if nvidia_key:
    print(f"✓ NVIDIA_API_KEY: {nvidia_key[:15]}...")
else:
    print("✗ NVIDIA_API_KEY: Not set")

if openai_key and openai_key != "YOUR_KEY":
    print(f"✓ OPENAI_KEY: {openai_key[:15]}...")
else:
    print("✗ OPENAI_KEY: Not set or placeholder")

if openrouter_key and openrouter_key != "YOUR_KEY":
    print(f"✓ OPEN_ROUTER_KEY: {openrouter_key[:15]}...")
else:
    print("✗ OPEN_ROUTER_KEY: Not set or placeholder")

if fireworks_key:
    print(f"✓ FIREWORKS_KEY: {fireworks_key[:15]}...")
else:
    print("✗ FIREWORKS_KEY: Not set")

# Test AI Provider
print("\n2. Testing AI Provider:")
print("-" * 60)

try:
    from src.ai.providers import get_model
    
    client, model_name = get_model()
    print(f"✓ Model initialized: {model_name}")
    
    # Try a simple completion
    print("\n3. Testing API Call:")
    print("-" * 60)
    print("Sending test request (this may take a few seconds)...")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API test successful' in exactly those words."}
            ],
            max_tokens=50,
            timeout=30  # 30 second timeout
        )
        
        result = response.choices[0].message.content
        print(f"✓ API Response: {result}")
        print("\n✅ ALL TESTS PASSED! Your API is working correctly.")
        
    except Exception as e:
        print(f"\n❌ API Call Failed: {type(e).__name__}")
        print(f"Error: {str(e)}")
        
        if "timeout" in str(e).lower():
            print("\n💡 TIMEOUT ISSUE DETECTED:")
            print("   Possible causes:")
            print("   1. Slow internet connection")
            print("   2. API server is slow/overloaded")
            print("   3. API key might be invalid")
            print("   4. Network firewall blocking requests")
            print("\n   Try:")
            print("   - Check your internet connection")
            print("   - Verify your API key is valid")
            print("   - Try a different API provider (set OPEN_ROUTER_KEY)")
        elif "authentication" in str(e).lower() or "invalid" in str(e).lower():
            print("\n💡 AUTHENTICATION ISSUE:")
            print("   Your API key might be invalid or expired.")
            print("   Please check your key at:")
            if nvidia_key:
                print("   - NVIDIA: https://build.nvidia.com")
            if openrouter_key:
                print("   - OpenRouter: https://openrouter.ai")
        
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()

# Test Firecrawl
print("\n4. Testing Firecrawl:")
print("-" * 60)

try:
    from firecrawl import FirecrawlApp
    
    firecrawl = FirecrawlApp(
        api_key=os.getenv("FIRECRAWL_KEY", ""),
        api_url=os.getenv("FIRECRAWL_BASE_URL")
    )
    
    print("✓ Firecrawl initialized")
    print("  Note: Firecrawl search will be tested during actual research")
    
except Exception as e:
    print(f"❌ Firecrawl initialization failed: {e}")

# Test Retrieval Processor
print("\n5. Testing Retrieval Processor:")
print("-" * 60)

try:
    from src.retrieval_processor import process_search_results
    print("✓ Retrieval processor available")
    
    use_reranking = os.getenv("USE_RERANKING", "true")
    dedup_threshold = os.getenv("DEDUP_THRESHOLD", "0.9")
    min_year = os.getenv("MIN_YEAR", "2020")
    
    print(f"  - USE_RERANKING: {use_reranking}")
    print(f"  - DEDUP_THRESHOLD: {dedup_threshold}")
    print(f"  - MIN_YEAR: {min_year}")
    
except ImportError:
    print("⚠️  Retrieval processor not available (install: pip install sentence-transformers torch)")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60 + "\n")
