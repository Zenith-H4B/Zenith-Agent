"""SMTP client for sending emails."""


from typing import List, Dict, Any, Optional
from loguru import logger
from config import settings
import resend

class EmailManager:
    """Manages email sending via SMTP and Resend API."""
    
    def __init__(self):
        self.email_from = settings.EMAIL_FROM
        
        # Initialize Resend if API key is available
        if hasattr(settings, 'RESEND_API_KEY') and settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.use_resend = True
            logger.info("EmailManager initialized with Resend API")
        else:
            self.use_resend = False
            logger.info(f"EmailManager initialized with SMTP: {self.smtp_server}:{self.smtp_port}")
    
    async def send_email_resend(self, to_emails: List[str], subject: str, 
                                body: str, html_body: Optional[str] = None) -> Dict[str, Any]:
        """Send email using Resend API."""
        try:
            logger.info(f"Sending email via Resend API to {len(to_emails)} recipients")
            logger.debug(f"Subject: {subject}")
            logger.debug(f"Recipients: {to_emails}")
            
            successful_recipients = []
            failed_recipients = []
            
            for email in to_emails:
                try:
                    params = {
                        "from": self.email_from,
                        "to": [email],
                        "subject": subject,
                        "text": body
                    }
                    
                    if html_body:
                        params["html"] = html_body
                    
                    response = resend.Emails.send(params)
                    successful_recipients.append(email)
                    logger.debug(f"Email sent successfully to {email} - ID: {response.get('id', 'N/A')}")
                    
                except Exception as e:
                    failed_recipients.append({'email': email, 'error': str(e)})
                    logger.error(f"Failed to send email to {email}: {str(e)}")
            
            logger.info(f"Resend email sending completed. Success: {len(successful_recipients)}, Failed: {len(failed_recipients)}")
            
            return {
                'method': 'Resend',
                'subject': subject,
                'total_recipients': len(to_emails),
                'successful_recipients': successful_recipients,
                'failed_recipients': failed_recipients,
                'status': 'completed' if not failed_recipients else 'partial_failure'
            }
            
        except Exception as e:
            logger.error(f"Resend email sending failed: {str(e)}")
            return {
                'method': 'Resend',
                'subject': subject,
                'total_recipients': len(to_emails),
                'error': str(e),
                'status': 'failed'
            }
    
    async def send_email(self, to_emails: List[str], subject: str, body: str, 
                        html_body: Optional[str] = None) -> Dict[str, Any]:
        """Send email using the preferred method (Resend or SMTP)."""
        try:
            logger.info(f"Sending email: {subject}")
            
            if self.use_resend:
                return await self.send_email_resend(to_emails, subject, body, html_body)

        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {
                'subject': subject,
                'total_recipients': len(to_emails),
                'error': str(e),
                'status': 'failed'
            }
    
    async def send_task_allocation_email(self, employee_email: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send task allocation email to an employee."""
        try:
            logger.info(f"Sending task allocation email to {employee_email}")
            
            subject = f"New Task Allocation: {task_data.get('title', 'Untitled Task')}"
            
            # Create text body
            body = f"""
Hello,

You have been allocated a new task:

Title: {task_data.get('title', 'N/A')}
Description: {task_data.get('description', 'N/A')}
Priority: {task_data.get('priority', 'Medium')}
Estimated Duration: {task_data.get('estimated_duration', 'N/A')}
Due Date: {task_data.get('due_date', 'N/A')}

Additional Details:
{task_data.get('additional_details', 'N/A')}

Please acknowledge receipt and start working on this task.

Best regards,
AI Task Allocation System
"""
            
            # Create HTML body
            html_body = f"""
<html>
<body>
    <h2>New Task Allocation</h2>
    <p>Hello,</p>
    <p>You have been allocated a new task:</p>
    
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Title</strong></td><td>{task_data.get('title', 'N/A')}</td></tr>
        <tr><td><strong>Description</strong></td><td>{task_data.get('description', 'N/A')}</td></tr>
        <tr><td><strong>Priority</strong></td><td>{task_data.get('priority', 'Medium')}</td></tr>
        <tr><td><strong>Estimated Duration</strong></td><td>{task_data.get('estimated_duration', 'N/A')}</td></tr>
        <tr><td><strong>Due Date</strong></td><td>{task_data.get('due_date', 'N/A')}</td></tr>
    </table>
    
    <h3>Additional Details:</h3>
    <p>{task_data.get('additional_details', 'N/A')}</p>
    
    <p>Please acknowledge receipt and start working on this task.</p>
    
    <p>Best regards,<br>AI Task Allocation System</p>
</body>
</html>
"""
            
            result = await self.send_email([employee_email], subject, body, html_body)
            logger.info(f"Task allocation email sent to {employee_email}: {result['status']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send task allocation email to {employee_email}: {str(e)}")
            return {
                'employee_email': employee_email,
                'error': str(e),
                'status': 'failed'
            }
    
    async def send_bulk_task_allocation_emails(self, allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send task allocation emails to multiple employees."""
        try:
            logger.info(f"Sending bulk task allocation emails to {len(allocations)} employees")
            
            results = []
            successful_sends = 0
            failed_sends = 0
            
            for allocation in allocations:
                employee_email = allocation.get('employee_email')
                task_data = allocation.get('task_data', {})
                
                if not employee_email:
                    logger.warning(f"No employee email found in allocation: {allocation}")
                    failed_sends += 1
                    continue
                
                result = await self.send_task_allocation_email(employee_email, task_data)
                results.append(result)
                
                if result['status'] in ['completed', 'partial_failure']:
                    successful_sends += 1
                else:
                    failed_sends += 1
            
            logger.info(f"Bulk email sending completed. Success: {successful_sends}, Failed: {failed_sends}")
            
            return {
                'total_allocations': len(allocations),
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'detailed_results': results,
                'status': 'completed' if failed_sends == 0 else 'partial_failure'
            }
            
        except Exception as e:
            logger.error(f"Bulk task allocation email sending failed: {str(e)}")
            return {
                'total_allocations': len(allocations),
                'error': str(e),
                'status': 'failed'
            }
    
    async def send_optimized_task_email(self, employee_email: str, task_data: Dict[str, Any], 
                                      is_simple_task: bool = False) -> Dict[str, Any]:
        """Send optimized task allocation email with urgency indicators."""
        try:
            logger.info(f"Sending optimized task email to {employee_email} (simple: {is_simple_task})")
            
            task_type = "URGENT SIMPLE TASK" if is_simple_task else "OPTIMIZED TASK ALLOCATION"
            priority_emoji = {
                "critical": "🔴",
                "high": "🟠", 
                "medium": "🟡",
                "low": "🟢"
            }
            
            priority = task_data.get('priority', 'medium')
            emoji = priority_emoji.get(priority, "🟡")
            
            subject = f"{emoji} {task_type}: {task_data.get('title', 'Untitled Task')}"
            
            # Create optimized text body
            if is_simple_task:
                body = f"""
🚀 SIMPLE TASK - QUICK ACTION REQUIRED

Hello,

You've been selected for this task based on optimal cost-efficiency analysis:

{emoji} TASK: {task_data.get('title', 'N/A')}
📝 DESCRIPTION: {task_data.get('description', 'N/A')}
⏱️ ESTIMATED TIME: {task_data.get('estimated_duration', 'N/A')}
📅 DUE: {task_data.get('due_date', 'N/A')}
🎯 PRIORITY: {priority.upper()}

💡 WHY YOU: This task was assigned to you for optimal resource utilization and cost efficiency.

🎯 ACTION: Please start immediately and confirm completion.

Additional Notes:
{task_data.get('additional_details', 'None')}

Best regards,
Optimized AI Task Allocation System
"""
            else:
                body = f"""
📋 OPTIMIZED TASK ALLOCATION

Hello,

You have been allocated a task through our profit-optimized allocation system:

{emoji} TASK: {task_data.get('title', 'N/A')}
📝 DESCRIPTION: {task_data.get('description', 'N/A')}
⏱️ ESTIMATED TIME: {task_data.get('estimated_duration', 'N/A')}
📅 DUE: {task_data.get('due_date', 'N/A')}
🎯 PRIORITY: {priority.upper()}

💼 ALLOCATION REASON: You were selected based on cost-efficiency analysis and workload optimization.

Please acknowledge receipt and begin work.

Additional Details:
{task_data.get('additional_details', 'None')}

Best regards,
Optimized AI Task Allocation System
"""
            
            # Create enhanced HTML body
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0;">{emoji} {'SIMPLE TASK' if is_simple_task else 'OPTIMIZED ALLOCATION'}</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Profit-optimized task assignment</p>
    </div>
    
    <div style="padding: 20px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
        <h2 style="color: #667eea; margin-top: 0;">{task_data.get('title', 'N/A')}</h2>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>📝 Description:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">{task_data.get('description', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>🎯 Priority:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                        <span style="background: {'#dc3545' if priority == 'critical' else '#fd7e14' if priority == 'high' else '#ffc107' if priority == 'medium' else '#28a745'}; 
                                     color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                            {priority.upper()}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>⏱️ Duration:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">{task_data.get('estimated_duration', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>📅 Due Date:</strong></td>
                    <td style="padding: 8px 0;">{task_data.get('due_date', 'N/A')}</td>
                </tr>
            </table>
        </div>
        
        {'<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 15px 0;"><strong>💡 Why you were selected:</strong> This task was assigned through our AI-powered cost-efficiency optimization system.</div>' if is_simple_task else ''}
        
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 15px 0;">
            <strong>📋 Additional Details:</strong><br>
            {task_data.get('additional_details', 'None')}
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <p style="font-size: 16px; font-weight: bold; color: #667eea;">
                {'🚀 Please start immediately!' if is_simple_task else '📝 Please acknowledge and begin work'}
            </p>
        </div>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px; text-align: center;">
            Optimized AI Task Allocation System | Zenith Agent
        </p>
    </div>
</body>
</html>
"""
            
            result = await self.send_email([employee_email], subject, body, html_body)
            logger.info(f"Optimized task email sent to {employee_email}: {result['status']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send optimized task email to {employee_email}: {str(e)}")
            return {
                'employee_email': employee_email,
                'error': str(e),
                'status': 'failed'
            }

# Global email manager instance
email_manager = EmailManager()
