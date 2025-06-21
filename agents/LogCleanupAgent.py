from agents import BaseAgent
from typing import Dict, Any, List
from loguru import logger
from models import AgentResponse

class LogCleanupAgent(BaseAgent):
    """Agent to extract and format important log steps for streaming."""
    def __init__(self):
        super().__init__("LogCleanup Agent")

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Expects input_data to contain:
            - 'raw_logs': List[str] of log lines
        Returns only important steps (e.g., info, success, error, reasoning).
        """
        raw_logs: List[str] = input_data.get('raw_logs', [])
        important_steps = []
        for line in raw_logs:
            if any(keyword in line.lower() for keyword in [
                'successfully', 'error', 'reasoning', 'step', 'proceed', 'rollback', 'created', 'generating', 'warning']):
                important_steps.append(line)
        logger.info(f"Extracted {len(important_steps)} important log steps for streaming.")
        return AgentResponse(
            agent_name=self.name,
            success=True,
            data={'cleaned_logs': important_steps},
            reasoning="Filtered important log steps for streaming."
        )
