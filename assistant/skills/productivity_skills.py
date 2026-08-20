import re
import base64
import mimetypes
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from ..utils.logger import logger
from ..config import settings, DATA_DIR

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    _GOOGLE_AVAILABLE = True
except ImportError:
    Credentials = None
    InstalledAppFlow = None
    Request = None
    build = None
    _GOOGLE_AVAILABLE = False

try:
    import todoist_api_python
    from todoist_api_python.api import TodoistAPI
    _TODOIST_AVAILABLE = True
except ImportError:
    TodoistAPI = None
    _TODOIST_AVAILABLE = False

try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _requests = None
    _REQUESTS_AVAILABLE = False


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]


class GmailIntegration:
    def __init__(self, credentials_file=None, token_file=None):
        self.credentials_file = credentials_file or str(DATA_DIR / "credentials.json")
        self.token_file = token_file or str(DATA_DIR / "gmail_token.json")
        self.service = None
        self._available = _GOOGLE_AVAILABLE
        if self._available:
            self.service = self._build_service()

    def _build_service(self):
        if not _GOOGLE_AVAILABLE:
            logger.debug("[Gmail] Google API packages not installed.")
            return None
        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, GMAIL_SCOPES)
            except Exception as e:
                logger.warning(f"[Gmail] Failed to load token file: {e}")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"[Gmail] Token refresh failed: {e}")
                    creds = None
            if not creds:
                if not os.path.exists(self.credentials_file):
                    logger.debug("[Gmail] credentials.json not found in data/ folder.")
                    return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, GMAIL_SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(self.token_file, "w", encoding="utf-8") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.warning(f"[Gmail] OAuth flow failed: {e}")
                    return None
        try:
            return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.warning(f"[Gmail] Service build failed: {e}")
            return None

    def send_email(self, to, subject, body, cc=None, attachments=None) -> Dict[str, Any]:
        if self.service is None:
            return {"success": False, "error": "Gmail API not configured. Enable it by placing credentials.json in the data/ folder."}
        try:
            if attachments:
                message = MIMEMultipart()
                message.attach(MIMEText(body, "plain"))
            else:
                message = MIMEText(body, "plain")
            message["to"] = to
            message["subject"] = subject
            if cc:
                message["cc"] = cc
            if attachments:
                for att_path in attachments:
                    if not os.path.isfile(att_path):
                        continue
                    ctype, encoding = mimetypes.guess_type(att_path)
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"
                    maintype, subtype = ctype.split("/", 1)
                    with open(att_path, "rb") as fp:
                        part = MIMEBase(maintype, subtype)
                        part.set_payload(fp.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(att_path)}")
                    message.attach(part)
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            result = self.service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return {"success": True, "message_id": result.get("id")}
        except Exception as e:
            logger.warning(f"[Gmail] send_email failed: {e}")
            return {"success": False, "error": str(e)}

    def search_inbox(self, query="", max_results=10) -> List[Dict[str, Any]]:
        if self.service is None:
            return []
        try:
            results = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])
            out = []
            for m in messages:
                msg = self.service.users().messages().get(userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                out.append({
                    "id": m["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", "(no subject)"),
                    "snippet": msg.get("snippet", ""),
                    "date": headers.get("Date", ""),
                })
            return out
        except Exception as e:
            logger.warning(f"[Gmail] search_inbox failed: {e}")
            return []

    def read_email(self, message_id) -> Dict[str, Any]:
        if self.service is None:
            return {"error": "Gmail API not configured. Enable it by placing credentials.json in the data/ folder."}
        try:
            msg = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
            payload = msg.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
            body_plain = ""
            attachments = []

            def walk_parts(parts):
                nonlocal body_plain
                text_parts = []
                for part in parts:
                    mime = part.get("mimeType", "")
                    if mime == "text/plain":
                        data = part.get("body", {}).get("data")
                        if data:
                            text_parts.append(base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"))
                    elif mime == "text/html" and not text_parts:
                        pass
                    elif "attachmentId" in part.get("body", {}):
                        att_id = part["body"]["attachmentId"]
                        att = self.service.users().messages().attachments().get(userId="me", messageId=message_id, id=att_id).execute()
                        filename = part.get("filename", "attachment")
                        attachments.append({"filename": filename, "size": att.get("size", 0), "attachment_id": att_id})
                    sub = part.get("parts")
                    if sub:
                        text_parts.extend(walk_parts(sub))
                return text_parts

            if "parts" in payload:
                parts_text = walk_parts(payload["parts"])
                if parts_text:
                    body_plain = parts_text[0]
            else:
                data = payload.get("body", {}).get("data")
                if data:
                    body_plain = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

            return {
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "body_plain": body_plain,
                "attachments": attachments,
            }
        except Exception as e:
            logger.warning(f"[Gmail] read_email failed: {e}")
            return {"error": str(e)}

    def draft_email(self, to, subject, body) -> Dict[str, Any]:
        if self.service is None:
            return {"success": False, "error": "Gmail API not configured. Enable it by placing credentials.json in the data/ folder."}
        try:
            message = MIMEText(body, "plain")
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            draft = self.service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
            return {"success": True, "draft_id": draft.get("id")}
        except Exception as e:
            logger.warning(f"[Gmail] draft_email failed: {e}")
            return {"success": False, "error": str(e)}


class GoogleCalendarIntegration:
    def __init__(self, credentials_file=None, token_file=None):
        self.credentials_file = credentials_file or str(DATA_DIR / "credentials.json")
        self.token_file = token_file or str(DATA_DIR / "calendar_token.json")
        self.service = None
        self._available = _GOOGLE_AVAILABLE
        if self._available:
            self.service = self._build_service()

    def _build_service(self):
        if not _GOOGLE_AVAILABLE:
            logger.debug("[Calendar] Google API packages not installed.")
            return None
        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, CALENDAR_SCOPES)
            except Exception as e:
                logger.warning(f"[Calendar] Failed to load token file: {e}")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"[Calendar] Token refresh failed: {e}")
                    creds = None
            if not creds:
                if not os.path.exists(self.credentials_file):
                    logger.debug("[Calendar] credentials.json not found in data/ folder.")
                    return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, CALENDAR_SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(self.token_file, "w", encoding="utf-8") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.warning(f"[Calendar] OAuth flow failed: {e}")
                    return None
        try:
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            logger.warning(f"[Calendar] Service build failed: {e}")
            return None

    def create_event(self, summary, start_datetime, end_datetime, description="", location="", attendees=None) -> Dict[str, Any]:
        if self.service is None:
            return {"success": False, "error": "Google Calendar API not configured. Enable it by placing credentials.json in the data/ folder."}
        try:
            if isinstance(start_datetime, str):
                start_dt = datetime.fromisoformat(start_datetime)
            else:
                start_dt = start_datetime
            if isinstance(end_datetime, str):
                end_dt = datetime.fromisoformat(end_datetime)
            else:
                end_dt = end_datetime
            tz = start_dt.tzinfo or datetime.now().astimezone().tzinfo
            event = {
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start_dt.isoformat(), "timeZone": str(tz)},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": str(tz)},
            }
            if attendees:
                event["attendees"] = [{"email": a} for a in attendees]
            result = self.service.events().insert(calendarId="primary", body=event).execute()
            return {"success": True, "event_id": result.get("id"), "html_link": result.get("htmlLink", "")}
        except Exception as e:
            logger.warning(f"[Calendar] create_event failed: {e}")
            return {"success": False, "error": str(e)}

    def list_events(self, max_results=10, time_min=None) -> List[Dict[str, Any]]:
        if self.service is None:
            return []
        try:
            if time_min is None:
                time_min_dt = datetime.utcnow()
            elif isinstance(time_min, str):
                time_min_dt = datetime.fromisoformat(time_min)
            else:
                time_min_dt = time_min
            tm = time_min_dt if time_min_dt.tzinfo else time_min_dt.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=tm.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = events_result.get("items", [])
            out = []
            for e in events:
                start = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date", "")
                end = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date", "")
                out.append({
                    "id": e.get("id"),
                    "summary": e.get("summary", "(no title)"),
                    "start": start,
                    "end": end,
                    "status": e.get("status", "confirmed"),
                })
            return out
        except Exception as e:
            logger.warning(f"[Calendar] list_events failed: {e}")
            return []

    def check_schedule(self, date_obj=None) -> List[Dict[str, Any]]:
        if date_obj is None:
            date_obj = date.today()
        elif isinstance(date_obj, str):
            try:
                date_obj = date.fromisoformat(date_obj)
            except Exception:
                date_obj = date.today()
        start_dt = datetime.combine(date_obj, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        return self.list_events(max_results=100, time_min=start_dt)

    def delete_event(self, event_id) -> bool:
        if self.service is None:
            return False
        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
            return True
        except Exception as e:
            logger.warning(f"[Calendar] delete_event failed: {e}")
            return False


class TodoistIntegration:
    def __init__(self, api_token=None):
        self.api_token = api_token or os.environ.get("TODOIST_API_TOKEN")
        self._api = None
        self._available = _TODOIST_AVAILABLE and bool(self.api_token)
        if self._available:
            try:
                self._api = TodoistAPI(self.api_token)
            except Exception as e:
                logger.warning(f"[Todoist] API init failed: {e}")
                self._available = False

    def add_task(self, content, due_string=None, priority=4) -> Dict[str, Any]:
        if not self._available or self._api is None:
            return {"success": False, "error": "Todoist not configured. Set TODOIST_API_TOKEN or pass api_token, and ensure todoist-api-python is installed."}
        try:
            kwargs = {"content": content, "priority": priority}
            if due_string:
                kwargs["due_string"] = due_string
            task = self._api.add_task(**kwargs)
            return {"success": True, "task_id": task.id if hasattr(task, "id") else task.get("id")}
        except Exception as e:
            logger.warning(f"[Todoist] add_task failed: {e}")
            return {"success": False, "error": str(e)}

    def list_tasks(self, filter_str=None) -> List[Dict[str, Any]]:
        if not self._available or self._api is None:
            return []
        try:
            kwargs = {}
            if filter_str:
                kwargs["filter"] = filter_str
            tasks = self._api.get_tasks(**kwargs)
            out = []
            for t in tasks:
                tid = getattr(t, "id", None) or (t.get("id") if isinstance(t, dict) else None)
                tcontent = getattr(t, "content", None) or (t.get("content") if isinstance(t, dict) else "")
                due = getattr(t, "due", None) or (t.get("due") if isinstance(t, dict) else None)
                out.append({
                    "id": tid,
                    "content": tcontent,
                    "due": due.string if due and hasattr(due, "string") else (due.get("string") if isinstance(due, dict) else None),
                    "priority": getattr(t, "priority", 4) or (t.get("priority", 4) if isinstance(t, dict) else 4),
                })
            return out
        except Exception as e:
            logger.warning(f"[Todoist] list_tasks failed: {e}")
            return []

    def close_task(self, task_id) -> bool:
        if not self._available or self._api is None:
            return False
        try:
            self._api.close_task(task_id=str(task_id))
            return True
        except Exception as e:
            logger.warning(f"[Todoist] close_task failed: {e}")
            return False


class SlackIntegration:
    def __init__(self, bot_token=None, webhook_url=None):
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self._base_url = "https://slack.com/api"
        self._available = _REQUESTS_AVAILABLE and (bool(self.bot_token) or bool(self.webhook_url))

    def send_message(self, channel, text, blocks=None) -> Dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Slack not configured. Set SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL."}
        try:
            if self.webhook_url:
                payload = {"text": text}
                if blocks:
                    payload["blocks"] = blocks
                resp = _requests.post(self.webhook_url, json=payload, timeout=10)
                return {"success": resp.status_code == 200, "status_code": resp.status_code}
            elif self.bot_token:
                headers = {"Authorization": f"Bearer {self.bot_token}", "Content-Type": "application/json"}
                payload = {"channel": channel, "text": text}
                if blocks:
                    payload["blocks"] = blocks
                resp = _requests.post(f"{self._base_url}/chat.postMessage", headers=headers, json=payload, timeout=10)
                data = resp.json()
                return {"success": data.get("ok", False), "data": data}
            return {"success": False, "error": "No valid Slack credentials configured"}
        except Exception as e:
            logger.warning(f"[Slack] send_message failed: {e}")
            return {"success": False, "error": str(e)}

    def list_channels(self) -> List[Dict[str, Any]]:
        if not self._available or not self.bot_token:
            return []
        try:
            headers = {"Authorization": f"Bearer {self.bot_token}"}
            resp = _requests.get(f"{self._base_url}/conversations.list", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return [{"id": c["id"], "name": c["name"]} for c in data.get("channels", [])]
            return []
        except Exception as e:
            logger.warning(f"[Slack] list_channels failed: {e}")
            return []


class DiscordIntegration:
    def __init__(self, bot_token=None, webhook_url=None):
        self.bot_token = bot_token or os.environ.get("DISCORD_BOT_TOKEN")
        self.webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
        self._base_url = "https://discord.com/api/v10"
        self._available = _REQUESTS_AVAILABLE and (bool(self.bot_token) or bool(self.webhook_url))

    def send_message(self, content, webhook_url=None, channel_id=None) -> Dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Discord not configured. Set DISCORD_BOT_TOKEN or DISCORD_WEBHOOK_URL."}
        try:
            url = webhook_url or self.webhook_url
            if url:
                payload = {"content": content}
                resp = _requests.post(url, json=payload, timeout=10)
                return {"success": resp.status_code in (200, 204), "status_code": resp.status_code}
            elif self.bot_token and channel_id:
                headers = {"Authorization": f"Bot {self.bot_token}", "Content-Type": "application/json"}
                payload = {"content": content}
                resp = _requests.post(f"{self._base_url}/channels/{channel_id}/messages", headers=headers, json=payload, timeout=10)
                return {"success": resp.status_code == 200, "status_code": resp.status_code}
            return {"success": False, "error": "No valid Discord credentials configured"}
        except Exception as e:
            logger.warning(f"[Discord] send_message failed: {e}")
            return {"success": False, "error": str(e)}

    def list_guilds(self) -> List[Dict[str, Any]]:
        if not self._available or not self.bot_token:
            return []
        try:
            headers = {"Authorization": f"Bot {self.bot_token}"}
            resp = _requests.get(f"{self._base_url}/users/@me/guilds", headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            logger.warning(f"[Discord] list_guilds failed: {e}")
            return []


class NotionIntegration:
    def __init__(self, token=None, database_id=None):
        self.token = token or os.environ.get("NOTION_TOKEN")
        self.database_id = database_id or os.environ.get("NOTION_DATABASE_ID")
        self._base_url = "https://api.notion.com/v1"
        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self._available = _REQUESTS_AVAILABLE and bool(self.token)

    def create_page(self, title, properties=None, content_blocks=None) -> Dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Notion API not configured. Set NOTION_TOKEN and ensure requests is installed."}
        try:
            parent = {}
            if self.database_id:
                parent["database_id"] = self.database_id
            page_props = properties or {}
            if self.database_id and "title" not in page_props:
                page_props["title"] = {
                    "title": [{"text": {"content": title}}]
                }
            elif not self.database_id and "title" not in page_props:
                page_props["title"] = [
                    {"type": "text", "text": {"content": title}}
                ]
            body: Dict[str, Any] = {"properties": page_props}
            if parent:
                body["parent"] = parent
            if content_blocks:
                body["children"] = content_blocks
            resp = _requests.post(f"{self._base_url}/pages", headers=self._headers, json=body, timeout=15)
            if resp.status_code in (200, 201):
                data = resp.json()
                return {"success": True, "page_id": data.get("id"), "url": data.get("url")}
            return {"success": False, "error": f"Notion API {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            logger.warning(f"[Notion] create_page failed: {e}")
            return {"success": False, "error": str(e)}

    def query_database(self, filter_dict=None, page_size=10) -> List[Dict[str, Any]]:
        if not self._available or not self.database_id:
            return []
        try:
            body: Dict[str, Any] = {"page_size": page_size}
            if filter_dict:
                body["filter"] = filter_dict
            resp = _requests.post(
                f"{self._base_url}/databases/{self.database_id}/query",
                headers=self._headers,
                json=body,
                timeout=15,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            out = []
            for page in data.get("results", []):
                props = page.get("properties", {})
                title_val = ""
                for pname, pval in props.items():
                    if isinstance(pval, dict) and pval.get("type") == "title":
                        titles = pval.get("title", [])
                        if titles:
                            title_val = "".join(t.get("plain_text", "") for t in titles)
                        break
                out.append({
                    "id": page.get("id"),
                    "title": title_val,
                    "url": page.get("url"),
                    "created_time": page.get("created_time"),
                })
            return out
        except Exception as e:
            logger.warning(f"[Notion] query_database failed: {e}")
            return []


class ProductivitySkillRouter:
    def __init__(self):
        try:
            self.gmail = GmailIntegration()
        except Exception as e:
            logger.debug(f"[Productivity] Gmail init skipped: {e}")
            self.gmail = None
        try:
            self.calendar = GoogleCalendarIntegration()
        except Exception as e:
            logger.debug(f"[Productivity] Calendar init skipped: {e}")
            self.calendar = None
        try:
            self.todoist = TodoistIntegration()
        except Exception as e:
            logger.debug(f"[Productivity] Todoist init skipped: {e}")
            self.todoist = None
        try:
            self.notion = NotionIntegration()
        except Exception as e:
            logger.debug(f"[Productivity] Notion init skipped: {e}")
            self.notion = None
        try:
            self.slack = SlackIntegration()
        except Exception as e:
            logger.debug(f"[Productivity] Slack init skipped: {e}")
            self.slack = None
        try:
            self.discord = DiscordIntegration()
        except Exception as e:
            logger.debug(f"[Productivity] Discord init skipped: {e}")
            self.discord = None

    def handle(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        tl = text.lower()

        m = re.search(r"send\s+(?:an?\s+)?email\s+to\s+([\w\-.]+@[\w\-.]+)\s+(?:saying|that|body)[:\s]+(.+)", text, re.IGNORECASE)
        if m:
            to_addr = m.group(1)
            body = m.group(2).strip().rstrip(".!?")
            if self.gmail is None:
                return {"text": "Gmail API not configured. Enable it by placing credentials.json in the data/ folder.", "intent": "gmail_send", "data": {"to": to_addr}}
            res = self.gmail.send_email(to=to_addr, subject="Message from Jarvis", body=body)
            if res.get("success"):
                return {"text": f"Email sent to {to_addr}.", "intent": "gmail_send", "data": res}
            return {"text": f"I couldn't send the email: {res.get('error', 'unknown error')}", "intent": "gmail_send", "data": res}

        m = re.search(r"search\s+(?:my\s+)?inbox\s+(?:for|about|with)\s+(.+)", text, re.IGNORECASE)
        if m or re.search(r"\b(search\s+inbox|inbox\s+search)\b", tl):
            q = m.group(1).strip().rstrip(".!?") if m else ""
            if self.gmail is None:
                return {"text": "Gmail API not configured. Enable it by placing credentials.json in the data/ folder.", "intent": "gmail_search", "data": {"query": q}}
            msgs = self.gmail.search_inbox(query=q, max_results=5)
            if not msgs:
                return {"text": f"No emails found matching '{q}' in your inbox." if q else "Your inbox looks empty right now.", "intent": "gmail_search", "data": {"query": q, "count": 0}}
            lines = [f"{i+1}. [{msg['date']}] {msg['from']}: {msg['subject']}" for i, msg in enumerate(msgs)]
            return {"text": f"Found {len(msgs)} email(s) for '{q}':\n" + "\n".join(lines), "intent": "gmail_search", "data": {"query": q, "results": msgs}}

        m = re.search(r"(?:read|open|check)\s+(?:the\s+)?email\s+(?:from|by|id)\s+(.+)", text, re.IGNORECASE)
        if m or re.search(r"\bread\s+(?:latest|last|first)\s+email\b", tl):
            if self.gmail is None:
                return {"text": "Gmail API not configured. Enable it by placing credentials.json in the data/ folder.", "intent": "gmail_read"}
            msgs = self.gmail.search_inbox(max_results=1)
            if not msgs:
                return {"text": "No recent email to read.", "intent": "gmail_read", "data": {"count": 0}}
            target = m.group(1).strip() if m else None
            if target and len(msgs) > 0 and target.lower() in (msgs[0].get("from") or "").lower():
                msg_id = msgs[0]["id"]
            else:
                msg_id = msgs[0]["id"]
            content = self.gmail.read_email(msg_id)
            if "error" in content:
                return {"text": f"Couldn't read that email: {content['error']}", "intent": "gmail_read", "data": content}
            snippet = (content.get("body_plain") or "")[:300]
            return {"text": f"Email from {content.get('from')} — Subject: {content.get('subject')}\n{snippet}", "intent": "gmail_read", "data": content}

        m = re.search(r"create\s+(?:a\s+)?(?:calendar\s+)?event\s+(?:titled|named|called)[:\s]?[\"']?(.+?)[\"']?\s+(?:on|at|date)\s+(.+?)(?:\s+at\s+(.+))?$", text, re.IGNORECASE)
        if m or re.search(r"(?:schedule|add)\s+(?:a\s+)?meeting", tl):
            summary = m.group(1).strip(" \t\"'") if m else (text.split("meeting", 1)[1].strip() if "meeting" in tl else "New Event")
            if self.calendar is None:
                return {"text": "Google Calendar API not configured. Enable it by placing credentials.json in the data/ folder.", "intent": "calendar_create", "data": {"summary": summary}}
            try:
                today = date.today()
                now = datetime.now()
                date_part = m.group(2).strip() if m and m.group(2) else today.isoformat()
                time_part = m.group(3).strip() if m and m.group(3) else None
                dd = today
                if "tomorrow" in date_part.lower():
                    dd = today + timedelta(days=1)
                elif "today" in date_part.lower():
                    dd = today
                else:
                    try:
                        dd = date.fromisoformat(date_part)
                    except Exception:
                        pass
                hh, mm = 9, 0
                if time_part:
                    tmm = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_part, re.IGNORECASE)
                    if tmm:
                        hh = int(tmm.group(1))
                        mm = int(tmm.group(2) or 0)
                        ampm = tmm.group(3)
                        if ampm and ampm.lower() == "pm" and hh < 12:
                            hh += 12
                        if ampm and ampm.lower() == "am" and hh == 12:
                            hh = 0
                start_dt = datetime.combine(dd, datetime.min.time()).replace(hour=hh, minute=mm)
                end_dt = start_dt + timedelta(hours=1)
                res = self.calendar.create_event(summary=summary, start_datetime=start_dt, end_datetime=end_dt)
                if res.get("success"):
                    return {"text": f"Created calendar event '{summary}' on {start_dt.strftime('%A %B %d at %I:%M %p')}.", "intent": "calendar_create", "data": res}
                return {"text": f"Couldn't create the event: {res.get('error', 'unknown error')}", "intent": "calendar_create", "data": res}
            except Exception as e:
                return {"text": f"Couldn't create the event: {e}", "intent": "calendar_create", "error": str(e)}

        if re.search(r"(what'?s|what is)\s+(on\s+)?my\s+schedule\s+today", tl) or re.search(r"\b(show|list)\s+(my\s+)?(today'?s\s+)?schedule\b", tl):
            if self.calendar is None:
                return {"text": "Google Calendar API not configured. Enable it by placing credentials.json in the data/ folder.", "intent": "calendar_schedule"}
            events = self.calendar.check_schedule()
            if not events:
                return {"text": "You have no events scheduled for today — enjoy your free time!", "intent": "calendar_schedule", "data": {"count": 0}}
            lines = []
            for e in events:
                st = e.get("start", "")
                try:
                    st_dt = datetime.fromisoformat(st.replace("Z", "+00:00"))
                    st_str = st_dt.strftime("%I:%M %p")
                except Exception:
                    st_str = st
                lines.append(f"• {st_str} — {e.get('summary')}")
            return {"text": f"Today's schedule ({len(events)} event(s)):\n" + "\n".join(lines), "intent": "calendar_schedule", "data": {"events": events}}

        m = re.search(r"(?:add|create|set|new)\s+(?:a\s+)?(?:todo|task|to\s*do)\s+(.+)", text, re.IGNORECASE)
        if m or re.search(r"\b(add.*todo|todo.*add)\b", tl):
            content = m.group(1).strip().rstrip(".!?") if m else (text.lower().replace("add todo", "").strip() or "New task")
            if self.todoist is None:
                return {"text": "Todoist not configured. Set TODOIST_API_TOKEN or pass api_token, and ensure todoist-api-python is installed.", "intent": "todo_add", "data": {"content": content}}
            due = None
            if "tomorrow" in text.lower():
                due = "tomorrow"
            elif "today" in text.lower():
                due = "today"
            res = self.todoist.add_task(content=content, due_string=due)
            if res.get("success"):
                return {"text": f"Added todo: '{content}'." + (f" Due: {due}." if due else ""), "intent": "todo_add", "data": res}
            return {"text": f"Couldn't add the task: {res.get('error', 'unknown error')}", "intent": "todo_add", "data": res}

        m = re.search(r"(?:add|create|new)\s+(?:a\s+)?(?:notion\s+)?(?:page|entry)\s+(?:titled|named|called)[:\s]?[\"']?(.+?)[\"']?(?:\s+with\s+(.+))?$", text, re.IGNORECASE)
        if m or re.search(r"\bnotion\b", tl):
            title = m.group(1).strip(" \t\"'") if m else (text.split("notion", 1)[1].strip() if "notion" in tl else "New Notion Page")
            if self.notion is None:
                return {"text": "Notion API not configured. Set NOTION_TOKEN (and optionally NOTION_DATABASE_ID) and ensure requests is installed.", "intent": "notion_create", "data": {"title": title}}
            content_blocks = None
            if m and m.group(2):
                content_blocks = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": m.group(2).strip()}}]
                        },
                    }
                ]
            res = self.notion.create_page(title=title, content_blocks=content_blocks)
            if res.get("success"):
                return {"text": f"Created Notion page: '{title}'. {res.get('url', '')}", "intent": "notion_create", "data": res}
            return {"text": f"Couldn't create the Notion page: {res.get('error', 'unknown error')}", "intent": "notion_create", "data": res}

        m = re.search(r"(?:send|post)\s+(?:a\s+)?(?:message|msg)\s+(?:to\s+)?(?:slack|channel)\s+([\w\-]+)\s+(?:saying|that)[:\s]+(.+)", text, re.IGNORECASE)
        if m or re.search(r"\bslack\b", tl):
            channel = m.group(1).strip() if m else "general"
            message = m.group(2).strip().rstrip(".!?") if m else (text.split("slack", 1)[1].strip() if "slack" in tl else "Hello from Jarvis")
            if self.slack is None:
                return {"text": "Slack not configured. Set SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL.", "intent": "slack_send", "data": {"channel": channel}}
            res = self.slack.send_message(channel=channel, text=message)
            if res.get("success"):
                return {"text": f"Sent message to Slack channel '{channel}'.", "intent": "slack_send", "data": res}
            return {"text": f"Couldn't send Slack message: {res.get('error', 'unknown error')}", "intent": "slack_send", "data": res}

        m = re.search(r"(?:send|post)\s+(?:a\s+)?(?:message|msg)\s+(?:to\s+)?(?:discord|server)\s+(?:saying|that)[:\s]+(.+)", text, re.IGNORECASE)
        if m or re.search(r"\bdiscord\b", tl):
            message = m.group(1).strip().rstrip(".!?") if m else (text.split("discord", 1)[1].strip() if "discord" in tl else "Hello from Jarvis")
            if self.discord is None:
                return {"text": "Discord not configured. Set DISCORD_BOT_TOKEN or DISCORD_WEBHOOK_URL.", "intent": "discord_send", "data": {}}
            res = self.discord.send_message(content=message)
            if res.get("success"):
                return {"text": "Sent message to Discord.", "intent": "discord_send", "data": res}
            return {"text": f"Couldn't send Discord message: {res.get('error', 'unknown error')}", "intent": "discord_send", "data": res}

        return {
            "text": "I didn't recognize that productivity command. Try: 'send email to john@example.com saying hello', 'what's on my schedule today', 'add todo buy milk', or 'search inbox for invoices'.",
            "intent": "productivity_unknown",
            "data": {"text": text},
        }


INTENT_PATTERNS = [
    r"send\s+(?:an?\s+)?email\s+to\s+[\w\-.]+@[\w\-.]+",
    r"search\s+(?:my\s+)?inbox\s+(?:for|about|with)",
    r"(?:read|open|check)\s+(?:the\s+)?email\s+(?:from|by|id)",
    r"read\s+(?:latest|last|first)\s+email",
    r"create\s+(?:a\s+)?(?:calendar\s+)?event\s+(?:titled|named|called)",
    r"(?:schedule|add)\s+(?:a\s+)?meeting",
    r"(?:what'?s|what is)\s+(?:on\s+)?my\s+schedule\s+today",
    r"(?:show|list)\s+(?:my\s+)?(?:today'?s\s+)?schedule",
    r"(?:add|create|set|new)\s+(?:a\s+)?(?:todo|task|to\s*do)\s+",
    r"add.*todo",
    r"(?:add|create|new)\s+(?:a\s+)?(?:notion\s+)?(?:page|entry)\s+(?:titled|named|called)",
    r"\bnotion\b",
    r"(?:send|post)\s+(?:a\s+)?(?:message|msg)\s+(?:to\s+)?(?:slack|channel)",
    r"\bslack\b",
    r"(?:send|post)\s+(?:a\s+)?(?:message|msg)\s+(?:to\s+)?(?:discord|server)",
    r"\bdiscord\b",
]

PLUGIN_NAME = "Productivity Suite"
ICON = "📅"
EXAMPLES = [
    "send email to john@example.com saying hello",
    "search inbox for invoices",
    "read latest email",
    "create calendar event titled Team standup on tomorrow at 9am",
    "what's on my schedule today",
    "add todo buy milk",
    "add Notion page titled Meeting notes with discussion about Q4 roadmap",
    "send message to slack general saying meeting in 10 minutes",
    "send message to discord saying deployment complete",
]

_router_instance: Optional[ProductivitySkillRouter] = None


def _get_router() -> ProductivitySkillRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = ProductivitySkillRouter()
    return _router_instance


def handle(text, match=None, assistant=None) -> Dict[str, Any]:
    router = _get_router()
    context = {"assistant": assistant} if assistant else None
    return router.handle(text, context=context)
