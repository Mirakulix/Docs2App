#!/usr/bin/env python3
"""
Docs2App - AI-powered tool to analyze software documentation PDFs and generate application code

Usage:
    python main.py analyze file1.pdf file2.pdf --project-name "MyApp"
    python main.py health-check
    python main.py config --provider ollama
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich import print as rprint

from docs2app.core.document_processor import DocumentProcessor
from docs2app.core.config import ConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.option('--config', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Docs2App - AI-powered document analysis and code generation"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.argument('pdf_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--project-name', '-p', help='Name for the generated project')
@click.option('--output-format', 
              type=click.Choice(['features', 'tasks', 'code', 'all']),
              default='all',
              help='What to generate')
@click.option('--provider', help='AI provider to use (ollama, openai, azure)')
@click.pass_context
async def analyze(ctx, pdf_files, project_name, output_format, provider):
    """Analyze PDF documents and generate features/code/tasks"""
    
    config_path = ctx.obj['config_path']
    
    try:
        # Initialize processor
        with console.status("[bold green]Initializing Docs2App..."):
            processor = DocumentProcessor(config_path)
            
            # Override provider if specified
            if provider:
                processor.config_manager.config.ai_providers.default = provider
        
        # Health check
        console.print("🔍 Performing health check...")
        health = await processor.health_check()
        
        if not health['system_ready']:
            console.print("❌ [red]System not ready![/red]")
            console.print(Panel(json.dumps(health, indent=2), title="Health Check Results"))
            sys.exit(1)
        
        console.print("✅ [green]System ready![/green]")
        
        # Process documents
        console.print(f"📄 Processing {len(pdf_files)} PDF files...")
        
        results = await processor.process_documents(
            list(pdf_files),
            project_name=project_name,
            output_format=output_format
        )
        
        # Display results
        _display_results(results, output_format)
        
        # Save results to file
        output_file = Path(processor.config_manager.config.output.directory) / f"analysis_results_{project_name or 'project'}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        console.print(f"💾 Results saved to: {output_file}")
        
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        logger.exception("Analysis failed")
        sys.exit(1)


@cli.command('health-check')
@click.pass_context
async def health_check(ctx):
    """Check system health and configuration"""
    config_path = ctx.obj['config_path']
    
    try:
        processor = DocumentProcessor(config_path)
        health = await processor.health_check()
        
        # Display health status
        console.print("🏥 [bold]System Health Check[/bold]")
        
        # Configuration status
        config_status = health['configuration']
        config_color = "green" if config_status['valid'] else "red"
        console.print(f"📋 Configuration: [{config_color}]{'✅ Valid' if config_status['valid'] else '❌ Issues'}[/{config_color}]")
        
        if config_status['issues']['errors']:
            console.print("   Errors:")
            for error in config_status['issues']['errors']:
                console.print(f"   - [red]{error}[/red]")
        
        # AI Providers status
        console.print("\n🤖 AI Providers:")
        providers_table = Table()
        providers_table.add_column("Provider")
        providers_table.add_column("Status")
        providers_table.add_column("Active")
        
        for provider, status in health['ai_providers'].items():
            status_icon = "✅" if status else "❌"
            active_icon = "⭐" if provider == health['active_provider'] else ""
            providers_table.add_row(provider, status_icon, active_icon)
        
        console.print(providers_table)
        
        # Overall status
        overall_color = "green" if health['system_ready'] else "red"
        console.print(f"\n🎯 Overall Status: [{overall_color}]{'✅ Ready' if health['system_ready'] else '❌ Not Ready'}[/{overall_color}]")
        
    except Exception as e:
        console.print(f"❌ [red]Health check failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--provider', type=click.Choice(['ollama', 'openai', 'azure']), help='Set default AI provider')
@click.option('--show', is_flag=True, help='Show current configuration')
@click.pass_context
def config(ctx, provider, show):
    """Manage configuration"""
    config_path = ctx.obj['config_path']
    
    try:
        config_manager = ConfigManager(config_path)
        
        if show:
            # Display current configuration
            console.print("⚙️  [bold]Current Configuration[/bold]")
            
            # AI Provider info
            console.print(f"🤖 Active Provider: [cyan]{config_manager.get_active_ai_provider()}[/cyan]")
            
            # Framework preferences
            prefs = config_manager.config.generation.framework_preferences
            console.print(f"🛠️  Framework Preferences:")
            console.print(f"   Frontend: {', '.join(prefs.get('frontend', []))}")
            console.print(f"   Backend: {', '.join(prefs.get('backend', []))}")
            console.print(f"   Database: {', '.join(prefs.get('database', []))}")
            
            return
        
        if provider:
            # Update provider
            config_manager.config.ai_providers.default = provider
            config_manager.save_config()
            console.print(f"✅ Default AI provider set to: [cyan]{provider}[/cyan]")
    
    except Exception as e:
        console.print(f"❌ [red]Configuration error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--project-name', '-p', help='Name for the generated project')
@click.pass_context
async def batch(ctx, directory, project_name):
    """Process all PDF files in a directory"""
    directory = Path(directory)
    pdf_files = list(directory.glob("*.pdf"))
    
    if not pdf_files:
        console.print(f"❌ [red]No PDF files found in {directory}[/red]")
        sys.exit(1)
    
    console.print(f"📁 Found {len(pdf_files)} PDF files in {directory}")
    
    # Call analyze with found files
    await analyze.callback(pdf_files, project_name, 'all', None)


def _display_results(results: dict, output_format: str):
    """Display analysis results in a nice format"""
    
    # PDF extraction results
    extraction_results = results.get('extraction_results', [])
    successful = [r for r in extraction_results if r['success']]
    
    console.print(f"📄 [green]{len(successful)}/{len(extraction_results)} PDFs processed successfully[/green]")
    
    # Feature analysis results
    if 'feature_analysis' in results:
        features = results['feature_analysis']
        console.print(f"\n🎯 [bold]Feature Analysis[/bold]")
        console.print(f"   Explicit Features: {len(features['features'])}")
        console.print(f"   Implicit Features: {len(features['implicit_features'])}")
        console.print(f"   Average Confidence: {features['analysis_summary']['avg_confidence']:.2f}")
        
        # Feature categories
        categories = features['analysis_summary']['categories']
        if categories:
            console.print("   Categories:")
            for category, count in categories.items():
                console.print(f"     - {category}: {count}")
    
    # Code generation results
    if 'code_generation' in results:
        code_gen = results['code_generation']
        console.print(f"\n🏗️  [bold]Code Generation[/bold]")
        console.print(f"   Project: {code_gen['project_structure']['name']}")
        console.print(f"   Claude Tasks: {len(code_gen['claude_tasks'])}")
        
        tech_stack = code_gen['project_structure']['technology_stack']
        if tech_stack:
            console.print("   Technology Stack:")
            for tech, framework in tech_stack.items():
                console.print(f"     - {tech}: {framework}")


def main():
    """Main entry point"""
    try:
        # Run the async CLI
        cli(_anyio_backend="asyncio")
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        logger.exception("Unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()