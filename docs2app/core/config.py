"""
Configuration management for Docs2App
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1:8b"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


@dataclass
class OpenAIConfig:
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


@dataclass
class AzureOpenAIConfig:
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    api_version: str = "2024-02-15-preview"
    deployment_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


@dataclass
class AIProvidersConfig:
    default: str = "ollama"
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    azure: AzureOpenAIConfig = field(default_factory=AzureOpenAIConfig)


@dataclass
class PDFConfig:
    method: str = "pdfplumber"
    preprocess: bool = True
    max_file_size_mb: int = 50


@dataclass
class AnalysisConfig:
    min_confidence: float = 0.6
    enable_implicit_features: bool = True
    categorization_threshold: float = 0.7
    feature_categories: Dict[str, float] = field(default_factory=lambda: {
        "core": 1.0,
        "optional": 0.7,
        "technisch": 0.8,
        "ui": 0.6,
        "api": 0.9
    })


@dataclass
class GenerationConfig:
    output_format: str = "structured"
    include_tests: bool = True
    include_documentation: bool = True
    framework_preferences: Dict[str, list] = field(default_factory=lambda: {
        "frontend": ["react", "vue", "svelte"],
        "backend": ["fastapi", "django", "flask"],
        "database": ["postgresql", "sqlite", "mongodb"]
    })


@dataclass
class OutputConfig:
    directory: str = "./output"
    create_project_structure: bool = True
    generate_readme: bool = True
    include_claude_tasks: bool = True


@dataclass
class AppConfig:
    ai_providers: AIProvidersConfig = field(default_factory=AIProvidersConfig)
    pdf: PDFConfig = field(default_factory=PDFConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


class ConfigManager:
    """Manage application configuration from YAML file and environment variables"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("CONFIG_FILE", "config.yaml")
        self.config = self._load_config()
    
    def _load_config(self) -> AppConfig:
        """Load configuration from YAML file and environment variables"""
        config_data = {}
        
        # Load from YAML file if it exists
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        
        # Override with environment variables
        config_data = self._apply_env_variables(config_data)
        
        # Create configuration objects
        return self._create_config_objects(config_data)
    
    def _apply_env_variables(self, config_data: Dict) -> Dict:
        """Apply environment variable overrides"""
        # Process AI provider configs
        if "ai_providers" not in config_data:
            config_data["ai_providers"] = {}
        
        ai_config = config_data["ai_providers"]
        
        # OpenAI
        if "openai" not in ai_config:
            ai_config["openai"] = {}
        ai_config["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
        
        # Azure OpenAI
        if "azure" not in ai_config:
            ai_config["azure"] = {}
        ai_config["azure"]["api_key"] = os.getenv("AZURE_OPENAI_API_KEY")
        ai_config["azure"]["endpoint"] = os.getenv("AZURE_OPENAI_ENDPOINT")
        ai_config["azure"]["deployment_name"] = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        
        # Ollama
        if "ollama" not in ai_config:
            ai_config["ollama"] = {}
        if os.getenv("OLLAMA_BASE_URL"):
            ai_config["ollama"]["base_url"] = os.getenv("OLLAMA_BASE_URL")
        
        return config_data
    
    def _create_config_objects(self, config_data: Dict) -> AppConfig:
        """Create typed configuration objects from dictionary"""
        # AI Providers
        ai_data = config_data.get("ai_providers", {})
        
        ollama_config = OllamaConfig(**ai_data.get("ollama", {}))
        openai_config = OpenAIConfig(**ai_data.get("openai", {}))
        azure_config = AzureOpenAIConfig(**ai_data.get("azure", {}))
        
        ai_providers = AIProvidersConfig(
            default=ai_data.get("default", "ollama"),
            ollama=ollama_config,
            openai=openai_config,
            azure=azure_config
        )
        
        # Other configurations
        pdf_config = PDFConfig(**config_data.get("pdf", {}))
        analysis_config = AnalysisConfig(**config_data.get("analysis", {}))
        generation_config = GenerationConfig(**config_data.get("generation", {}))
        output_config = OutputConfig(**config_data.get("output", {}))
        
        return AppConfig(
            ai_providers=ai_providers,
            pdf=pdf_config,
            analysis=analysis_config,
            generation=generation_config,
            output=output_config
        )
    
    def get_active_ai_provider(self) -> str:
        """Get the currently active AI provider"""
        return self.config.ai_providers.default
    
    def get_ai_config(self, provider: Optional[str] = None):
        """Get configuration for specified AI provider"""
        provider = provider or self.get_active_ai_provider()
        
        if provider == "ollama":
            return self.config.ai_providers.ollama
        elif provider == "openai":
            return self.config.ai_providers.openai
        elif provider == "azure":
            return self.config.ai_providers.azure
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration and return any issues"""
        issues = {
            "errors": [],
            "warnings": []
        }
        
        # Validate AI provider configurations
        provider = self.get_active_ai_provider()
        
        if provider == "openai":
            if not self.config.ai_providers.openai.api_key:
                issues["errors"].append("OpenAI API key not configured")
        
        elif provider == "azure":
            azure_config = self.config.ai_providers.azure
            if not azure_config.api_key:
                issues["errors"].append("Azure OpenAI API key not configured")
            if not azure_config.endpoint:
                issues["errors"].append("Azure OpenAI endpoint not configured")
            if not azure_config.deployment_name:
                issues["errors"].append("Azure OpenAI deployment name not configured")
        
        elif provider == "ollama":
            # Ollama validation could check if service is running
            pass
        
        # Validate output directory
        output_dir = Path(self.config.output.directory)
        if not output_dir.parent.exists():
            issues["warnings"].append(f"Output directory parent does not exist: {output_dir.parent}")
        
        return issues
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to YAML file"""
        path = config_path or self.config_path
        
        # Convert config objects back to dictionary
        config_dict = self._config_to_dict()
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def _config_to_dict(self) -> Dict:
        """Convert configuration objects to dictionary format"""
        # This is a simplified version - in a real implementation,
        # you'd want to properly serialize all dataclass objects
        return {
            "ai_providers": {
                "default": self.config.ai_providers.default,
                "ollama": {
                    "base_url": self.config.ai_providers.ollama.base_url,
                    "model": self.config.ai_providers.ollama.model,
                    "temperature": self.config.ai_providers.ollama.temperature,
                    "max_tokens": self.config.ai_providers.ollama.max_tokens,
                    "timeout": self.config.ai_providers.ollama.timeout
                }
                # Add other providers as needed
            }
            # Add other config sections as needed
        }