"""Employee Allocator Agent: assigns tasks to team members based on capacity."""

import asyncio
from typing import Dict, Any, List
from loguru import logger
from utils.db import db
from datetime import datetime, timedelta
import random

class EmployeeAllocatorAgent:
    """Employee Allocator Agent using skill-based allocation."""
    
    def __init__(self):
        self.agent_name = "EmployeeAllocator"
        self.role = "Task Assignment and Resource Allocation"
        self.employees_collection = db.employees
        self.tasks_collection = db.tasks
        self.allocations_collection = db.task_allocations
        logger.info(f"Initialized {self.agent_name} agent")
    
    async def analyze_architecture_for_tasks(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze architecture design and extract tasks."""
        try:
            logger.info("Allocator Agent analyzing architecture for task extraction")
            
            # Extract architecture information
            tech_stack = architecture.get("technology_stack", {})
            components = architecture.get("system_overview", {}).get("key_components", [])
            development_workflow = architecture.get("development_workflow", {})
            
            # Generate tasks based on architecture
            tasks = self._generate_tasks_from_architecture(architecture)
            
            # Estimate effort and complexity
            task_analysis = {
                "total_tasks": len(tasks),
                "task_categories": self._categorize_tasks(tasks),
                "skill_requirements": self._extract_skill_requirements(tasks, tech_stack),
                "estimated_timeline": self._estimate_project_timeline(tasks),
                "complexity_breakdown": self._analyze_task_complexity(tasks),
                "dependencies": self._identify_task_dependencies(tasks),
                "tasks": tasks
            }
            
            logger.info(f"Extracted {len(tasks)} tasks from architecture")
            logger.debug(f"Task categories: {list(task_analysis['task_categories'].keys())}")
            
            return task_analysis
            
        except Exception as e:
            logger.error(f"Architecture task analysis failed: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _generate_tasks_from_architecture(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific tasks from architecture design."""
        tasks = []
        
        # Extract components and generate tasks
        components = architecture.get("system_overview", {}).get("key_components", [])
        tech_stack = architecture.get("technology_stack", {})
        
        # Database setup tasks
        database_info = architecture.get("data_architecture", {})
        if database_info:
            tasks.extend([
                {
                    "id": f"task_db_{len(tasks)+1}",
                    "title": "Database Schema Design",
                    "description": "Design and implement database schema based on data models",
                    "category": "Backend",
                    "skills_required": ["SQL", "Database Design", "PostgreSQL"],
                    "estimated_hours": 16,
                    "priority": "High",
                    "complexity": "Medium",
                    "dependencies": []
                },
                {
                    "id": f"task_db_{len(tasks)+2}",
                    "title": "Database Migration Scripts",
                    "description": "Create database migration scripts and version control",
                    "category": "Backend",
                    "skills_required": ["SQL", "Migration Tools", "Version Control"],
                    "estimated_hours": 8,
                    "priority": "High",
                    "complexity": "Low",
                    "dependencies": ["task_db_1"]
                }
            ])
        
        # API development tasks
        if "backend" in tech_stack:
            tasks.extend([
                {
                    "id": f"task_api_{len(tasks)+1}",
                    "title": "API Design and Documentation",
                    "description": "Design RESTful APIs and create OpenAPI documentation",
                    "category": "Backend",
                    "skills_required": ["FastAPI", "REST API Design", "OpenAPI"],
                    "estimated_hours": 20,
                    "priority": "High",
                    "complexity": "Medium",
                    "dependencies": []
                },
                {
                    "id": f"task_api_{len(tasks)+2}",
                    "title": "Authentication System",
                    "description": "Implement JWT-based authentication and authorization",
                    "category": "Backend",
                    "skills_required": ["FastAPI", "JWT", "Security", "Python"],
                    "estimated_hours": 24,
                    "priority": "High",
                    "complexity": "High",
                    "dependencies": [f"task_api_{len(tasks)+1}"]
                },
                {
                    "id": f"task_api_{len(tasks)+3}",
                    "title": "Core API Endpoints",
                    "description": "Implement core business logic API endpoints",
                    "category": "Backend",
                    "skills_required": ["FastAPI", "Python", "Database Integration"],
                    "estimated_hours": 40,
                    "priority": "High",
                    "complexity": "High",
                    "dependencies": [f"task_api_{len(tasks)+1}", f"task_db_{len(tasks)-1}"]
                }
            ])
        
        # Frontend development tasks
        if "frontend" in tech_stack:
            tasks.extend([
                {
                    "id": f"task_fe_{len(tasks)+1}",
                    "title": "UI/UX Design Implementation",
                    "description": "Create responsive user interface components",
                    "category": "Frontend",
                    "skills_required": ["React", "TypeScript", "CSS", "Responsive Design"],
                    "estimated_hours": 32,
                    "priority": "Medium",
                    "complexity": "Medium",
                    "dependencies": []
                },
                {
                    "id": f"task_fe_{len(tasks)+2}",
                    "title": "State Management Setup",
                    "description": "Implement state management and API integration",
                    "category": "Frontend",
                    "skills_required": ["React", "State Management", "API Integration"],
                    "estimated_hours": 16,
                    "priority": "Medium",
                    "complexity": "Medium",
                    "dependencies": [f"task_fe_{len(tasks)+1}"]
                },
                {
                    "id": f"task_fe_{len(tasks)+3}",
                    "title": "Authentication UI",
                    "description": "Create login, registration, and user management interfaces",
                    "category": "Frontend",
                    "skills_required": ["React", "Forms", "Validation", "UX"],
                    "estimated_hours": 20,
                    "priority": "High",
                    "complexity": "Medium",
                    "dependencies": [f"task_api_{len(tasks)-1}"]
                }
            ])
        
        # DevOps and infrastructure tasks
        infrastructure = architecture.get("deployment_architecture", {})
        if infrastructure:
            tasks.extend([
                {
                    "id": f"task_devops_{len(tasks)+1}",
                    "title": "Containerization Setup",
                    "description": "Create Docker containers for all services",
                    "category": "DevOps",
                    "skills_required": ["Docker", "Containerization", "Linux"],
                    "estimated_hours": 12,
                    "priority": "Medium",
                    "complexity": "Medium",
                    "dependencies": []
                },
                {
                    "id": f"task_devops_{len(tasks)+2}",
                    "title": "CI/CD Pipeline",
                    "description": "Set up automated CI/CD pipeline",
                    "category": "DevOps",
                    "skills_required": ["GitHub Actions", "CI/CD", "Deployment"],
                    "estimated_hours": 16,
                    "priority": "Medium",
                    "complexity": "High",
                    "dependencies": [f"task_devops_{len(tasks)+1}"]
                },
                {
                    "id": f"task_devops_{len(tasks)+3}",
                    "title": "Monitoring Setup",
                    "description": "Implement monitoring, logging, and alerting",
                    "category": "DevOps",
                    "skills_required": ["Monitoring", "Logging", "Grafana", "Prometheus"],
                    "estimated_hours": 20,
                    "priority": "Low",
                    "complexity": "Medium",
                    "dependencies": [f"task_devops_{len(tasks)+2}"]
                }
            ])
        
        # Testing tasks
        testing_strategy = architecture.get("development_workflow", {}).get("testing_strategy", {})
        if testing_strategy:
            tasks.extend([
                {
                    "id": f"task_test_{len(tasks)+1}",
                    "title": "Unit Test Implementation",
                    "description": "Write comprehensive unit tests for all components",
                    "category": "Testing",
                    "skills_required": ["pytest", "Unit Testing", "Test Coverage"],
                    "estimated_hours": 24,
                    "priority": "Medium",
                    "complexity": "Medium",
                    "dependencies": []
                },
                {
                    "id": f"task_test_{len(tasks)+2}",
                    "title": "Integration Testing",
                    "description": "Implement API and database integration tests",
                    "category": "Testing",
                    "skills_required": ["Integration Testing", "API Testing", "Database Testing"],
                    "estimated_hours": 16,
                    "priority": "Medium",
                    "complexity": "Medium",
                    "dependencies": [f"task_api_{len(tasks)-5}"]
                },
                {
                    "id": f"task_test_{len(tasks)+3}",
                    "title": "End-to-End Testing",
                    "description": "Create automated E2E tests for user workflows",
                    "category": "Testing",
                    "skills_required": ["E2E Testing", "Cypress", "Test Automation"],
                    "estimated_hours": 20,
                    "priority": "Low",
                    "complexity": "High",
                    "dependencies": [f"task_fe_{len(tasks)-3}"]
                }
            ])
        
        # Documentation tasks
        tasks.extend([
            {
                "id": f"task_doc_{len(tasks)+1}",
                "title": "Technical Documentation",
                "description": "Create comprehensive technical documentation",
                "category": "Documentation",
                "skills_required": ["Technical Writing", "Documentation Tools", "Architecture"],
                "estimated_hours": 12,
                "priority": "Low",
                "complexity": "Low",
                "dependencies": []
            },
            {
                "id": f"task_doc_{len(tasks)+2}",
                "title": "User Documentation",
                "description": "Create user guides and help documentation",
                "category": "Documentation",
                "skills_required": ["Technical Writing", "User Experience", "Documentation"],
                "estimated_hours": 8,
                "priority": "Low",
                "complexity": "Low",
                "dependencies": [f"task_fe_{len(tasks)-5}"]
            }
        ])
        
        return tasks
    
    def _categorize_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize tasks by type."""
        categories = {}
        for task in tasks:
            category = task.get("category", "Other")
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _extract_skill_requirements(self, tasks: List[Dict[str, Any]], tech_stack: Dict[str, List[str]]) -> Dict[str, int]:
        """Extract and count skill requirements."""
        skills = {}
        
        # Count skills from tasks
        for task in tasks:
            for skill in task.get("skills_required", []):
                skills[skill] = skills.get(skill, 0) + 1
        
        # Add tech stack skills
        for category, techs in tech_stack.items():
            for tech in techs:
                skills[tech] = skills.get(tech, 0) + 1
        
        return dict(sorted(skills.items(), key=lambda x: x[1], reverse=True))
    
    def _estimate_project_timeline(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate overall project timeline."""
        total_hours = sum(task.get("estimated_hours", 0) for task in tasks)
        
        # Assume 6 hours productive work per day, 5 days per week
        productive_hours_per_week = 30
        
        return {
            "total_estimated_hours": total_hours,
            "estimated_weeks": round(total_hours / productive_hours_per_week, 1),
            "estimated_months": round(total_hours / (productive_hours_per_week * 4), 1),
            "parallel_development": True,
            "critical_path_weeks": self._calculate_critical_path(tasks)
        }
    
    def _calculate_critical_path(self, tasks: List[Dict[str, Any]]) -> float:
        """Calculate critical path duration."""
        # Simplified critical path calculation
        # In a real implementation, this would use proper critical path method
        high_priority_hours = sum(
            task.get("estimated_hours", 0) 
            for task in tasks 
            if task.get("priority") == "High"
        )
        return round(high_priority_hours / 30, 1)  # 30 productive hours per week
    
    def _analyze_task_complexity(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze task complexity distribution."""
        complexity = {"Low": 0, "Medium": 0, "High": 0}
        for task in tasks:
            comp = task.get("complexity", "Medium")
            complexity[comp] = complexity.get(comp, 0) + 1
        return complexity
    
    def _identify_task_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify and analyze task dependencies."""
        dependencies = []
        for task in tasks:
            if task.get("dependencies"):
                dependencies.append({
                    "task_id": task["id"],
                    "depends_on": task["dependencies"],
                    "title": task["title"]
                })
        return dependencies
    
    async def get_available_employees(self) -> List[Dict[str, Any]]:
        """Get list of available employees with their skills and capacity."""
        try:
            logger.info("Fetching available employees from database")
            
            # Check if employees collection exists and has data
            employee_count = await asyncio.to_thread(self.employees_collection.count_documents, {})
            
            if employee_count == 0:
                logger.warning("No employees found in database, creating sample employees")
                await self._create_sample_employees()
            
            # Fetch employees
            employees_cursor = self.employees_collection.find({"status": {"$ne": "inactive"}})
            employees = await asyncio.to_thread(list, employees_cursor)
            
            logger.info(f"Found {len(employees)} available employees")
            return employees
            
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            # Return sample employees if database is not available
            return await self._get_sample_employees()
    
    async def _create_sample_employees(self):
        """Create sample employees for demonstration."""
        sample_employees = [
            {
                "id": "emp_001",
                "name": "Alice Johnson",
                "email": "alice.johnson@company.com",
                "role": "Senior Full-Stack Developer",
                "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"],
                "seniority_level": "Senior",
                "availability": 40,  # hours per week
                "current_workload": 20,  # hours currently allocated
                "hourly_rate": 85,
                "preferences": ["Backend", "API Development"],
                "status": "active",
                "timezone": "UTC-5",
                "performance_rating": 4.8
            },
            {
                "id": "emp_002",
                "name": "Bob Smith",
                "email": "bob.smith@company.com",
                "role": "Frontend Developer",
                "skills": ["React", "TypeScript", "CSS", "JavaScript", "UI/UX", "Responsive Design"],
                "seniority_level": "Mid",
                "availability": 40,
                "current_workload": 15,
                "hourly_rate": 65,
                "preferences": ["Frontend", "UI Development"],
                "status": "active",
                "timezone": "UTC-5",
                "performance_rating": 4.5
            },
            {
                "id": "emp_003",
                "name": "Carol Davis",
                "email": "carol.davis@company.com",
                "role": "DevOps Engineer",
                "skills": ["Docker", "Kubernetes", "CI/CD", "AWS", "Monitoring", "Linux"],
                "seniority_level": "Senior",
                "availability": 40,
                "current_workload": 25,
                "hourly_rate": 90,
                "preferences": ["Infrastructure", "Deployment"],
                "status": "active",
                "timezone": "UTC-8",
                "performance_rating": 4.7
            },
            {
                "id": "emp_004",
                "name": "David Wilson",
                "email": "david.wilson@company.com",
                "role": "Backend Developer",
                "skills": ["Python", "FastAPI", "PostgreSQL", "SQL", "API Development"],
                "seniority_level": "Mid",
                "availability": 40,
                "current_workload": 10,
                "hourly_rate": 70,
                "preferences": ["Backend", "Database"],
                "status": "active",
                "timezone": "UTC-5",
                "performance_rating": 4.3
            },
            {
                "id": "emp_005",
                "name": "Eva Martinez",
                "email": "eva.martinez@company.com",
                "role": "QA Engineer",
                "skills": ["Testing", "pytest", "Selenium", "Test Automation", "Quality Assurance"],
                "seniority_level": "Mid",
                "availability": 40,
                "current_workload": 12,
                "hourly_rate": 60,
                "preferences": ["Testing", "Quality Assurance"],
                "status": "active",
                "timezone": "UTC-6",
                "performance_rating": 4.4
            },
            {
                "id": "emp_006",
                "name": "Frank Brown",
                "email": "frank.brown@company.com",
                "role": "Junior Developer",
                "skills": ["JavaScript", "React", "Python", "Git", "HTML", "CSS"],
                "seniority_level": "Junior",
                "availability": 40,
                "current_workload": 8,
                "hourly_rate": 45,
                "preferences": ["Learning", "Frontend"],
                "status": "active",
                "timezone": "UTC-5",
                "performance_rating": 4.0
            }
        ]
        
        try:
            await asyncio.to_thread(self.employees_collection.insert_many, sample_employees)
            logger.info(f"Created {len(sample_employees)} sample employees")
        except Exception as e:
            logger.error(f"Error creating sample employees: {str(e)}")
    
    async def _get_sample_employees(self) -> List[Dict[str, Any]]:
        """Get sample employees if database is not available."""
        return [
            {
                "id": "emp_001",
                "name": "Alice Johnson",
                "email": "alice.johnson@company.com",
                "role": "Senior Full-Stack Developer",
                "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"],
                "seniority_level": "Senior",
                "availability": 40,
                "current_workload": 20,
                "hourly_rate": 85,
                "preferences": ["Backend", "API Development"],
                "status": "active",
                "performance_rating": 4.8
            },
            {
                "id": "emp_002",
                "name": "Bob Smith",
                "email": "bob.smith@company.com",
                "role": "Frontend Developer",
                "skills": ["React", "TypeScript", "CSS", "JavaScript", "UI/UX", "Responsive Design"],
                "seniority_level": "Mid",
                "availability": 40,
                "current_workload": 15,
                "hourly_rate": 65,
                "preferences": ["Frontend", "UI Development"],
                "status": "active",
                "performance_rating": 4.5
            }
        ]
    
    def _calculate_employee_skill_match(self, employee: Dict[str, Any], task: Dict[str, Any]) -> float:
        """Calculate how well an employee's skills match a task."""
        employee_skills = set(skill.lower() for skill in employee.get("skills", []))
        required_skills = set(skill.lower() for skill in task.get("skills_required", []))
        
        if not required_skills:
            return 0.5  # Neutral match if no skills specified
        
        matching_skills = employee_skills.intersection(required_skills)
        skill_match_ratio = len(matching_skills) / len(required_skills)
        
        # Bonus for seniority matching complexity
        seniority_bonus = 0
        employee_seniority = employee.get("seniority_level", "Mid")
        task_complexity = task.get("complexity", "Medium")
        
        seniority_map = {"Junior": 1, "Mid": 2, "Senior": 3}
        complexity_map = {"Low": 1, "Medium": 2, "High": 3}
        
        emp_level = seniority_map.get(employee_seniority, 2)
        task_level = complexity_map.get(task_complexity, 2)
        
        if emp_level >= task_level:
            seniority_bonus = 0.1
        
        # Preference bonus
        preference_bonus = 0
        employee_prefs = [pref.lower() for pref in employee.get("preferences", [])]
        task_category = task.get("category", "").lower()
        
        if task_category in employee_prefs:
            preference_bonus = 0.15
        
        total_match = skill_match_ratio + seniority_bonus + preference_bonus
        return min(total_match, 1.0)
    
    def _calculate_employee_availability(self, employee: Dict[str, Any]) -> float:
        """Calculate employee availability as a ratio."""
        total_availability = employee.get("availability", 40)
        current_workload = employee.get("current_workload", 0)
        available_hours = max(0, total_availability - current_workload)
        
        return available_hours / total_availability if total_availability > 0 else 0
    
    def _calculate_allocation_score(self, employee: Dict[str, Any], task: Dict[str, Any]) -> float:
        """Calculate overall allocation score for employee-task pair."""
        skill_match = self._calculate_employee_skill_match(employee, task)
        availability = self._calculate_employee_availability(employee)
        performance = employee.get("performance_rating", 4.0) / 5.0
        
        # Weighted score
        score = (skill_match * 0.5) + (availability * 0.3) + (performance * 0.2)
        
        return score
    
    async def allocate_tasks(self, task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate tasks to employees based on skills and availability."""
        try:
            logger.info("Starting task allocation process")
            
            tasks = task_analysis.get("tasks", [])
            employees = await self.get_available_employees()
            
            if not employees:
                raise Exception("No employees available for task allocation")
            
            allocations = []
            unallocated_tasks = []
            
            # Sort tasks by priority and complexity
            sorted_tasks = sorted(tasks, key=lambda t: (
                {"High": 3, "Medium": 2, "Low": 1}.get(t.get("priority", "Medium"), 2),
                {"High": 3, "Medium": 2, "Low": 1}.get(t.get("complexity", "Medium"), 2)
            ), reverse=True)
            
            # Track employee workload during allocation
            employee_workloads = {
                emp["id"]: emp.get("current_workload", 0) 
                for emp in employees
            }
            
            for task in sorted_tasks:
                best_employee = None
                best_score = 0
                
                logger.debug(f"Allocating task: {task['title']}")
                
                # Find best employee for this task
                for employee in employees:
                    # Check if employee has capacity
                    current_load = employee_workloads[employee["id"]]
                    available_capacity = employee.get("availability", 40) - current_load
                    task_hours = task.get("estimated_hours", 8)
                    
                    if available_capacity < task_hours * 0.5:  # Need at least 50% capacity
                        continue
                    
                    score = self._calculate_allocation_score(employee, task)
                    
                    if score > best_score:
                        best_score = score
                        best_employee = employee
                
                if best_employee and best_score > 0.3:  # Minimum acceptable score
                    # Create allocation
                    allocation = {
                        "task_id": task["id"],
                        "task_title": task["title"],
                        "employee_id": best_employee["id"],
                        "employee_name": best_employee["name"],
                        "employee_email": best_employee["email"],
                        "allocation_score": best_score,
                        "estimated_hours": task.get("estimated_hours", 8),
                        "priority": task.get("priority", "Medium"),
                        "skills_match": self._calculate_employee_skill_match(best_employee, task),
                        "employee_availability": self._calculate_employee_availability(best_employee),
                        "start_date": datetime.now().isoformat(),
                        "estimated_completion": self._estimate_completion_date(
                            task.get("estimated_hours", 8),
                            best_employee
                        ),
                        "status": "allocated",
                        "task_data": {
                            "title": task["title"],
                            "description": task["description"],
                            "category": task["category"],
                            "complexity": task["complexity"],
                            "priority": task["priority"],
                            "estimated_duration": f"{task.get('estimated_hours', 8)} hours",
                            "skills_required": task.get("skills_required", []),
                            "dependencies": task.get("dependencies", []),
                            "additional_details": f"Allocated based on {best_score:.2f} match score"
                        }
                    }
                    
                    allocations.append(allocation)
                    
                    # Update employee workload
                    employee_workloads[best_employee["id"]] += task.get("estimated_hours", 8)
                    
                    logger.debug(f"Allocated '{task['title']}' to {best_employee['name']} (score: {best_score:.2f})")
                
                else:
                    unallocated_tasks.append(task)
                    logger.warning(f"Could not allocate task: {task['title']}")
            
            # Store allocations in database
            if allocations:
                try:
                    await asyncio.to_thread(self.allocations_collection.insert_many, allocations)
                    logger.info(f"Stored {len(allocations)} allocations in database")
                except Exception as e:
                    logger.error(f"Error storing allocations: {str(e)}")
            
            allocation_summary = {
                "total_tasks": len(tasks),
                "allocated_tasks": len(allocations),
                "unallocated_tasks": len(unallocated_tasks),
                "allocation_rate": len(allocations) / len(tasks) if tasks else 0,
                "total_estimated_hours": sum(alloc["estimated_hours"] for alloc in allocations),
                "employees_involved": len(set(alloc["employee_id"] for alloc in allocations)),
                "average_allocation_score": sum(alloc["allocation_score"] for alloc in allocations) / len(allocations) if allocations else 0
            }
            
            logger.info(f"Task allocation completed: {allocation_summary['allocated_tasks']}/{allocation_summary['total_tasks']} tasks allocated")
            
            return {
                "agent": self.agent_name,
                "allocation_summary": allocation_summary,
                "allocations": allocations,
                "unallocated_tasks": unallocated_tasks,
                "employee_utilization": self._calculate_employee_utilization(employees, employee_workloads),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Task allocation failed: {str(e)}")
            return {
                "agent": self.agent_name,
                "error": str(e),
                "status": "failed"
            }
    
    def _estimate_completion_date(self, estimated_hours: int, employee: Dict[str, Any]) -> str:
        """Estimate task completion date based on employee availability."""
        available_hours_per_day = (employee.get("availability", 40) - employee.get("current_workload", 0)) / 5
        
        if available_hours_per_day <= 0:
            available_hours_per_day = 2  # Minimum assumption
        
        days_needed = max(1, estimated_hours / available_hours_per_day)
        completion_date = datetime.now() + timedelta(days=days_needed)
        
        return completion_date.isoformat()
    
    def _calculate_employee_utilization(self, employees: List[Dict[str, Any]], workloads: Dict[str, float]) -> List[Dict[str, Any]]:
        """Calculate employee utilization after allocation."""
        utilization = []
        
        for employee in employees:
            emp_id = employee["id"]
            total_capacity = employee.get("availability", 40)
            new_workload = workloads.get(emp_id, employee.get("current_workload", 0))
            utilization_rate = new_workload / total_capacity if total_capacity > 0 else 0
            
            utilization.append({
                "employee_id": emp_id,
                "employee_name": employee["name"],
                "total_capacity": total_capacity,
                "allocated_hours": new_workload,
                "utilization_rate": utilization_rate,
                "status": "overloaded" if utilization_rate > 1.0 else "fully_utilized" if utilization_rate > 0.9 else "available"
            })
        
        return utilization
    
    async def send_allocation_notifications(self, allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare allocation data for email notifications."""
        try:
            logger.info(f"Preparing allocation notifications for {len(allocations)} allocations")
            
            # Group allocations by employee
            employee_allocations = {}
            for allocation in allocations:
                emp_email = allocation["employee_email"]
                if emp_email not in employee_allocations:
                    employee_allocations[emp_email] = []
                employee_allocations[emp_email].append(allocation)
            
            # Prepare notification data
            notification_data = []
            for employee_email, emp_allocations in employee_allocations.items():
                for allocation in emp_allocations:
                    notification_data.append({
                        "employee_email": employee_email,
                        "task_data": allocation["task_data"]
                    })
            
            logger.info(f"Prepared {len(notification_data)} notifications for {len(employee_allocations)} employees")
            
            return {
                "notification_data": notification_data,
                "employees_count": len(employee_allocations),
                "total_notifications": len(notification_data),
                "status": "prepared"
            }
            
        except Exception as e:
            logger.error(f"Error preparing allocation notifications: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def run(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for the Employee Allocator Agent."""
        try:
            logger.info("Employee Allocator Agent starting execution")
            
            # Analyze architecture and extract tasks
            task_analysis = await self.analyze_architecture_for_tasks(architecture)
            
            if task_analysis.get("status") == "failed":
                return task_analysis
            
            # Allocate tasks to employees
            allocation_result = await self.allocate_tasks(task_analysis)
            
            if allocation_result.get("status") == "failed":
                return allocation_result
            
            # Prepare notification data
            allocations = allocation_result.get("allocations", [])
            notification_result = await self.send_allocation_notifications(allocations)
            
            # Combine results
            result = {
                "agent": self.agent_name,
                "task_analysis": task_analysis,
                "allocation_result": allocation_result,
                "notification_preparation": notification_result,
                "status": "completed"
            }
            
            logger.info("Employee Allocator Agent execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Employee Allocator Agent execution failed: {str(e)}")
            return {
                "agent": self.agent_name,
                "error": str(e),
                "status": "failed"
            }
