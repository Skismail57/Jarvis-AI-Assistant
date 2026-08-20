"""
Advanced Email Processing Module
Provides email summarization, drafting, prioritization, and smart responses.
"""

import os
import re
import json
import base64
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests


@dataclass
class EmailSummary:
    subject: str
    sender: str
    summary: str
    key_points: List[str]
    action_items: List[str]
    priority: str
    category: str
    sentiment: str
    suggested_response: Optional[str] = None
    urgency: str = "normal"


@dataclass
class EmailDraft:
    to: str
    subject: str
    body: str
    cc: List[str] = None
    bcc: List[str] = None
    attachments: List[str] = None
    tone: str = "professional"


@dataclass
class EmailAction:
    action_type: str  # reply, forward, archive, delete, label, schedule
    email_id: str
    parameters: Dict[str, Any]
    confidence: float


class EmailProcessor:
    def __init__(self, llm_core=None):
        self.llm = llm_core
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.email_cache_file = os.path.join(self.base_dir, "data", "email_cache.json")
        self.email_cache = self._load_cache()
        
        # Gmail API setup
        self.gmail_service = None
        self._setup_gmail_api()
        
        # Priority keywords
        self.urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 
                               'deadline', 'time sensitive', 'important', 'priority']
        self.high_priority_keywords = ['important', 'review', 'approval', 'meeting', 
                                       'action required', 'response needed']
        
        # Category patterns
        self.category_patterns = {
            'work': ['project', 'meeting', 'deadline', 'client', 'report', 'proposal'],
            'personal': ['personal', 'family', 'friend', 'birthday', 'vacation'],
            'finance': ['invoice', 'payment', 'receipt', 'budget', 'expense', 'billing'],
            'newsletter': ['unsubscribe', 'newsletter', 'update', 'digest', 'weekly'],
            'social': ['invitation', 'event', 'party', 'social', 'network'],
            'support': ['support', 'help', 'ticket', 'issue', 'problem', 'error']
        }

    def _load_cache(self) -> Dict:
        """Load email cache from disk."""
        if os.path.exists(self.email_cache_file):
            try:
                with open(self.email_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        """Save email cache to disk."""
        try:
            with open(self.email_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.email_cache, f, indent=2)
        except Exception:
            pass

    def _setup_gmail_api(self):
        """Setup Gmail API service."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                     'https://www.googleapis.com/auth/gmail.send',
                     'https://www.googleapis.com/auth/gmail.modify']
            
            creds_file = os.path.join(self.base_dir, 'data', 'gmail_credentials.json')
            token_file = os.path.join(self.base_dir, 'data', 'gmail_token.json')
            
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            elif os.path.exists(creds_file):
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            else:
                print("[EmailProcessor] Gmail credentials not found. Email features limited.")
                return
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            print("[EmailProcessor] Gmail API connected successfully.")
            
        except Exception as e:
            print(f"[EmailProcessor] Gmail API setup failed: {e}")

    def get_recent_emails(self, max_results: int = 20, unread_only: bool = False) -> List[Dict]:
        """Fetch recent emails from Gmail."""
        if not self.gmail_service:
            return []
        
        try:
            query = 'is:unread' if unread_only else ''
            results = self.gmail_service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                msg_data = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                email = self._parse_gmail_message(msg_data)
                emails.append(email)
            
            return emails
            
        except Exception as e:
            print(f"[EmailProcessor] Failed to fetch emails: {e}")
            return []

    def _parse_gmail_message(self, msg_data: Dict) -> Dict:
        """Parse Gmail message data."""
        headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
        
        # Extract email body
        body = self._extract_email_body(msg_data['payload'])
        
        return {
            'id': msg_data['id'],
            'thread_id': msg_data.get('threadId'),
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'date': headers.get('Date', ''),
            'body': body,
            'snippet': msg_data.get('snippet', ''),
            'labels': msg_data.get('labelIds', [])
        }

    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Simple HTML to text conversion
                        import re
                        text = re.sub('<[^<]+?>', '', html)
                        return text.strip()
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return ''

    def summarize_email(self, email: Dict) -> EmailSummary:
        """Generate a comprehensive summary of an email."""
        subject = email.get('subject', '')
        sender = email.get('from', '')
        body = email.get('body', '')
        
        # Check cache
        cache_key = f"summary_{email.get('id', '')}"
        if cache_key in self.email_cache:
            cached = self.email_cache[cache_key]
            if datetime.now() - datetime.fromisoformat(cached['timestamp']) < timedelta(hours=24):
                return EmailSummary(**cached['data'])
        
        # Analyze priority
        priority = self._determine_priority(subject, body)
        
        # Categorize email
        category = self._categorize_email(subject, body)
        
        # Analyze sentiment
        sentiment =self._analyze_sentiment(subject + ' ' + body)
        
        # Generate summary using LLM if available
        if self.llm:
            summary, key_points, action_items = self._llm_summarize(subject, body, sender)
        else:
            summary, key_points, action_items = self._rule_based_summarize(subject, body)
        
        # Determine urgency
        urgency = self._determine_urgency(priority, action_items)
        
        # Generate suggested response
        suggested_response = None
        if self.llm:
            suggested_response = self._generate_suggested_response(subject, body, sender)
        
        email_summary = EmailSummary(
            subject=subject,
            sender=sender,
            summary=summary,
            key_points=key_points,
            action_items=action_items,
            priority=priority,
            category=category,
            sentiment=sentiment,
            suggested_response=suggested_response,
            urgency=urgency
        )
        
        # Cache result
        self.email_cache[cache_key] = {
            'data': asdict(email_summary),
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
        
        return email_summary

    def _determine_priority(self, subject: str, body: str) -> str:
        """Determine email priority based on content."""
        text = (subject + ' ' + body).lower()
        
        if any(keyword in text for keyword in self.urgent_keywords):
            return 'urgent'
        elif any(keyword in text for keyword in self.high_priority_keywords):
            return 'high'
        else:
            return 'normal'

    def _categorize_email(self, subject: str, body: str) -> str:
        """Categorize email based on content patterns."""
        text = (subject + ' ' + body).lower()
        
        scores = {}
        for category, keywords in self.category_patterns.items():
            scores[category] = sum(1 for keyword in keywords if keyword in text)
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of email content."""
        text_lower = text.lower()
        
        positive_words = ['thank', 'thanks', 'appreciate', 'great', 'good', 'excellent', 
                         'happy', 'pleased', 'wonderful', 'love', 'excited']
        negative_words = ['angry', 'frustrated', 'disappointed', 'unhappy', 'sad', 
                         'concern', 'worry', 'problem', 'issue', 'error', 'fail']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _llm_summarize(self, subject: str, body: str, sender: str) -> Tuple[str, List[str], List[str]]:
        """Use LLM to generate summary, key points, and action items."""
        prompt = f"""
        Analyze this email and provide:
        1. A concise 2-3 sentence summary
        2. 3-5 key bullet points
        3. Any action items or tasks mentioned
        
        Subject: {subject}
        From: {sender}
        Body: {body[:2000]}
        
        Format your response as:
        SUMMARY: [your summary]
        KEY_POINTS: [bullet points]
        ACTION_ITEMS: [action items]
        """
        
        try:
            response = self.llm.answer(prompt)
            text = response.text
            
            # Parse response
            summary = ""
            key_points = []
            action_items = []
            
            current_section = None
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('SUMMARY:'):
                    current_section = 'summary'
                    summary = line.replace('SUMMARY:', '').strip()
                elif line.startswith('KEY_POINTS:'):
                    current_section = 'key_points'
                elif line.startswith('ACTION_ITEMS:'):
                    current_section = 'action_items'
                elif line.startswith('-') or line.startswith('*'):
                    item = line.lstrip('-*').strip()
                    if current_section == 'key_points':
                        key_points.append(item)
                    elif current_section == 'action_items':
                        action_items.append(item)
                elif current_section and line:
                    if current_section == 'summary':
                        summary += ' ' + line
            
            return summary, key_points, action_items
            
        except Exception as e:
            print(f"[EmailProcessor] LLM summarization failed: {e}")
            return self._rule_based_summarize(subject, body)

    def _rule_based_summarize(self, subject: str, body: str) -> Tuple[str, List[str], List[str]]:
        """Rule-based summarization as fallback."""
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', body)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first few sentences as summary
        summary = ' '.join(sentences[:3]) if sentences else body[:500]
        
        # Extract potential key points (sentences with important keywords)
        important_keywords = ['important', 'key', 'main', 'primary', 'significant', 'note']
        key_points = [s for s in sentences if any(kw in s.lower() for kw in important_keywords)][:5]
        
        # Extract action items
        action_patterns = [r'please\s+(?:.+?)', r'need\s+to\s+(?:.+?)[^.!?]', 
                          r'action\s+(?:.+?)[^.!?]', r'required\s+(?:.+?)[^.!?]']
        action_items = []
        for pattern in action_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            action_items.extend(matches[:3])
        
        return summary, key_points[:5], action_items[:5]

    def _determine_urgency(self, priority: str, action_items: List[str]) -> str:
        """Determine urgency based on priority and action items."""
        if priority == 'urgent':
            return 'immediate'
        elif action_items and priority == 'high':
            return 'high'
        elif action_items:
            return 'normal'
        else:
            return 'low'

    def _generate_suggested_response(self, subject: str, body: str, sender: str) -> str:
        """Generate a suggested response using LLM."""
        prompt = f"""
        Generate a professional, concise email response to this message.
        Keep it under 200 words and maintain a helpful, professional tone.
        
        Subject: {subject}
        From: {sender}
        Body: {body[:1500]}
        """
        
        try:
            response = self.llm.answer(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[EmailProcessor] Response generation failed: {e}")
            return None

    def draft_email(self, instruction: str, context: Dict = None) -> EmailDraft:
        """
        Draft an email based on natural language instruction.
        
        Args:
            instruction: Natural language instruction (e.g., "Send a meeting request to John about the project")
            context: Additional context (previous emails, user info, etc.)
        """
        if not self.llm:
            raise RuntimeError("LLM required for email drafting")
        
        prompt = f"""
        Draft an email based on this instruction: {instruction}
        
        Context: {json.dumps(context) if context else 'None'}
        
        Extract the following information and format as JSON:
        {{
            "to": "recipient email",
            "subject": "email subject",
            "body": "email body",
            "cc": ["cc emails"],
            "tone": "professional/casual/formal"
        }}
        """
        
        try:
            response = self.llm.answer(prompt)
            # Parse JSON response
            import json
            draft_data = json.loads(response.text)
            
            return EmailDraft(
                to=draft_data.get('to', ''),
                subject=draft_data.get('subject', ''),
                body=draft_data.get('body', ''),
                cc=draft_data.get('cc', []),
                tone=draft_data.get('tone', 'professional')
            )
        except Exception as e:
            print(f"[EmailProcessor] Email drafting failed: {e}")
            raise

    def send_email(self, draft: EmailDraft) -> bool:
        """Send an email using Gmail API."""
        if not self.gmail_service:
            print("[EmailProcessor] Gmail API not available")
            return False
        
        try:
            message = MIMEMultipart()
            message['to'] = draft.to
            message['subject'] = draft.subject
            
            if draft.cc:
                message['cc'] = ', '.join(draft.cc)
            
            message.attach(MIMEText(draft.body, 'plain'))
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message_body = {'raw': raw}
            
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=message_body
            ).execute()
            
            print(f"[EmailProcessor] Email sent successfully: {sent_message['id']}")
            return True
            
        except Exception as e:
            print(f"[EmailProcessor] Failed to send email: {e}")
            return False

    def batch_summarize_emails(self, emails: List[Dict]) -> List[EmailSummary]:
        """Summarize multiple emails in batch."""
        summaries = []
        for email in emails:
            try:
                summary = self.summarize_email(email)
                summaries.append(summary)
            except Exception as e:
                print(f"[EmailProcessor] Failed to summarize email {email.get('id')}: {e}")
                continue
        return summaries

    def get_email_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get email statistics for the past N days."""
        if not self.gmail_service:
            return {}
        
        try:
            from datetime import datetime, timedelta
            date_since = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            
            query = f'after:{date_since}'
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            total_emails = len(results.get('messages', []))
            
            # Get unread count
            unread_results = self.gmail_service.users().messages().list(
                userId='me',
                q=f'{query} is:unread'
            ).execute()
            unread_count = len(unread_results.get('messages', []))
            
            return {
                'total_emails': total_emails,
                'unread_emails': unread_count,
                'days': days,
                'date_range': f"Last {days} days"
            }
            
        except Exception as e:
            print(f"[EmailProcessor] Failed to get statistics: {e}")
            return {}

    def suggest_email_actions(self, email: Dict) -> List[EmailAction]:
        """Suggest actions for an email based on its content."""
        summary = self.summarize_email(email)
        actions = []
        
        # Suggest reply if action items exist
        if summary.action_items:
            actions.append(EmailAction(
                action_type='reply',
                email_id=email.get('id'),
                parameters={'draft_response': summary.suggested_response},
                confidence=0.8
            ))
        
        # Suggest archive if low priority and no action items
        if summary.priority == 'normal' and not summary.action_items:
            actions.append(EmailAction(
                action_type='archive',
                email_id=email.get('id'),
                parameters={},
                confidence=0.7
            ))
        
        # Suggest label based on category
        if summary.category != 'general':
            actions.append(EmailAction(
                action_type='label',
                email_id=email.get('id'),
                parameters={'label': summary.category},
                confidence=0.6
            ))
        
        # Schedule follow-up if high priority
        if summary.priority in ['urgent', 'high']:
            actions.append(EmailAction(
                action_type='schedule',
                email_id=email.get('id'),
                parameters={'follow_up_hours': 24},
                confidence=0.75
            ))
        
        return actions

    def execute_email_action(self, action: EmailAction) -> bool:
        """Execute a suggested email action."""
        if not self.gmail_service:
            return False
        
        try:
            if action.action_type == 'archive':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=action.email_id,
                    body={'removeLabelIds': ['INBOX']}
                ).execute()
                return True
            
            elif action.action_type == 'label':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=action.email_id,
                    body={'addLabelIds': [action.parameters['label'].upper()]}
                ).execute()
                return True
            
            # Other actions would require additional implementation
            return False
            
        except Exception as e:
            print(f"[EmailProcessor] Failed to execute action: {e}")
            return False
