"""
Document segmentation module to identify and categorize sections
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import nltk

logger = logging.getLogger(__name__)


@dataclass
class DocumentSection:
    """Represents a document section with content and metadata"""

    title: str
    content: str
    section_type: str
    confidence: float
    start_position: int
    end_position: int


class DocumentSegmenter:
    """Segment documents into logical sections based on content patterns"""

    def __init__(self):
        self._ensure_nltk_data()
        self.section_patterns = {
            "ziele": [
                r"ziele?",
                r"objectives?",
                r"goals?",
                r"zweck",
                r"purpose",
                r"vision",
                r"mission",
            ],
            "anforderungen": [
                r"anforderungen?",
                r"requirements?",
                r"spezifikation",
                r"specification",
                r"bedingungen",
                r"conditions",
            ],
            "features": [
                r"features?",
                r"funktionen?",
                r"functions?",
                r"capabilities",
                r"eigenschaften",
                r"merkmale",
            ],
            "technisch": [
                r"technisch",
                r"technical",
                r"architektur",
                r"architecture",
                r"implementation",
                r"implementierung",
                r"system",
                r"infrastruktur",
            ],
            "user_stories": [
                r"user stor(y|ies)",
                r"anwendungsfälle",
                r"use cases?",
                r"szenarien",
                r"scenarios?",
                r"workflows?",
            ],
            "api": [
                r"api",
                r"schnittstelle",
                r"interface",
                r"endpoints?",
                r"services?",
                r"rest",
                r"graphql",
            ],
            "daten": [
                r"daten",
                r"data",
                r"database",
                r"datenbank",
                r"modell",
                r"model",
                r"schema",
                r"entities",
            ],
        }

        self.heading_patterns = [
            r"^#{1,6}\s+(.+)$",  # Markdown headers
            r"^(\d+\.?\s+.+)$",  # Numbered sections
            r"^([A-Z][A-Z\s]{5,})$",  # ALL CAPS headings
            r"^(.+)\n=+$",  # Underlined with =
            r"^(.+)\n-+$",  # Underlined with -
        ]

    def _ensure_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find("tokenizers/punkt")
            nltk.data.find("corpora/stopwords")
        except LookupError:
            logger.info("Downloading required NLTK data...")
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)

    def segment_document(self, text: str) -> List[DocumentSection]:
        """
        Segment document into logical sections

        Args:
            text: Full document text

        Returns:
            List of DocumentSection objects
        """
        sections = []

        # First, try to identify sections by headers
        header_sections = self._segment_by_headers(text)

        if header_sections:
            # Classify each header-based section
            for section in header_sections:
                section_type, confidence = self._classify_section(
                    section["title"], section["content"]
                )

                sections.append(
                    DocumentSection(
                        title=section["title"],
                        content=section["content"],
                        section_type=section_type,
                        confidence=confidence,
                        start_position=section["start"],
                        end_position=section["end"],
                    )
                )
        else:
            # Fallback: segment by content patterns
            pattern_sections = self._segment_by_patterns(text)
            sections.extend(pattern_sections)

        return sections

    def _segment_by_headers(self, text: str) -> List[Dict[str, Any]]:
        """Segment document based on detected headers"""
        sections: List[Dict[str, Any]] = []
        lines = text.split("\n")
        current_section: Optional[Dict[str, Any]] = None

        for i, line in enumerate(lines):
            header_match = self._detect_header(line, lines, i)

            if header_match:
                # Save previous section
                if current_section is not None:
                    current_section["content"] = "\n".join(
                        current_section["content"]
                    ).strip()
                    current_section["end"] = i
                    sections.append(current_section)

                # Start new section
                current_section = {"title": header_match, "content": [], "start": i}
            elif current_section is not None:
                current_section["content"].append(line)

        # Don't forget the last section
        if current_section is not None:
            current_section["content"] = "\n".join(current_section["content"]).strip()
            current_section["end"] = len(lines)
            sections.append(current_section)

        return sections

    def _detect_header(self, line: str, lines: List[str], index: int) -> Optional[str]:
        """Detect if a line is a header and return the header text"""
        line = line.strip()

        for pattern in self.heading_patterns:
            match = re.match(pattern, line, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Check for underlined headers
        if index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if len(next_line) > 0 and all(c in "=-_" for c in next_line):
                return line

        return None

    def _segment_by_patterns(self, text: str) -> List[DocumentSection]:
        """Fallback segmentation using content patterns"""
        sections: List[DocumentSection] = []
        paragraphs = text.split("\n\n")

        current_section: Dict[str, Any] = {
            "content": [],
            "type": "general",
            "confidence": 0.3,
        }

        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if paragraph indicates a new section type
            detected_type, confidence = self._classify_text(paragraph)

            if detected_type != "general" and confidence > 0.6:
                # Start new section
                if current_section["content"]:
                    sections.append(
                        DocumentSection(
                            title=f"Section {len(sections) + 1}",
                            content="\n\n".join(current_section["content"]),
                            section_type=str(current_section["type"]),
                            confidence=float(current_section["confidence"]),
                            start_position=0,
                            end_position=0,
                        )
                    )

                current_section = {
                    "content": [paragraph],
                    "type": detected_type,
                    "confidence": confidence,
                }
            else:
                current_section["content"].append(paragraph)

        # Add final section
        if current_section["content"]:
            sections.append(
                DocumentSection(
                    title=f"Section {len(sections) + 1}",
                    content="\n\n".join(current_section["content"]),
                    section_type=str(current_section["type"]),
                    confidence=float(current_section["confidence"]),
                    start_position=0,
                    end_position=0,
                )
            )

        return sections

    def _classify_section(self, title: str, content: str) -> Tuple[str, float]:
        """Classify a section based on title and content"""
        title_score = self._classify_text(title)
        content_score = self._classify_text(content)

        # Weighted combination (title has higher weight)
        if title_score[1] > 0.5:
            return title_score[0], title_score[1] * 0.7 + content_score[1] * 0.3
        else:
            return content_score[0], content_score[1]

    def _classify_text(self, text: str) -> Tuple[str, float]:
        """Classify text into section type with confidence score"""
        text_lower = text.lower()
        scores = {}

        for section_type, patterns in self.section_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches

            if score > 0:
                # Normalize by text length and pattern count
                normalized_score = min(score / (len(text.split()) * 0.1), 1.0)
                scores[section_type] = normalized_score

        if not scores:
            return "general", 0.3

        best_type = max(scores.keys(), key=lambda k: scores[k])
        return best_type, scores[best_type]

    def get_section_summary(self, sections: List[DocumentSection]) -> Dict[str, Any]:
        """Generate summary statistics about sections"""
        section_types: Dict[str, int] = {}
        total_confidence = 0.0
        total_content_length = 0

        for section in sections:
            section_type = section.section_type
            if section_type not in section_types:
                section_types[section_type] = 0
            section_types[section_type] += 1

            total_content_length += len(section.content)
            total_confidence += section.confidence

        avg_confidence = total_confidence / len(sections) if sections else 0.0

        summary = {
            "total_sections": len(sections),
            "section_types": section_types,
            "avg_confidence": avg_confidence,
            "total_content_length": total_content_length,
        }

        return summary
