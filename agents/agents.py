"""Individual agents for the multi-agent system."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger
import google.generativeai as genai
from config import settings
from models.models import (
    AgentResponse, FeatureSpec, SystemArchitecture, Task, TaskAllocation, 
    Priority, ProductRequirement, Employee
)
from datetime import datetime, timedelta
import json


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input data and return agent response."""
        pass
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response using Gemini."""
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response in {self.name}: {str(e)}")
            raise

