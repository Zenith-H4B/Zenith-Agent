from agents import BaseAgent
from typing import Dict, Any, List
from loguru import logger
from models import AgentResponse

class FeedbackAgent(BaseAgent):
    """Agent to detect workflow loops and trigger rollback to last successful node."""
    def __init__(self):
        super().__init__("Feedback Agent")

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Expects input_data to contain:
            - 'node_history': List[str] of node names visited in order
            - 'last_successful_state': Dict[str, Any] representing last stable state
        """
        node_history: List[str] = input_data.get('node_history', [])
        last_successful_state = input_data.get('last_successful_state', {})
        current_node = input_data.get('current_node')

        # Detect loop: if the same node appears more than once in the last 5 steps
        if node_history.count(current_node) > 1:
            logger.warning(f"Loop detected at node '{current_node}'. Rolling back to last successful state.")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={'rollback_state': last_successful_state},
                error=f"Loop detected at node '{current_node}'. Rolled back to last successful state."
            )
        else:
            logger.info("No loop detected. Proceeding with workflow.")
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={'proceed': True},
                reasoning="No loop detected."
            )
