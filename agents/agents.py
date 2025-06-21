"""Individual agents for the multi-agent system."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from config import settings
from models.models import (
    AgentResponse, FeatureSpec, SystemArchitecture, Task, TaskAllocation, 
    Priority, ProductRequirement, Employee
)
from datetime import datetime, timedelta

T = TypeVar('T', bound=BaseModel)


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input data and return agent response."""
        pass
    
    async def _generate_structured_response(self, prompt: str, response_model: Type[T]) -> T:
        """Generate structured response using LangChain with Pydantic validation."""
        try:
            structured_llm = self.llm.with_structured_output(response_model)
            response = await structured_llm.ainvoke(prompt)
            logger.debug(f"Generated structured response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error generating structured response in {self.name}: {str(e)}")
            raise

