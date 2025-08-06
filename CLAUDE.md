# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Python CLI database assistant application that provides an interactive interface for connecting to and analyzing databases. The application uses AI agents to handle database connections, queries, and analytics visualization.

## Development Setup

### Requirements
- Python 3.12+
- uv package manager (already installed)

### Installation and Running
```bash
# Install dependencies
uv install

# Set up environment (create .env file with OPENAI_API_KEY)
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the application
python main.py
```

## Architecture Overview

### Core Components

**main.py** - Main CLI interface with Rich-based UI
- `CLIChatbot` class handles user interaction and command routing
- Supports slash commands (`/connect`, `/query`, `/analytics`, etc.)
- Manages conversation history and message rendering

**chat_agent.py** - Orchestration layer
- `ChatAgent` routes between casual conversation and database operations
- Delegates database tasks to `DatabaseAgent`
- Handles natural language to structured command translation

**database_agents.py** - Database operations using smolagents
- Three specialized AI agents: orchestrator, connector, and querier
- `connect_database()` - Establishes database connections with auto-detection
- `query_database()` - Executes queries and returns formatted results
- `analyze_data()` - Performs data analysis with visualization

**session_manager.py** - Session state management
- `DatabaseSession` dataclass tracks connection state, schema info, and connection code
- Global `session_mgr` maintains current session context

**analytics_visualizer.py** - Terminal-based data visualization
- `TerminalAnalytics` creates charts, tables, and dashboards using Rich
- Supports bar charts, correlation matrices, and summary statistics

**llm_tools.py** - Tool functions for AI agents
- Decorated functions for session creation, schema saving, and connection management

## Database Support

The application supports multiple database types:
- MySQL/MariaDB (`mysql://`, `mysql+pymysql://`)
- PostgreSQL (`postgresql://`, `postgres://`)
- MongoDB (`mongodb://`, `mongodb+srv://`)
- Redis (`redis://`)
- SQLite (`sqlite://`)

Connection URIs are auto-detected and appropriate drivers are used.

## CLI Commands

Available slash commands in the application:
- `/connect <uri>` - Connect to database
- `/query <question>` - Query current database
- `/analytics <query>` - Show analytics dashboard
- `/schema` - Display database schema
- `/session` - Show current session info
- `/history` - View conversation history
- `/clear` - Clear chat history
- `/export` - Export conversation to file

## Key Dependencies

- `smolagents` - AI agent framework with Docker support
- `openai` - GPT model integration
- `rich` - Terminal UI components
- `prompt_toolkit` - Advanced CLI input handling
- Database drivers: `psycopg2`, `pymysql`, `pymongo`, `redis`
- Data processing: `pandas`, `numpy`

## Environment Configuration

Required environment variable:
- `OPENAI_API_KEY` - OpenAI API key for GPT models

## Agent Architecture

The system uses a multi-agent approach:

1. **Orchestrator Agent** - Main coordinator, understands user intent
2. **Connector Agent** - Specializes in database connections and schema analysis
3. **Querier Agent** - Handles database queries and data retrieval

Each agent has specific instructions and can execute Python code with authorized imports for database operations.