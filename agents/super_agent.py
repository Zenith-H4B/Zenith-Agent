"""Super Agent: Orchestrates the process from requirement to email notification."""

import asyncio
from typing import Dict, Any, List
from loguru import logger
from agents.product_manager import ProductManagerAgent
from agents.architecture import ArchitectureAgent
from agents.allocator import EmployeeAllocatorAgent
from core.emailer import email_manager
from core.embeddings import embedding_manager
from core.metaGPT_client import metagpt_client
import json
import time

class SuperAgent:
    """Super Agent that orchestrates the entire multi-agent workflow."""
    
    def __init__(self):
        self.agent_name = "SuperAgent"
        self.role = "Workflow Orchestration and Coordination"
        
        # Initialize sub-agents
        self.pm_agent = ProductManagerAgent()
        self.architecture_agent = ArchitectureAgent()
        self.allocator_agent = EmployeeAllocatorAgent()
        
        # Workflow state
        self.workflow_state = {}
        self.execution_log = []
        
        logger.info(f"Initialized {self.agent_name} with all sub-agents")
    
    def _log_step(self, step: str, status: str, data: Dict[str, Any] = None, duration: float = None):
        """Log workflow step with timing and status."""
        log_entry = {
            "step": step,
            "status": status,
            "timestamp": time.time(),
            "duration_seconds": duration,
            "data_summary": self._summarize_data(data) if data else None
        }
        
        self.execution_log.append(log_entry)
        
        if status == "started":
            logger.info(f"🚀 Starting step: {step}")
        elif status == "completed":
            logger.info(f"✅ Completed step: {step}" + (f" in {duration:.2f}s" if duration else ""))
        elif status == "failed":
            logger.error(f"❌ Failed step: {step}" + (f" after {duration:.2f}s" if duration else ""))
        else:
            logger.info(f"📊 Step update: {step} - {status}")
    
    def _summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of data for logging."""
        if not data:
            return {}
        
        summary = {}
        
        # Summarize common data structures
        if "specification" in data:
            spec = data["specification"]
            summary["specification_sections"] = list(spec.keys()) if isinstance(spec, dict) else "non-dict"
        
        if "architecture" in data:
            arch = data["architecture"]
            summary["architecture_sections"] = list(arch.keys()) if isinstance(arch, dict) else "non-dict"
        
        if "allocations" in data:
            allocs = data["allocations"]
            summary["allocations_count"] = len(allocs) if isinstance(allocs, list) else "non-list"
        
        if "tasks" in data:
            tasks = data["tasks"]
            summary["tasks_count"] = len(tasks) if isinstance(tasks, list) else "non-list"
        
        if "error" in data:
            summary["error"] = str(data["error"])[:100] + "..." if len(str(data["error"])) > 100 else str(data["error"])
        
        return summary
    
    async def validate_requirement(self, requirement: str) -> Dict[str, Any]:
        """Validate and preprocess the initial requirement."""
        try:
            step_start = time.time()
            self._log_step("requirement_validation", "started")
            
            # Basic validation
            if not requirement or len(requirement.strip()) < 10:
                raise ValueError("Requirement must be at least 10 characters long")
            
            if len(requirement) > 5000:
                raise ValueError("Requirement is too long (max 5000 characters)")
            
            # Clean and normalize requirement
            cleaned_requirement = requirement.strip()
            
            # Analyze requirement complexity
            word_count = len(cleaned_requirement.split())
            complexity_indicators = [
                "integrate", "scale", "real-time", "machine learning", "ai",
                "microservice", "distributed", "cloud", "mobile", "web"
            ]
            
            complexity_score = sum(1 for indicator in complexity_indicators 
                                 if indicator in cleaned_requirement.lower())
            
            if word_count < 20:
                estimated_complexity = "Simple"
            elif word_count < 100 and complexity_score < 3:
                estimated_complexity = "Moderate"
            else:
                estimated_complexity = "Complex"
            
            validation_result = {
                "original_requirement": requirement,
                "cleaned_requirement": cleaned_requirement,
                "word_count": word_count,
                "complexity_score": complexity_score,
                "estimated_complexity": estimated_complexity,
                "validation_status": "passed",
                "preprocessing_applied": ["strip_whitespace", "complexity_analysis"]
            }
            
            # Store embeddings for future reference
            try:
                embedding_data = [0.1] * 384  # Placeholder embedding
                embedding_manager.add_embedding(
                    text=cleaned_requirement,
                    embedding=embedding_data,
                    metadata={
                        "type": "requirement",
                        "complexity": estimated_complexity,
                        "timestamp": time.time()
                    }
                )
                logger.debug("Stored requirement embedding")
            except Exception as e:
                logger.warning(f"Could not store embedding: {str(e)}")
            
            duration = time.time() - step_start
            self._log_step("requirement_validation", "completed", validation_result, duration)
            
            return validation_result
            
        except Exception as e:
            duration = time.time() - step_start
            error_result = {
                "original_requirement": requirement,
                "validation_status": "failed",
                "error": str(e)
            }
            self._log_step("requirement_validation", "failed", error_result, duration)
            return error_result
    
    async def execute_product_management_phase(self, requirement: str) -> Dict[str, Any]:
        """Execute Product Manager Agent phase."""
        try:
            step_start = time.time()
            self._log_step("product_management", "started")
            
            logger.info("🎯 Executing Product Management Phase")
            
            # Run Product Manager Agent
            pm_result = await self.pm_agent.run(requirement)
            
            if pm_result.get("status") == "failed":
                raise Exception(f"Product Manager failed: {pm_result.get('error')}")
            
            # Extract and validate specification
            specification = pm_result.get("specification", {})
            if not specification:
                raise Exception("Product Manager did not generate specification")
            
            # Store specification state
            self.workflow_state["product_specification"] = specification
            self.workflow_state["pm_result"] = pm_result
            
            duration = time.time() - step_start
            self._log_step("product_management", "completed", pm_result, duration)
            
            logger.info(f"✅ Product specification created with {len(specification)} sections")
            return pm_result
            
        except Exception as e:
            duration = time.time() - step_start
            error_result = {"error": str(e), "status": "failed"}
            self._log_step("product_management", "failed", error_result, duration)
            raise Exception(f"Product Management phase failed: {str(e)}")
    
    async def execute_architecture_phase(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Architecture Agent phase."""
        try:
            step_start = time.time()
            self._log_step("architecture_design", "started")
            
            logger.info("🏗️ Executing Architecture Design Phase")
            
            # Run Architecture Agent
            arch_result = await self.architecture_agent.run(specification)
            
            if arch_result.get("status") == "failed":
                raise Exception(f"Architecture Agent failed: {arch_result.get('error')}")
            
            # Extract and validate architecture
            architecture = arch_result.get("architecture", {})
            if not architecture:
                raise Exception("Architecture Agent did not generate architecture")
            
            # Store architecture state
            self.workflow_state["system_architecture"] = architecture
            self.workflow_state["arch_result"] = arch_result
            
            duration = time.time() - step_start
            self._log_step("architecture_design", "completed", arch_result, duration)
            
            logger.info(f"✅ System architecture created with {len(architecture)} components")
            return arch_result
            
        except Exception as e:
            duration = time.time() - step_start
            error_result = {"error": str(e), "status": "failed"}
            self._log_step("architecture_design", "failed", error_result, duration)
            raise Exception(f"Architecture phase failed: {str(e)}")
    
    async def execute_allocation_phase(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Employee Allocator Agent phase."""
        try:
            step_start = time.time()
            self._log_step("task_allocation", "started")
            
            logger.info("👥 Executing Task Allocation Phase")
            
            # Run Employee Allocator Agent
            alloc_result = await self.allocator_agent.run(architecture)
            
            if alloc_result.get("status") == "failed":
                raise Exception(f"Employee Allocator failed: {alloc_result.get('error')}")
            
            # Extract allocation data
            allocations = alloc_result.get("allocation_result", {}).get("allocations", [])
            if not allocations:
                logger.warning("No task allocations were created")
            
            # Store allocation state
            self.workflow_state["task_allocations"] = allocations
            self.workflow_state["alloc_result"] = alloc_result
            
            duration = time.time() - step_start
            self._log_step("task_allocation", "completed", alloc_result, duration)
            
            logger.info(f"✅ Task allocation completed with {len(allocations)} assignments")
            return alloc_result
            
        except Exception as e:
            duration = time.time() - step_start
            error_result = {"error": str(e), "status": "failed"}
            self._log_step("task_allocation", "failed", error_result, duration)
            raise Exception(f"Task allocation phase failed: {str(e)}")
    
    async def execute_notification_phase(self, allocation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email notification phase."""
        try:
            step_start = time.time()
            self._log_step("email_notifications", "started")
            
            logger.info("📧 Executing Email Notification Phase")
            
            # Get notification data
            notification_prep = allocation_result.get("notification_preparation", {})
            notification_data = notification_prep.get("notification_data", [])
            
            if not notification_data:
                logger.warning("No notification data available")
                return {
                    "status": "skipped",
                    "reason": "No allocations to notify"
                }
            
            # Send bulk emails
            email_result = await email_manager.send_bulk_task_allocation_emails(notification_data)
            
            # Store notification state
            self.workflow_state["email_notifications"] = email_result
            
            duration = time.time() - step_start
            self._log_step("email_notifications", "completed", email_result, duration)
            
            successful_sends = email_result.get("successful_sends", 0)
            failed_sends = email_result.get("failed_sends", 0)
            
            logger.info(f"✅ Email notifications sent: {successful_sends} successful, {failed_sends} failed")
            return email_result
            
        except Exception as e:
            duration = time.time() - step_start
            error_result = {"error": str(e), "status": "failed"}
            self._log_step("email_notifications", "failed", error_result, duration)
            logger.error(f"Email notification phase failed: {str(e)}")
            # Don't raise here as email failure shouldn't stop the workflow
            return error_result
    
    async def generate_workflow_summary(self) -> Dict[str, Any]:
        """Generate comprehensive workflow summary."""
        try:
            step_start = time.time()
            
            total_duration = sum(
                log["duration_seconds"] for log in self.execution_log 
                if log.get("duration_seconds")
            )
            
            # Count successful vs failed steps
            completed_steps = [log for log in self.execution_log if log["status"] == "completed"]
            failed_steps = [log for log in self.execution_log if log["status"] == "failed"]
            
            # Extract key metrics
            pm_result = self.workflow_state.get("pm_result", {})
            arch_result = self.workflow_state.get("arch_result", {})
            alloc_result = self.workflow_state.get("alloc_result", {})
            email_result = self.workflow_state.get("email_notifications", {})
            
            # Build summary
            summary = {
                "workflow_overview": {
                    "total_execution_time": f"{total_duration:.2f} seconds",
                    "completed_steps": len(completed_steps),
                    "failed_steps": len(failed_steps),
                    "overall_status": "completed" if not failed_steps else "partial_failure"
                },
                "product_management_summary": {
                    "status": pm_result.get("status", "unknown"),
                    "specification_sections": len(pm_result.get("specification", {})),
                    "features_identified": len(pm_result.get("specification", {}).get("functional_requirements", {}).get("core_features", []))
                },
                "architecture_summary": {
                    "status": arch_result.get("status", "unknown"),
                    "architecture_components": len(arch_result.get("architecture", {})),
                    "technology_stack": arch_result.get("architecture", {}).get("technology_stack", {})
                },
                "allocation_summary": {
                    "status": alloc_result.get("status", "unknown"),
                    "total_tasks": alloc_result.get("allocation_result", {}).get("allocation_summary", {}).get("total_tasks", 0),
                    "allocated_tasks": alloc_result.get("allocation_result", {}).get("allocation_summary", {}).get("allocated_tasks", 0),
                    "employees_involved": alloc_result.get("allocation_result", {}).get("allocation_summary", {}).get("employees_involved", 0)
                },
                "notification_summary": {
                    "status": email_result.get("status", "unknown"),
                    "successful_sends": email_result.get("successful_sends", 0),
                    "failed_sends": email_result.get("failed_sends", 0)
                },
                "execution_log": self.execution_log,
                "recommendations": self._generate_recommendations()
            }
            
            # Store summary embedding
            try:
                summary_text = json.dumps(summary, indent=2)
                embedding_data = [0.2] * 384  # Placeholder embedding
                embedding_manager.add_embedding(
                    text=summary_text,
                    embedding=embedding_data,
                    metadata={
                        "type": "workflow_summary",
                        "timestamp": time.time(),
                        "status": summary["workflow_overview"]["overall_status"]
                    }
                )
                logger.debug("Stored workflow summary embedding")
            except Exception as e:
                logger.warning(f"Could not store summary embedding: {str(e)}")
            
            duration = time.time() - step_start
            logger.info(f"📊 Workflow summary generated in {duration:.2f}s")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating workflow summary: {str(e)}")
            return {
                "error": str(e),
                "execution_log": self.execution_log,
                "status": "failed"
            }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on workflow execution."""
        recommendations = []
        
        # Check for failed steps
        failed_steps = [log for log in self.execution_log if log["status"] == "failed"]
        if failed_steps:
            recommendations.append(f"Address {len(failed_steps)} failed workflow steps")
        
        # Check allocation success rate
        alloc_result = self.workflow_state.get("alloc_result", {})
        allocation_summary = alloc_result.get("allocation_result", {}).get("allocation_summary", {})
        allocation_rate = allocation_summary.get("allocation_rate", 0)
        
        if allocation_rate < 0.8:
            recommendations.append("Consider hiring additional developers or adjusting task complexity")
        
        # Check email delivery
        email_result = self.workflow_state.get("email_notifications", {})
        failed_sends = email_result.get("failed_sends", 0)
        
        if failed_sends > 0:
            recommendations.append("Review and fix email delivery issues")
        
        # Performance recommendations
        total_duration = sum(
            log["duration_seconds"] for log in self.execution_log 
            if log.get("duration_seconds")
        )
        
        if total_duration > 60:
            recommendations.append("Consider optimizing workflow performance for faster execution")
        
        if not recommendations:
            recommendations.append("Workflow executed successfully with no immediate issues")
        
        return recommendations
    
    async def execute(self, requirement: str) -> Dict[str, Any]:
        """Execute the complete multi-agent workflow."""
        try:
            workflow_start = time.time()
            logger.info("🎬 Starting Super Agent Multi-Agent Workflow")
            logger.info(f"📝 Requirement: {requirement[:100]}...")
            
            # Reset workflow state
            self.workflow_state = {}
            self.execution_log = []
            
            # Phase 1: Validate requirement
            validation_result = await self.validate_requirement(requirement)
            if validation_result.get("validation_status") == "failed":
                raise Exception(f"Requirement validation failed: {validation_result.get('error')}")
            
            cleaned_requirement = validation_result["cleaned_requirement"]
            
            # Phase 2: Product Management
            pm_result = await self.execute_product_management_phase(cleaned_requirement)
            specification = pm_result["specification"]
            
            # Phase 3: Architecture Design
            arch_result = await self.execute_architecture_phase(specification)
            architecture = arch_result["architecture"]
            
            # Phase 4: Task Allocation
            alloc_result = await self.execute_allocation_phase(architecture)
            
            # Phase 5: Email Notifications
            email_result = await self.execute_notification_phase(alloc_result)
            
            # Phase 6: Generate Summary
            workflow_summary = await self.generate_workflow_summary()
            
            # Calculate total execution time
            total_execution_time = time.time() - workflow_start
            
            # Final result
            final_result = {
                "super_agent": self.agent_name,
                "workflow_status": "completed",
                "total_execution_time": f"{total_execution_time:.2f} seconds",
                "original_requirement": requirement,
                "validation_result": validation_result,
                "product_management_result": pm_result,
                "architecture_result": arch_result,
                "allocation_result": alloc_result,
                "email_result": email_result,
                "workflow_summary": workflow_summary,
                "timestamp": time.time()
            }
            
            logger.info(f"🎉 Super Agent workflow completed successfully in {total_execution_time:.2f}s")
            
            # Log final statistics
            total_tasks = alloc_result.get("allocation_result", {}).get("allocation_summary", {}).get("total_tasks", 0)
            allocated_tasks = alloc_result.get("allocation_result", {}).get("allocation_summary", {}).get("allocated_tasks", 0)
            employees_involved = alloc_result.get("allocation_result", {}).get("allocation_summary", {}).get("employees_involved", 0)
            
            logger.info(f"📊 Final Stats: {allocated_tasks}/{total_tasks} tasks allocated to {employees_involved} employees")
            
            return final_result
            
        except Exception as e:
            total_execution_time = time.time() - workflow_start
            logger.error(f"💥 Super Agent workflow failed after {total_execution_time:.2f}s: {str(e)}")
            
            # Generate partial summary even on failure
            try:
                partial_summary = await self.generate_workflow_summary()
            except:
                partial_summary = {"error": "Could not generate summary"}
            
            return {
                "super_agent": self.agent_name,
                "workflow_status": "failed",
                "total_execution_time": f"{total_execution_time:.2f} seconds",
                "original_requirement": requirement,
                "error": str(e),
                "partial_results": self.workflow_state,
                "execution_log": self.execution_log,
                "partial_summary": partial_summary,
                "timestamp": time.time()
            }
    
    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "agent": self.agent_name,
            "current_state": self.workflow_state,
            "execution_log": self.execution_log,
            "is_running": len(self.execution_log) > 0 and self.execution_log[-1]["status"] == "started"
        }
    
    async def run(self, requirement: str) -> Dict[str, Any]:
        """Main entry point for the Super Agent (alias for execute)."""
        return await self.execute(requirement)
