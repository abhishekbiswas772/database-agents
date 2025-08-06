from session_manager import session_mgr
from typing import Dict, Any
from smolagents import tool
import json



@tool
def create_database_session(db_uri: str) -> Dict[str, Any]:
    """
    Create a new database session with the given URI.
    
    Args:
        db_uri: Database connection string (mysql://..., postgresql://..., mongodb://..., etc.)
        
    Returns:
        Session info including session_id
    """
    session = session_mgr.create_session(db_uri)
    
    if db_uri.startswith(('mysql://', 'mysql+pymysql://')):
        db_type = 'mysql'
    elif db_uri.startswith(('postgresql://', 'postgres://')):
        db_type = 'postgresql'
    elif db_uri.startswith(('mongodb://', 'mongodb+srv://')):
        db_type = 'mongodb'
    elif db_uri.startswith('redis://'):
        db_type = 'redis'
    elif db_uri.startswith('sqlite://'):
        db_type = 'sqlite'
    else:
        db_type = 'unknown'
    
    session_mgr.update_session(session.session_id, db_type=db_type)
    
    return {
        "session_id": session.session_id,
        "db_uri": db_uri,
        "db_type": db_type,
        "status": "created",
        "message": f"Session {session.session_id} created for {db_type} database"
    }


@tool
def get_current_session() -> Dict[str, Any]:
    """
    Get the current active session information.
    
    Returns:
        Current session details or error if no session
    """
    session = session_mgr.get_session()
    if not session:
        return {"error": "No active session. Please create one first."}
    
    return {
        "session_id": session.session_id,
        "db_uri": session.db_uri,
        "db_type": session.db_type,
        "connected": session.connected,
        "analyzed": session.analyzed,
        "schema_info": session.schema_info
    }


@tool
def save_connection_code(session_id: str, code: str) -> Dict[str, Any]:
    """
    Save the connection code for a session.
    
    Args:
        session_id: Session ID
        code: Python code to connect to the database
        
    Returns:
        Success status
    """
    session_mgr.update_session(session_id, connection_code=code, connected=True)
    return {"status": "success", "message": "Connection code saved"}


@tool
def save_schema_info(session_id: str, schema_info: str) -> Dict[str, Any]:
    """
    Save the database schema information for a session.
    
    Args:
        session_id: Session ID
        schema_info: JSON string of schema information
        
    Returns:
        Success status
    """
    try:
        schema_dict = json.loads(schema_info)
        session_mgr.update_session(session_id, schema_info=schema_dict, analyzed=True)
        return {"status": "success", "message": "Schema information saved"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format for schema_info"}
