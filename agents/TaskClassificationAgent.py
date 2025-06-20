"""Task Classification Agent that uses AI to determine task complexity."""
from typing import Dict, Any, Optional
from loguru import logger
from .agents import BaseAgent
from models.models import ProductRequirement, AgentResponse
import json
import re


class TaskClassificationAgent(BaseAgent):
    """Agent responsible for classifying task complexity using AI reasoning."""
    
    def __init__(self):
        super().__init__("TaskClassificationAgent")
        logger.info("TaskClassificationAgent initialized")
    
    async def classify_task_complexity(self, requirement: ProductRequirement, org_context: Optional[Dict] = None) -> AgentResponse:
        """
        Classify task complexity based on requirement analysis.
        
        Args:
            requirement: The product requirement to classify
            org_context: Optional organization context for better classification
            
        Returns:
            AgentResponse with classification result
        """
        try:
            logger.info(f"Classifying task complexity for requirement: {requirement.requirement_text[:100]}...")
            
            # Build context for classification
            org_info = ""
            if org_context:
                org_info = f"""
Organization Context:
- Name: {org_context.get('name', 'Unknown')}
- Industry: {org_context.get('industry', 'Unknown')}
- Team Size: {org_context.get('team_size', 'Unknown')}
- Tech Stack: {', '.join(org_context.get('tech_stack', []))}
"""
            
            classification_prompt = f"""You are a technical project manager expert at classifying software development tasks.

Your job is to analyze the given requirement and classify it as either "simple" or "complex" based on technical complexity, scope, and implementation effort.

{org_info}

Requirement Details:
- Title/Text: {requirement.requirement_text}
- Priority: {requirement.priority}
- Additional Context: {requirement.additional_context or 'None provided'}

Classification Criteria:

SIMPLE tasks typically involve:
- Bug fixes and hotfixes
- UI/UX text updates, color changes, copy modifications
- Configuration changes
- Single-file modifications
- Database record updates
- Simple CRUD operations
- Minor styling adjustments
- Documentation updates
- Environment variable changes
- Simple feature toggles
- Tasks that can be completed by one person in 1-8 hours

COMPLEX tasks typically involve:
- New feature development
- System architecture changes
- Database schema modifications
- API integrations
- Security implementations (authentication, authorization)
- Performance optimizations
- Multi-service/microservice changes
- Third-party integrations
- Machine learning implementations
- Large refactoring efforts
- Tasks requiring multiple team members
- Tasks estimated to take more than 8 hours
- Tasks requiring cross-team coordination

Additional Considerations:
- High priority doesn't automatically make a task complex
- Consider the technical skills required
- Evaluate dependencies on other systems
- Assess testing complexity
- Consider deployment complexity

Analyze the requirement and provide your classification with detailed reasoning.

Respond in this exact JSON format:
{{
    "classification": "simple" or "complex",
    "confidence": 0.0 to 1.0,
    "reasoning": "Detailed explanation of why this task is classified as simple or complex",
    "estimated_hours": estimated hours to complete,
    "risk_factors": ["list", "of", "potential", "risks"],
    "required_skills": ["list", "of", "technical", "skills", "needed"],
    "dependencies": ["list", "of", "dependencies", "if", "any"]
}}"""

            # Get classification from Gemini model
            response_text = await self._generate_response(classification_prompt)
            
            # Parse the response
            try:
                # Extract JSON from response
                response_text = response_text.strip()
                
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    classification_data = json.loads(json_str)
                else:
                    # Fallback parsing if no clear JSON structure
                    raise ValueError("No JSON structure found in response")
                
                # Validate required fields
                if "classification" not in classification_data:
                    raise ValueError("Missing classification field")
                
                classification = classification_data["classification"].lower()
                if classification not in ["simple", "complex"]:
                    raise ValueError(f"Invalid classification: {classification}")
                
                # Extract other fields with defaults
                confidence = classification_data.get("confidence", 0.5)
                reasoning = classification_data.get("reasoning", "Classification provided without detailed reasoning")
                estimated_hours = classification_data.get("estimated_hours", 4)
                risk_factors = classification_data.get("risk_factors", [])
                required_skills = classification_data.get("required_skills", [])
                dependencies = classification_data.get("dependencies", [])
                
                result_data = {
                    "classification": classification,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "estimated_hours": estimated_hours,
                    "risk_factors": risk_factors,
                    "required_skills": required_skills,
                    "dependencies": dependencies,
                    "agent_used": "TaskClassificationAgent"
                }
                
                logger.info(f"Task classified as: {classification} (confidence: {confidence:.2f})")
                logger.info(f"Reasoning: {reasoning[:200]}...")
                
                return AgentResponse(
                    success=True,
                    data=result_data,
                    agent_name="TaskClassificationAgent"
                )
                
            except (json.JSONDecodeError, ValueError, KeyError) as parse_error:
                logger.warning(f"Failed to parse LLM response, using fallback classification: {str(parse_error)}")
                
                # Fallback to keyword-based classification
                fallback_classification = self._fallback_classification(requirement)
                
                return AgentResponse(
                    success=True,
                    data={
                        "classification": fallback_classification,
                        "confidence": 0.3,  # Lower confidence for fallback
                        "reasoning": f"Used fallback classification due to parsing error: {str(parse_error)}",
                        "estimated_hours": 4,
                        "risk_factors": ["Classification uncertainty"],
                        "required_skills": ["General development"],
                        "dependencies": [],
                        "agent_used": "TaskClassificationAgent (fallback)"
                    },
                    agent_name="TaskClassificationAgent"
                )
                
        except Exception as e:
            logger.error(f"Error in task classification: {str(e)}")
            
            # Return fallback classification on error
            fallback_classification = self._fallback_classification(requirement)
            
            return AgentResponse(
                success=False,
                error=f"Classification error: {str(e)}",
                data={
                    "classification": fallback_classification,
                    "confidence": 0.2,
                    "reasoning": f"Error occurred during classification, used fallback: {str(e)}",
                    "estimated_hours": 4,
                    "risk_factors": ["Classification error"],
                    "required_skills": ["General development"],
                    "dependencies": [],
                    "agent_used": "TaskClassificationAgent (error fallback)"
                },
                agent_name="TaskClassificationAgent"
            )
    
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process method for compatibility with other agents.
        
        Args:
            input_data: Dictionary containing 'requirement' and optional 'org_context'
            
        Returns:
            AgentResponse with classification result
        """
        requirement = input_data.get("requirement")
        org_context = input_data.get("org_context")
        
        if not requirement:
            return AgentResponse(
                success=False,
                error="No requirement provided for classification",
                agent_name="TaskClassificationAgent"
            )
        
        return await self.classify_task_complexity(requirement, org_context)
