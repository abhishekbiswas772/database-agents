import json
from typing import Dict, Any
from smolagents import CodeAgent, OpenAIServerModel
from database_agents import DatabaseAgent  
from session_manager import session_mgr

class ChatAgent:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.model = OpenAIServerModel(
            model_id=model,
            api_key=api_key
        )
        self.database_agent = DatabaseAgent(api_key=api_key)  
        self.chat_orchestrator = CodeAgent(
            tools=[],
            model=self.model,
            # max_steps=10,
            instructions=self._get_chat_instructions(),
            additional_authorized_imports=["json"]
        )

    def _get_chat_instructions(self) -> str:
        return """
            You are a friendly, conversational CLI chatbot. Your job is to:
            1. Handle natural language conversations (greetings, casual chat, etc.)
            2. Identify when the user is asking about database-related tasks
            3. Delegate database tasks to the DatabaseAgent without hardcoding logic
            4. Respond in a natural, human-like way

            ### Guidelines:
            - Be friendly, engaging, and conversational.
            - For casual chat (e.g., "hi", "hello", "how are you"), respond naturally without involving the DatabaseAgent.
            - For database-related requests (e.g., "give me all host names", "connect to my database", "what is the db type"), delegate to the DatabaseAgent by generating a prompt for it.
            - Do NOT hardcode logic, regex, or predefined patterns—rely on your understanding of the user's intent.
            - If the user provides a database URI, treat it as a connection request and delegate to the DatabaseAgent.
            - If the user asks about database details (e.g., host names, db type), delegate to the DatabaseAgent to query the current session.
            - If the user input is unclear, ask for clarification in a friendly way.

            ### How to Delegate to DatabaseAgent:
            - For connection requests, use the `connect_database` method with the provided URI.
            - For database queries, use the `query_database` method with the user's question.
            - For general database-related tasks, use the `chat` method with the user's message.

            ### Current Session Info:
            You can access the current session info to provide context. Use this to inform your responses or delegation:
            ```python
            current_session = json.dumps(get_current_session(), indent=2)
            ```

            ### Response Format:
            - For casual chat, return a string with your natural language response.
            - For database tasks, create a Python dictionary (not JSON) like this:
            ```python
            response = {
                "delegate_to_database_agent": True,
                "method": "connect_database",  # or "query_database" or "chat"
                "input": "user_input_or_prompt"
            }
            final_answer(response)
            ```
            - If clarification is needed, return a string asking for more details.
        """
    def _handle_database_delegation(self, delegation_info: Dict[str, Any]) -> str:
        method = delegation_info["method"]
        input_data = delegation_info["input"]

        if method == "connect_database":
            return self.database_agent.connect_database(input_data)
        elif method == "query_database":
            return self.database_agent.query_database(input_data)
        elif method == "chat":
            return self.database_agent.chat(input_data)
        else:
            return "Error: Invalid delegation method."

    def chat(self, user_input: str) -> str:
        current_session = session_mgr.get_session()
        session_info = json.dumps(
            {
                "session_id": current_session.session_id if current_session else None,
                "db_uri": current_session.db_uri if current_session else None,
                "db_type": current_session.db_type if current_session else None,
                "connected": current_session.connected if current_session else False,
                "schema_info": current_session.schema_info if current_session else None
            },
            indent=2
        )

        orchestrator_prompt = f"""
        USER INPUT: {user_input}

        CURRENT SESSION INFO:
        {session_info}

        Respond according to the guidelines in the instructions.
        """
    
        orchestrator_response = self.chat_orchestrator.run(orchestrator_prompt)
        
        # Check if response is already a dict (from agent execution)
        if isinstance(orchestrator_response, dict):
            delegation_info = orchestrator_response
        else:
            try:
                delegation_info = json.loads(orchestrator_response)
            except json.JSONDecodeError:
                # If it's not JSON, return the raw response
                return str(orchestrator_response)
        
        if delegation_info.get("delegate_to_database_agent", False):
            return self._handle_database_delegation(delegation_info)
        else:
            return str(orchestrator_response)
