"""Task Classification Agent that uses AI to determine task complexity."""
from typing import Dict, Any, Optional
from loguru import logger
from .agents import BaseAgent
from models.models import ProductRequirement, AgentResponse, TaskClassificationResponse


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
Ensure the classification field is exactly "simple" or "complex".
"""

            # Generate structured response
            response_data = await self._generate_structured_response(classification_prompt, TaskClassificationResponse)
            
            # Validate classification
            if response_data.classification not in ["simple", "complex"]:
                logger.warning(f"Invalid classification received: {response_data.classification}, defaulting to 'complex'")
                response_data.classification = "complex"
            
            result_data = {
                "classification": response_data.classification,
                "confidence": response_data.confidence,
                "reasoning": response_data.reasoning,
                "estimated_hours": response_data.estimated_hours,
                "risk_factors": response_data.risk_factors,
                "required_skills": response_data.required_skills,
                "dependencies": response_data.dependencies,
                "agent_used": "TaskClassificationAgent"
            }
            
            logger.info(f"Task classified as: {response_data.classification} (confidence: {response_data.confidence:.2f})")
            logger.info(f"Reasoning: {response_data.reasoning[:200]}...")
            
            return AgentResponse(
                success=True,
                data=result_data,
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
    
    def _fallback_classification(self, requirement: ProductRequirement) -> str:
        """
        Fallback classification based on keywords when LLM parsing fails.
        
        Args:
            requirement: The product requirement to classify
            
        Returns:
            Classification as 'simple' or 'complex'
        """
        requirement_text = requirement.requirement_text.lower()
        
        # Keywords that typically indicate simple tasks
        simple_keywords = [
            'fix', 'bug', 'update', 'change', 'modify', 'text', 'color', 'style',
            'config', 'setting', 'typo', 'copy', 'documentation', 'readme',
            'comment', 'variable', 'constant', 'toggle', 'enable', 'disable'
        ]
        
        # Keywords that typically indicate complex tasks
        complex_keywords = [
            'implement', 'develop', 'create', 'build', 'design', 'architecture',
            'database', 'api', 'integration', 'authentication', 'authorization',
            'security', 'performance', 'optimization', 'refactor', 'migration',
            'machine learning', 'ai', 'algorithm', 'service', 'microservice'
        ]
        
        simple_score = sum(1 for keyword in simple_keywords if keyword in requirement_text)
        complex_score = sum(1 for keyword in complex_keywords if keyword in requirement_text)
        
        # Default to complex if scores are equal or no keywords found
        return 'simple' if simple_score > complex_score else 'complex'
