"""
Offline Mode Foundation
Enables JARVIS to function without internet connectivity using local models and cached data.
"""

import os
import json
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import pickle


@dataclass
class OfflineCapability:
    name: str
    available: bool
    quality: str  # 'full', 'limited', 'basic'
    last_updated: str
    size_mb: float


@dataclass
class CachedResponse:
    query: str
    response: str
    timestamp: str
    source: str
    confidence: float
    ttl_hours: int


@dataclass
class SyncStatus:
    last_sync: str
    pending_uploads: int
    pending_downloads: int
    sync_required: bool


class OfflineModeManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.offline_dir = os.path.join(self.base_dir, "data", "offline")
        self.cache_db = os.path.join(self.offline_dir, "cache.db")
        self.capabilities_file = os.path.join(self.offline_dir, "capabilities.json")
        self.sync_status_file = os.path.join(self.offline_dir, "sync_status.json")
        
        os.makedirs(self.offline_dir, exist_ok=True)
        
        self.is_offline = False
        self.capabilities = self._load_capabilities()
        self.sync_status = self._load_sync_status()
        
        # Initialize cache database
        self._init_cache_db()
        
        # Detect offline status
        self._detect_offline_status()

    def _init_cache_db(self):
        """Initialize SQLite cache database."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                response TEXT,
                source TEXT,
                confidence REAL,
                timestamp TEXT,
                ttl_hours INTEGER,
                size_bytes INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT,
                data_key TEXT UNIQUE,
                data_value BLOB,
                timestamp TEXT,
                size_bytes INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_query_hash ON cache(query_hash)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_type ON offline_data(data_type)
        ''')
        
        conn.commit()
        conn.close()

    def _load_capabilities(self) -> Dict[str, OfflineCapability]:
        """Load offline capabilities from disk."""
        if os.path.exists(self.capabilities_file):
            try:
                with open(self.capabilities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {name: OfflineCapability(**cap) for name, cap in data.items()}
            except Exception:
                pass
        
        # Default capabilities
        return {
            'intent_classification': OfflineCapability(
                name='intent_classification',
                available=True,
                quality='full',
                last_updated=datetime.now().isoformat(),
                size_mb=5.0
            ),
            'basic_qa': OfflineCapability(
                name='basic_qa',
                available=True,
                quality='limited',
                last_updated=datetime.now().isoformat(),
                size_mb=10.0
            ),
            'calculator': OfflineCapability(
                name='calculator',
                available=True,
                quality='full',
                last_updated=datetime.now().isoformat(),
                size_mb=0.5
            ),
            'time_date': OfflineCapability(
                name='time_date',
                available=True,
                quality='full',
                last_updated=datetime.now().isoformat(),
                size_mb=0.1
            ),
            'weather': OfflineCapability(
                name='weather',
                available=False,
                quality='none',
                last_updated=datetime.now().isoformat(),
                size_mb=0.0
            ),
            'web_search': OfflineCapability(
                name='web_search',
                available=False,
                quality='none',
                last_updated=datetime.now().isoformat(),
                size_mb=0.0
            ),
            'llm_knowledge': OfflineCapability(
                name='llm_knowledge',
                available=False,
                quality='none',
                last_updated=datetime.now().isoformat(),
                size_mb=0.0
            )
        }

    def _save_capabilities(self):
        """Save offline capabilities to disk."""
        try:
            data = {name: asdict(cap) for name, cap in self.capabilities.items()}
            with open(self.capabilities_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[OfflineMode] Failed to save capabilities: {e}")

    def _load_sync_status(self) -> SyncStatus:
        """Load sync status from disk."""
        if os.path.exists(self.sync_status_file):
            try:
                with open(self.sync_status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return SyncStatus(**data)
            except Exception:
                pass
        
        return SyncStatus(
            last_sync=datetime.now().isoformat(),
            pending_uploads=0,
            pending_downloads=0,
            sync_required=False
        )

    def _save_sync_status(self):
        """Save sync status to disk."""
        try:
            with open(self.sync_status_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.sync_status), f, indent=2)
        except Exception as e:
            print(f"[OfflineMode] Failed to save sync status: {e}")

    def _detect_offline_status(self):
        """Detect if the system is currently offline."""
        try:
            import requests
            response = requests.get('https://www.google.com', timeout=3)
            self.is_offline = False
            print("[OfflineMode] Online mode detected")
        except Exception:
            self.is_offline = True
            print("[OfflineMode] Offline mode detected")

    def set_offline_mode(self, offline: bool):
        """Manually set offline mode."""
        self.is_offline = offline
        status = "OFFLINE" if offline else "ONLINE"
        print(f"[OfflineMode] Mode set to {status}")

    def cache_response(self, query: str, response: str, source: str, 
                      confidence: float = 1.0, ttl_hours: int = 24):
        """Cache a response for offline use."""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO cache 
                (query_hash, query, response, source, confidence, timestamp, ttl_hours, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query_hash,
                query,
                response,
                source,
                confidence,
                datetime.now().isoformat(),
                ttl_hours,
                len(response.encode('utf-8'))
            ))
            
            conn.commit()
            print(f"[OfflineMode] Cached response for: {query[:50]}...")
            
        except Exception as e:
            print(f"[OfflineMode] Failed to cache response: {e}")
        finally:
            conn.close()

    def get_cached_response(self, query: str) -> Optional[CachedResponse]:
        """Retrieve a cached response if available."""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT query, response, source, confidence, timestamp, ttl_hours
                FROM cache WHERE query_hash = ?
            ''', (query_hash,))
            
            row = cursor.fetchone()
            
            if row:
                query_text, response, source, confidence, timestamp, ttl_hours = row
                
                # Check if cache is expired
                cache_time = datetime.fromisoformat(timestamp)
                if datetime.now() - cache_time > timedelta(hours=ttl_hours):
                    return None
                
                return CachedResponse(
                    query=query_text,
                    response=response,
                    timestamp=timestamp,
                    source=source,
                    confidence=confidence,
                    ttl_hours=ttl_hours
                )
            
            return None
            
        except Exception as e:
            print(f"[OfflineMode] Failed to retrieve cached response: {e}")
            return None
        finally:
            conn.close()

    def store_offline_data(self, data_type: str, data_key: str, data: Any):
        """Store data for offline use."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            serialized_data = pickle.dumps(data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO offline_data 
                (data_type, data_key, data_value, timestamp, size_bytes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data_type,
                data_key,
                serialized_data,
                datetime.now().isoformat(),
                len(serialized_data)
            ))
            
            conn.commit()
            print(f"[OfflineMode] Stored offline data: {data_type}/{data_key}")
            
        except Exception as e:
            print(f"[OfflineMode] Failed to store offline data: {e}")
        finally:
            conn.close()

    def get_offline_data(self, data_type: str, data_key: str) -> Optional[Any]:
        """Retrieve stored offline data."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data_value FROM offline_data 
                WHERE data_type = ? AND data_key = ?
            ''', (data_type, data_key))
            
            row = cursor.fetchone()
            
            if row:
                return pickle.loads(row[0])
            
            return None
            
        except Exception as e:
            print(f"[OfflineMode] Failed to retrieve offline data: {e}")
            return None
        finally:
            conn.close()

    def get_offline_capabilities(self) -> Dict[str, OfflineCapability]:
        """Get current offline capabilities."""
        return self.capabilities

    def update_capability(self, name: str, available: bool, quality: str, size_mb: float):
        """Update an offline capability."""
        if name in self.capabilities:
            self.capabilities[name] = OfflineCapability(
                name=name,
                available=available,
                quality=quality,
                last_updated=datetime.now().isoformat(),
                size_mb=size_mb
            )
            self._save_capabilities()

    def prepare_offline_mode(self, force_download: bool = False) -> Tuple[bool, str]:
        """
        Prepare the system for offline mode by downloading necessary resources.
        
        Args:
            force_download: Force re-download of all resources
        """
        if not force_download and not self.is_offline:
            return True, "System is online. Offline preparation not required."
        
        print("[OfflineMode] Preparing offline mode...")
        
        try:
            # Cache common responses
            common_queries = [
                ("what time is it", "time_date"),
                ("what is the date", "time_date"),
                ("calculate 2+2", "calculator"),
                ("hello", "greeting"),
                ("who are you", "identity"),
            ]
            
            for query, capability in common_queries:
                if self.capabilities.get(capability, OfflineCapability("", False, "", "", 0)).available:
                    # Generate and cache response
                    self.cache_response(query, f"Cached response for {query}", capability, 0.9, 168)
            
            # Store essential data
            self._store_essential_data()
            
            # Update capabilities
            self.capabilities['basic_qa'].available = True
            self.capabilities['basic_qa'].quality = 'limited'
            self._save_capabilities()
            
            # Update sync status
            self.sync_status.last_sync = datetime.now().isoformat()
            self._save_sync_status()
            
            return True, "Offline mode prepared successfully"
            
        except Exception as e:
            return False, f"Offline preparation failed: {str(e)}"

    def _store_essential_data(self):
        """Store essential data for offline use."""
        # Store country data
        try:
            from assistant.core.data_provider import DataProvider
            dp = DataProvider()
            
            countries = dp.list_countries()
            self.store_offline_data('countries', 'all', countries)
            
            # Store time zones
            timezones = [
                ("UTC", "UTC"),
                ("America/New_York", "EST"),
                ("America/Los_Angeles", "PST"),
                ("Europe/London", "GMT"),
                ("Asia/Tokyo", "JST"),
                ("Asia/Kolkata", "IST"),
            ]
            
            for tz_name, tz_code in timezones:
                time_info = dp.get_time_in(tz_name)
                self.store_offline_data('time', tz_name, time_info)
            
            print("[OfflineMode] Essential data stored successfully")
            
        except Exception as e:
            print(f"[OfflineMode] Failed to store essential data: {e}")

    def sync_with_cloud(self) -> Tuple[bool, str]:
        """Sync offline data with cloud when connection is available."""
        if self.is_offline:
            return False, "Cannot sync while offline"
        
        print("[OfflineMode] Syncing with cloud...")
        
        try:
            # Upload pending data
            pending_uploads = self._get_pending_uploads()
            for upload in pending_uploads:
                self._upload_to_cloud(upload)
            
            # Download new data
            self._download_from_cloud()
            
            # Update sync status
            self.sync_status.last_sync = datetime.now().isoformat()
            self.sync_status.pending_uploads = 0
            self.sync_status.pending_downloads = 0
            self.sync_status.sync_required = False
            self._save_sync_status()
            
            return True, "Sync completed successfully"
            
        except Exception as e:
            return False, f"Sync failed: {str(e)}"

    def _get_pending_uploads(self) -> List[Dict]:
        """Get data pending upload to cloud."""
        # This would query a pending uploads table in a real implementation
        return []

    def _upload_to_cloud(self, data: Dict):
        """Upload data to cloud storage."""
        # This would implement actual cloud upload
        pass

    def _download_from_cloud(self):
        """Download new data from cloud."""
        # This would implement actual cloud download
        pass

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached data."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            # Cache statistics
            cursor.execute('SELECT COUNT(*) FROM cache')
            cache_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(size_bytes) FROM cache')
            cache_size = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM offline_data')
            data_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(size_bytes) FROM offline_data')
            data_size = cursor.fetchone()[0] or 0
            
            # Expired entries
            cursor.execute('''
                SELECT COUNT(*) FROM cache 
                WHERE datetime(timestamp, '+' || ttl_hours || ' hours') < datetime('now')
            ''')
            expired_count = cursor.fetchone()[0]
            
            return {
                'cache_entries': cache_count,
                'cache_size_mb': round(cache_size / (1024 * 1024), 2),
                'offline_data_entries': data_count,
                'offline_data_size_mb': round(data_size / (1024 * 1024), 2),
                'expired_entries': expired_count,
                'total_size_mb': round((cache_size + data_size) / (1024 * 1024), 2),
                'is_offline': self.is_offline,
                'last_sync': self.sync_status.last_sync
            }
            
        except Exception as e:
            print(f"[OfflineMode] Failed to get cache statistics: {e}")
            return {}
        finally:
            conn.close()

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM cache 
                WHERE datetime(timestamp, '+' || ttl_hours || ' hours') < datetime('now')
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"[OfflineMode] Cleared {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            print(f"[OfflineMode] Failed to clear expired cache: {e}")
            return 0
        finally:
            conn.close()

    def clear_all_cache(self) -> bool:
        """Clear all cached data."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM cache')
            cursor.execute('DELETE FROM offline_data')
            conn.commit()
            
            print("[OfflineMode] Cleared all cache")
            return True
            
        except Exception as e:
            print(f"[OfflineMode] Failed to clear cache: {e}")
            return False
        finally:
            conn.close()

    def optimize_cache(self) -> Tuple[bool, str]:
        """Optimize cache database."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute('VACUUM')
            cursor.execute('ANALYZE')
            conn.commit()
            
            return True, "Cache optimized successfully"
            
        except Exception as e:
            return False, f"Cache optimization failed: {str(e)}"
        finally:
            conn.close()

    def export_cache(self, export_path: str) -> Tuple[bool, str]:
        """Export cache to a file for backup."""
        try:
            import shutil
            shutil.copy2(self.cache_db, export_path)
            return True, f"Cache exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_cache(self, import_path: str) -> Tuple[bool, str]:
        """Import cache from a backup file."""
        try:
            import shutil
            shutil.copy2(import_path, self.cache_db)
            return True, f"Cache imported from {import_path}"
        except Exception as e:
            return False, f"Import failed: {str(e)}"


class OfflineIntentHandler:
    """Handle intents in offline mode with limited capabilities."""
    
    def __init__(self, offline_manager: OfflineModeManager):
        self.offline = offline_manager
        self.local_models = {}
        self._load_local_models()

    def _load_local_models(self):
        """Load local ML models for offline use."""
        try:
            # Load intent classifier
            from assistant.nlp.intent_classifier import IntentClassifier
            self.local_models['intent_classifier'] = IntentClassifier()
            print("[OfflineIntentHandler] Intent classifier loaded")
            
        except Exception as e:
            print(f"[OfflineIntentHandler] Failed to load models: {e}")

    def handle_offline_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle a query in offline mode."""
        # Check cache first
        cached = self.offline.get_cached_response(query)
        if cached:
            return {
                'response': cached.response,
                'source': f'cache ({cached.source})',
                'confidence': cached.confidence,
                'offline': True
            }
        
        # Try local intent classification
        if 'intent_classifier' in self.local_models:
            try:
                intent_result = self.local_models['intent_classifier'].get_intent(query)
                intent = intent_result['intent']
                
                # Handle basic offline intents
                if intent == 'greeting':
                    return self._handle_greeting()
                elif intent == 'farewell':
                    return self._handle_farewell()
                elif intent == 'calculator':
                    return self._handle_calculator(query)
                elif intent in ['time', 'date']:
                    return self._handle_time_date(intent)
                elif intent == 'name':
                    return self._handle_identity()
                
            except Exception as e:
                print(f"[OfflineIntentHandler] Intent handling failed: {e}")
        
        # Fallback response
        return {
            'response': "I'm currently in offline mode with limited capabilities. I can handle basic calculations, time/date queries, and greetings. For full functionality, please connect to the internet.",
            'source': 'offline_fallback',
            'confidence': 0.5,
            'offline': True
        }

    def _handle_greeting(self) -> Dict[str, Any]:
        """Handle greeting in offline mode."""
        import datetime
        hour = datetime.datetime.now().hour
        
        if 5 <= hour < 12:
            greeting = "Good morning! I'm running in offline mode, but I'm here to help with basic tasks."
        elif 12 <= hour < 17:
            greeting = "Good afternoon! I'm operating in offline mode with limited capabilities."
        elif 17 <= hour < 21:
            greeting = "Good evening! I'm in offline mode but can still assist with basic queries."
        else:
            greeting = "Hello! I'm running in offline mode. How can I help with basic tasks?"
        
        return {
            'response': greeting,
            'source': 'offline_local',
            'confidence': 0.9,
            'offline': True
        }

    def _handle_farewell(self) -> Dict[str, Any]:
        """Handle farewell in offline mode."""
        return {
            'response': "Goodbye! I'll be here when you return, even in offline mode.",
            'source': 'offline_local',
            'confidence': 0.9,
            'offline': True
        }

    def _handle_calculator(self, query: str) -> Dict[str, Any]:
        """Handle calculator in offline mode."""
        try:
            import re
            # Extract mathematical expression
            expr_match = re.search(r'[\d+\-*/().\^]+', query)
            if expr_match:
                expr = expr_match.group(0)
                result = eval(expr)
                return {
                    'response': f"The result is {result}",
                    'source': 'offline_calculator',
                    'confidence': 0.95,
                    'offline': True
                }
        except Exception:
            pass
        
        return {
            'response': "I couldn't calculate that. Please provide a valid mathematical expression.",
            'source': 'offline_calculator',
            'confidence': 0.5,
            'offline': True
        }

    def _handle_time_date(self, intent: str) -> Dict[str, Any]:
        """Handle time/date queries in offline mode."""
        import datetime
        
        if intent == 'time':
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return {
                'response': f"The current time is {current_time}",
                'source': 'offline_time',
                'confidence': 1.0,
                'offline': True
            }
        elif intent == 'date':
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return {
                'response': f"Today is {current_date}",
                'source': 'offline_date',
                'confidence': 1.0,
                'offline': True
            }
        
        return {
            'response': "I couldn't process that time/date query.",
            'source': 'offline_time_date',
            'confidence': 0.5,
            'offline': True
        }

    def _handle_identity(self) -> Dict[str, Any]:
        """Handle identity query in offline mode."""
        return {
            'response': "I'm JARVIS, your AI assistant. I'm currently running in offline mode with limited capabilities, but I can still help with basic tasks.",
            'source': 'offline_identity',
            'confidence': 0.9,
            'offline': True
        }
