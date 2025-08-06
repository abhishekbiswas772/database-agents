# Database Assistant CLI

A powerful, AI-driven command-line interface for interacting with databases through natural language. Connect to any database, ask questions, and visualize data with intelligent agent-based processing.

## Features

- **Universal Database Support**: MySQL, PostgreSQL, MongoDB, Redis, SQLite
- **Natural Language Queries**: Ask questions in plain English
- **Interactive Analytics**: Real-time data visualization in the terminal
- **AI-Powered Agents**: Specialized agents for connection, querying, and analysis
- **Rich CLI Experience**: Beautiful terminal interface with syntax highlighting
- **Session Management**: Persistent connections and schema caching
- **Export Functionality**: Save conversations and analysis results

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Architecture](#architecture)
- [Commands Reference](#commands-reference)
- [Database Support](#database-support)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd poc

# 2. Install dependencies with uv
uv install

# 3. Set up your OpenAI API key
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env

# 4. Run the application
python main.py
```

Once running, try these commands:
```
/connect postgresql://user:pass@localhost:5432/mydb
/analytics show me all records in the users table
/query what are the top 10 most active users?
```

## Installation

### Prerequisites

- **Python 3.12+** (Required)
- **uv package manager** (Recommended - faster than pip)
- **OpenAI API Key** (For AI agent functionality)

### Step-by-Step Installation

1. **Install Python 3.12+**
   ```bash
   # Check your Python version
   python --version
   ```

2. **Install uv (if not already installed)**
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Clone and setup the project**
   ```bash
   git clone <your-repo-url>
   cd poc
   uv install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env  # If .env.example exists
   # Or create .env manually:
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

### Alternative Installation with pip

```bash
pip install -r requirements.txt  # If requirements.txt is generated
```

## � Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional
DEFAULT_MODEL=gpt-4o-mini
MAX_AGENT_STEPS=15
ENABLE_DOCKER=true
```

### Database Connection Strings

The application supports various database connection formats:

```bash
# PostgreSQL
postgresql://user:password@host:port/database

# MySQL
mysql://user:password@host:port/database
mysql+pymysql://user:password@host:port/database

# MongoDB
mongodb://user:password@host:port/database
mongodb+srv://user:password@cluster.mongodb.net/database

# SQLite
sqlite:///path/to/database.db

# Redis
redis://user:password@host:port/database
```

## Usage Guide

### Starting the Application

```bash
python main.py
```

You'll see a welcome screen with the Database Assistant CLI interface.

### Basic Workflow

1. **Connect to Database**
   ```
   /connect postgresql://user:pass@localhost:5432/mydb
   ```

2. **Explore Your Data**
   ```
   /schema
   /analytics show me all tables
   ```

3. **Ask Natural Language Questions**
   ```
   What are the top 5 customers by revenue?
   Show me users who signed up this month
   /query count of orders by status
   ```

4. **Create Visualizations**
   ```
   /dashboard sales data by month
   /analyze user engagement metrics
   ```

### Interactive Features

- **Auto-completion**: Tab to complete commands
- **History**: Use arrow keys to navigate command history
- **Multi-line**: Continue typing for complex queries
- **Export**: Save your analysis with `/export`


### Agent Architecture

The system uses three specialized AI agents:

#### 1. **Orchestrator Agent**
- **Role**: Main coordinator and intent understanding
- **Responsibilities**: 
  - Parse user requests
  - Delegate to appropriate specialized agents
  - Coordinate overall workflow

#### 2. **Connector Agent**
- **Role**: Database connection specialist
- **Responsibilities**:
  - Establish database connections
  - Auto-detect database types
  - Extract and cache schema information
  - Handle connection errors gracefully

#### 3. **Querier Agent**
- **Role**: Query execution and data retrieval
- **Responsibilities**:
  - Convert natural language to SQL/NoSQL queries
  - Execute queries safely
  - Format results for visualization
  - Handle different database syntaxes

### Key Components

#### **Main CLI (main.py)**
- Rich-based terminal interface
- Command routing and history management
- Message rendering with syntax highlighting
- Progress indicators and error handling

#### **Session Management (session_manager.py)**
- Persistent connection state
- Schema information caching
- Connection code storage
- Session lifecycle management

#### **Analytics Visualizer (analytics_visualizer.py)**
- Terminal-based charts and graphs
- Summary statistics generation
- Data table formatting
- Dashboard layout management

## =� Commands Reference

### Connection Commands
```bash
/connect <database_uri>     # Connect to database
/session                    # Show current session info
```

### Query Commands
```bash
/query <question>          # Ask natural language questions
/schema                    # Display database schema
```

### Analytics Commands
```bash
/analytics <request>       # General analytics request
/dashboard <request>       # Create analytics dashboard
/analyze <request>         # Analyze data with visualizations
```

### Utility Commands
```bash
/help                      # Show command help
/history                   # View conversation history
/clear                     # Clear chat history
/export                    # Export conversation to file
/exit or /quit            # Exit application
```

### Analytics Examples
```bash
/analytics show all records in the database
/dashboard count of users by region
/analyze latest 50 entries
/analytics records in known_faces table
```

## =� Database Support

### Supported Databases

| Database | Connection String | Driver | Features |
|----------|-------------------|---------|----------|
| PostgreSQL | `postgresql://...` | `psycopg2` | Full SQL support |
| MySQL | `mysql://...` | `pymysql` | Full SQL support |
| MongoDB | `mongodb://...` | `pymongo` | Document queries |
| SQLite | `sqlite://...` | Built-in | File-based SQL |
| Redis | `redis://...` | `redis-py` | Key-value operations |

### Connection Examples

```bash
# Local PostgreSQL
/connect postgresql://postgres:password@localhost:5432/myapp

# Remote MySQL
/connect mysql://user:pass@mysql.example.com:3306/production

# MongoDB Atlas
/connect mongodb+srv://user:pass@cluster.mongodb.net/mydb

# Local SQLite
/connect sqlite:///./data/app.db

# Redis with auth
/connect redis://:password@localhost:6379/0
```

## =� Examples

### Basic Usage Example

```bash
$ python main.py

# Connect to your database
You > /connect postgresql://user:pass@localhost:5432/ecommerce

# Explore the schema
You > /schema

# Ask business questions
You > What are our top selling products this month?

# Create visualizations
You > /dashboard sales trends by product category

# Export your analysis
You > /export
```

### Advanced Analytics Example

```bash
# Complex data analysis
You > /analyze user behavior patterns for last 90 days

# Custom dashboard
You > /dashboard show revenue, user count, and order volume by month

# Cross-table analysis
You > What's the correlation between user registration date and lifetime value?
```

### Natural Language Query Examples

```bash
"Show me users who haven't logged in for 30 days"
"What's the average order value by customer segment?"
"Find products with inventory below 10 units"
"Compare sales performance across different regions"
"Show me the most active users this week"
```

## =' Troubleshooting

### Common Issues

#### **Connection Issues**
```bash
# Error: Connection timeout
- Check if database server is running
- Verify network connectivity
- Confirm connection string format

# Error: Authentication failed
- Double-check username/password
- Verify database permissions
- Check SSL requirements
```

#### **Environment Issues**
```bash
# Error: OPENAI_API_KEY not set
echo "OPENAI_API_KEY=your-key-here" > .env

# Error: Missing dependencies
uv install --all-extras

# Error: Python version
python --version  # Should be 3.12+
```

#### **Performance Issues**
```bash
# Large datasets causing slowdowns
- Use LIMIT clauses in queries
- Enable pagination in analytics
- Consider database indexing
```

### Debug Mode

Enable verbose logging:
```bash
export DEBUG=1
python main.py
```

### Getting Help

1. **In-app help**: Use `/help` command
2. **Check logs**: Look for error messages in terminal
3. **Verify setup**: Ensure all dependencies are installed
4. **Test connection**: Try with a simple local database first

## > Contributing

### Development Setup

```bash
# Fork and clone
git clone <your-fork>
cd poc

# Install development dependencies
uv install --dev

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
python main.py

# Commit and push
git commit -m "Add your feature"
git push origin feature/your-feature
```

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to functions
- Test with multiple database types

### Testing

```bash
# Run manual tests with different databases
python main.py

# Test connection strings
/connect sqlite:///test.db
/connect postgresql://test:test@localhost:5432/test
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [smolagents](https://github.com/huggingface/smolagents) - AI agent framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [OpenAI](https://openai.com/) - Language model API
- Database driver maintainers and communities

## Links

- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Python 3.12 Download](https://www.python.org/downloads/)

---

**Need help?** Open an issue or start a discussion in the repository!
