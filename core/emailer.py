"""SMTP client for sending emails."""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from loguru import logger
from config import settings
import resend

class EmailManager:
    """Manages email sending via SMTP and Resend API."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM
        
        # Initialize Resend if API key is available
        if hasattr(settings, 'RESEND_API_KEY') and settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.use_resend = True
            logger.info("EmailManager initialized with Resend API")
        else:
            self.use_resend = False
            logger.info(f"EmailManager initialized with SMTP: {self.smtp_server}:{self.smtp_port}")
    
    async def send_email_smtp(self, to_emails: List[str], subject: str, body: str, 
                             html_body: Optional[str] = None) -> Dict[str, Any]:
        """Send email using SMTP."""
        try:
            logger.info(f"Sending email via SMTP to {len(to_emails)} recipients")
            logger.debug(f"Subject: {subject}")
            logger.debug(f"Recipients: {to_emails}")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text part
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML part if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                failed_recipients = []
                successful_recipients = []
                
                for email in to_emails:
                    try:
                        server.send_message(msg, to_addrs=[email])
                        successful_recipients.append(email)
                        logger.debug(f"Email sent successfully to {email}")
                    except Exception as e:
                        failed_recipients.append({'email': email, 'error': str(e)})
                        logger.error(f"Failed to send email to {email}: {str(e)}")
            
            logger.info(f"Email sending completed. Success: {len(successful_recipients)}, Failed: {len(failed_recipients)}")
            
            return {
                'method': 'SMTP',
                'subject': subject,
                'total_recipients': len(to_emails),
                'successful_recipients': successful_recipients,
                'failed_recipients': failed_recipients,
                'status': 'completed' if not failed_recipients else 'partial_failure'
            }
            
        except Exception as e:
            logger.error(f"SMTP email sending failed: {str(e)}")
            return {
                'method': 'SMTP',
                'subject': subject,
                'total_recipients': len(to_emails),
                'error': str(e),
                'status': 'failed'
            }
    
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
            else:
                return await self.send_email_smtp(to_emails, subject, body, html_body)
                
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

# Global email manager instance
email_manager = EmailManager()
import os
import resend
#TODO : Implement email sending logic using Resend API
resend.api_key = os.environ["RESEND_API_KEY"]

params: resend.Emails.SendParams = {
    "from": "Zenith <zenith@noreply.anirban-majumder.xyz>",
    "to": ["delivered@resend.dev"],
    "subject": "hello world",
    "html": "<strong>it works!</strong>",
}

email = resend.Emails.send(params)
print(email)