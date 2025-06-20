from agents import BaseAgent
from models import Task, TaskAllocation, Priority
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from loguru import logger
from models.models import AgentResponse


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
            
            # Create task breakdown prompt
            prompt = f"""
You are a Senior Project Manager and Team Lead. Based on the feature specification and system architecture, break down the work into specific tasks and allocate them to team members.

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

Available Team Members:
{self._format_employees(employees)}

Please break down the work into specific, actionable tasks and allocate them to appropriate team members based on their skills and current workload.

For each task allocation, provide:
1. Task title and detailed description
2. Assigned employee and reasoning
3. Estimated duration in hours
4. Priority level
5. Dependencies
6. Due date suggestion

Return your response in the following JSON format:
{{
    "task_allocations": [
        {{
            "employee_id": "employee_id",
            "employee_email": "email@company.com",
            "employee_name": "John Doe",
            "tasks": [
                {{
                    "title": "Task title",
                    "description": "Detailed task description",
                    "priority": "high|medium|low|critical",
                    "estimated_duration_hours": 8,
                    "due_date": "2025-01-15",
                    "additional_details": "Any additional context"
                }}
            ],
            "total_estimated_hours": 24,
            "allocation_reasoning": "Why this employee was chosen"
        }}
    ],
    "overall_reasoning": "Overall allocation strategy and considerations"
}}
"""
            
            response_text = await self._generate_response(prompt)
            
            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                
                response_data = json.loads(json_str)
                
                # Create TaskAllocation objects
                task_allocations = []
                for allocation_data in response_data.get('task_allocations', []):
                    tasks = []
                    for task_data in allocation_data.get('tasks', []):
                        # Parse due date
                        due_date = None
                        if task_data.get('due_date'):
                            try:
                                due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d')
                            except:
                                due_date = datetime.now() + timedelta(days=7)  # Default to 1 week
                        
                        task = Task(
                            title=task_data.get('title', 'Untitled Task'),
                            description=task_data.get('description', ''),
                            priority=Priority(task_data.get('priority', 'medium')),
                            estimated_duration_hours=task_data.get('estimated_duration_hours', 8),
                            due_date=due_date,
                            assigned_to=allocation_data.get('employee_id'),
                            assigned_to_email=allocation_data.get('employee_email'),
                            created_by_agent=self.name,
                            org_id=requirement.org_id,
                            additional_details=task_data.get('additional_details')
                        )
                        tasks.append(task)
                    
                    allocation = TaskAllocation(
                        employee_id=allocation_data.get('employee_id', ''),
                        employee_email=allocation_data.get('employee_email', ''),
                        employee_name=allocation_data.get('employee_name', ''),
                        tasks=tasks,
                        total_estimated_hours=allocation_data.get('total_estimated_hours', 0),
                        allocation_reasoning=allocation_data.get('allocation_reasoning', '')
                    )
                    task_allocations.append(allocation)
                
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    data={'task_allocations': [alloc.dict() for alloc in task_allocations]},
                    reasoning=response_data.get('overall_reasoning', 'Tasks allocated successfully')
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    data={},
                    error=f"Failed to parse response: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error in EmployeeAllocatorAgent: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e)
            )
    
    def _format_employees(self, employees: List[Dict[str, Any]]) -> str:
        """Format employee list for prompt."""
        if not employees:
            return "No employees available"
        
        formatted = []
        for emp in employees:
            workload_pct = (emp.get('current_workload_hours', 0) / emp.get('capacity_hours_per_week', 40)) * 100
            formatted.append(
                f"- {emp.get('name', 'Unknown')} ({emp.get('email', 'no-email')}) - "
                f"Role: {emp.get('role', 'Unknown')}, "
                f"Skills: {', '.join(emp.get('skills', []))}, "
                f"Capacity: {emp.get('capacity_hours_per_week', 40)}h/week, "
                f"Current workload: {workload_pct:.1f}%"
            )
        return '\n'.join(formatted)
