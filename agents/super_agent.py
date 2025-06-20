"""Super agent that orchestrates the multi-agent system using LangGraph."""
from typing import Dict, Any, List, Optional
from loguru import logger
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import asyncio
from datetime import datetime
import time
from bson import ObjectId
#from agents import ProductManagerAgent, ArchitectureAgent, EmployeeAllocatorAgent
from agents.ProductManager import ProductManagerAgent
from agents.Architecture import ArchitectureAgent
from agents.EmployeeAllocator import EmployeeAllocatorAgent
from models import ProductRequirement, ProcessingResult, AgentResponse
from database.database import db
from utils.embedding_service import embedding_service
from utils.email_manager import email_manager


class SuperAgent:
    """Super agent that coordinates all other agents using LangGraph."""
    
    def __init__(self):
        self.product_manager = ProductManagerAgent()
        self.architect = ArchitectureAgent()
        self.employee_allocator = EmployeeAllocatorAgent()
        
        # Create the graph
        self.graph = self._create_graph()
        logger.info("SuperAgent initialized with LangGraph workflow")
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow."""
        # Define the workflow state
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("fetch_org_data", self._fetch_org_data)
        workflow.add_node("product_manager", self._run_product_manager)
        workflow.add_node("architect", self._run_architect)
        workflow.add_node("employee_allocator", self._run_employee_allocator)
        workflow.add_node("send_emails", self._send_emails)
        workflow.add_node("save_results", self._save_results)
        
        # Define the flow
        workflow.set_entry_point("fetch_org_data")
        
        workflow.add_edge("fetch_org_data", "product_manager")
        workflow.add_edge("product_manager", "architect")
        workflow.add_edge("architect", "employee_allocator")
        workflow.add_edge("employee_allocator", "send_emails")
        workflow.add_edge("send_emails", "save_results")
        workflow.add_edge("save_results", END)
        
        return workflow.compile()
    
    async def process_requirement(self, requirement: ProductRequirement) -> ProcessingResult:
        """Process a product requirement through the agent workflow."""
        start_time = time.time()
        logger.info(f"Starting requirement processing for org {requirement.org_id}")
        
        # Initialize state
        initial_state = {
            "requirement": requirement,
            "org_data": None,
            "employees": [],
            "feature_spec": None,
            "architecture": None,
            "task_allocations": [],
            "email_results": None,
            "errors": [],
            "success": True
        }
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            processing_time = time.time() - start_time
            
            # Create result
            result = ProcessingResult(
                org_id=requirement.org_id,
                requirement=requirement,
                feature_specs=final_state.get("feature_spec"),
                architecture=final_state.get("architecture"),
                task_allocations=final_state.get("task_allocations", []),
                email_results=final_state.get("email_results"),
                processing_time_seconds=processing_time,
                success=final_state.get("success", True),
                errors=final_state.get("errors", [])
            )
            
            logger.info(f"Requirement processing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in requirement processing: {str(e)}")
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                org_id=requirement.org_id,
                requirement=requirement,
                processing_time_seconds=processing_time,
                success=False,
                errors=[str(e)]
            )
    
    async def _fetch_org_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch organization and employee data."""
        try:
            requirement = state["requirement"]
            logger.info(f"Fetching org data for {requirement.org_id}")
            
            # Get organization
            org = db.organizations.find_one({"_id":  ObjectId(requirement.org_id)})
            if not org:
                raise ValueError(f"Organization {requirement.org_id} not found")
            
            # Get employees
            employees = list(db.users.find({
                "org_id": ObjectId(requirement.org_id),
                "is_on_leave": False
            }))
            
            # Index employee skills in embedding service
            await embedding_service.index_employee_skills(requirement.org_id)
            
            state["org_data"] = org
            state["employees"] = employees
            
            logger.info(f"Fetched data for org {org['name']} with {len(employees)} employees")
            
        except Exception as e:
            logger.error(f"Error fetching org data: {str(e)}")
            state["errors"].append(f"Org data fetch error: {str(e)}")
            state["success"] = False
        
        return state
    
    async def _run_product_manager(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Product Manager Agent."""
        try:
            logger.info("Running Product Manager Agent")
            
            input_data = {
                "requirement": state["requirement"],
                "org_context": state["org_data"]
            }
            
            response = await self.product_manager.process(input_data)
            
            if response.success:
                state["feature_spec"] = response.data.get("feature_spec")
                logger.info("Product Manager Agent completed successfully")
            else:
                logger.error(f"Product Manager Agent failed: {response.error}")
                state["errors"].append(f"Product Manager error: {response.error}")
                state["success"] = False
                
        except Exception as e:
            logger.error(f"Error in Product Manager Agent: {str(e)}")
            state["errors"].append(f"Product Manager error: {str(e)}")
            state["success"] = False
        
        return state
    
    async def _run_architect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Architecture Agent."""
        try:
            logger.info("Running Architecture Agent")
            
            if not state["feature_spec"]:
                logger.warning("No feature spec available, skipping Architecture Agent")
                return state
            
            input_data = {
                "feature_spec": state["feature_spec"],
                "requirement": state["requirement"],
                "org_context": state["org_data"]
            }
            
            response = await self.architect.process(input_data)
            
            if response.success:
                state["architecture"] = response.data.get("architecture")
                logger.info("Architecture Agent completed successfully")
            else:
                logger.error(f"Architecture Agent failed: {response.error}")
                state["errors"].append(f"Architecture error: {response.error}")
                state["success"] = False
                
        except Exception as e:
            logger.error(f"Error in Architecture Agent: {str(e)}")
            state["errors"].append(f"Architecture error: {str(e)}")
            state["success"] = False
        
        return state
    
    async def _run_employee_allocator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Employee Allocator Agent."""
        try:
            logger.info("Running Employee Allocator Agent")
            
            if not state["feature_spec"] or not state["architecture"]:
                logger.warning("Missing feature spec or architecture, skipping Employee Allocator")
                return state
            
            input_data = {
                "feature_spec": state["feature_spec"],
                "architecture": state["architecture"],
                "requirement": state["requirement"],
                "employees": state["employees"]
            }
            
            response = await self.employee_allocator.process(input_data)
            
            if response.success:
                state["task_allocations"] = response.data.get("task_allocations", [])
                logger.info(f"Employee Allocator completed with {len(state['task_allocations'])} allocations")
            else:
                logger.error(f"Employee Allocator failed: {response.error}")
                state["errors"].append(f"Employee Allocator error: {response.error}")
                state["success"] = False
                
        except Exception as e:
            logger.error(f"Error in Employee Allocator Agent: {str(e)}")
            state["errors"].append(f"Employee Allocator error: {str(e)}")
            state["success"] = False
        
        return state
    
    async def _send_emails(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send task allocation emails."""
        try:
            logger.info("Sending task allocation emails")
            
            task_allocations = state.get("task_allocations", [])
            if not task_allocations:
                logger.warning("No task allocations to send emails for")
                state["email_results"] = {"status": "no_allocations"}
                return state
            
            # Prepare email data
            email_allocations = []
            for allocation in task_allocations:
                for task in allocation.get("tasks", []):
                    email_allocations.append({
                        "employee_email": allocation.get("employee_email"),
                        "task_data": {
                            "title": task.get("title"),
                            "description": task.get("description"),
                            "priority": task.get("priority"),
                            "estimated_duration": f"{task.get('estimated_duration_hours', 0)} hours",
                            "due_date": task.get("due_date"),
                            "additional_details": task.get("additional_details", "")
                        }
                    })
            
            # Send emails
            email_results = await email_manager.send_bulk_task_allocation_emails(email_allocations)
            state["email_results"] = email_results
            
            logger.info(f"Email sending completed: {email_results.get('status')}")
            
        except Exception as e:
            logger.error(f"Error sending emails: {str(e)}")
            state["errors"].append(f"Email error: {str(e)}")
            state["email_results"] = {"status": "failed", "error": str(e)}
        
        return state
    
    async def _save_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save processing results to database."""
        try:
            logger.info("Saving processing results")
            
            # Save to processing_results collection
            result_doc = {
                "org_id": state["requirement"].org_id,
                "requirement": state["requirement"].dict(),
                "feature_spec": state.get("feature_spec"),
                "architecture": state.get("architecture"),
                "task_allocations": state.get("task_allocations", []),
                "email_results": state.get("email_results"),
                "success": state.get("success", True),
                "errors": state.get("errors", []),
                "created_at": datetime.now()
            }
            
            result = db.processing_results.insert_one(result_doc)
            logger.info(f"Results saved with ID: {result.inserted_id}")
            
            # Save individual tasks to tasks collection
            for allocation in state.get("task_allocations", []):
                for task in allocation.get("tasks", []):
                    task_doc = task.copy()
                    task_doc["allocation_id"] = str(result.inserted_id)
                    task_doc["created_at"] = datetime.now()
                    db.tasks.insert_one(task_doc)
            
            logger.info("All results saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            state["errors"].append(f"Save error: {str(e)}")
        
        return state


# Global super agent instance
super_agent = SuperAgent()
