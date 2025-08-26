# Docs2App 🚀

[![CI](https://github.com/Mirakulix/Docs2App/actions/workflows/ci.yml/badge.svg)](https://github.com/Mirakulix/Docs2App/actions/workflows/ci.yml)
[![Code Quality](https://github.com/Mirakulix/Docs2App/actions/workflows/code-quality.yml/badge.svg)](https://github.com/Mirakulix/Docs2App/actions/workflows/code-quality.yml)
[![Docker Build](https://github.com/Mirakulix/Docs2App/actions/workflows/docker.yml/badge.svg)](https://github.com/Mirakulix/Docs2App/actions/workflows/docker.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Unlicense-green.svg)](https://unlicense.org)

AI-powered tool that analyzes software documentation PDFs and generates complete application code with Claude Code implementation tasks. Features comprehensive CI/CD pipelines, Docker containerization, and multi-AI provider support.

## 🎯 Features

- **Multi-AI Support**: Ollama (local), OpenAI, Azure OpenAI
- **Smart PDF Analysis**: Extract features, requirements, and technical specs
- **Automated Code Generation**: Complete project structures with files
- **Claude Code Integration**: Ready-to-use implementation tasks
- **Docker Ready**: Full containerization with Docker Compose

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and setup
git clone <repository>
cd Docs2App

# Quick start (builds everything)
make quick-start

# Place PDF files in ./pdfs directory
# Then analyze them
make analyze PROJECT=myapp
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
# Edit .env with your API keys

# Analyze PDFs
python main.py analyze document.pdf --project-name "MyApp"
```

## 🐳 Docker Usage

### Basic Commands

```bash
# Start all services (includes Ollama)
make up

# Check system health
make health

# Analyze PDFs in ./pdfs directory
make analyze PROJECT=myproject

# View logs
make logs

# Interactive shell
make shell

# Stop services
make down
```

### Available Services

- **docs2app**: Main application
- **ollama**: Local AI model server (llama3.1:8b)
- **redis**: Caching (optional, use `make up-full`)
- **postgres**: Database (optional, use `make up-full`)

## 📁 Project Structure

```
Docs2App/
├── docs2app/           # Main Python package
│   ├── core/          # Core processing
│   ├── extractors/    # PDF extraction
│   ├── analyzers/     # Feature analysis
│   └── generators/    # Code generation
├── pdfs/              # Input PDF files
├── output/            # Generated projects
├── config.yaml        # Configuration
├── docker-compose.yaml # Docker services
└── Makefile          # Build automation
```

## 🔧 Configuration

### AI Provider Setup

#### Ollama (Default - No API Key Needed)
```bash
# Included in Docker setup
make up
```

#### OpenAI
```bash
# Add to .env file
OPENAI_API_KEY=your_api_key_here
```

#### Azure OpenAI
```bash
# Add to .env file
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment
```

## 📝 Usage Examples

### Analyze Single PDF
```bash
make analyze-file FILE=requirements.pdf PROJECT=webapp
```

### Batch Process Directory
```bash
# Place PDFs in ./pdfs/
make analyze PROJECT=myapp
```

### Custom Configuration
```bash
# Change AI provider
make config
docker-compose exec docs2app python main.py config --provider openai
```

## 🎯 Output

Generated projects include:

- **Project Structure**: Complete directory layout
- **Source Code**: Framework-specific implementation
- **claude-tasks.json**: Detailed Claude Code tasks
- **implementation-plan.json**: Development roadmap
- **README.md**: Project documentation
- **Configuration Files**: Framework configs

## 🧪 Example: Sudoku App

See the included Sudoku example:

```bash
# Test with Sudoku PDF (included)
make analyze-file FILE=sudoku-requirements.pdf PROJECT=sudoku-app

# Check generated webapp
ls output/sudoku-app/
```

## 🛠️ Development

### Available Make Commands

```bash
make help           # Show all commands
make build          # Build Docker images
make test           # Run tests
make lint           # Code linting
make clean          # Clean up Docker
make debug          # Debug mode
```

### Continuous Integration

This project uses GitHub Actions for automated testing and quality assurance:

- **CI Workflow**: Comprehensive testing suite including unit tests, integration tests, and type checking
- **Code Quality**: Automated linting with Black, isort, flake8, mypy, pylint, and bandit
- **Security Scanning**: Vulnerability detection with safety and pip-audit  
- **Docker Build**: Multi-stage containerization with health checks
- **Multi-Python Support**: Tests against Python 3.11 and 3.12
- **Dependency Management**: Automated security and compatibility checks

All workflows run on push to `main`/`develop` branches and pull requests. The project maintains high code quality standards with comprehensive linting, type safety, and security scanning.

### Code Quality & Testing

This project maintains high code quality standards:

**Type Checking**
```bash
# Static type checking with mypy
python -m mypy docs2app/ main.py --ignore-missing-imports
```

**Code Formatting & Linting**
```bash
# Format code with Black
python -m black docs2app/ main.py --line-length 88

# Sort imports with isort  
python -m isort docs2app/ main.py --profile black

# Lint with flake8
python -m flake8 docs2app/ main.py --max-line-length=88

# Security scanning with bandit
python -m bandit -r docs2app/ -f json
```

**Testing**
```bash
# Run test suite
python -m pytest tests/ -v --cov=docs2app

# Test with Docker
make test
```

### Local Development
```bash
# Setup Python environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install core dependencies (tested working combination)
pip install -r requirements.txt

# Optional: Install development tools
pip install -r requirements-dev.txt

# Test installation
python test_functionality.py

# Run tests
python -m pytest tests/

# Analyze without Docker
python main.py analyze document.pdf --project-name "test"
```

## 📋 Requirements

- **Docker & Docker Compose** (recommended for deployment)
- **Python 3.11+** (required for local development) 
- **8GB RAM** (recommended for Ollama AI models)
- **API Keys** (optional, for OpenAI/Azure providers)

### Dependencies

This project uses carefully tested Python libraries with guaranteed compatibility:

**Core Dependencies** (`requirements.txt` - always installs cleanly):
- **AI Libraries**: OpenAI 1.3.5, Ollama 0.1.7, httpx 0.25.2 for reliable API communication
- **PDF Processing**: pdfplumber 0.10.3, PyPDF2 3.0.1 for robust text extraction  
- **Core Tools**: pydantic 1.10.12, pytest 7.4.3, mypy 1.8.0

**Development Dependencies** (`requirements-dev.txt` - install after core):
- **Data Processing**: pandas 2.1.4, numpy 1.26.4, scikit-learn 1.3.2, spacy 3.6.1
- **Code Quality**: black 23.12.1, isort 5.13.2, flake8 6.1.0
- **Testing**: pytest extensions, security tools

**Testing**: Run `python test_functionality.py` to verify installation.

**Note**: The dependency versions are specifically chosen to avoid conflicts. Install core dependencies first, then development tools separately.

## 🔍 Troubleshooting

### Common Issues

1. **Ollama not starting**: Increase Docker memory to 8GB
2. **PDF processing fails**: Check file permissions in `./pdfs`
3. **API errors**: Verify API keys in `.env`

### Health Check
```bash
make health
```

### Debug Mode
```bash
make debug
```

## 📄 License

Unlicense - Public Domain

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📞 Support

- **Health Check**: `make health`
- **Logs**: `make logs`
- **Shell Access**: `make shell`
- **Documentation**: See CLAUDE.md for development details
