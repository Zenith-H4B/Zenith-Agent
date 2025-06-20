from agents import BaseAgent
from models import  Priority,AgentResponse,FeatureSpec
from typing import Dict, Any
import json
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

Return your response in the following JSON format:
{{
    "title": "Feature title",
    "description": "Detailed description",
    "user_stories": ["As a user...", "As a admin..."],
    "acceptance_criteria": ["Given when then...", "Given when then..."],
    "priority": "high|medium|low|critical",
    "estimated_effort": "X story points / X weeks",
    "dependencies": ["List of dependencies"],
    "reasoning": "Your reasoning for this specification"
}}
"""
            
            response_text = await self._generate_response(prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                
                response_data = json.loads(json_str)
                
                # Create FeatureSpec object
                feature_spec = FeatureSpec(
                    title=response_data.get('title', 'Untitled Feature'),
                    description=response_data.get('description', ''),
                    user_stories=response_data.get('user_stories', []),
                    acceptance_criteria=response_data.get('acceptance_criteria', []),
                    priority=Priority(response_data.get('priority', 'medium')),
                    estimated_effort=response_data.get('estimated_effort', 'TBD'),
                    dependencies=response_data.get('dependencies', [])
                )
                
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    data={'feature_spec': feature_spec.dict()},
                    reasoning=response_data.get('reasoning', 'Feature specification generated successfully')
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                # Fallback to basic parsing
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    data={},
                    error=f"Failed to parse response: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error in ProductManagerAgent: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e)
            )

