# Docs2App 🚀

AI-powered tool that analyzes software documentation PDFs and generates complete application code with Claude Code implementation tasks.

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

### Local Development
```bash
# Setup Python environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Analyze without Docker
python main.py analyze document.pdf --project-name "test"
```

## 📋 Requirements

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **8GB RAM** (for Ollama models)
- **API Keys** (optional, for OpenAI/Azure)

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
