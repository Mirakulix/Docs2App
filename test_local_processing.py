#!/usr/bin/env python3
"""
Test local PDF processing without AI providers
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from docs2app.extractors.pdf_extractor import PDFExtractor
from docs2app.analyzers.document_segmenter import DocumentSegmenter

console = Console()

def test_pdf_processing():
    """Test complete PDF processing pipeline"""
    
    console.print("[bold blue]🚀 Testing Docs2App Local Processing Pipeline[/bold blue]")
    console.print()
    
    # Test comprehensive Sudoku PDF
    pdf_path = "pdfs/sudoku-requirements-complete.pdf"
    
    # Step 1: PDF Extraction
    console.print("[bold green]Step 1: PDF Text Extraction[/bold green]")
    extractor = PDFExtractor()
    extraction_result = extractor.extract_text(pdf_path)
    
    console.print(f"✅ Extracted {len(extraction_result['text'])} characters")
    console.print(f"📄 Source: {pdf_path}")
    
    # Step 2: Document Segmentation
    console.print("\n[bold green]Step 2: Document Segmentation[/bold green]")
    segmenter = DocumentSegmenter()
    sections = segmenter.segment_document(extraction_result['text'])
    
    console.print(f"✅ Identified {len(sections)} document sections")
    
    # Create sections summary table
    sections_table = Table()
    sections_table.add_column("Section", style="cyan")
    sections_table.add_column("Type", style="yellow")
    sections_table.add_column("Confidence", style="green")
    sections_table.add_column("Content Preview", style="white")
    
    for i, section in enumerate(sections[:10]):  # Show first 10 sections
        preview = section.content[:50].replace('\n', ' ') + "..." if len(section.content) > 50 else section.content
        sections_table.add_row(
            f"{i+1}",
            section.section_type,
            f"{section.confidence:.2f}",
            preview
        )
    
    console.print(sections_table)
    
    # Step 3: Section Type Analysis
    console.print("\n[bold green]Step 3: Content Analysis[/bold green]")
    
    section_types = {}
    for section in sections:
        section_type = section.section_type
        if section_type not in section_types:
            section_types[section_type] = []
        section_types[section_type].append(section)
    
    analysis_table = Table()
    analysis_table.add_column("Content Type", style="cyan")
    analysis_table.add_column("Count", style="yellow")
    analysis_table.add_column("Avg Confidence", style="green")
    analysis_table.add_column("Description", style="white")
    
    type_descriptions = {
        'anforderungen': 'Requirements and specifications',
        'features': 'Feature descriptions and functionality',
        'technisch': 'Technical implementation details',
        'ziele': 'Goals and objectives',
        'daten': 'Data structures and models',
        'general': 'General content and descriptions'
    }
    
    for section_type, type_sections in section_types.items():
        avg_confidence = sum(s.confidence for s in type_sections) / len(type_sections)
        description = type_descriptions.get(section_type, 'Other content')
        
        analysis_table.add_row(
            section_type.title(),
            str(len(type_sections)),
            f"{avg_confidence:.2f}",
            description
        )
    
    console.print(analysis_table)
    
    # Step 4: Content Quality Assessment
    console.print("\n[bold green]Step 4: Content Quality Assessment[/bold green]")
    
    # Find high-confidence sections by type
    high_conf_sections = [s for s in sections if s.confidence > 0.7]
    technical_sections = [s for s in sections if s.section_type == 'technisch']
    requirements_sections = [s for s in sections if s.section_type == 'anforderungen']
    
    quality_stats = [
        f"📊 Total Content: {len(extraction_result['text']):,} characters",
        f"📑 Document Sections: {len(sections)} identified",
        f"🎯 High Confidence: {len(high_conf_sections)} sections (>0.7)",
        f"🔧 Technical Content: {len(technical_sections)} sections",
        f"📋 Requirements: {len(requirements_sections)} sections",
        f"🏷️  Content Categories: {len(section_types)} types"
    ]
    
    console.print(Panel("\n".join(quality_stats), title="Processing Results", border_style="green"))
    
    # Step 5: Demonstrate what would happen with AI
    console.print("\n[bold yellow]Step 5: AI Processing Simulation[/bold yellow]")
    
    ai_pipeline = [
        "🤖 Feature Analysis: Would extract specific features from requirements",
        "📝 User Story Generation: Would create user stories from specifications", 
        "🏗️  Code Structure: Would generate project architecture",
        "📋 Task Creation: Would create Claude Code implementation tasks",
        "🎨 UI/UX Analysis: Would identify interface requirements",
        "🔧 Technical Stack: Would recommend technology choices"
    ]
    
    for step in ai_pipeline:
        console.print(f"   {step}")
    
    console.print()
    console.print("[bold blue]🎉 Local Processing Pipeline Complete![/bold blue]")
    console.print("ℹ️  To enable full AI analysis, configure API keys in .env or run with Docker+Ollama")
    
    return {
        'extraction': extraction_result,
        'sections': sections,
        'section_types': section_types,
        'stats': {
            'total_chars': len(extraction_result['text']),
            'total_sections': len(sections),
            'high_confidence_sections': len(high_conf_sections),
            'technical_sections': len(technical_sections),
            'requirements_sections': len(requirements_sections),
            'content_categories': len(section_types)
        }
    }

if __name__ == "__main__":
    results = test_pdf_processing()
    
    # Save results to JSON
    output_file = Path("output") / "local_processing_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    # Convert sections to serializable format
    serializable_results = {
        'stats': results['stats'],
        'section_types': {k: len(v) for k, v in results['section_types'].items()},
        'sections_preview': [
            {
                'title': s.title,
                'type': s.section_type,
                'confidence': s.confidence,
                'content_length': len(s.content)
            } for s in results['sections']
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    console.print(f"💾 Results saved to: {output_file}")