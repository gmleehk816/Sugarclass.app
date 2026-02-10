"""
API Configuration Module
========================
Central configuration for all LLM API calls.
Reads from environment variables (set via .env / docker-compose).
"""
import os
import requests
import time
from threading import Lock


class RateLimiter:
    """Simple rate limiter to avoid API rate limits"""

    def __init__(self, max_calls: int = 15, period: int = 60):
        """
        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds (default: 60 seconds = 1 minute)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = Lock()

    def wait_if_needed(self):
        """Wait if we've hit the rate limit"""
        with self.lock:
            now = time.time()
            # Remove calls older than the period
            self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

            if len(self.calls) >= self.max_calls:
                # We've hit the limit, wait until the oldest call is past the period
                oldest_call = self.calls[0]
                wait_time = self.period - (now - oldest_call) + 0.1  # Add small buffer
                if wait_time > 0:
                    print(f"⏳ Rate limit reached, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    # Clean up old calls after waiting
                    now = time.time()
                    self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

            # Record this call
            self.calls.append(now)


# Global rate limiter instance (15 requests per minute by default)
_rate_limiter = RateLimiter(max_calls=15, period=60)

def get_api_config():
    """Get API configuration from environment variables"""
    return {
        'url': os.environ.get('LLM_API_URL', ''),
        'key': os.environ.get('LLM_API_KEY', ''),
        'model': os.environ.get('LLM_MODEL', 'gemini-3-pro-preview'),
        'fallbacks': []
    }

def make_api_call(messages, model=None, max_tokens=4096, temperature=0.7, auto_fallback=False, **kwargs):
    """Make an LLM API call with rate limiting"""
    # Apply rate limiting before making the API call
    _rate_limiter.wait_if_needed()
    api_config = get_api_config()
    apis_to_try = []
    
    if api_config.get('url') and api_config.get('key'):
        apis_to_try.append({
            'url': api_config['url'],
            'key': api_config['key'],
            'model': model or api_config.get('model', 'gemini-3-pro-preview')
        })
    
    if auto_fallback and api_config.get('fallbacks'):
        for fb in api_config['fallbacks']:
            if fb.get('url') and fb.get('key'):
                apis_to_try.append({
                    'url': fb['url'],
                    'key': fb['key'],
                    'model': fb.get('model', 'gemini-2.5-pro')
                })
    
    if not apis_to_try:
        return {
            'content': None,
            'model': None,
            'success': False,
            'error': 'API not configured'
        }
    
    last_error = None
    for api_cfg in apis_to_try:
        url = api_cfg['url'].rstrip('/')
        if not url.endswith('/chat/completions'):
            url = f"{url}/v1/chat/completions" if '/v1' not in url else f"{url}/chat/completions"
        
        headers = {
            'Authorization': f"Bearer {api_cfg['key']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': api_cfg['model'],
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    content = message.get('content') or message.get('reasoning_content') or message.get('reasoning') or ''
                    
                    if not content.strip():
                        last_error = 'Empty response from API'
                        continue
                    
                    return {
                        'content': content,
                        'model': data.get('model', payload['model']),
                        'success': True,
                        'usage': data.get('usage', {}),
                        'api_used': url
                    }
            else:
                last_error = f"Status {response.status_code} - {response.text[:200]}"
                continue
        except Exception as e:
            last_error = str(e)
            continue
    
    return {
        'content': None,
        'model': None,
        'success': False,
        'error': last_error or 'All APIs failed'
    }

API_CONFIG = get_api_config()