from typing import Dict, List, Optional, Any
import os
from rich.console import Console
import logging
import json
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from CONFIG import SBERT_MODEL_NAME, DEFAULT_MODEL, SBERT_MODEL_NAME


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


class EmbeddingProvider:
    """Abstract base class for embedding providers"""
    
    def __init__(self):
        self.model = self._load_model()
        
    def _load_model(self):
        """Load the embedding model - to be implemented by subclasses"""
        raise NotImplementedError
        
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text"""
        raise NotImplementedError
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts"""
        raise NotImplementedError
    

class LLMProvider:
    """Abstract base class for LLM providers"""
    
    def __init__(self):
        self.client = self._setup_client()
        
    def _setup_client(self):
        """Set up the LLM client - to be implemented by subclasses"""
        raise NotImplementedError
        
    def generate_response(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          tools: Optional[List[Dict[str, Any]]] = None, 
                          temperature: float = 0.0) -> Dict[str, Any]:
        """Generate a response from the LLM"""
        raise NotImplementedError
    

class SentenceTransformerEmbedding(EmbeddingProvider):
    """Sentence Transformer embedding implementation"""
    
    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(SBERT_MODEL_NAME)
        except ImportError:
            logger.error("sentence-transformers package not installed. Run 'pip install sentence-transformers'.")
            raise
            
    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()


class GroqLLMProvider(LLMProvider):
    """Groq LLM provider implementation"""
    
    def _setup_client(self):
        try:
            from groq import Groq
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            return Groq(api_key=api_key)
        except ImportError:
            logger.error("groq package not installed. Run 'pip install groq'.")
            raise
    
    def generate_response(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          tools: Optional[List[Dict[str, Any]]] = None, 
                          temperature: float = 0.0) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "messages": messages,
            "temperature": temperature,
            "model": DEFAULT_MODEL,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            completion = self.client.chat.completions.create(**kwargs)
            
            response = {
                "content": completion.choices[0].message.content,
                "tool_calls": []
            }
            
            if hasattr(completion.choices[0].message, "tool_calls") and completion.choices[0].message.tool_calls:
                response["tool_calls"] = [
                    {
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    }
                    for tool_call in completion.choices[0].message.tool_calls
                ]
            
            return response
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            raise


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    def _setup_client(self):
        try:
            from openai import OpenAI
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            return OpenAI(api_key=api_key)
        except ImportError:
            logger.error("openai package not installed. Run 'pip install openai'.")
            raise
    
    def generate_response(self, 
                          system_prompt: str, 
                          user_prompt: str, 
                          tools: Optional[List[Dict[str, Any]]] = None, 
                          temperature: float = 0.0) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "messages": messages,
            "temperature": temperature,
            "model": "gpt-3.5-turbo-0125",
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            completion = self.client.chat.completions.create(**kwargs)
            
            response = {
                "content": completion.choices[0].message.content,
                "tool_calls": []
            }
            
            if hasattr(completion.choices[0].message, "tool_calls") and completion.choices[0].message.tool_calls:
                response["tool_calls"] = [
                    {
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    }
                    for tool_call in completion.choices[0].message.tool_calls
                ]
            
            return response
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {e}")
            raise