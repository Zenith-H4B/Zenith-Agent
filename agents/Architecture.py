from agents import BaseAgent
from typing import Dict, Any
import json
from loguru import logger
from models import AgentResponse, SystemArchitecture



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

Return your response in the following JSON format:
{{
    "tech_stack": ["React", "Node.js", "PostgreSQL", "AWS"],
    "system_components": ["Frontend App", "API Gateway", "Auth Service"],
    "architecture_diagram_description": "Detailed description of system architecture",
    "database_schema": "Description of database tables and relationships",
    "api_endpoints": ["/api/users", "/api/products"],
    "security_considerations": ["Authentication", "Authorization", "Data encryption"],
    "reasoning": "Your reasoning for this architecture"
}}
"""
            
            response_text = await self._generate_response(prompt)
            
            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                
                response_data = json.loads(json_str)
                logger.debug(f"Raw LLM response data: {response_data}")
                
                # Transform nested dictionaries to expected flat structure
                def transform_to_list(data):
                    """Transform dict/nested structure to flat list."""
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        # Extract all values if it's a nested dict
                        result = []
                        for key, value in data.items():
                            if isinstance(value, str):
                                result.append(f"{key}: {value}")
                            elif isinstance(value, list):
                                result.extend([f"{key}: {item}" for item in value])
                            else:
                                result.append(f"{key}: {str(value)}")
                        return result
                    else:
                        return [str(data)] if data else []
                
                def transform_to_string(data):
                    """Transform dict/nested structure to string."""
                    if isinstance(data, str):
                        return data
                    elif isinstance(data, dict):
                        # Convert dict to structured string
                        parts = []
                        for key, value in data.items():
                            if isinstance(value, dict):
                                sub_parts = [f"  {k}: {v}" for k, v in value.items()]
                                parts.append(f"{key}:\n" + "\n".join(sub_parts))
                            else:
                                parts.append(f"{key}: {value}")
                        return "\n".join(parts)
                    else:
                        return str(data) if data else ""
                
                # Transform the data to match model expectations
                tech_stack = transform_to_list(response_data.get('tech_stack', []))
                system_components = transform_to_list(response_data.get('system_components', []))
                database_schema = transform_to_string(response_data.get('database_schema'))
                api_endpoints = transform_to_list(response_data.get('api_endpoints', []))
                security_considerations = transform_to_list(response_data.get('security_considerations', []))
                
                # Create SystemArchitecture object
                architecture = SystemArchitecture(
                    tech_stack=tech_stack,
                    system_components=system_components,
                    architecture_diagram_description=response_data.get('architecture_diagram_description', ''),
                    database_schema=database_schema,
                    api_endpoints=api_endpoints,
                    security_considerations=security_considerations
                )
                
                logger.info(f"Successfully created SystemArchitecture with {len(tech_stack)} tech stack items, {len(system_components)} components")
                
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    data={'architecture': architecture.dict()},
                    reasoning=response_data.get('reasoning', 'System architecture designed successfully')
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Raw response text: {response_text[:500]}...")
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    data={},
                    error=f"Failed to parse response: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Failed to create SystemArchitecture: {str(e)}")
                logger.error(f"Response data: {response_data}")
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    data={},
                    error=f"Failed to create architecture object: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error in ArchitectureAgent: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e)
            )

