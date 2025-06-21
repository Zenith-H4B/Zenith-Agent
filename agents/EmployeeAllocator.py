from agents import BaseAgent
from models import Task, TaskAllocation, Priority
from models.models import AgentResponse, TaskAllocationResponse
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger


class EmployeeAllocatorAgent(BaseAgent):
    """Agent responsible for allocating tasks to team members."""
    
    def __init__(self):
        super().__init__("Employee Allocator Agent")
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process feature specs and architecture to allocate tasks."""
        try:
            feature_spec = input_data.get('feature_spec')
            architecture = input_data.get('architecture')
            requirement = input_data.get('requirement')
            employees = input_data.get('employees', [])
            
            # Create optimized task breakdown prompt
            prompt = f"""
You are a Senior Project Manager and Team Lead focused on PROFIT MAXIMIZATION and EFFICIENT RESOURCE UTILIZATION. Based on the feature specification and system architecture, break down the work into specific tasks and allocate them to the MINIMUM NUMBER of team members while maximizing cost efficiency.

OPTIMIZATION PRIORITIES:
1. Use the FEWEST employees possible
2. Prioritize cost-effective employees (lower roles when possible)
3. Consolidate related tasks to single employees
4. Avoid over-engineering - keep it simple and efficient

Feature Specification:
- Title: {feature_spec.get('title', 'N/A')}
- Description: {feature_spec.get('description', 'N/A')}
- User Stories: {feature_spec.get('user_stories', [])}
- Acceptance Criteria: {feature_spec.get('acceptance_criteria', [])}
- Estimated Effort: {feature_spec.get('estimated_effort', 'TBD')}

System Architecture:
- Tech Stack: {architecture.get('tech_stack', [])}
- Components: {architecture.get('system_components', [])}
- API Endpoints: {architecture.get('api_endpoints', [])}

Available Team Members (sorted by cost efficiency):
{self._format_employees_with_efficiency(employees)}

ALLOCATION STRATEGY:
- Assign multiple related tasks to the same employee when possible
- Use junior/mid-level developers over seniors when tasks allow
- Avoid splitting simple tasks across multiple people
- Consider current workload but prioritize consolidation

IMPORTANT: For each employee allocation, you MUST provide:
1. employee_id: Use the employee ID from the available team members list
2. employee_email: Use the email from the available team members list  
3. employee_name: Use the name from the available team members list
4. tasks: List of tasks with all required fields
5. total_estimated_hours: Sum of all task hours
6. allocation_reasoning: Detailed cost-efficiency reasoning

For each task, provide:
1. title: Clear task title
2. description: Detailed task description
3. priority: One of "low", "medium", "high", "critical"
4. estimated_duration_hours: Realistic hours estimate
5. due_date: Date in YYYY-MM-DD format
6. additional_details: Any extra context (optional)

CRITICAL: Ensure you extract the correct employee_id, employee_email, and employee_name from the team members list provided above.

Provide comprehensive task allocations with profit-maximizing employee selection strategy.
"""
            
            # Generate structured response
            response_data = await self._generate_structured_response(prompt, TaskAllocationResponse)
            
            # Create TaskAllocation objects
            task_allocations = []
            for allocation_data in response_data.task_allocations:
                tasks = []
                for task_data in allocation_data.tasks:
                    # Parse due date
                    due_date = None
                    if task_data.due_date:
                        try:
                            due_date = datetime.strptime(task_data.due_date, '%Y-%m-%d')
                        except:
                            due_date = datetime.now() + timedelta(days=7)  # Default to 1 week
                    
                    task = Task(
                        title=task_data.title,
                        description=task_data.description,
                        priority=task_data.priority,
                        estimated_duration_hours=task_data.estimated_duration_hours,
                        due_date=due_date,
                        assigned_to=allocation_data.employee_id,
                        assigned_to_email=allocation_data.employee_email,
                        created_by_agent=self.name,
                        org_id=requirement.org_id,
                        additional_details=task_data.additional_details
                    )
                    tasks.append(task)
                
                allocation = TaskAllocation(
                    employee_id=allocation_data.employee_id,
                    employee_email=allocation_data.employee_email,
                    employee_name=allocation_data.employee_name,
                    tasks=tasks,
                    total_estimated_hours=allocation_data.total_estimated_hours,
                    allocation_reasoning=allocation_data.allocation_reasoning
                )
                task_allocations.append(allocation)
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={'task_allocations': [alloc.dict() for alloc in task_allocations]},
                reasoning=response_data.overall_reasoning
            )
                
        except Exception as e:
            logger.error(f"Error in EmployeeAllocatorAgent: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e)
            )
    
    def _format_employees_with_efficiency(self, employees: List[Dict[str, Any]]) -> str:
        """Format employee list with cost efficiency information for prompt."""
        if not employees:
            return "No employees available"
        
        formatted = []
        for i, emp in enumerate(employees):
            workload_pct = (emp.get('current_workload_hours', 0) / emp.get('capacity_hours_per_week', 40)) * 100
            cost_score = emp.get('cost_efficiency_score', 1.0)
            
            # Add ranking indicator
            rank_indicator = f"RANK #{i+1} (Most Efficient)" if i == 0 else f"RANK #{i+1}"
            
            formatted.append(
                f"{rank_indicator} - ID: {emp.get('id', 'unknown-id')}, "
                f"Name: {emp.get('name', 'Unknown')}, "
                f"Email: {emp.get('email', 'no-email')}, "
                f"Role: {emp.get('role', 'Unknown')}, "
                f"Skills: {', '.join(emp.get('skills', []))}, "
                f"Capacity: {emp.get('capacity_hours_per_week', 40)}h/week, "
                f"Current workload: {workload_pct:.1f}%, "
                f"Cost Efficiency Score: {cost_score:.2f} (lower = more efficient)"
            )
        return '\n'.join(formatted)
