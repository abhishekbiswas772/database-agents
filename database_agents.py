import json
from session_manager import session_mgr
from smolagents import CodeAgent, OpenAIServerModel
from typing import List
from llm_tools import create_database_session, get_current_session, save_connection_code, save_schema_info
from analytics_visualizer import TerminalAnalytics

class DatabaseAgent:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.model = OpenAIServerModel(
            model_id=model,
            api_key=api_key
        )
        
        self.tools = [
            create_database_session,
            get_current_session,
            save_connection_code,
            save_schema_info
        ]
        
        self.analytics = TerminalAnalytics()
        
        self.orchestrator = CodeAgent(
            tools=self.tools,
            model=self.model,
            # max_steps=15,
            instructions=self._get_orchestrator_instructions(),
            additional_authorized_imports=self._get_imports()
        )
        
        self.connector = CodeAgent(
            tools=self.tools,
            model=self.model,
            # max_steps=10,
            instructions=self._get_connector_instructions(),
            additional_authorized_imports=self._get_imports()
        )
        
        self.querier = CodeAgent(
            tools=self.tools,
            model=self.model,
            # max_steps=10,
            # executor_type='docker',
            instructions=self._get_querier_instructions(),
            additional_authorized_imports=self._get_imports()
        )
    
    def _get_imports(self) -> List[str]:
        return [
            "urllib.parse", "json", "re", "subprocess", "sys", "os",
            "sqlite3", "sqlalchemy", "pymysql", "psycopg2", "pymongo", 
            "redis", "pandas", "numpy", "typing", "dataclasses"
        ]
    
    def _get_orchestrator_instructions(self) -> str:
        return """
            You are the main orchestrator agent. Your job is to:
            1. Understand what the user wants
            2. Delegate to specialized agents when needed
            3. Coordinate the overall workflow

            You're flexible and adaptive - don't follow rigid patterns. Think step by step about what needs to be done.

            When a database URI is provided:
            - First create a session using create_database_session
            - Then dynamically figure out how to connect based on the URI
            - Write code that actually works for that specific database

            Remember: Be ADAPTIVE, not prescriptive. Every database is different.
        """
    
    def _get_connector_instructions(self) -> str:
        return """
            You are a database connection specialist. Your job is to:
            1. Take a database URI and establish a connection
            2. Write WORKING code that connects to the specific database
            3. Analyze the database structure
            4. Save all information for future use

            IMPORTANT: 
            - Always use the EXACT URI provided by the user
            - Don't try random URIs or assume credentials
            - Test your connection code before saving it
            - Extract and save comprehensive schema information


            Always save your working connection code using save_connection_code() tool.
            Always save schema information using save_schema_info() tool.
        """
    
    def _get_querier_instructions(self) -> str:
        return """
            You are a database query specialist. Your job is to:
            1. Understand user questions about the database
            2. Use the saved connection code to reconnect
            3. Write and execute queries to answer questions
            4. Present results clearly

            IMPORTANT:
            - Always get current session first using get_current_session()
            - Use the exact connection code that was saved
            - Write efficient queries
            - Handle different database types appropriately
            - Format results in a user-friendly way
        """
    
    def connect_database(self, db_uri: str) -> str:
        import sys
        from io import StringIO
        import threading
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        # Capture stdout to hide agent verbose output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        def run_connection():
            try:
                orchestrator_prompt = f"""
                    Create a new database session for this URI and prepare for connection:
                    {db_uri}

                    Use create_database_session tool and note the session_id.
                """
                result = self.orchestrator.run(orchestrator_prompt)
                
                session = session_mgr.get_session()
                if not session:
                    return "Failed to create session"
                
                connector_prompt = f"""
                    CONNECT TO DATABASE MISSION

                    Session ID: {session.session_id}
                    Database URI: {db_uri}
                    Database Type: {session.db_type}

                    YOUR TASKS:
                    1. Write Python code to connect to this EXACT database URI
                    2. DO NOT try other URIs or make assumptions
                    3. Test the connection and make sure it works
                    4. Analyze the database structure (tables, collections, etc.)
                    5. Save the working connection code using save_connection_code()
                    6. Save the schema information using save_schema_info()

                    BE ADAPTIVE: Write code that specifically works for THIS database.
                    IMPORTANT: Provide a brief final answer only.
                """
                
                connector_result = self.connector.run(connector_prompt)
                return connector_result
            except Exception as e:
                return f"Connection error: {str(e)}"
        
        try:
            # Use ThreadPoolExecutor with timeout for cross-platform compatibility
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_connection)
                try:
                    connector_result = future.result(timeout=45)  # 45 second timeout
                except FutureTimeoutError:
                    return "Connection timed out after 45 seconds. Please check your database URI and network connection."
                
        except Exception as e:
            return f"Connection failed: {str(e)}"
        finally:
            # Restore stdout
            sys.stdout = old_stdout
        
        # Extract clean response from agent result
        if hasattr(connector_result, 'final_answer'):
            clean_result = str(connector_result.final_answer)
        else:
            clean_result = str(connector_result).split('Final answer: ')[-1] if 'Final answer: ' in str(connector_result) else str(connector_result)
        
        session = session_mgr.get_session()
        if not session:
            return "Connection failed"
            
        tables_list = "Unknown"
        if session.schema_info:
            try:
                schema = json.loads(session.schema_info)
                tables_list = ", ".join(schema.get('tables', []))
            except:
                tables_list = "Unknown"
        
        return f"""**Connected to {session.db_type} database successfully!**

Database: {session.db_uri.split('/')[-1] if '/' in session.db_uri else 'database'}
Tables: {tables_list}

Ready for queries! Use /analytics for data visualization."""
    
    def query_database(self, question: str) -> str:
        session = session_mgr.get_session()
        if not session or not session.connected:
            return "No active database connection. Please connect first."
        
        querier_prompt = f"""
            QUERY DATABASE MISSION

            User Question: {question}

            CONTEXT:
            - Session ID: {session.session_id}
            - Database URI: {session.db_uri}
            - Database Type: {session.db_type}
            - Connection Code Available: {session.connection_code is not None}
            - Schema Info Available: {session.schema_info is not None}

            YOUR TASKS:
            1. Get the current session using get_current_session()
            2. Reconnect to the database using the saved connection approach
            3. Write and execute queries to answer: {question}
            4. Present the results clearly

            The connection code that worked before:
            {session.connection_code if session.connection_code else 'Not saved - create new connection'}

            Schema information:
            {json.dumps(session.schema_info, indent=2) if session.schema_info else 'Not available'}

            BE FLEXIBLE: Adapt your query approach to the database type and structure.
            """
        
        result = self.querier.run(querier_prompt)
        
        # Extract clean response from agent result
        if hasattr(result, 'final_answer'):
            clean_result = str(result.final_answer)
        else:
            clean_result = str(result).split('Final answer: ')[-1] if 'Final answer: ' in str(result) else str(result)
        
        return f"""**QUERY RESULT**
Question: {question}

{clean_result}"""
    
    def analyze_data(self, query: str, analytics_type: str = "dashboard") -> str:
        """Query database and display analytics visualization"""
        session = session_mgr.get_session()
        if not session or not session.connected:
            return "No active database connection. Please connect first."
        
        # First get the data using querier
        connection_code_str = session.connection_code if session.connection_code else 'Not saved - create new connection'
        schema_info_str = json.dumps(session.schema_info, indent=2) if session.schema_info else 'Not available'
        
        querier_prompt = f"""
            ANALYTICS DATA QUERY MISSION
            
            User's natural language request: "{query}"
            Analytics Type: {analytics_type}
            
            CONTEXT:
            - Session ID: {session.session_id}
            - Database URI: {session.db_uri}
            - Database Type: {session.db_type}
            - Available tables: {schema_info_str}
            
            YOUR TASKS:
            1. Get the current session using get_current_session()
            2. Understand what the user wants from their natural language request
            3. Reconnect to the database using the saved connection approach
            4. Convert the user's natural language request into appropriate database query
            5. Execute the query and get the data
            6. Return the actual data rows for visualization
            
            EXAMPLES of natural language to query conversion:
            - "records in database" → SELECT * FROM main_table LIMIT 50
            - "show all users" → SELECT * FROM users
            - "count of records" → SELECT COUNT(*) as count FROM main_table
            - "latest entries" → SELECT * FROM main_table ORDER BY date_column DESC LIMIT 20
            
            IMPORTANT: Just return the query results as structured data that can be visualized.
            
            The connection code that worked before:
            {connection_code_str}
            
            Schema information:
            {schema_info_str}
            """
        
        result = self.querier.run(querier_prompt)
        
        # Extract clean response from agent result
        if hasattr(result, 'final_answer'):
            clean_result = str(result.final_answer)
        else:
            clean_result = str(result).split('Final answer: ')[-1] if 'Final answer: ' in str(result) else str(result)
        
        # Try to extract structured data from the result
        try:
            # Look for data patterns in the result
            import re
            
            # Try to find JSON-like data in the result
            json_match = re.search(r'\[[\s\S]*\]', clean_result)
            if json_match:
                data_str = json_match.group(0)
                try:
                    data = json.loads(data_str)
                    if isinstance(data, list) and len(data) > 0:
                        self.analytics.display_analytics(data, analytics_type, f"Analytics: {query}")
                        return f"**Analytics displayed for:** {query}\n\nRaw query result:\n{clean_result}"
                except json.JSONDecodeError:
                    pass
            
            # Try to parse as CSV-like data
            lines = clean_result.split('\n')
            if len(lines) > 2:
                # Look for tabular data
                data_lines = [line for line in lines if '|' in line or '\t' in line]
                if len(data_lines) > 1:
                    # Try to create a DataFrame from the tabular data
                    try:
                        # This is a simplified parser - in reality you might want more robust parsing
                        self.analytics.display_analytics({'message': 'Data visualization attempted', 'raw_data': clean_result}, 
                                                       analytics_type, f"Analytics: {query}")
                        return f"**Analytics displayed for:** {query}\n\nNote: Complex data format detected, showing summary visualization.\n\nRaw query result:\n{clean_result}"
                    except:
                        pass
            
            # Fallback - create analytics from summary text
            summary_data = {
                'query': query,
                'result_length': len(clean_result),
                'result_preview': clean_result[:200] + "..." if len(clean_result) > 200 else clean_result
            }
            self.analytics.display_analytics(summary_data, "table", f"Query Summary: {query}")
            return f"**Analytics displayed for:** {query}\n\n{clean_result}"
            
        except Exception as e:
            return f"""**Analytics Error**
Query: {query}
Error processing data for visualization: {str(e)}

Raw query result:
{clean_result}"""
    
    def chat(self, message: str) -> str:
        """General chat interface for any request"""
        orchestrator_prompt = f"""
            USER REQUEST: {message}

            Analyze this request and handle it appropriately:
            - If it's a database URI, connect to it
            - If it's a question about the database, query it
            - If it's something else, handle it flexibly

            Current session info:
            {json.dumps(get_current_session(), indent=2)}

            Be adaptive and smart about what the user needs.
        """
        result = self.orchestrator.run(orchestrator_prompt)
        
        # Extract clean response from agent result
        if hasattr(result, 'final_answer'):
            return str(result.final_answer)
        else:
            clean_result = str(result).split('Final answer: ')[-1] if 'Final answer: ' in str(result) else str(result)
            return clean_result

