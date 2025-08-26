# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docs2App is an AI-powered tool that analyzes software documentation PDFs and generates application code with Claude Code tasks. It supports multiple AI providers (Ollama, OpenAI, Azure OpenAI) for feature analysis and code generation.

## Development Commands

### Docker Development (Recommended)
```bash
# Quick setup
make quick-start

# Start services
make up

# Health check
make health

# Analyze PDFs
make analyze PROJECT=myapp

# Interactive shell
make shell

# View logs
make logs

# Stop services
make down
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with API keys

# Run application
python main.py analyze document.pdf --project-name "MyApp"
python main.py health-check
python main.py batch ./pdfs/ --project-name "BatchApp"
python main.py config --show
```

### Testing
```bash
# Docker
make test

# Local
python -m pytest tests/
```

## Architecture

### Core Components
- `docs2app/core/document_processor.py`: Main orchestrator
- `docs2app/core/ai_providers.py`: AI provider implementations (Ollama, OpenAI, Azure)
- `docs2app/core/config.py`: Configuration management

### Processing Pipeline
1. **PDF Extraction**: Extract text using pdfplumber/PyPDF2
2. **Document Segmentation**: Identify sections (features, requirements, etc.)
3. **AI Feature Analysis**: Extract and categorize features using AI
4. **Code Generation**: Generate project structure and Claude Code tasks

### AI Provider Configuration
- **Ollama**: Local AI models (default: llama3.1:8b)
- **OpenAI**: GPT models (default: gpt-4o-mini)
- **Azure OpenAI**: Enterprise OpenAI deployment

## Key Files
- `main.py`: CLI entry point
- `config.yaml`: Main configuration
- `.env`: Environment variables for API keys
- `requirements.txt`: Python dependencies

## Output Structure
Generated projects include:
- Project structure with directories and files
- `claude-tasks.json`: Detailed tasks for Claude Code
- `implementation-plan.json`: Project roadmap
- `README.md`: Project documentation

## Docker Workflow

### Container Services
- **docs2app**: Main application container
- **ollama**: Local AI model server (llama3.1:8b)
- **redis**: Caching (optional with `make up-full`)
- **postgres**: Database (optional with `make up-full`)

### Docker Commands
```bash
# Build and start everything
make quick-start

# Individual services
make up           # Start core services
make up-full      # Start with optional services
make down         # Stop all services
make restart      # Restart services

# Analysis
make analyze PROJECT=myapp                    # Batch process ./pdfs/
make analyze-file FILE=doc.pdf PROJECT=webapp # Single file

# Maintenance
make logs         # View all logs
make logs-app     # App logs only
make clean        # Clean Docker resources
make backup       # Backup current state
```

## AI Provider Setup

### Ollama (Default - Docker)
```bash
# Included in Docker setup
make up
# Model auto-downloads on first start
```

### OpenAI/Azure (API Keys)
```bash
# Add to .env file
OPENAI_API_KEY=your_key
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment

# Switch provider
make config
# or
docker-compose exec docs2app python main.py config --provider openai
```