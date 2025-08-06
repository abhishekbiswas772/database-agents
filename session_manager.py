from typing import Dict, Optional
from dataclasses import dataclass
import uuid

@dataclass
class DatabaseSession:
    session_id: str
    db_uri: str
    db_type: Optional[str] = None
    connection_code: Optional[str] = None
    schema_info: Optional[Dict] = None
    connected: bool = False
    analyzed: bool = False
    
    
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, DatabaseSession] = {}
        self.current_session_id: Optional[str] = None
    
    def create_session(self, db_uri: str) -> DatabaseSession:
        session_id = str(uuid.uuid4())
        session = DatabaseSession(session_id=session_id, db_uri=db_uri)
        self.sessions[session_id] = session
        self.current_session_id = session_id
        return session
    
    def get_session(self, session_id: Optional[str] = None) -> Optional[DatabaseSession]:
        if session_id:
            return self.sessions.get(session_id)
        elif self.current_session_id:
            return self.sessions.get(self.current_session_id)
        return None
    
    def update_session(self, session_id: str, **kwargs):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)


session_mgr = SessionManager()