import os
import sys
import json
from datetime import datetime
from typing import List
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from dotenv import load_dotenv

from chat_agent import ChatAgent
from session_manager import session_mgr

load_dotenv()

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

@dataclass
class Message:
    type: MessageType
    content: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class CLIChatbot:
    def __init__(self, api_key: str):
        self.console = Console()
        self.chat_agent = ChatAgent(api_key=api_key)
        self.messages: List[Message] = []
        self.session_active = False
        
        # Command completions
        self.commands = [
            '/help', '/clear', '/history', '/session', '/export', 
            '/connect', '/query', '/schema', '/analytics', '/analyze', '/dashboard', 
            '/exit', '/quit'
        ]
        
        # Prompt style
        self.prompt_style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'input': '#ffffff',
        })
        
        # Initialize with welcome message
        self._add_system_message("Database Assistant initialized. Type /help for commands.")
    
    def _add_system_message(self, content: str):
        self.messages.append(Message(MessageType.SYSTEM, content))
    
    def _add_user_message(self, content: str):
        self.messages.append(Message(MessageType.USER, content))
    
    def _add_assistant_message(self, content: str):
        self.messages.append(Message(MessageType.ASSISTANT, content))
    
    def _add_error_message(self, content: str):
        self.messages.append(Message(MessageType.ERROR, content))
    
    def _render_message(self, message: Message) -> Panel:
        """Render a message as a rich Panel"""
        if message.type == MessageType.USER:
            return Panel(
                Text(message.content, style="cyan"),
                title=f"[bold cyan]You[/bold cyan] • {message.timestamp.strftime('%H:%M:%S')}",
                border_style="cyan",
                padding=(0, 1)
            )
        elif message.type == MessageType.ASSISTANT:
            if "```" in message.content:
                parts = message.content.split("```")
                rendered_parts = []
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        rendered_parts.append(Markdown(part))
                    else:
                        lines = part.split('\n', 1)
                        lang = lines[0].strip() if len(lines) > 1 and lines[0].strip() else "text"
                        code = lines[1] if len(lines) > 1 else part
                        rendered_parts.append(Syntax(code, lang, theme="monokai"))

                # ✅ Use Group instead of Panel.fit(*...)
                from rich.console import Group
                content = Group(*rendered_parts)
            else:
                content = Markdown(message.content)
            
            return Panel(
                content,
                title=f"[bold green]Assistant[/bold green] • {message.timestamp.strftime('%H:%M:%S')}",
                border_style="green",
                padding=(0, 1)
            )
        elif message.type == MessageType.SYSTEM:
            return Panel(
                Text(message.content, style="yellow"),
                title=f"[bold yellow]System[/bold yellow] • {message.timestamp.strftime('%H:%M:%S')}",
                border_style="yellow",
                padding=(0, 1)
            )
        else:  # ERROR
            return Panel(
                Text(message.content, style="red"),
                title=f"[bold red]Error[/bold red] • {message.timestamp.strftime('%H:%M:%S')}",
                border_style="red",
                padding=(0, 1)
            )
    
    def _display_help(self):
        """Display help information"""
        help_table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        
        commands = [
            ("/help", "Show this help message"),
            ("/clear", "Clear the chat history"),
            ("/history", "Show conversation history"),
            ("/session", "Show current database session info"),
            ("/export", "Export conversation to file"),
            ("/connect <uri>", "Quick connect to database"),
            ("/query <question>", "Quick query current database"),
            ("/schema", "Show database schema"),
            ("/analytics <query>", "Show analytics dashboard for query"),
            ("/analyze <query>", "Analyze data with visualizations"),
            ("/dashboard <query>", "Create analytics dashboard"),
            ("/exit or /quit", "Exit the application"),
        ]
        
        for cmd, desc in commands:
            help_table.add_row(cmd, desc)
        
        self.console.print(help_table)
    
    def _display_history(self):
        """Display conversation history"""
        if not self.messages:
            self.console.print("[yellow]No conversation history yet.[/yellow]")
            return
        
        for message in self.messages[-10:]:  # Show last 10 messages
            self.console.print(self._render_message(message))
    
    def _display_session_info(self):
        """Display current session information"""
        with self.console.status("[bold green]Fetching session info..."):
            result = self.chat_agent.chat("show me the current session details")
        self._add_assistant_message(result)
        self.console.print(self._render_message(self.messages[-1]))
    
    def _export_conversation(self):
        """Export conversation to file"""
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w') as f:
                for message in self.messages:
                    f.write(f"[{message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] ")
                    f.write(f"{message.type.value.upper()}: {message.content}\n\n")
            self._add_system_message(f"Conversation exported to {filename}")
            self.console.print(self._render_message(self.messages[-1]))
        except Exception as e:
            self._add_error_message(f"Failed to export: {str(e)}")
            self.console.print(self._render_message(self.messages[-1]))
    
    def _process_command(self, command: str) -> bool:
        """Process slash commands. Returns True if handled, False otherwise."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "/help":
            self._display_help()
            return True
        elif cmd == "/clear":
            self.console.clear()
            self.messages.clear()
            self._add_system_message("Chat history cleared.")
            self.console.print(self._render_message(self.messages[-1]))
            return True
        elif cmd == "/history":
            self._display_history()
            return True
        elif cmd == "/session":
            self._display_session_info()
            return True
        elif cmd == "/export":
            self._export_conversation()
            return True
        elif cmd == "/connect" and args:
            self._add_user_message(f"Connect to database: {args}")
            self.console.print(self._render_message(self.messages[-1]))
            
            # Show simple connecting message
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Connecting to database...", total=None)
                
                # Directly call database connection
                result = self.chat_agent.database_agent.connect_database(args)
                progress.update(task, completed=True)
            
            self._add_assistant_message(result)
            self.console.print(self._render_message(self.messages[-1]))
            return True
        elif cmd == "/query" and args:
            self._add_user_message(f"Query: {args}")
            self.console.print(self._render_message(self.messages[-1]))
            # Directly call database query
            result = self.chat_agent.database_agent.query_database(args)
            self._add_assistant_message(result)
            self.console.print(self._render_message(self.messages[-1]))
            return True
        elif cmd == "/schema":
            self._add_user_message("Show me the database schema")
            self.console.print(self._render_message(self.messages[-1]))
            self._process_message("Show me the database schema")
            return True
        elif cmd in ["/analytics", "/analyze", "/dashboard"]:
            if not args:
                # Show analytics help if no arguments provided
                help_text = """**Analytics Commands Help**

Use natural language to request database analytics:

**Examples:**
- `/analytics show all records in the database`
- `/dashboard count of users by region`  
- `/analyze latest 50 entries`
- `/analytics records in known_faces table`
- `/dashboard show me all data`

**Available Analytics Types:**
- **Dashboard** - Full analytics with charts, stats, and tables
- **Summary** - Quick statistics overview
- **Table** - Data table view

**Your Database Tables:** """ + (str(list(json.loads(session_mgr.get_session().schema_info)['tables']) if session_mgr.get_session() and session_mgr.get_session().schema_info else "No database connected"))

                self._add_assistant_message(help_text)
                self.console.print(self._render_message(self.messages[-1]))
                return True
            
            analytics_type = "dashboard" if cmd == "/dashboard" else "dashboard"
            if cmd == "/analyze":
                analytics_type = "dashboard"  # Default to dashboard for analyze
            
            self._add_user_message(f"Analytics request: {args}")
            self.console.print(self._render_message(self.messages[-1]))
            
            # Call analytics method directly
            result = self.chat_agent.database_agent.analyze_data(args, analytics_type)
            self._add_assistant_message(result)
            self.console.print(self._render_message(self.messages[-1]))
            return True
        elif cmd in ["/exit", "/quit"]:
            return True
        
        return False
    
    def _process_message(self, user_input: str):
        """Process regular messages through the chat agent"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Thinking...", total=None)
            
            try:
                result = self.chat_agent.chat(user_input)
                progress.update(task, completed=True)
                self._add_assistant_message(result)
                self.console.print(self._render_message(self.messages[-1]))
            except Exception as e:
                progress.update(task, completed=True)
                self._add_error_message(f"Error: {str(e)}")
                self.console.print(self._render_message(self.messages[-1]))
    
    def run(self):
        """Main chat loop"""
        # Clear screen and show header
        self.console.clear()
        
        # Display header
        header = Panel(
            Text.from_markup(
                "[bold cyan]Database Assistant CLI[/bold cyan]\n"
                "[dim]Your intelligent database companion[/dim]\n\n"
                "[yellow]Type /help for commands • Ctrl+C to exit[/yellow]"
            ),
            border_style="bright_blue",
            padding=(1, 2)
        )
        self.console.print(header)
        self.console.print()
        
        # Show initial system message
        self.console.print(self._render_message(self.messages[0]))
        
        # History file for prompt
        history = FileHistory('.chat_history')
        
        # Command completer
        completer = WordCompleter(self.commands, ignore_case=True)
        
        while True:
            try:
                # Get user input with advanced features
                user_input = prompt(
                    "You > ",
                    history=history,
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=completer,
                    style=self.prompt_style,
                    multiline=False
                ).strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', '/exit', '/quit']:
                    self.console.print("\n[bold green]Goodbye! Thanks for using Database Assistant![/bold green]")
                    break
                
                # Process commands
                if user_input.startswith('/'):
                    if self._process_command(user_input):
                        if user_input.lower() in ['/exit', '/quit']:
                            self.console.print("\n[bold green]Goodbye! Thanks for using Database Assistant![/bold green]")
                            break
                    else:
                        self._add_error_message(f"Unknown command: {user_input}")
                        self.console.print(self._render_message(self.messages[-1]))
                else:
                    # Regular message
                    self._add_user_message(user_input)
                    self.console.print(self._render_message(self.messages[-1]))
                    self._process_message(user_input)
                
                self.console.print()  # Add spacing between messages
                
            except KeyboardInterrupt:
                self.console.print("\n\n[bold yellow]Interrupted. Type /exit to quit or continue chatting.[/bold yellow]")
                continue
            except EOFError:
                break
            except Exception as e:
                self._add_error_message(f"Unexpected error: {str(e)}")
                self.console.print(self._render_message(self.messages[-1]))

def main():
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console = Console()
        console.print("[bold red]Error: OPENAI_API_KEY environment variable not set![/bold red]")
        console.print("\nPlease set it using:")
        console.print("[cyan]export OPENAI_API_KEY='your-api-key-here'[/cyan]")
        sys.exit(1)
    
    # Create and run the chatbot
    bot = CLIChatbot(api_key)
    
    try:
        bot.run()
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()