"""
AI-powered code generation and Claude Code task creation
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from jinja2 import Template, Environment, FileSystemLoader
from ..core.ai_providers import AIProviderManager, AIMessage
from ..core.config import ConfigManager
from ..analyzers.feature_analyzer import Feature, FeatureAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ClaudeTask:
    """Represents a task for Claude Code"""
    id: str
    title: str
    description: str
    priority: str
    category: str
    dependencies: List[str]
    acceptance_criteria: List[str]
    technical_hints: List[str]
    files_to_create: List[str]
    files_to_modify: List[str]
    estimated_effort: str  # klein/mittel/groß


@dataclass
class ProjectStructure:
    """Represents the generated project structure"""
    name: str
    description: str
    technology_stack: Dict[str, str]
    directories: List[str]
    files: Dict[str, str]  # filename -> content
    dependencies: Dict[str, List[str]]  # package.json, requirements.txt etc.


@dataclass
class CodeGenerationResult:
    """Result of code generation process"""
    project_structure: ProjectStructure
    claude_tasks: List[ClaudeTask]
    implementation_plan: Dict
    readme_content: str
    generated_at: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class CodeGenerator:
    """AI-powered code and task generation for Claude Code"""
    
    def __init__(self, config_manager: ConfigManager, ai_manager: AIProviderManager):
        self.config = config_manager
        self.ai_manager = ai_manager
        self.generation_config = config_manager.config.generation
        self.output_config = config_manager.config.output
        
        # Template environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)) if template_dir.exists() else None
        )
        
        self.prompts = {
            "project_structure": self._get_project_structure_prompt(),
            "claude_tasks": self._get_claude_tasks_prompt(),
            "code_generation": self._get_code_generation_prompt(),
            "implementation_plan": self._get_implementation_plan_prompt()
        }
    
    async def generate_project(self, analysis_result: FeatureAnalysisResult, project_name: Optional[str] = None) -> CodeGenerationResult:
        """
        Generate complete project structure and Claude Code tasks
        
        Args:
            analysis_result: Results from feature analysis
            project_name: Optional project name override
            
        Returns:
            CodeGenerationResult with project structure and tasks
        """
        logger.info("Starting AI-powered project generation")
        
        if not project_name:
            project_name = analysis_result.project_metadata.get("name", "generated_app")
        
        # Step 1: Generate project structure
        project_structure = await self._generate_project_structure(analysis_result, project_name)
        
        # Step 2: Generate Claude Code tasks
        claude_tasks = await self._generate_claude_tasks(analysis_result, project_structure)
        
        # Step 3: Create implementation plan
        implementation_plan = await self._generate_implementation_plan(analysis_result, claude_tasks)
        
        # Step 4: Generate README
        readme_content = await self._generate_readme(analysis_result, project_structure, implementation_plan)
        
        result = CodeGenerationResult(
            project_structure=project_structure,
            claude_tasks=claude_tasks,
            implementation_plan=implementation_plan,
            readme_content=readme_content,
            generated_at=datetime.now().isoformat()
        )
        
        # Step 5: Write to filesystem if configured
        if self.output_config.create_project_structure:
            await self._write_project_to_filesystem(result)
        
        return result
    
    async def _generate_project_structure(self, analysis: FeatureAnalysisResult, project_name: str) -> ProjectStructure:
        """Generate project structure based on features"""
        logger.info("Generating project structure")
        
        # Prepare feature summary for AI
        features_summary = self._create_features_summary(analysis.features + analysis.implicit_features)
        
        messages = [
            AIMessage(role="system", content=self.prompts["project_structure"]),
            AIMessage(role="user", content=f"""
Projekt: {project_name}
Projektbeschreibung: {analysis.project_metadata.get('beschreibung', '')}

Features:
{features_summary}

Präferenzen: {self.generation_config.framework_preferences}

Generiere eine vollständige Projektstruktur.
""")
        ]
        
        try:
            response = await self.ai_manager.generate(messages, max_tokens=4000)
            structure_data = self._parse_ai_response(response.content)
            
            return ProjectStructure(
                name=project_name,
                description=structure_data.get("description", ""),
                technology_stack=structure_data.get("technology_stack", {}),
                directories=structure_data.get("directories", []),
                files=structure_data.get("files", {}),
                dependencies=structure_data.get("dependencies", {})
            )
            
        except Exception as e:
            logger.error(f"Project structure generation failed: {e}")
            # Return minimal fallback structure
            return self._create_fallback_structure(project_name)
    
    async def _generate_claude_tasks(self, analysis: FeatureAnalysisResult, structure: ProjectStructure) -> List[ClaudeTask]:
        """Generate Claude Code tasks for each feature"""
        logger.info("Generating Claude Code implementation tasks")
        
        all_features = analysis.features + analysis.implicit_features
        claude_tasks = []
        
        # Group features by priority and dependencies
        task_groups = self._group_features_for_tasks(all_features)
        
        for group_name, features in task_groups.items():
            tasks = await self._create_tasks_for_feature_group(features, structure, group_name)
            claude_tasks.extend(tasks)
        
        # Add setup tasks
        setup_tasks = self._create_setup_tasks(structure)
        claude_tasks = setup_tasks + claude_tasks
        
        # Add finalization tasks
        final_tasks = self._create_finalization_tasks(structure, analysis)
        claude_tasks.extend(final_tasks)
        
        return claude_tasks
    
    async def _create_tasks_for_feature_group(self, features: List[Feature], structure: ProjectStructure, group_name: str) -> List[ClaudeTask]:
        """Create Claude tasks for a group of related features"""
        
        features_text = "\n".join([
            f"- {f.feature_name}: {f.beschreibung}" for f in features
        ])
        
        messages = [
            AIMessage(role="system", content=self.prompts["claude_tasks"]),
            AIMessage(role="user", content=f"""
Feature-Gruppe: {group_name}

Features:
{features_text}

Projektstruktur: {structure.technology_stack}

Erstelle detaillierte Claude Code Tasks für diese Features.
""")
        ]
        
        try:
            response = await self.ai_manager.generate(messages, max_tokens=3000)
            tasks_data = self._parse_ai_response(response.content)
            
            tasks = []
            for task_dict in tasks_data.get("tasks", []):
                try:
                    task = ClaudeTask(**task_dict)
                    tasks.append(task)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not create task from {task_dict}: {e}")
            
            return tasks
            
        except Exception as e:
            logger.error(f"Task generation failed for {group_name}: {e}")
            return []
    
    async def _generate_implementation_plan(self, analysis: FeatureAnalysisResult, tasks: List[ClaudeTask]) -> Dict:
        """Generate high-level implementation plan"""
        logger.info("Generating implementation plan")
        
        messages = [
            AIMessage(role="system", content=self.prompts["implementation_plan"]),
            AIMessage(role="user", content=f"""
Projekt-Features: {len(analysis.features)} explizite, {len(analysis.implicit_features)} implizite Features
Claude Tasks: {len(tasks)} Tasks

Erstelle einen strukturierten Implementierungsplan mit Meilensteinen.
""")
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            return self._parse_ai_response(response.content)
        except Exception as e:
            logger.error(f"Implementation plan generation failed: {e}")
            return self._create_fallback_plan(tasks)
    
    async def _generate_readme(self, analysis: FeatureAnalysisResult, structure: ProjectStructure, plan: Dict) -> str:
        """Generate project README"""
        logger.info("Generating README")
        
        messages = [
            AIMessage(role="system", content="""
Erstelle eine professionelle README.md für ein Software-Projekt.
Struktur:
- Projektbeschreibung
- Features
- Technologie-Stack
- Installation
- Nutzung
- Entwicklung
- Lizenz

Verwende Markdown-Format.
"""),
            AIMessage(role="user", content=f"""
Projekt: {structure.name}
Beschreibung: {structure.description}
Technologien: {structure.technology_stack}
Features: {len(analysis.features)} Features
Meilensteine: {len(plan.get('milestones', []))} Meilensteine
""")
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            return response.content
        except Exception as e:
            logger.error(f"README generation failed: {e}")
            return self._create_fallback_readme(structure)
    
    async def _write_project_to_filesystem(self, result: CodeGenerationResult):
        """Write generated project to filesystem"""
        logger.info("Writing project to filesystem")
        
        project_dir = Path(self.output_config.directory) / result.project_structure.name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        for directory in result.project_structure.directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)
        
        # Write files
        for filename, content in result.project_structure.files.items():
            file_path = project_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Write README
        with open(project_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(result.readme_content)
        
        # Write Claude tasks
        with open(project_dir / "claude-tasks.json", 'w', encoding='utf-8') as f:
            json.dump([asdict(task) for task in result.claude_tasks], f, ensure_ascii=False, indent=2)
        
        # Write implementation plan
        with open(project_dir / "implementation-plan.json", 'w', encoding='utf-8') as f:
            json.dump(result.implementation_plan, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Project written to: {project_dir}")
    
    # Helper methods
    
    def _create_features_summary(self, features: List[Feature]) -> str:
        """Create a text summary of features for AI prompts"""
        summary_lines = []
        for feature in features:
            summary_lines.append(f"- {feature.feature_name} ({feature.kategorie}, {feature.priorität}): {feature.beschreibung}")
        return "\n".join(summary_lines)
    
    def _group_features_for_tasks(self, features: List[Feature]) -> Dict[str, List[Feature]]:
        """Group features into logical task groups"""
        groups = {
            "Authentifizierung": [],
            "Core Features": [],
            "API Integration": [],
            "User Interface": [],
            "Datenmanagement": [],
            "Technische Infrastruktur": []
        }
        
        for feature in features:
            if any(keyword in feature.feature_name.lower() for keyword in ["auth", "login", "benutzer", "user"]):
                groups["Authentifizierung"].append(feature)
            elif feature.kategorie == "api":
                groups["API Integration"].append(feature)
            elif feature.kategorie == "ui":
                groups["User Interface"].append(feature)
            elif feature.kategorie == "core":
                groups["Core Features"].append(feature)
            elif any(keyword in feature.feature_name.lower() for keyword in ["daten", "database", "speicher"]):
                groups["Datenmanagement"].append(feature)
            else:
                groups["Technische Infrastruktur"].append(feature)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _create_setup_tasks(self, structure: ProjectStructure) -> List[ClaudeTask]:
        """Create initial setup tasks"""
        return [
            ClaudeTask(
                id="setup-001",
                title="Projektstruktur erstellen",
                description="Erstelle die grundlegende Projektstruktur mit Verzeichnissen und Konfigurationsdateien",
                priority="hoch",
                category="setup",
                dependencies=[],
                acceptance_criteria=[
                    "Alle Projektverzeichnisse sind erstellt",
                    "package.json/requirements.txt ist konfiguriert",
                    "Grundlegende Konfigurationsdateien existieren"
                ],
                technical_hints=[
                    f"Verwende {structure.technology_stack}",
                    "Folge Best Practices für Projektstruktur"
                ],
                files_to_create=list(structure.files.keys()),
                files_to_modify=[],
                estimated_effort="mittel"
            )
        ]
    
    def _create_finalization_tasks(self, structure: ProjectStructure, analysis: FeatureAnalysisResult) -> List[ClaudeTask]:
        """Create final tasks like testing and documentation"""
        tasks = []
        
        if self.generation_config.include_tests:
            tasks.append(ClaudeTask(
                id="final-001",
                title="Tests implementieren",
                description="Erstelle Unit- und Integrationstests für alle Features",
                priority="hoch",
                category="testing",
                dependencies=["alle-feature-tasks"],
                acceptance_criteria=["Mindestens 80% Code Coverage", "Alle Critical Path Tests"],
                technical_hints=["Verwende pytest/jest je nach Stack"],
                files_to_create=["tests/", "test_*.py"],
                files_to_modify=[],
                estimated_effort="groß"
            ))
        
        if self.generation_config.include_documentation:
            tasks.append(ClaudeTask(
                id="final-002",
                title="Dokumentation vervollständigen",
                description="API-Dokumentation, Deployment Guide und User Manual erstellen",
                priority="mittel",
                category="documentation",
                dependencies=[],
                acceptance_criteria=["API Docs", "Deployment Guide", "User Manual"],
                technical_hints=["Verwende OpenAPI/Swagger für APIs"],
                files_to_create=["docs/", "api.yaml"],
                files_to_modify=["README.md"],
                estimated_effort="mittel"
            ))
        
        return tasks
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response JSON with fallback"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Could not parse AI response as JSON")
            return {}
    
    def _create_fallback_structure(self, project_name: str) -> ProjectStructure:
        """Create minimal fallback project structure"""
        return ProjectStructure(
            name=project_name,
            description="Generated application",
            technology_stack={"backend": "python", "frontend": "react"},
            directories=["src/", "tests/", "docs/"],
            files={"src/main.py": "# Main application file\n"},
            dependencies={"python": ["fastapi", "uvicorn"]}
        )
    
    def _create_fallback_plan(self, tasks: List[ClaudeTask]) -> Dict:
        """Create minimal fallback implementation plan"""
        return {
            "milestones": [
                {"name": "Setup", "tasks": [t.id for t in tasks[:2]]},
                {"name": "Core Features", "tasks": [t.id for t in tasks[2:-2]]},
                {"name": "Finalization", "tasks": [t.id for t in tasks[-2:]]}
            ],
            "estimated_duration": "4-6 weeks",
            "team_size": "1-2 developers"
        }
    
    def _create_fallback_readme(self, structure: ProjectStructure) -> str:
        """Create minimal fallback README"""
        return f"""# {structure.name}

{structure.description}

## Technology Stack

{', '.join(f"{k}: {v}" for k, v in structure.technology_stack.items())}

## Installation

```bash
# Installation steps will be added
```

## Usage

```bash
# Usage instructions will be added
```

## Development

This project was generated by Docs2App.
"""
    
    # Prompt templates
    
    def _get_project_structure_prompt(self) -> str:
        return """
Du bist ein Senior Software Architect. Erstelle eine vollständige Projektstruktur basierend auf den gegebenen Features.

Berücksichtige:
- Moderne Best Practices
- Skalierbare Architektur
- Framework-Präferenzen des Users
- Separation of Concerns

Antworte mit JSON:
{
  "description": "Projektbeschreibung",
  "technology_stack": {
    "backend": "framework",
    "frontend": "framework", 
    "database": "system",
    "deployment": "platform"
  },
  "directories": ["src/", "tests/", ...],
  "files": {
    "filename": "file content",
    ...
  },
  "dependencies": {
    "python": ["package1", "package2"],
    "npm": ["package1", "package2"]
  }
}
"""
    
    def _get_claude_tasks_prompt(self) -> str:
        return """
Du erstellst detaillierte Tasks für Claude Code (claude.ai/code).

Jeder Task sollte:
- Konkret und umsetzbar sein
- Klare Acceptance Criteria haben
- Technische Hinweise enthalten
- Dateien spezifizieren

Antworte mit JSON:
{
  "tasks": [
    {
      "id": "unique-id",
      "title": "Task Titel",
      "description": "Detaillierte Beschreibung", 
      "priority": "hoch/mittel/niedrig",
      "category": "feature/api/ui/data",
      "dependencies": ["andere-task-ids"],
      "acceptance_criteria": ["Kriterium 1", "Kriterium 2"],
      "technical_hints": ["Hinweis 1", "Hinweis 2"],
      "files_to_create": ["file1.py", "file2.js"],
      "files_to_modify": ["existing_file.py"],
      "estimated_effort": "klein/mittel/groß"
    }
  ]
}
"""
    
    def _get_code_generation_prompt(self) -> str:
        return """
Generiere funktionsfähigen Code für die spezifizierten Features.
Code sollte:
- Produktionsreif sein
- Best Practices befolgen
- Gut dokumentiert sein
- Testbar sein
"""
    
    def _get_implementation_plan_prompt(self) -> str:
        return """
Erstelle einen strategischen Implementierungsplan mit:
- Meilensteinen
- Abhängigkeiten
- Zeitschätzungen
- Risiken

Antworte mit JSON:
{
  "milestones": [
    {
      "name": "Milestone Name",
      "description": "Beschreibung",
      "tasks": ["task-ids"],
      "estimated_duration": "2 weeks"
    }
  ],
  "critical_path": ["wichtige-tasks"],
  "risks": ["Risiko 1", "Risiko 2"],
  "estimated_duration": "X weeks",
  "team_size": "X developers"
}
"""