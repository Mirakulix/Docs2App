"""
PDF text extraction module using multiple PDF parsing libraries
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import PyPDF2
import pdfplumber
import pandas as pd

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and metadata from PDF documents"""
    
    def __init__(self, method='pdfplumber'):
        """
        Initialize PDFExtractor
        
        Args:
            method: 'pdfplumber' or 'pypdf2' for extraction method
        """
        self.method = method
        self.supported_formats = ['.pdf']
    
    def extract_text(self, file_path: str) -> Dict:
        """
        Extract text from a single PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dict with extracted text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_path_obj = Path(file_path)
        if file_path_obj.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
        
        try:
            if self.method == 'pdfplumber':
                return self._extract_with_pdfplumber(file_path_obj)
            elif self.method == 'pypdf2':
                return self._extract_with_pypdf2(file_path_obj)
            else:
                raise ValueError(f"Unknown extraction method: {self.method}")
                
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            raise
    
    def _extract_with_pdfplumber(self, file_path: Path) -> Dict:
        """Extract text using pdfplumber (better for complex layouts)"""
        text_content = []
        metadata = {
            'filename': file_path.name,
            'method': 'pdfplumber',
            'extracted_at': datetime.now().isoformat(),
            'pages': 0
        }
        
        with pdfplumber.open(file_path) as pdf:
            metadata['pages'] = len(pdf.pages)
            metadata['pdf_metadata'] = pdf.metadata or {}
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"--- Page {page_num} ---\n{page_text}\n")
        
        return {
            'text': '\n'.join(text_content),
            'metadata': metadata
        }
    
    def _extract_with_pypdf2(self, file_path: Path) -> Dict:
        """Extract text using PyPDF2 (faster but less accurate)"""
        text_content = []
        metadata = {
            'filename': file_path.name,
            'method': 'pypdf2', 
            'extracted_at': datetime.now().isoformat(),
            'pages': 0
        }
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata['pages'] = len(pdf_reader.pages)
            
            if pdf_reader.metadata:
                metadata['pdf_metadata'] = dict(pdf_reader.metadata)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"--- Page {page_num} ---\n{page_text}\n")
        
        return {
            'text': '\n'.join(text_content),
            'metadata': metadata
        }
    
    def extract_from_multiple(self, file_paths: List[str]) -> List[Dict]:
        """
        Extract text from multiple PDF files
        
        Args:
            file_paths: List of paths to PDF files
            
        Returns:
            List of extraction results
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.extract_text(file_path)
                results.append({
                    'success': True,
                    'file_path': file_path,
                    'data': result
                })
            except Exception as e:
                logger.error(f"Failed to extract {file_path}: {e}")
                results.append({
                    'success': False,
                    'file_path': file_path,
                    'error': str(e)
                })
        
        return results
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Normalize line breaks
        text = text.replace('\n\n\n+', '\n\n')
        
        # Remove page markers
        import re
        text = re.sub(r'--- Page \d+ ---\s*', '\n\n', text)
        
        return text.strip()
    
    def find_pdf_files(self, directory: str) -> List[str]:
        """
        Find all PDF files in a directory
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of PDF file paths
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        pdf_files = []
        for file_path in directory_path.rglob("*.pdf"):
            pdf_files.append(str(file_path))
        
        return sorted(pdf_files)