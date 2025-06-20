"""Optimized Super agent that orchestrates the multi-agent system using LangGraph."""
from typing import Dict, Any, List, Optional
from loguru import logger
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import asyncio
from datetime import datetime, timedelta
import time
import re
from bson import ObjectId
#from agents import ProductManagerAgent, ArchitectureAgent, EmployeeAllocatorAgent
from agents.ProductManager import ProductManagerAgent
from agents.Architecture import ArchitectureAgent
from agents.EmployeeAllocator import EmployeeAllocatorAgent
from agents.TaskClassificationAgent import TaskClassificationAgent
from models import ProductRequirement, ProcessingResult, AgentResponse, Task, Priority
from database.database import db
from utils.embedding_service import embedding_service
from utils.email_manager import email_manager


class OptimizedSuperAgent:
    """Optimized super agent that coordinates agents with profit maximization and minimal employee usage."""
    
    def __init__(self):
        self.product_manager = ProductManagerAgent()
        self.architect = ArchitectureAgent()
        self.employee_allocator = EmployeeAllocatorAgent()
        self.task_classifier = TaskClassificationAgent()
        
        # Create the graph
        self.graph = self._create_graph()
        logger.info("OptimizedSuperAgent initialized with profit-optimized LangGraph workflow")
    
    def _create_graph(self) -> StateGraph:
        """Create the optimized LangGraph workflow with conditional routing."""
        # Define the workflow state
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("fetch_org_data", self._fetch_org_data)
        workflow.add_node("analyze_complexity", self._analyze_complexity)
        workflow.add_node("simple_task_handler", self._handle_simple_task)
        workflow.add_node("product_manager", self._run_product_manager)
        workflow.add_node("architect", self._run_architect)
        workflow.add_node("optimized_allocator", self._run_optimized_allocator)
        workflow.add_node("send_emails", self._send_emails)
        workflow.add_node("save_results", self._save_results)
        
        # Define the flow with conditional routing
        workflow.set_entry_point("fetch_org_data")
        
        workflow.add_edge("fetch_org_data", "analyze_complexity")
        
        # Conditional routing based on task complexity
        workflow.add_conditional_edges(
            "analyze_complexity",
            self._route_based_on_complexity,
            {
                "simple": "simple_task_handler",
                "complex": "product_manager"
            }
        )
        
        # Simple task flow (direct to email)
        workflow.add_edge("simple_task_handler", "send_emails")
        
        # Complex task flow
        workflow.add_edge("product_manager", "architect")
        workflow.add_edge("architect", "optimized_allocator")
        workflow.add_edge("optimized_allocator", "send_emails")
        
        # Final steps
        workflow.add_edge("send_emails", "save_results")
        workflow.add_edge("save_results", END)
        
        return workflow.compile()
    
    def _calculate_employee_cost_efficiency(self, employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate cost efficiency scores for employees."""
        for emp in employees:
            # Base cost efficiency on role, workload, and skills
            role_cost_multiplier = {
                "developer": 1.0,
                "designer": 1.2,
                "product_manager": 1.5,
                "architect": 2.0,
                "qa_engineer": 0.8,
                "devops_engineer": 1.3,
                "data_scientist": 1.8
            }
            
            role = emp.get('role', 'developer')
            cost_multiplier = role_cost_multiplier.get(role, 1.0)
            
            # Lower cost if employee has lower workload (more available)
            workload_pct = (emp.get('current_workload_hours', 0) / emp.get('capacity_hours_per_week', 40)) * 100
            availability_bonus = max(0, (100 - workload_pct) / 100)
            
            # Skills count as efficiency
            skills_count = len(emp.get('skills', []))
            skills_bonus = min(skills_count / 10, 0.5)  # Cap at 50% bonus
            
            # Calculate final efficiency score (lower is better for cost)
            efficiency_score = cost_multiplier - availability_bonus - skills_bonus
            emp['cost_efficiency_score'] = max(0.1, efficiency_score)
            
        return sorted(employees, key=lambda x: x['cost_efficiency_score'])
    
    async def _analyze_complexity(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task complexity using TaskClassificationAgent."""
        try:
            requirement = state["requirement"]
            org_data = state.get("org_data")
            logger.info("Analyzing task complexity using TaskClassificationAgent")
            
            # Use TaskClassificationAgent for intelligent classification
            input_data = {
                "requirement": requirement,
                "org_context": org_data
            }
            
            classification_response = await self.task_classifier.process(input_data)
            
            if classification_response.success:
                classification_data = classification_response.data
                complexity = classification_data.get("classification", "complex")
                confidence = classification_data.get("confidence", 0.5)
                reasoning = classification_data.get("reasoning", "No reasoning provided")
                estimated_hours = classification_data.get("estimated_hours", 4)
                
                state["task_complexity"] = complexity
                state["classification_details"] = {
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "estimated_hours": estimated_hours,
                    "risk_factors": classification_data.get("risk_factors", []),
                    "required_skills": classification_data.get("required_skills", []),
                    "dependencies": classification_data.get("dependencies", [])
                }
                
                logger.info(f"Task classified as: {complexity} (confidence: {confidence:.2f})")
                logger.info(f"Reasoning: {reasoning[:200]}...")
                
            else:
                logger.error(f"TaskClassificationAgent failed: {classification_response.error}")
                state["errors"].append(f"Task classification error: {classification_response.error}")
                state["task_complexity"] = "complex"  # Default to complex on error
                state["classification_details"] = {
                    "confidence": 0.1,
                    "reasoning": f"Classification failed: {classification_response.error}",
                    "estimated_hours": 4,
                    "risk_factors": ["Classification uncertainty"],
                    "required_skills": ["General development"],
                    "dependencies": []
                }
            
        except Exception as e:
            logger.error(f"Error in complexity analysis: {str(e)}")
            state["errors"].append(f"Complexity analysis error: {str(e)}")
            state["task_complexity"] = "complex"  # Default to complex on error
            state["classification_details"] = {
                "confidence": 0.1,
                "reasoning": f"Error during classification: {str(e)}",
                "estimated_hours": 4,
                "risk_factors": ["Classification error"],
                "required_skills": ["General development"],
                "dependencies": []
            }
        
        return state
    
    def _route_based_on_complexity(self, state: Dict[str, Any]) -> str:
        """Route workflow based on task complexity."""
        complexity = state.get("task_complexity", "complex")
        logger.info(f"Routing workflow based on complexity: {complexity}")
        return complexity
    
    async def _handle_simple_task(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle simple tasks directly without full agent pipeline."""
        try:
            requirement = state["requirement"]
            employees = state["employees"]
            classification_details = state.get("classification_details", {})
            
            logger.info("Handling simple task with optimized flow")
            
            # Find the most cost-effective available employee
            cost_efficient_employees = self._calculate_employee_cost_efficiency(employees)
            
            # Filter employees by required skills if available
            required_skills = classification_details.get("required_skills", [])
            if required_skills:
                logger.info(f"Filtering employees by required skills: {required_skills}")
                skilled_employees = []
                for emp in cost_efficient_employees:
                    emp_skills = [skill.lower() for skill in emp.get('skills', [])]
                    if any(req_skill.lower() in emp_skills for req_skill in required_skills):
                        skilled_employees.append(emp)
                
                # Use skilled employees if available, otherwise fall back to all employees
                if skilled_employees:
                    cost_efficient_employees = skilled_employees
                    logger.info(f"Found {len(skilled_employees)} employees with required skills")
                else:
                    logger.warning("No employees found with required skills, using all available employees")
            
            # Find first available employee with reasonable workload
            selected_employee = None
            for emp in cost_efficient_employees:
                workload_pct = (emp.get('current_workload_hours', 0) / emp.get('capacity_hours_per_week', 40)) * 100
                if workload_pct < 90:  # Less than 90% utilized
                    selected_employee = emp
                    break
            
            if not selected_employee and cost_efficient_employees:
                selected_employee = cost_efficient_employees[0]  # Take the most efficient even if busy
            
            if not selected_employee:
                raise ValueError("No available employees found")
            
            # Use estimated hours from TaskClassificationAgent
            estimated_hours = classification_details.get("estimated_hours", 4)
            confidence = classification_details.get("confidence", 0.5)
            reasoning = classification_details.get("reasoning", "Simple task classification")
            
            # Adjust due date based on priority and estimated hours
            if requirement.priority in ["critical", "high"]:
                due_days = 1 if estimated_hours <= 4 else 2
            else:
                due_days = 3 if estimated_hours <= 8 else 5
                
            due_date = datetime.now() + timedelta(days=due_days)
            
            task = Task(
                title=f"Simple Task: {requirement.requirement_text[:50]}...",
                description=requirement.requirement_text,
                priority=Priority(requirement.priority),
                estimated_duration_hours=estimated_hours,
                due_date=due_date,
                assigned_to=str(selected_employee.get('_id')),
                assigned_to_email=selected_employee.get('email'),
                created_by_agent="OptimizedSuperAgent",
                org_id=requirement.org_id,
                additional_details=f"""Task Classification Details:
- Classification: Simple (confidence: {confidence:.2f})
- AI Reasoning: {reasoning}
- Required Skills: {', '.join(required_skills) if required_skills else 'General development'}
- Risk Factors: {', '.join(classification_details.get('risk_factors', [])) if classification_details.get('risk_factors') else 'Low risk'}
- Dependencies: {', '.join(classification_details.get('dependencies', [])) if classification_details.get('dependencies') else 'No dependencies'}

Additional Context: {requirement.additional_context or 'None provided'}"""
            )
            
            # Create allocation with enhanced reasoning
            allocation = {
                "employee_id": str(selected_employee.get('_id')),
                "employee_email": selected_employee.get('email'),
                "employee_name": selected_employee.get('name'),
                "tasks": [task.dict()],
                "total_estimated_hours": task.estimated_duration_hours,
                "allocation_reasoning": f"""AI-Optimized Simple Task Allocation:
- Employee: {selected_employee.get('name')} ({selected_employee.get('role', 'unknown')})
- Cost Efficiency Score: {selected_employee.get('cost_efficiency_score', 1.0):.2f}
- Skills Match: {'Yes' if required_skills else 'General assignment'}
- Estimated Hours: {estimated_hours}h (AI predicted)
- Classification Confidence: {confidence:.2f}
- Reasoning: {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}"""
            }
            
            state["task_allocations"] = [allocation]
            state["feature_spec"] = {
                "title": "Simple Task",
                "description": requirement.requirement_text,
                "priority": requirement.priority,
                "estimated_effort": f"{task.estimated_duration_hours} hours",
                "classification_details": classification_details
            }
            
            logger.info(f"Simple task assigned to {selected_employee.get('name')} with {task.estimated_duration_hours}h estimate (AI confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error handling simple task: {str(e)}")
            state["errors"].append(f"Simple task handler error: {str(e)}")
            state["success"] = False
        
        return state
    
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
                "is_on_leave": "FALSE"
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
    
    async def _run_optimized_allocator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run optimized employee allocator focused on minimal employees and max profit."""
        try:
            logger.info("Running Optimized Employee Allocator Agent")
            
            if not state["feature_spec"] or not state["architecture"]:
                logger.warning("Missing feature spec or architecture, skipping Employee Allocator")
                return state
            
            employees = state["employees"]
            cost_efficient_employees = self._calculate_employee_cost_efficiency(employees)
            
            input_data = {
                "feature_spec": state["feature_spec"],
                "architecture": state["architecture"],
                "requirement": state["requirement"],
                "employees": cost_efficient_employees  # Use sorted employees
            }
            
            # Enhance the allocator prompt for optimization
            original_response = await self.employee_allocator.process(input_data)
            
            if original_response.success:
                task_allocations = original_response.data.get("task_allocations", [])
                
                # Post-process to optimize allocations
                optimized_allocations = self._optimize_task_allocations(task_allocations, cost_efficient_employees)
                
                state["task_allocations"] = optimized_allocations
                logger.info(f"Optimized allocator completed with {len(optimized_allocations)} allocations")
            else:
                logger.error(f"Optimized Employee Allocator failed: {original_response.error}")
                state["errors"].append(f"Optimized Employee Allocator error: {original_response.error}")
                state["success"] = False
                
        except Exception as e:
            logger.error(f"Error in Optimized Employee Allocator Agent: {str(e)}")
            state["errors"].append(f"Optimized Employee Allocator error: {str(e)}")
            state["success"] = False
        
        return state
    
    def _optimize_task_allocations(self, allocations: List[Dict], employees: List[Dict]) -> List[Dict]:
        """Optimize task allocations to use fewer employees and maximize profit."""
        if not allocations:
            return allocations
        
        logger.info("Optimizing task allocations for minimal employees and maximum profit")
        
        # Create employee lookup
        emp_lookup = {str(emp.get('_id')): emp for emp in employees}
        
        # Consolidate tasks where possible
        optimized = []
        all_tasks = []
        
        # Collect all tasks
        for alloc in allocations:
            for task in alloc.get("tasks", []):
                task["original_employee_id"] = alloc.get("employee_id")
                task["original_employee_email"] = alloc.get("employee_email")
                task["original_employee_name"] = alloc.get("employee_name")
                all_tasks.append(task)
        
        # Sort tasks by priority and estimated hours
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_tasks.sort(key=lambda t: (
            priority_order.get(t.get("priority", "medium"), 2),
            -t.get("estimated_duration_hours", 0)  # Higher duration first for better consolidation
        ))
        
        # Reassign tasks to minimize employees used
        employee_assignments = {}
        
        for task in all_tasks:
            best_employee = None
            min_cost_score = float('inf')
            
            # Find best employee for this task
            for emp in employees:
                emp_id = str(emp.get('_id'))
                
                # Calculate current load for this employee
                current_hours = sum(
                    t.get("estimated_duration_hours", 0) 
                    for tasks in employee_assignments.get(emp_id, {}).get("tasks", [])
                    for t in [tasks]
                )
                
                # Check if employee can handle the additional load
                capacity = emp.get('capacity_hours_per_week', 40)
                current_workload = emp.get('current_workload_hours', 0)
                available_hours = capacity - current_workload
                
                if current_hours + task.get("estimated_duration_hours", 0) <= available_hours:
                    # Calculate cost efficiency
                    cost_score = emp.get('cost_efficiency_score', 1.0)
                    
                    # Bonus for already assigned employees (consolidation)
                    if emp_id in employee_assignments:
                        cost_score *= 0.7  # 30% bonus for consolidation
                    
                    if cost_score < min_cost_score:
                        min_cost_score = cost_score
                        best_employee = emp
            
            # Assign task to best employee
            if best_employee:
                emp_id = str(best_employee.get('_id'))
                if emp_id not in employee_assignments:
                    employee_assignments[emp_id] = {
                        "employee_id": emp_id,
                        "employee_email": best_employee.get('email'),
                        "employee_name": best_employee.get('name'),
                        "tasks": [],
                        "total_estimated_hours": 0,
                        "allocation_reasoning": ""
                    }
                
                employee_assignments[emp_id]["tasks"].append(task)
                employee_assignments[emp_id]["total_estimated_hours"] += task.get("estimated_duration_hours", 0)
        
        # Create final allocations with reasoning
        for emp_id, assignment in employee_assignments.items():
            emp = emp_lookup.get(emp_id)
            if emp:
                task_count = len(assignment["tasks"])
                total_hours = assignment["total_estimated_hours"]
                cost_score = emp.get('cost_efficiency_score', 1.0)
                
                assignment["allocation_reasoning"] = (
                    f"Optimized allocation: {task_count} tasks totaling {total_hours}h assigned to "
                    f"{assignment['employee_name']} (cost efficiency: {cost_score:.2f}, "
                    f"role: {emp.get('role', 'unknown')}). Chosen for optimal cost-benefit ratio."
                )
                
                optimized.append(assignment)
        
        logger.info(f"Optimization complete: Reduced from {len(allocations)} to {len(optimized)} employees")
        logger.info(f"Total tasks allocated: {sum(len(a['tasks']) for a in optimized)}")
        
        return optimized
    
    async def _run_employee_allocator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirects to optimized allocator."""
        return await self._run_optimized_allocator(state)
    
    async def _send_emails(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send optimized task allocation emails."""
        try:
            logger.info("Sending optimized task allocation emails")
            
            task_allocations = state.get("task_allocations", [])
            if not task_allocations:
                logger.warning("No task allocations to send emails for")
                state["email_results"] = {"status": "no_allocations"}
                return state
            
            is_simple_task = state.get("task_complexity") == "simple"
            
            # Send optimized emails
            email_results = []
            successful_count = 0
            failed_count = 0
            
            for allocation in task_allocations:
                employee_email = allocation.get("employee_email")
                if not employee_email:
                    logger.warning(f"No email found for allocation: {allocation.get('employee_name')}")
                    continue
                
                # Send email for each task in the allocation
                for task in allocation.get("tasks", []):
                    try:
                        task_data = {
                            "title": task.get("title"),
                            "description": task.get("description"),
                            "priority": task.get("priority"),
                            "estimated_duration": f"{task.get('estimated_duration_hours', 0)} hours",
                            "due_date": task.get("due_date"),
                            "additional_details": (
                                f"Allocation reasoning: {allocation.get('allocation_reasoning', '')}\n\n"
                                f"Additional task details: {task.get('additional_details', '')}"
                            )
                        }
                        
                        result = await email_manager.send_optimized_task_email(
                            employee_email, 
                            task_data, 
                            is_simple_task=is_simple_task
                        )
                        
                        if result.get("status") == "completed":
                            successful_count += 1
                        else:
                            failed_count += 1
                            
                        email_results.append({
                            "employee_email": employee_email,
                            "task_title": task.get("title"),
                            "result": result
                        })
                        
                    except Exception as e:
                        logger.error(f"Error sending email for task {task.get('title')}: {str(e)}")
                        failed_count += 1
                        email_results.append({
                            "employee_email": employee_email,
                            "task_title": task.get("title"),
                            "error": str(e),
                            "status": "failed"
                        })
            
            final_status = "completed" if failed_count == 0 else "partial_failure" if successful_count > 0 else "failed"
            
            state["email_results"] = {
                "status": final_status,
                "total_emails": successful_count + failed_count,
                "successful": successful_count,
                "failed": failed_count,
                "is_simple_task": is_simple_task,
                "results": email_results
            }
            
            logger.info(f"Email sending completed: {successful_count} successful, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Error sending emails: {str(e)}")
            state["errors"].append(f"Email error: {str(e)}")
            state["email_results"] = {"status": "failed", "error": str(e)}
        
        return state
    
    async def _save_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save optimized processing results to database with metrics."""
        try:
            logger.info("Saving optimized processing results")
            
            # Calculate optimization metrics
            task_allocations = state.get("task_allocations", [])
            classification_details = state.get("classification_details", {})
            employees_used = len(task_allocations)
            total_tasks = sum(len(alloc.get("tasks", [])) for alloc in task_allocations)
            total_hours = sum(alloc.get("total_estimated_hours", 0) for alloc in task_allocations)
            
            # Calculate average cost efficiency
            avg_cost_efficiency = 0
            if task_allocations:
                cost_scores = []
                for alloc in task_allocations:
                    # Extract cost efficiency from reasoning or default
                    reasoning = alloc.get("allocation_reasoning", "")
                    if "cost efficiency:" in reasoning.lower():
                        try:
                            score_part = reasoning.lower().split("cost efficiency:")[1].split(",")[0].strip()
                            score = float(score_part)
                            cost_scores.append(score)
                        except:
                            cost_scores.append(1.0)  # Default
                    else:
                        cost_scores.append(1.0)
                avg_cost_efficiency = sum(cost_scores) / len(cost_scores) if cost_scores else 1.0
            
            # Save to processing_results collection with optimization metrics
            result_doc = {
                "org_id": state["requirement"].org_id,
                "requirement": state["requirement"].dict(),
                "feature_spec": state.get("feature_spec"),
                "architecture": state.get("architecture"),
                "task_allocations": task_allocations,
                "email_results": state.get("email_results"),
                "success": state.get("success", True),
                "errors": state.get("errors", []),
                "created_at": datetime.now(),
                
                # Optimization metrics
                "optimization_metrics": {
                    "task_complexity": state.get("task_complexity"),
                    "classification_confidence": classification_details.get("confidence", 0.5),
                    "classification_reasoning": classification_details.get("reasoning", ""),
                    "ai_estimated_hours": classification_details.get("estimated_hours", 4),
                    "required_skills": classification_details.get("required_skills", []),
                    "risk_factors": classification_details.get("risk_factors", []),
                    "dependencies": classification_details.get("dependencies", []),
                    "employees_used": employees_used,
                    "total_tasks": total_tasks,
                    "total_estimated_hours": total_hours,
                    "average_cost_efficiency": avg_cost_efficiency,
                    "workflow_path": "simple" if state.get("task_complexity") == "simple" else "complex",
                    "nodes_skipped": 2 if state.get("task_complexity") == "simple" else 0,  # Skipped product_manager and architect
                    "optimization_enabled": True,
                    "ai_classification_used": True
                }
            }
            
            result = db.processing_results.insert_one(result_doc)
            logger.info(f"Optimized results saved with ID: {result.inserted_id}")
            
            # Save individual tasks to tasks collection with optimization context
            for allocation in task_allocations:
                for task in allocation.get("tasks", []):
                    task_doc = task.copy()
                    task_doc["allocation_id"] = str(result.inserted_id)
                    task_doc["created_at"] = datetime.now()
                    task_doc["optimization_context"] = {
                        "is_optimized": True,
                        "task_complexity": state.get("task_complexity"),
                        "classification_confidence": classification_details.get("confidence", 0.5),
                        "ai_estimated_hours": classification_details.get("estimated_hours", 4),
                        "cost_efficiency_selected": True,
                        "employee_minimization": True,
                        "ai_classification_used": True
                    }
                    db.tasks.insert_one(task_doc)
            
            # Log optimization summary
            logger.info(f"Optimization Summary:")
            logger.info(f"  - Task Complexity: {state.get('task_complexity')} (AI confidence: {classification_details.get('confidence', 0.5):.2f})")
            logger.info(f"  - AI Estimated Hours: {classification_details.get('estimated_hours', 4)}")
            logger.info(f"  - Required Skills: {', '.join(classification_details.get('required_skills', [])) if classification_details.get('required_skills') else 'General'}")
            logger.info(f"  - Employees Used: {employees_used}")
            logger.info(f"  - Total Tasks: {total_tasks}")
            logger.info(f"  - Total Hours: {total_hours}")
            logger.info(f"  - Avg Cost Efficiency: {avg_cost_efficiency:.2f}")
            logger.info(f"  - Workflow Path: {'Simplified' if state.get('task_complexity') == 'simple' else 'Full'}")
            logger.info(f"  - Classification Reasoning: {classification_details.get('reasoning', 'N/A')[:100]}...")
            
        except Exception as e:
            logger.error(f"Error saving optimized results: {str(e)}")
            state["errors"].append(f"Save error: {str(e)}")
        
        return state


# Global optimized super agent instance
super_agent = OptimizedSuperAgent()
