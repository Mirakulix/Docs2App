"""
AI-powered feature analysis and extraction from documents
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime

from ..core.ai_providers import AIProviderManager, AIMessage
from ..core.config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class Feature:
    """Represents a software feature with metadata"""
    feature_name: str
    beschreibung: str
    kategorie: str  # core/optional/technisch/ui/api
    abhängigkeiten: List[str]
    priorität: str  # hoch/mittel/niedrig
    confidence: float
    user_story: Optional[str] = None
    acceptance_criteria: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    estimated_complexity: Optional[str] = None  # niedrig/mittel/hoch


@dataclass
class FeatureAnalysisResult:
    """Results of feature analysis"""
    features: List[Feature]
    implicit_features: List[Feature]
    project_metadata: Dict
    analysis_summary: Dict
    extracted_at: str
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class FeatureAnalyzer:
    """AI-powered feature analysis and extraction"""
    
    def __init__(self, config_manager: ConfigManager, ai_manager: AIProviderManager):
        self.config = config_manager
        self.ai_manager = ai_manager
        self.analysis_config = config_manager.config.analysis
        
        # Prompts for different analysis tasks
        self.prompts = {
            "feature_extraction": self._get_feature_extraction_prompt(),
            "implicit_analysis": self._get_implicit_analysis_prompt(),
            "categorization": self._get_categorization_prompt(),
            "priority_assessment": self._get_priority_prompt(),
            "technical_analysis": self._get_technical_analysis_prompt()
        }
    
    async def analyze_document(self, text: str, document_sections: Optional[List] = None) -> FeatureAnalysisResult:
        """
        Analyze document and extract features using AI
        
        Args:
            text: Full document text
            document_sections: Optional pre-segmented document sections
            
        Returns:
            FeatureAnalysisResult with extracted features
        """
        logger.info("Starting AI-powered feature analysis")
        
        # Step 1: Extract explicit features
        explicit_features = await self._extract_explicit_features(text, document_sections)
        
        # Step 2: Identify implicit features if enabled
        implicit_features = []
        if self.analysis_config.enable_implicit_features:
            implicit_features = await self._extract_implicit_features(text, explicit_features)
        
        # Step 3: Enhance features with additional analysis
        enhanced_features = await self._enhance_features(explicit_features, text)
        enhanced_implicit = await self._enhance_features(implicit_features, text)
        
        # Step 4: Generate project metadata
        project_metadata = await self._analyze_project_metadata(text)
        
        # Step 5: Create analysis summary
        analysis_summary = self._create_analysis_summary(
            enhanced_features, enhanced_implicit, project_metadata
        )
        
        return FeatureAnalysisResult(
            features=enhanced_features,
            implicit_features=enhanced_implicit,
            project_metadata=project_metadata,
            analysis_summary=analysis_summary,
            extracted_at=datetime.now().isoformat()
        )
    
    async def _extract_explicit_features(self, text: str, sections: Optional[List] = None) -> List[Feature]:
        """Extract explicitly mentioned features using AI"""
        logger.info("Extracting explicit features")
        
        messages = [
            AIMessage(role="system", content=self.prompts["feature_extraction"]),
            AIMessage(role="user", content=f"Analysiere dieses Dokument und extrahiere alle Features:\n\n{text}")
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            features_data = self._parse_ai_response(response.content)
            
            features = []
            for feature_dict in features_data.get("features", []):
                try:
                    feature = Feature(**feature_dict)
                    if feature.confidence >= self.analysis_config.min_confidence:
                        features.append(feature)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not create feature from {feature_dict}: {e}")
            
            logger.info(f"Extracted {len(features)} explicit features")
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return []
    
    async def _extract_implicit_features(self, text: str, explicit_features: List[Feature]) -> List[Feature]:
        """Extract implicit features that aren't directly mentioned"""
        logger.info("Analyzing implicit features")
        
        explicit_names = [f.feature_name for f in explicit_features]
        
        messages = [
            AIMessage(role="system", content=self.prompts["implicit_analysis"]),
            AIMessage(role="user", content=f"""
Dokument: {text}

Bereits identifizierte Features: {', '.join(explicit_names)}

Identifiziere zusätzliche implizite Features, die für diese Anwendung erforderlich sind.
""")
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            features_data = self._parse_ai_response(response.content)
            
            implicit_features = []
            for feature_dict in features_data.get("implicit_features", []):
                try:
                    feature = Feature(**feature_dict)
                    if feature.confidence >= self.analysis_config.min_confidence:
                        implicit_features.append(feature)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not create implicit feature from {feature_dict}: {e}")
            
            logger.info(f"Identified {len(implicit_features)} implicit features")
            return implicit_features
            
        except Exception as e:
            logger.error(f"Implicit feature analysis failed: {e}")
            return []
    
    async def _enhance_features(self, features: List[Feature], text: str) -> List[Feature]:
        """Enhance features with additional details using AI"""
        if not features:
            return features
        
        logger.info(f"Enhancing {len(features)} features with additional details")
        
        enhanced_features = []
        
        for feature in features:
            try:
                # Enhance with technical analysis
                enhanced = await self._enhance_single_feature(feature, text)
                enhanced_features.append(enhanced)
            except Exception as e:
                logger.warning(f"Failed to enhance feature {feature.feature_name}: {e}")
                enhanced_features.append(feature)  # Keep original if enhancement fails
        
        return enhanced_features
    
    async def _enhance_single_feature(self, feature: Feature, context: str) -> Feature:
        """Enhance a single feature with AI analysis"""
        messages = [
            AIMessage(role="system", content=self.prompts["technical_analysis"]),
            AIMessage(role="user", content=f"""
Feature: {feature.feature_name}
Beschreibung: {feature.beschreibung}
Kategorie: {feature.kategorie}

Kontext aus Dokument: {context[:2000]}...

Erweitere dieses Feature um:
1. User Story
2. Acceptance Criteria
3. Technical Requirements
4. Complexity Estimation
5. Dependencies
""")
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            enhancement_data = self._parse_ai_response(response.content)
            
            # Update feature with enhanced data
            enhanced = Feature(
                feature_name=feature.feature_name,
                beschreibung=enhancement_data.get("beschreibung", feature.beschreibung),
                kategorie=feature.kategorie,
                abhängigkeiten=enhancement_data.get("abhängigkeiten", feature.abhängigkeiten),
                priorität=enhancement_data.get("priorität", feature.priorität),
                confidence=feature.confidence,
                user_story=enhancement_data.get("user_story"),
                acceptance_criteria=enhancement_data.get("acceptance_criteria", []),
                technical_requirements=enhancement_data.get("technical_requirements", []),
                estimated_complexity=enhancement_data.get("estimated_complexity")
            )
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Feature enhancement failed for {feature.feature_name}: {e}")
            return feature
    
    async def _analyze_project_metadata(self, text: str) -> Dict:
        """Extract project-level metadata using AI"""
        messages = [
            AIMessage(role="system", content="""
Du bist ein Experte für Software-Projektanalyse. Analysiere das Dokument und extrahiere:
- Projektname und -beschreibung
- Zielgruppe/Stakeholder
- Technische Rahmenbedingungen
- Geschätzte Projektgröße
- Hauptfunktionsbereiche

Antworte mit einem JSON-Objekt.
"""),
            AIMessage(role="user", content=f"Analysiere dieses Projektdokument:\n\n{text}")
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            metadata = self._parse_ai_response(response.content)
            return metadata
        except Exception as e:
            logger.error(f"Project metadata analysis failed: {e}")
            return {}
    
    def _create_analysis_summary(self, features: List[Feature], implicit_features: List[Feature], metadata: Dict) -> Dict:
        """Create analysis summary statistics"""
        all_features = features + implicit_features
        
        # Count by category
        categories: Dict[str, int] = {}
        priorities: Dict[str, int] = {}
        complexities: Dict[str, int] = {}
        
        for feature in all_features:
            categories[feature.kategorie] = categories.get(feature.kategorie, 0) + 1
            priorities[feature.priorität] = priorities.get(feature.priorität, 0) + 1
            if feature.estimated_complexity:
                complexities[feature.estimated_complexity] = complexities.get(feature.estimated_complexity, 0) + 1
        
        return {
            "total_features": len(all_features),
            "explicit_features": len(features),
            "implicit_features": len(implicit_features),
            "categories": categories,
            "priorities": priorities,
            "complexities": complexities,
            "avg_confidence": sum(f.confidence for f in all_features) / len(all_features) if all_features else 0,
            "high_priority_features": len([f for f in all_features if f.priorität == "hoch"]),
            "core_features": len([f for f in all_features if f.kategorie == "core"]),
        }
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response and extract JSON"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON found, try to parse the whole response
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse AI response as JSON: {e}")
            return {}
    
    def _get_feature_extraction_prompt(self) -> str:
        """System prompt for feature extraction"""
        return """
Du bist ein Experte für Software-Anforderungsanalyse. Analysiere Dokumente und extrahiere alle beschriebenen Features/Funktionen.

Für jedes Feature erstelle ein JSON-Objekt mit:
- feature_name: Eindeutiger Name
- beschreibung: Detaillierte Beschreibung
- kategorie: core/optional/technisch/ui/api
- abhängigkeiten: Liste anderer Features
- priorität: hoch/mittel/niedrig
- confidence: 0.0-1.0 (Sicherheit der Extraktion)

Antworte mit JSON:
{
  "features": [
    {
      "feature_name": "...",
      "beschreibung": "...",
      "kategorie": "...",
      "abhängigkeiten": [...],
      "priorität": "...",
      "confidence": 0.8
    }
  ]
}
"""
    
    def _get_implicit_analysis_prompt(self) -> str:
        """System prompt for implicit feature analysis"""
        return """
Du bist ein Experte für Software-Architektur. Identifiziere implizite Features, die für eine Anwendung erforderlich sind, aber nicht explizit erwähnt werden.

Denke an:
- Benutzerauthentifizierung und -verwaltung
- Datensicherheit und Backup
- Logging und Monitoring
- API-Dokumentation
- Fehlerbehandlung
- Performance-Optimierung
- Skalierbarkeit
- Wartung und Updates

Antworte mit JSON:
{
  "implicit_features": [
    {
      "feature_name": "...",
      "beschreibung": "...",
      "kategorie": "...",
      "abhängigkeiten": [...],
      "priorität": "...",
      "confidence": 0.7
    }
  ]
}
"""
    
    def _get_categorization_prompt(self) -> str:
        """System prompt for feature categorization"""
        return """
Kategorisiere Features in:
- core: Kernfunktionalität der Anwendung
- optional: Nice-to-have Features
- technisch: Infrastruktur, APIs, Architektur
- ui: User Interface und User Experience
- api: Externe Schnittstellen und Integrationen
"""
    
    def _get_priority_prompt(self) -> str:
        """System prompt for priority assessment"""
        return """
Bewerte Priorität basierend auf:
- hoch: Kritisch für MVP, Blockiert andere Features
- mittel: Wichtig für Benutzerfreundlichkeit
- niedrig: Nice-to-have, kann später implementiert werden
"""
    
    def _get_technical_analysis_prompt(self) -> str:
        """System prompt for technical feature analysis"""
        return """
Du bist ein Senior Software Architect. Erweitere Features um technische Details:

1. User Story: Als [Benutzertyp] möchte ich [Ziel] um [Nutzen]
2. Acceptance Criteria: Liste messbarer Kriterien
3. Technical Requirements: Technische Implementierungsanforderungen
4. Complexity Estimation: niedrig/mittel/hoch
5. Dependencies: Technische Abhängigkeiten

Antworte mit JSON:
{
  "beschreibung": "...",
  "user_story": "...",
  "acceptance_criteria": [...],
  "technical_requirements": [...],
  "estimated_complexity": "...",
  "abhängigkeiten": [...]
}
"""