#!/usr/bin/env python3
"""
Script to create a comprehensive Sudoku requirements PDF from markdown
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

def markdown_to_pdf(markdown_file, output_pdf):
    """Convert markdown content to PDF"""
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=11,
        spaceAfter=8,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=20
    )
    
    # Story list for PDF content
    story = []
    
    # Split content into lines
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 6))
            continue
            
        # Main title (single #)
        if line.startswith('# ') and not line.startswith('## '):
            title_text = line[2:].strip()
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 12))
            
        # Heading 1 (##)
        elif line.startswith('## '):
            heading_text = line[3:].strip()
            story.append(Paragraph(heading_text, heading1_style))
            
        # Heading 2 (###)
        elif line.startswith('### '):
            heading_text = line[4:].strip()
            story.append(Paragraph(heading_text, heading2_style))
            
        # Heading 3 (####)
        elif line.startswith('#### '):
            heading_text = line[5:].strip()
            story.append(Paragraph(heading_text, heading3_style))
            
        # Bullet points
        elif line.startswith('- '):
            bullet_text = line[2:].strip()
            # Process bold text
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            story.append(Paragraph(f"• {bullet_text}", bullet_style))
            
        # Code blocks (ignore for PDF)
        elif line.startswith('```'):
            continue
            
        # Regular text
        else:
            if line:
                # Process bold text
                line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                # Process code spans
                line = re.sub(r'`(.*?)`', r'<i>\1</i>', line)
                story.append(Paragraph(line, normal_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF created: {output_pdf}")

if __name__ == "__main__":
    markdown_to_pdf(
        "pdfs/sudoku-requirements-complete.md",
        "pdfs/sudoku-requirements-complete.pdf"
    )