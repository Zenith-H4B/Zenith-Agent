"""Wraps metaGPT agent instantiation and management."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from loguru import logger
from config import settings

# Simple metaGPT-style agent implementation
class BaseAgent:
    """Base agent class for metaGPT-style agents."""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        logger.info(f"Initialized {self.role} agent: {self.name}")
    
    async def think(self, message: str) -> str:
        """Agent thinking process."""
        logger.debug(f"{self.role} agent thinking about: {message[:100]}...")
        return f"{self.role} thoughts on: {message}"
    
    async def act(self, thoughts: str) -> str:
        """Agent action based on thoughts."""
        logger.debug(f"{self.role} agent acting on thoughts")
        return f"{self.role} action result"

class MetaGPTClient:
    """Wrapper for metaGPT-style multi-agent management."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        logger.info("MetaGPTClient initialized")
    
    def create_agent(self, name: str, role: str) -> BaseAgent:
        """Create a new agent with specified role."""
        try:
            logger.info(f"Creating agent '{name}' with role '{role}'")
            
            agent = BaseAgent(name, role)
            self.agents[name] = agent
            
            logger.info(f"Agent '{name}' created successfully")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent '{name}': {str(e)}")
            raise
    
    async def run_multi_agent_workflow(self, requirement: str, agent_roles: List[str]) -> Dict[str, Any]:
        """Run a complete multi-agent workflow."""
        try:
            logger.info(f"Starting multi-agent workflow with roles: {agent_roles}")
            logger.info(f"Requirement: {requirement[:100]}...")
            
            workflow_results = {}
            current_input = requirement
            
            # Create agents if they don't exist
            for role in agent_roles:
                agent_name = f"{role.lower()}_agent"
                if agent_name not in self.agents:
                    self.create_agent(agent_name, role)
            
            # Run agents in sequence
            for role in agent_roles:
                agent_name = f"{role.lower()}_agent"
                agent = self.agents[agent_name]
                
                logger.info(f"Running {role} agent")
                
                # Agent thinks and acts
                thoughts = await agent.think(current_input)
                action_result = await agent.act(thoughts)
                
                # Store results
                workflow_results[role] = {
                    "thoughts": thoughts,
                    "action": action_result,
                    "input": current_input
                }
                
                # Use this result as input for next agent
                current_input = action_result
                
                # Add to conversation history
                self.conversation_history.append({
                    "agent": agent_name,
                    "role": role,
                    "input": current_input,
                    "output": action_result,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                logger.debug(f"{role} agent completed successfully")
            
            logger.info("Multi-agent workflow completed successfully")
            return {
                "requirement": requirement,
                "agents_used": agent_roles,
                "results": workflow_results,
                "final_output": current_input,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Multi-agent workflow failed: {str(e)}")
            return {
                "requirement": requirement,
                "agents_used": agent_roles,
                "error": str(e),
                "status": "failed"
            }
    
    async def get_product_spec(self, requirement: str) -> Dict[str, Any]:
        """Get product specification using ProductManager role."""
        try:
            logger.info(f"Generating product spec for: {requirement[:100]}...")
            
            if "product_manager" not in self.agents:
                self.create_agent("product_manager", "ProductManager")
            
            agent = self.agents["product_manager"]
            thoughts = await agent.think(f"Create detailed product specification for: {requirement}")
            spec = await agent.act(thoughts)
            
            logger.info("Product specification generated successfully")
            return {
                "role": "ProductManager",
                "requirement": requirement,
                "specification": spec,
                "thoughts": thoughts,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Product spec generation failed: {str(e)}")
            return {
                "role": "ProductManager",
                "requirement": requirement,
                "error": str(e),
                "status": "failed"
            }
    
    async def get_architecture_design(self, specification: str) -> Dict[str, Any]:
        """Get architecture design using Architect role."""
        try:
            logger.info(f"Generating architecture design for: {specification[:100]}...")
            
            if "architect" not in self.agents:
                self.create_agent("architect", "Architect")
            
            agent = self.agents["architect"]
            thoughts = await agent.think(f"Design system architecture for: {specification}")
            design = await agent.act(thoughts)
            
            logger.info("Architecture design generated successfully")
            return {
                "role": "Architect",
                "specification": specification,
                "architecture": design,
                "thoughts": thoughts,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Architecture design generation failed: {str(e)}")
            return {
                "role": "Architect",
                "specification": specification,
                "error": str(e),
                "status": "failed"
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history between agents."""
        return self.conversation_history

# Global client instance
metagpt_client = MetaGPTClient()
