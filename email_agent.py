# email_agent.py
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailAgent:
    """Complete Email Agent with ALL Required Methods"""
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Default credentials
        self.default_smtp_username = "sudharaju6143@gmail.com"
        self.default_smtp_password = "zkgaybvfsbjeuudh"  # App password
    
    def detect_email_type(self, user_message):
        """Detect what type of email the user wants to send"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['birthday', 'party', 'celebrate', 'invite', 'invitation']):
            return 'birthday_invitation'
        elif any(word in message_lower for word in ['meet', 'meeting', 'hod', 'professor', 'sir', 'madam', 'discuss', 'appointment']):
            return 'professional_meeting'
        elif any(word in message_lower for word in ['thank', 'thanks', 'grateful', 'appreciation']):
            return 'thank_you'
        elif any(word in message_lower for word in ['complain', 'complaint', 'issue', 'problem']):
            return 'complaint'
        elif any(word in message_lower for word in ['job', 'application', 'resume', 'cv', 'hire']):
            return 'job_application'
        elif any(word in message_lower for word in ['casual', 'friend', 'hi ', 'hello', 'hey', 'catch up']):
            return 'casual'
        else:
            return 'general'

    def _extract_date_time(self, user_message, email_info):
        """Extract date and time from user message"""
        # Date patterns
        date_patterns = [
            r'(\d{1,2}\s+(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)\s+\d{4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        # Time patterns
        time_patterns = [
            r'(\d{1,2}[\s]*[\'o\']?[\s]*clock[\s]*(?:noon|morning|afternoon|evening|night)?)',
            r'(\d{1,2}:\d{2}\s*(?:am|pm))',
            r'(\d{1,2}\s*(?:am|pm))'
        ]
        
        # Extract date
        for pattern in date_patterns:
            date_match = re.search(pattern, user_message.lower())
            if date_match:
                email_info['date'] = date_match.group(1).title()
                break
        
        # Extract time  
        for pattern in time_patterns:
            time_match = re.search(pattern, user_message.lower())
            if time_match:
                email_info['time'] = time_match.group(1).title()
                break
        
        return email_info

    def _extract_main_content(self, user_message, email_type):
        """Extract the main message content from user input"""
        # Remove common email patterns to get the actual message
        patterns_to_remove = [
            r'send email to', r'write mail to', r'email to', r'mail to',
            r'write a mail', r'write an email', r'send a mail',
            r'to\s+\w+@\w+\.\w+', r'\b\w+@\w+\.\w+\b'
        ]
        
        content = user_message
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content.strip()

    def _parse_professional_details(self, user_message):
        """Parse details for professional emails"""
        details = {
            'recipient_name': 'Respected Sir/Madam',
            'recipient_title': 'Head of Department',
            'subject': 'Meeting Request',
            'purpose': 'to discuss an important matter',
            'sender_department': 'Computer Science and Engineering',
            'college_name': 'Your College'
        }
        
        # Extract recipient information
        if 'hod' in user_message.lower() or 'head of department' in user_message.lower():
            details['recipient_title'] = 'Head of Department'
            details['recipient_name'] = 'Respected Sir/Madam'
            details['subject'] = 'Meeting Request with HOD - CSE Department'
        elif 'professor' in user_message.lower():
            details['recipient_title'] = 'Professor'
            details['recipient_name'] = 'Respected Professor'
            details['subject'] = 'Meeting Request with Professor'
        
        # Extract purpose
        if 'project' in user_message.lower():
            details['purpose'] = 'to discuss my academic project'
        elif 'guidance' in user_message.lower():
            details['purpose'] = 'to seek your valuable guidance'
        elif 'academic' in user_message.lower():
            details['purpose'] = 'regarding academic matters'
        
        return details

    def _parse_birthday_details(self, user_message):
        """Parse details for birthday invitations"""
        details = {
            'subject': 'You\'re Invited! Birthday Party 🎉',
            'venue': 'SV Hotel',
            'location': 'Parlakhimundi',
            'friend_name': 'Friend',
            'occasion': 'my birthday'
        }
        
        # Extract venue/location
        if 'sv hotel' in user_message.lower():
            details['venue'] = 'SV Hotel'
        if 'parlakhimundi' in user_message.lower():
            details['location'] = 'Parlakhimundi'
        
        return details

    def _parse_casual_details(self, user_message):
        """Parse details for casual emails"""
        details = {
            'subject': 'Hello!',
            'friend_name': 'Friend',
            'purpose': 'just to catch up'
        }
        
        return details

    def _parse_thank_you_details(self, user_message):
        """Parse details for thank you emails"""
        details = {
            'subject': 'Thank You',
            'recipient_name': 'Respected Sir/Madam',
            'reason': 'your help and support',
            'gratitude_level': 'sincere'
        }
        
        if 'professor' in user_message.lower():
            details['recipient_name'] = 'Respected Professor'
            details['subject'] = 'Thank You Note'
        elif 'friend' in user_message.lower():
            details['recipient_name'] = 'Dear Friend'
            details['subject'] = 'Thanks!'
        
        return details

    def _parse_complaint_details(self, user_message):
        """Parse details for complaint emails"""
        details = {
            'subject': 'Complaint Regarding Services',
            'recipient_name': 'Respected Sir/Madam',
            'issue': 'the mentioned problem',
            'urgency': 'kind attention'
        }
        
        return details

    def _parse_job_application_details(self, user_message):
        """Parse details for job application emails"""
        details = {
            'subject': 'Job Application',
            'recipient_name': 'Hiring Manager',
            'position': 'the available position',
            'experience': 'relevant experience and skills'
        }
        
        return details

    def _parse_general_details(self, user_message):
        """Parse details for general emails"""
        details = {
            'subject': 'Important Message',
            'recipient_name': 'Respected Sir/Madam',
            'purpose': 'to share important information'
        }
        
        return details

    def _get_default_email_info(self):
        """Get default email structure"""
        return {
            'email_type': 'general',
            'recipient_email': 'recipient@example.com',
            'recipient_name': 'Respected Sir/Madam',
            'subject': 'Important Message',
            'purpose': 'to share important information',
            'date': '',
            'time': '',
            'sender_name': 'Student'
        }

    def parse_email_request(self, user_message):
        """Intelligently parse user message to extract email details"""
        try:
            email_type = self.detect_email_type(user_message)
            
            # Common fields for ALL email types
            email_info = {
                'email_type': email_type,
                'recipient_email': '',
                'subject': '',
                'sender_name': 'Student',
                'date': '',
                'time': '',
                'location': '',
                'main_content': self._extract_main_content(user_message, email_type)
            }
            
            # Extract email address
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_message)
            if email_match:
                email_info['recipient_email'] = email_match.group(0)
            
            # Extract date and time
            email_info = self._extract_date_time(user_message, email_info)
            
            # Type-specific parsing
            if email_type == 'professional_meeting':
                email_info.update(self._parse_professional_details(user_message))
            elif email_type == 'birthday_invitation':
                email_info.update(self._parse_birthday_details(user_message))
            elif email_type == 'thank_you':
                email_info.update(self._parse_thank_you_details(user_message))
            elif email_type == 'complaint':
                email_info.update(self._parse_complaint_details(user_message))
            elif email_type == 'job_application':
                email_info.update(self._parse_job_application_details(user_message))
            elif email_type == 'casual':
                email_info.update(self._parse_casual_details(user_message))
            else:
                email_info.update(self._parse_general_details(user_message))
            
            return email_info
            
        except Exception as e:
            print(f"Error parsing email request: {e}")
            return self._get_default_email_info()

    def _build_datetime_string(self, email_info):
        """Build date-time string for emails"""
        if email_info['date'] and email_info['time']:
            return f"on {email_info['date']} at {email_info['time']}"
        elif email_info['date']:
            return f"on {email_info['date']}"
        elif email_info['time']:
            return f"at {email_info['time']}"
        else:
            return "at your earliest convenience"

    def _compose_professional_email(self, email_info):
        """Compose professional meeting request email"""
        salutation = email_info.get('recipient_name', 'Dear Sir/Madam')
        
        # Build date and time string
        date_time = self._build_datetime_string(email_info)
        
        email_body = f"""Subject: {email_info['subject']}

{salutation},

I hope this email finds you well.

I am {email_info['sender_name']}, a student from the {email_info['sender_department']} Department. I am writing to request a meeting with you {email_info['purpose']}.

I would be grateful if we could schedule a meeting {date_time}. Please let me know if this time is convenient for you, or kindly suggest an alternative time that works with your schedule.

Thank you for your time and consideration. I look forward to your positive response.

Yours sincerely,
{email_info['sender_name']}
{email_info['sender_department']} Department
{email_info['college_name']}"""

        return email_body.strip()

    def _compose_birthday_invitation(self, email_info):
        """Compose birthday party invitation email"""
        subject = email_info.get('subject', 'Birthday Party Invitation! 🎉')
        
        email_body = f"""Subject: {subject}

Hi {email_info.get('friend_name', 'Friend')}!

Hope you're doing well!

I'm excited to invite you to my birthday party! It would mean a lot to me if you could come and celebrate with me.

Here are the details:
• **When:** {email_info.get('date', '1 June 2026')} at {email_info.get('time', "6 o'clock")}
• **Where:** {email_info.get('venue', 'SV Hotel')} in {email_info.get('location', 'Parlakhimundi')}

It's going to be a fun evening with good food and great company. Please do come – the more, the merrier!

Let me know if you can make it so I can finalize the plans.

Can't wait to celebrate with you!

Best,
{email_info['sender_name']}"""

        return email_body.strip()

    def _compose_casual_email(self, email_info):
        """Compose casual email to friend"""
        email_body = f"""Subject: {email_info.get('subject', 'Hello!')}

Hi {email_info.get('friend_name', 'Friend')}!

Hope you're doing well. {email_info.get('purpose', 'Just wanted to catch up!')}

Let me know when you're free to chat!

Best,
{email_info['sender_name']}"""

        return email_body.strip()

    def _compose_thank_you_email(self, email_info):
        """Compose thank you email"""
        email_body = f"""Subject: {email_info['subject']}

{email_info['recipient_name']},

I hope this message finds you well.

I am writing to express my {email_info['gratitude_level']} thanks for {email_info['reason']}. 
{email_info.get('main_content', 'I truly appreciate your assistance and support.')}

Your help has been invaluable, and I am very grateful for your time and consideration.

Thank you once again for everything.

Warm regards,
{email_info['sender_name']}"""

        return email_body.strip()

    def _compose_complaint_email(self, email_info):
        """Compose complaint email"""
        email_body = f"""Subject: {email_info['subject']}

{email_info['recipient_name']},

I hope this email finds you well.

I am writing to bring to your {email_info['urgency']} regarding {email_info['issue']}. 
{email_info.get('main_content', 'I have been facing some issues that require your immediate attention.')}

I would appreciate it if you could look into this matter and provide a resolution at the earliest.

Thank you for your understanding and cooperation.

Sincerely,
{email_info['sender_name']}"""

        return email_body.strip()

    def _compose_job_application_email(self, email_info):
        """Compose job application email"""
        email_body = f"""Subject: {email_info['subject']} - {email_info['position']}

{email_info['recipient_name']},

I hope this email finds you well.

I am writing to express my interest in {email_info['position']} at your organization. 
{email_info.get('main_content', 'I believe my qualifications and experience make me a strong candidate for this role.')}

I have attached my resume for your review and would welcome the opportunity to discuss how my skills and experiences align with your requirements.

Thank you for considering my application. I look forward to the possibility of contributing to your team.

Best regards,
{email_info['sender_name']}"""

        return email_body.strip()

    def _compose_general_email(self, email_info):
        """Compose general purpose email"""
        email_body = f"""Subject: {email_info['subject']}

{email_info['recipient_name']},

I hope this email finds you well.

{email_info.get('main_content', 'I am writing to share some important information with you.')}

Please let me know if you need any further details or clarification.

Best regards,
{email_info['sender_name']}"""

        return email_body.strip()

    def compose_email(self, email_info):
        """Compose appropriate email based on detected type"""
        if email_info['email_type'] == 'professional_meeting':
            return self._compose_professional_email(email_info)
        elif email_info['email_type'] == 'birthday_invitation':
            return self._compose_birthday_invitation(email_info)
        elif email_info['email_type'] == 'thank_you':
            return self._compose_thank_you_email(email_info)
        elif email_info['email_type'] == 'complaint':
            return self._compose_complaint_email(email_info)
        elif email_info['email_type'] == 'job_application':
            return self._compose_job_application_email(email_info)
        elif email_info['email_type'] == 'casual':
            return self._compose_casual_email(email_info)
        else:
            return self._compose_general_email(email_info)

    def generate_email_preview(self, user_message):
        """Generate email preview for user confirmation"""
        try:
            email_info = self.parse_email_request(user_message)
            email_body = self.compose_email(email_info)
            
            email_type_display = {
                'professional_meeting': '📊 Professional Meeting Request',
                'birthday_invitation': '🎉 Birthday Party Invitation',
                'thank_you': '🙏 Thank You Email',
                'complaint': '⚠️ Complaint Email',
                'job_application': '💼 Job Application',
                'casual': '💬 Casual Message',
                'general': '📧 General Email'
            }
            
            preview = f"""
{email_type_display.get(email_info['email_type'], '📧 EMAIL')}

**To:** {email_info['recipient_email']}
**Subject:** {email_info['subject']}

**Message:**
{email_body}

---
*Detected as: {email_info['email_type'].replace('_', ' ').title()}*
"""
            return preview
            
        except Exception as e:
            return f"❌ Error composing email: {str(e)}"

    def send_email_auto(self, user_message):
        """Automatically send ANY type of email"""
        try:
            # Parse the email request
            email_info = self.parse_email_request(user_message)
            
            # Check if we have a recipient email
            if not email_info['recipient_email']:
                return "❌ No recipient email address found. Please specify an email address in your request."
            
            # Compose the email
            email_body = self.compose_email(email_info)
            
            # Extract subject from email body (first line)
            subject_line = email_body.split('\n')[0]
            subject = subject_line.replace('Subject: ', '').strip()
            message_body = '\n'.join(email_body.split('\n')[2:])  # Remove subject line
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.default_smtp_username
            msg['To'] = email_info['recipient_email']
            msg['Subject'] = subject
            
            # Add email body
            msg.attach(MIMEText(message_body, 'plain'))
            
            # Send email
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.default_smtp_username, self.default_smtp_password)
                server.send_message(msg)
                server.quit()
                
                email_type_name = email_info['email_type'].replace('_', ' ').title()
                return f"✅ **{email_type_name} SENT SUCCESSFULLY!**\n\n📧 **To:** {email_info['recipient_email']}\n📋 **Subject:** {subject}\n\nYour {email_type_name.lower()} has been sent successfully!"
                
            except smtplib.SMTPAuthenticationError:
                return "❌ SMTP Authentication Failed. Please check your email credentials."
            except Exception as e:
                return f"❌ Failed to send email: {str(e)}"
                
        except Exception as e:
            return f"❌ Error processing email request: {str(e)}"

# Test the COMPLETE email agent
def test_complete_email_agent():
    """Test the complete email agent with ALL email types"""
    email_agent = EmailAgent()
    
    test_messages = [
        # Birthday invitation
        "write a mail to friend invite you to my birthday party on 1 june 2026 in sv hotel in parlakhimundi in the evening , the party start onward 6 'o' clock . the mail is nm8879402@gmail.com",
        
        # Thank you email
        "send thank you email to professor@college.edu for helping me with my project",
        
        # Complaint email
        "write a complaint email to support@company.com about the poor service I received",
        
        # Job application
        "send job application email to hr@company.com for software developer position",
        
        # Casual message
        "send a casual email to my friend john@gmail.com just to say hi",
        
        # General email
        "email to info@website.com requesting more information about your services"
    ]
    
    print("🧪 Testing COMPLETE Email Agent - ALL Email Types...")
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"💬 Test {i}: {message}")
        print(f"{'='*60}")
        
        # Test detection
        email_type = email_agent.detect_email_type(message)
        print(f"🔍 Detected Type: {email_type}")
        
        # Test preview
        preview = email_agent.generate_email_preview(message)
        print("📧 PREVIEW:")
        print(preview)
        
        print(f"{'='*60}")

if __name__ == "__main__":
    test_complete_email_agent()