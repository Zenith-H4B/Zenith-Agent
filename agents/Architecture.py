from agents import BaseAgent
from typing import Dict, Any
from loguru import logger
from models import AgentResponse, SystemArchitecture
from models.models import SystemArchitectureResponse


class ArchitectureAgent(BaseAgent):
    """Agent responsible for designing system architecture and tech stacks."""
    
    def __init__(self):
        super().__init__("Architecture Agent")
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process feature specs and generate system architecture."""
        try:
            feature_spec = input_data.get('feature_spec')
            requirement = input_data.get('requirement')
            org_context = input_data.get('org_context', {})
            
            prompt = f"""
You are a Senior Software Architect. Based on the following feature specification and requirements, design a comprehensive system architecture.

Organization Context:
- Organization: {org_context.get('name', 'Unknown')}
- Industry: {org_context.get('industry', 'Not specified')}

Feature Specification:
- Title: {feature_spec.get('title', 'N/A')}
- Description: {feature_spec.get('description', 'N/A')}
- User Stories: {feature_spec.get('user_stories', [])}
- Priority: {feature_spec.get('priority', 'medium')}

Original Requirement: "{requirement.requirement_text}"

Please design a system architecture including:
1. Recommended tech stack (frontend, backend, database, infrastructure)
2. System components and their responsibilities
3. Architecture diagram description
4. Database schema recommendations
5. API endpoints design
6. Security considerations
7. Scalability considerations
8. Your reasoning for this architecture

Provide comprehensive and detailed information for each field.
"""
            logger.info("Generating system architecture based on feature spec and requirement...")
            logger.debug(f"Feature Spec: {feature_spec}")
            logger.debug(f"Requirement: {requirement}")
            logger.debug(f"Organization Context: {org_context}")    
            # Generate structured response
            response_data = await self._generate_structured_response(prompt, SystemArchitectureResponse)
            
            # Create SystemArchitecture object
            architecture = SystemArchitecture(
                tech_stack=response_data.tech_stack,
                system_components=response_data.system_components,
                architecture_diagram_description=response_data.architecture_diagram_description,
                database_schema=response_data.database_schema,
                api_endpoints=response_data.api_endpoints,
                security_considerations=response_data.security_considerations
            )
            
            logger.info(f"Successfully created SystemArchitecture with {len(response_data.tech_stack)} tech stack items")
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={'architecture': architecture.dict()},
                reasoning=response_data.reasoning
            )
                
        except Exception as e:
            logger.error(f"Error in ArchitectureAgent: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e)
            )