from typing import Optional, Dict, Any, Union, AsyncIterator
import aiohttp
import asyncio
import json
import logging
import re
import hashlib
from datetime import datetime

from src.core.config import settings
from .rate_limiter import RateLimiter, RateLimitError
from .cache import ResponseCache

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass

class APIError(LLMError):
    """Exception raised for API errors"""
    pass

class ResponseParsingError(LLMError):
    """Exception raised when response parsing fails"""
    pass

class LLMClient:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.MODEL_NAME
        self.rate_limiter = RateLimiter()
        self.session: Optional[aiohttp.ClientSession] = None
        self.retry_attempts = 3
        self.retry_delay = 1
        self.response_cache = ResponseCache()
        
    def _calculate_cache_key(self, prompt: str) -> str:
        """Calculate a cache key for a prompt"""
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()

    async def _ensure_session(self):
        """Ensure session exists and is active"""
        timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds total timeout
        
        try:
            current_loop = asyncio.get_running_loop()
            
            # Check if we need to create a new session
            if self.session is None or self.session.closed:
                # Create new session
                if self.session is not None and self.session.closed:
                    logger.info("Session exists but is closed - creating new session")
                else:
                    logger.info("No session exists - creating new session")
                
                self.session = aiohttp.ClientSession(timeout=timeout)
                self.session_loop = current_loop
                logger.info("Created new aiohttp session")
            else:
                # Check if session belongs to current event loop
                if hasattr(self, 'session_loop') and self.session_loop is not current_loop:
                    logger.warning("Session belongs to a different event loop - creating new session")
                    old_session = self.session
                    self.session = None
                    # Close in background without awaiting to avoid cross-loop problems
                    asyncio.create_task(self._close_session_safe(old_session))
                    self.session = aiohttp.ClientSession(timeout=timeout)
                    self.session_loop = current_loop
        except RuntimeError as e:
            logger.error(f"RuntimeError in _ensure_session: {e}")
            # This can happen if we're not in an async context
            self.session = None
            self.session_loop = None
            # Create a new session anyway
            try:
                self.session = aiohttp.ClientSession(timeout=timeout)
                logger.info("Created new session after RuntimeError")
            except Exception as session_error:
                logger.error(f"Failed to create session after RuntimeError: {session_error}")
                raise APIError(f"Cannot create API session: {session_error}")
        except Exception as e:
            logger.error(f"Unexpected error in _ensure_session: {e}")
            self.session = None
            self.session_loop = None
            raise APIError(f"Failed to ensure API session: {e}")
                
        return self.session

    async def _close_session_safe(self, session):
        """Safely close a session without expecting it to work"""
        if session and not session.closed:
            try:
                await session.close()
                logger.info("Closed aiohttp session successfully")
            except Exception as e:
                logger.warning(f"Error closing session: {e}")

    async def generate(self, prompt: str, expect_json: bool = False) -> Any:
        """Generate LLM response with high-performance optimizations"""
        try:
            # Ensure we have a valid session
            self.session = await self._ensure_session()
            if not self.session:
                logger.error("Failed to create a valid session")
                if expect_json:
                    return self._get_fallback_json_response("Failed to initialize API session")
                else:
                    return "I'm afraid I cannot provide a response at the moment due to technical difficulties."
            
            # Check cache
            cache_key = self._calculate_cache_key(prompt)
            cached_result = self.response_cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute with retries
            for attempt in range(self.retry_attempts):
                try:
                    # Check rate limit
                    await self.rate_limiter.acquire()
                    
                    # Make API request
                    response = await self._make_api_request(prompt)
                    
                    # Cache the result
                    self.response_cache.set(cache_key, response)
                    
                    # Parse response for JSON if needed
                    if expect_json:
                        try:
                            return json.loads(response)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {str(e)}")
                            return self._get_fallback_json_response(f"Failed to parse JSON response: {str(e)}")
                    return response
                    
                except RateLimitError:
                    raise
                
                except asyncio.TimeoutError as e:
                    logger.warning(f"Timeout error on attempt {attempt+1}: {str(e)}")
                    if attempt == self.retry_attempts - 1:
                        logger.error(f"Final timeout error after {self.retry_attempts} attempts")
                        if expect_json:
                            return self._get_fallback_json_response("Request timed out")
                        else:
                            return "I need a moment to gather my thoughts. The case presents some intriguing elements that require careful consideration."
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    # Create a new session for the next attempt
                    if self.session and not self.session.closed:
                        await self._close_session_safe(self.session)
                    self.session = None
                    self.session = await self._ensure_session()
                    
                except Exception as e:
                    logger.error(f"Error on attempt {attempt+1}: {str(e)}")
                    if attempt == self.retry_attempts - 1:
                        logger.error(f"Final error after {self.retry_attempts} attempts")
                        if expect_json:
                            return self._get_fallback_json_response(f"API error: {str(e)}")
                        else:
                            return "I'm afraid there was an unexpected complication. Let us focus on the facts we've gathered so far."
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    
                    # Try to recreate the session but handle errors
                    if self.session and not self.session.closed:
                        await self._close_session_safe(self.session)
                    self.session = None
                    try:
                        self.session = await self._ensure_session()
                    except Exception as session_error:
                        logger.error(f"Failed to recreate session: {session_error}")
                    
        except Exception as outer_e:
            logger.error(f"Outer exception in generate: {outer_e}")
            import traceback
            logger.error(traceback.format_exc())
            
            if expect_json:
                return self._get_fallback_json_response(f"Unexpected error: {str(outer_e)}")
            else:
                return "I apologize, but I seem to be experiencing some technical difficulties. Let's focus on the evidence at hand."
    
    async def _make_api_request(self, prompt: str) -> str:
        """Make API request to OpenAI using the provided prompt string which is expected to be a JSON list of messages."""
        try:
            # Check for closed session before getting session
            if self.session is not None and self.session.closed:
                logger.warning("Session is closed before making request - reinitializing")
                self.session = None
                
            session = await self._ensure_session()
            if not session:
                raise APIError("Failed to create a valid API session")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Parse the incoming prompt string (expected to be JSON) into a message list
            try:
                messages = json.loads(prompt)
                if not isinstance(messages, list):
                    raise ValueError("Parsed prompt is not a list")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse prompt string as JSON list: {e}. Prompt was: {prompt[:500]}...")
                raise APIError(f"Invalid prompt format: Expected JSON list, received: {type(prompt)}")

            data = {
                "model": self.model_name,
                "messages": messages, # Use the parsed message list directly
                "temperature": settings.TEMPERATURE,
                "max_tokens": settings.MAX_TOKENS,
                "top_p": 0.9
            }
            
            try:
                # Double check session is still valid before making request
                if session.closed:
                    raise APIError("Session closed before making request")
                    
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(f"API returned {response.status}: {error_text}")
                    
                    response_data = await response.json()
                    if 'choices' not in response_data or not response_data['choices']:
                        raise APIError("API response missing choices")
                    
                    return response_data['choices'][0]['message']['content']
            except asyncio.CancelledError:
                # Properly handle cancellation
                logger.warning("API request cancelled")
                raise
            except asyncio.TimeoutError:
                raise APIError("API request timed out after 10 seconds")
            except aiohttp.ClientError as e:
                raise APIError(f"API request failed: {str(e)}")
        except asyncio.CancelledError:
            # Make sure to propagate cancellations
            logger.warning("API request outer context cancelled")
            raise
        except Exception as e:
            raise APIError(f"Error making API request: {str(e)}")
    
    async def _make_api_request_from_string(self, prompt_string: str) -> str:
        """Make API request to OpenAI using a plain prompt string."""
        try:
            session = await self._ensure_session()
            if not session:
                raise APIError("Failed to create a valid API session")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Format the plain string prompt into the basic user message structure
            messages = [{"role": "user", "content": prompt_string}]

            data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": settings.TEMPERATURE, # Use configured settings
                "max_tokens": settings.MAX_TOKENS,   # Use configured settings
                "top_p": 0.9 # Or other default if needed
            }

            try:
                if session.closed:
                    raise APIError("Session closed before making request")

                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10 # Standard timeout for non-streaming
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(f"API returned {response.status}: {error_text}")

                    response_data = await response.json()
                    if 'choices' not in response_data or not response_data['choices']:
                        raise APIError("API response missing choices")

                    return response_data['choices'][0]['message']['content']
            except asyncio.CancelledError:
                logger.warning("API request (from string) cancelled")
                raise
            except asyncio.TimeoutError:
                raise APIError("API request (from string) timed out after 10 seconds")
            except aiohttp.ClientError as e:
                raise APIError(f"API request (from string) failed: {str(e)}")
        except asyncio.CancelledError:
            logger.warning("API request (from string) outer context cancelled")
            raise
        except Exception as e:
            # Ensure the original error type isn't lost if it's already APIError
            if isinstance(e, APIError):
                raise
            raise APIError(f"Error making API request from string: {str(e)}")

    async def generate_response_from_string(self, prompt_string: str) -> str:
        """Public method to generate response from a plain string prompt with retries."""
        # Similar retry logic as the main 'generate' method, but calling
        # _make_api_request_from_string instead.
        # For simplicity here, we'll just call it directly without full retry/cache.
        # In a real scenario, you'd likely want to replicate the retry/timeout handling
        # from the 'generate' method here, calling _make_api_request_from_string.
        try:
             # Check rate limit
            await self.rate_limiter.acquire()
            # NOTE: No caching applied to this specific path for now.
            return await self._make_api_request_from_string(prompt_string)
        except RateLimitError:
            logger.error("Rate limit hit for generate_response_from_string")
            # Provide a fallback or re-raise
            return "Processing is currently unavailable due to high load."
        except APIError as e:
            logger.error(f"APIError in generate_response_from_string: {e}")
            # Provide a fallback or re-raise
            return f"Error during processing: {e}"
        except Exception as e:
            logger.error(f"Unexpected error in generate_response_from_string: {e}")
            return "An unexpected error occurred during processing."

    def _get_fallback_json_response(self, error_message: str) -> Dict[str, Any]:
        """Get a standardized fallback JSON response when errors occur"""
        return {
            "error": error_message,
            "plot_threads": [
                "Interview the household staff about their movements",
                "Examine the crime scene for overlooked evidence",
                "Research the history of the stolen item or victim"
            ],
            "critical_context": "The crime appears connected to historical events or personal vendettas that must be uncovered.",
            "initial_clues": [
                "A distinctive boot print found at the scene suggests someone with a military background",
                "The timing of the incident coincides with the full moon, potentially significant"
            ]
        }
    
    async def close(self):
        """Close the client session and release all resources"""
        try:
            # Store reference to session before nullifying it
            session_to_close = self.session
            
            # Clear self references immediately to prevent duplicate closing
            self.session = None
            self.session_loop = None
            
            # Only try to close the session if it exists and isn't already closed
            if session_to_close and not session_to_close.closed:
                try:
                    # Close the session (this will also close the connector if we're the last reference)
                    await session_to_close.close()
                    logger.info("Session closed successfully")
                except Exception as e:
                    logger.warning(f"Error during session close: {e}")
            
            logger.info("LLMClient successfully closed")
        except Exception as e:
            logger.error(f"Error during LLMClient close: {e}")
            
        # As a last resort, check for any remaining active tasks and wait for them
        try:
            current_task = asyncio.current_task()
            all_tasks = asyncio.all_tasks()
            
            my_pending_tasks = [t for t in all_tasks 
                               if t != current_task and not t.done() 
                               and 'aiohttp' in str(t) and 'llm' in str(t).lower()]
            
            if my_pending_tasks:
                logger.warning(f"Waiting for {len(my_pending_tasks)} pending LLM-related tasks to complete")
                try:
                    # Set a short timeout to avoid blocking indefinitely
                    await asyncio.wait(my_pending_tasks, timeout=1.0)
                except Exception as task_e:
                    logger.warning(f"Error waiting for pending tasks: {task_e}")
        except Exception as e:
            logger.warning(f"Error checking pending tasks: {e}")
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text response only (not JSON)"""
        return await self.generate(prompt, expect_json=False)
    
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """Generate JSON response"""
        return await self.generate(prompt, expect_json=True)
    
    async def stream_generate(self, prompt: str) -> AsyncIterator[str]:
        """Generate LLM response as a stream of chunks"""
        # We use the main session for streaming to avoid creating/destroying connections
        try:
            # Ensure we have a valid session
            self.session = await self._ensure_session()
            if not self.session:
                logger.error("Failed to create a valid session for streaming")
                yield "I'm afraid I cannot provide a response at the moment due to technical difficulties."
                return
                
            # Check rate limit
            await self.rate_limiter.acquire()
            
            # Streaming doesn't use cache as we're sending partial responses
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Parse the incoming prompt string (expected to be JSON) into a message list
            try:
                messages = json.loads(prompt)
                if not isinstance(messages, list):
                    raise ValueError("Parsed prompt is not a list")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse prompt string as JSON list for streaming: {e}. Prompt was: {prompt[:500]}...")
                yield f"Error: Invalid prompt format: Expected JSON list, received: {type(prompt)}"
                return

            data = {
                "model": self.model_name,
                "messages": messages, # Use the parsed message list directly
                "temperature": settings.TEMPERATURE,
                "max_tokens": settings.MAX_TOKENS,
                "top_p": 0.9,
                "stream": True  # Enable streaming
            }
            
            try:
                async with self.session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30  # Longer timeout for streaming
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"API returned {response.status}: {error_text}"
                        logger.error(error_msg)
                        yield f"Error: {error_msg}"
                        return
                    
                    # Process the streaming response
                    buffer = ""
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            # Skip empty lines and "data: [DONE]" messages
                            if line == "data: [DONE]":
                                break
                                
                            if line.startswith("data: "):
                                try:
                                    # Parse the JSON data
                                    data = json.loads(line[6:])  # Remove "data: " prefix
                                    if 'choices' in data and data['choices']:
                                        delta = data['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            # Only yield actual content
                                            buffer += content
                                            yield content
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse streaming data: {line}")
                                    continue
                                    
            except asyncio.CancelledError:
                logger.warning("Streaming API request cancelled")
                # We're not closing the session - just propagate the cancellation
                raise
                
            except asyncio.TimeoutError:
                error_msg = "API request timed out after 30 seconds"
                logger.error(error_msg)
                yield f"Error: {error_msg}"
                
            except Exception as e:
                error_msg = f"Streaming API error: {str(e)}"
                logger.error(error_msg)
                yield f"Error: {error_msg}"
                
        except Exception as outer_e:
            error_msg = f"Outer exception in stream_generate: {str(outer_e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            yield f"Error: {error_msg}"
        
        # Explicitly avoiding any session closing here to prevent premature resource cleanup