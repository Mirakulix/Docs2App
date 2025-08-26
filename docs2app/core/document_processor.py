"""
Main document processing orchestrator
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..analyzers.document_segmenter import DocumentSegmenter
from ..analyzers.feature_analyzer import FeatureAnalyzer
from ..extractors.pdf_extractor import PDFExtractor
from ..generators.code_generator import CodeGenerator
from .ai_providers import AIProviderManager
from .config import ConfigManager

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main orchestrator for document processing pipeline"""

    def __init__(self, config_path: Optional[str] = None):
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)

        # Initialize AI providers
        self.ai_manager = AIProviderManager(self.config_manager)

        # Initialize processing components
        self.pdf_extractor = PDFExtractor(method=self.config_manager.config.pdf.method)
        self.document_segmenter = DocumentSegmenter()
        self.feature_analyzer = FeatureAnalyzer(self.config_manager, self.ai_manager)
        self.code_generator = CodeGenerator(self.config_manager, self.ai_manager)

        logger.info("Document processor initialized")

    async def process_documents(
        self,
        pdf_paths: List[str],
        project_name: Optional[str] = None,
        output_format: str = "all",
    ) -> Dict[str, Any]:
        """
        Process PDF documents through the complete pipeline

        Args:
            pdf_paths: List of PDF file paths
            project_name: Optional project name override
            output_format: "features", "tasks", "code", or "all"

        Returns:
            Complete processing results
        """
        logger.info(f"Processing {len(pdf_paths)} documents")

        # Step 1: Extract text from PDFs
        logger.info("Step 1: Extracting text from PDFs")
        extraction_results = self.pdf_extractor.extract_from_multiple(pdf_paths)

        # Filter successful extractions
        successful_extractions = [r for r in extraction_results if r["success"]]
        if not successful_extractions:
            raise ValueError("No PDFs could be successfully extracted")

        # Combine all extracted text
        combined_text = self._combine_extracted_texts(successful_extractions)

        # Step 2: Segment documents
        logger.info("Step 2: Segmenting document content")
        document_sections = self.document_segmenter.segment_document(combined_text)

        # Step 3: Analyze features with AI
        logger.info("Step 3: Analyzing features with AI")
        analysis_result = await self.feature_analyzer.analyze_document(
            combined_text, document_sections
        )

        results = {
            "extraction_results": extraction_results,
            "document_sections": [
                {
                    "title": section.title,
                    "content": section.content,
                    "section_type": section.section_type,
                    "confidence": section.confidence,
                }
                for section in document_sections
            ],
            "feature_analysis": analysis_result.to_dict(),
        }

        # Step 4: Generate code and tasks if requested
        if output_format in ["code", "tasks", "all"]:
            logger.info("Step 4: Generating project structure and tasks")
            generation_result = await self.code_generator.generate_project(
                analysis_result, project_name
            )
            results["code_generation"] = generation_result.to_dict()

        logger.info("Document processing completed successfully")
        return results

    async def analyze_features_only(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """Quick feature analysis without code generation"""
        return await self.process_documents(pdf_paths, output_format="features")

    async def generate_claude_tasks(
        self, pdf_paths: List[str], project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate only Claude Code tasks"""
        return await self.process_documents(
            pdf_paths, project_name, output_format="tasks"
        )

    def _combine_extracted_texts(self, extraction_results: List[Dict]) -> str:
        """Combine texts from multiple PDFs"""
        combined_parts = []

        for result in extraction_results:
            filename = result["data"]["metadata"]["filename"]
            text = result["data"]["text"]

            # Add document separator
            combined_parts.append(f"=== DOKUMENT: {filename} ===\n\n{text}\n\n")

        return "\n".join(combined_parts)

    async def health_check(self) -> Dict[str, Any]:
        """Check system health and configuration"""
        logger.info("Performing system health check")

        # Check configuration
        config_issues = self.config_manager.validate_config()

        # Check AI providers
        provider_status = await self.ai_manager.health_check_all()

        # Check output directory
        output_dir = Path(self.config_manager.config.output.directory)
        output_writable = output_dir.parent.exists() and os.access(
            output_dir.parent, os.W_OK
        )

        return {
            "configuration": {
                "valid": len(config_issues["errors"]) == 0,
                "issues": config_issues,
            },
            "ai_providers": provider_status,
            "active_provider": self.config_manager.get_active_ai_provider(),
            "output_directory": {"path": str(output_dir), "writable": output_writable},
            "system_ready": (
                len(config_issues["errors"]) == 0
                and any(provider_status.values())
                and output_writable
            ),
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and configuration"""
        return {
            "ai_providers": self.ai_manager.get_provider_info(),
            "active_provider": self.config_manager.get_active_ai_provider(),
            "configuration": {
                "pdf_method": self.config_manager.config.pdf.method,
                "output_format": self.config_manager.config.generation.output_format,
                "include_tests": self.config_manager.config.generation.include_tests,
                "include_documentation": (
                    self.config_manager.config.generation.include_documentation
                ),
            },
            "framework_preferences": (
                self.config_manager.config.generation.framework_preferences
            ),
        }
