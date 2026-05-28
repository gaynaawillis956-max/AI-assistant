import httpx
import logging
import json

logger = logging.getLogger("ai-client")


class OpenRouterClient:
    """AI client for OpenRouter API."""
    
    def __init__(self, api_key: str, model: str = "qwen/qwen3"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def generate_reply(self, system_prompt: str, user_message: str, conversation: list = None) -> str:
        """Generate AI response using OpenRouter."""
        if conversation is None:
            conversation = []
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation,
            {"role": "user", "content": user_message}
        ]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.exception("OpenRouter API error: %s", exc)
            raise
