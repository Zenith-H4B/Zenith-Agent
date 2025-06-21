from agents import BaseAgent
from models import Priority, AgentResponse, FeatureSpec
from models.models import FeatureSpecResponse
from typing import Dict, Any
from loguru import logger


class ProductManagerAgent(BaseAgent):
    """Agent responsible for defining feature specs and roadmaps."""
    
    def __init__(self):
        super().__init__("Product Manager Agent")
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process requirement and generate feature specifications."""
        try:
            requirement = input_data.get('requirement')
            org_context = input_data.get('org_context', {})
            
            prompt = f"""
You are a Senior Product Manager. Analyze the following product requirement and create detailed feature specifications.

Organization Context:
- Organization: {org_context.get('name', 'Unknown')}
- Industry: {org_context.get('industry', 'Not specified')}

Product Requirement:
"{requirement.requirement_text}"

Priority: {requirement.priority}
Deadline: {requirement.deadline}
Additional Context: {requirement.additional_context}

Please provide a detailed analysis and create feature specifications including:
1. Feature title and description
2. User stories (at least 3-5)
3. Acceptance criteria (at least 5-7)
4. Priority assessment
5. Effort estimation (in story points or time)
6. Dependencies
7. Your reasoning for this specification

Ensure all fields are properly filled out with meaningful content.
"""
            
            # Generate structured response
            response_data = await self._generate_structured_response(prompt, FeatureSpecResponse)
            
            # Create FeatureSpec object from structured response
            feature_spec = FeatureSpec(
                title=response_data.title,
                description=response_data.description,
                user_stories=response_data.user_stories,
                acceptance_criteria=response_data.acceptance_criteria,
                priority=response_data.priority,
                estimated_effort=response_data.estimated_effort,
                dependencies=response_data.dependencies
            )
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={'feature_spec': feature_spec.dict()},
                reasoning=response_data.reasoning
            )
                
        except Exception as e:
            logger.error(f"Error in ProductManagerAgent: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e)
            )

