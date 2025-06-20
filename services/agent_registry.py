"""Agent registry for managing and extending agents."""
from typing import Dict, Type, List
from abc import ABC
from agents.agents import BaseAgent, ProductManagerAgent, ArchitectureAgent, EmployeeAllocatorAgent
from loguru import logger


class AgentRegistry:
    """Registry for managing agents and enabling easy addition of new agents."""
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register the default agents."""
        self.register("product_manager", ProductManagerAgent)
        self.register("architect", ArchitectureAgent)
        self.register("employee_allocator", EmployeeAllocatorAgent)
        logger.info("Registered default agents")
    
    def register(self, name: str, agent_class: Type[BaseAgent]):
        """Register a new agent type."""
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent class must inherit from BaseAgent")
        
        self._agents[name] = agent_class
        logger.info(f"Registered agent: {name}")
    
    def get_agent(self, name: str) -> BaseAgent:
        """Get an agent instance by name."""
        if name not in self._agent_instances:
            if name not in self._agents:
                raise ValueError(f"Agent '{name}' not registered")
            
            self._agent_instances[name] = self._agents[name]()
            logger.info(f"Created instance of agent: {name}")
        
        return self._agent_instances[name]
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def create_custom_workflow(self, agent_sequence: List[str]) -> List[BaseAgent]:
        """Create a custom workflow with specific agent sequence."""
        workflow = []
        for agent_name in agent_sequence:
            agent = self.get_agent(agent_name)
            workflow.append(agent)
        
        logger.info(f"Created custom workflow with {len(workflow)} agents")
        return workflow


# Example of how to add a new agent
class QualityAssuranceAgent(BaseAgent):
    """Agent responsible for quality assurance and testing specifications."""
    
    def __init__(self):
        super().__init__("Quality Assurance Agent")
    
    async def process(self, input_data):
        """Process feature specs and create QA test plans."""
        try:
            feature_spec = input_data.get('feature_spec')
            architecture = input_data.get('architecture')
            
            prompt = f"""
You are a Senior QA Engineer. Based on the feature specification and system architecture, create comprehensive test plans.

Feature Specification:
- Title: {feature_spec.get('title', 'N/A')}
- Description: {feature_spec.get('description', 'N/A')}
- Acceptance Criteria: {feature_spec.get('acceptance_criteria', [])}

System Architecture:
- Tech Stack: {architecture.get('tech_stack', [])}
- API Endpoints: {architecture.get('api_endpoints', [])}

Please create:
1. Unit test specifications
2. Integration test plans
3. End-to-end test scenarios
4. Performance test guidelines
5. Security test considerations

Return your response in JSON format with test specifications.
"""
            
            response_text = await self._generate_response(prompt)
            
            # Parse and return response (similar to other agents)
            return {
                "agent_name": self.name,
                "success": True,
                "data": {"test_plan": response_text},
                "reasoning": "QA test plan generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in QualityAssuranceAgent: {str(e)}")
            return {
                "agent_name": self.name,
                "success": False,
                "data": {},
                "error": str(e)
            }


class SecurityAgent(BaseAgent):
    """Agent responsible for security analysis and recommendations."""
    
    def __init__(self):
        super().__init__("Security Agent")
    
    async def process(self, input_data):
        """Process architecture and create security recommendations."""
        try:
            architecture = input_data.get('architecture')
            feature_spec = input_data.get('feature_spec')
            
            prompt = f"""
You are a Senior Security Engineer. Analyze the system architecture and feature requirements to provide security recommendations.

System Architecture:
- Tech Stack: {architecture.get('tech_stack', [])}
- Components: {architecture.get('system_components', [])}
- API Endpoints: {architecture.get('api_endpoints', [])}

Feature Requirements:
- Title: {feature_spec.get('title', 'N/A')}
- Description: {feature_spec.get('description', 'N/A')}

Please provide:
1. Security threat analysis
2. Authentication and authorization recommendations
3. Data encryption requirements
4. API security best practices
5. Compliance considerations
6. Security testing requirements

Return your response in JSON format with security recommendations.
"""
            
            response_text = await self._generate_response(prompt)
            
            return {
                "agent_name": self.name,
                "success": True,
                "data": {"security_analysis": response_text},
                "reasoning": "Security analysis completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in SecurityAgent: {str(e)}")
            return {
                "agent_name": self.name,
                "success": False,
                "data": {},
                "error": str(e)
            }


# Global agent registry
agent_registry = AgentRegistry()

# Register additional agents
agent_registry.register("qa", QualityAssuranceAgent)
agent_registry.register("security", SecurityAgent)

# Example usage:
# To add the QA and Security agents to your workflow, you can modify the super_agent.py
# to include these agents in the graph or create custom workflows
