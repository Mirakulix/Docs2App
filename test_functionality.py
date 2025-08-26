#!/usr/bin/env python3
"""
Basic functionality test for Docs2App
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing imports...")
    
    try:
        from docs2app.extractors.pdf_extractor import PDFExtractor
        from docs2app.analyzers.document_segmenter import DocumentSegmenter
        from docs2app.core.config import ConfigManager
        from docs2app.core.ai_providers import AIProviderManager
        print("✅ All core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_pdf_extractor():
    """Test PDF extractor initialization"""
    print("Testing PDF extractor...")
    
    try:
        from docs2app.extractors.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        assert extractor.supported_formats == ['.pdf']
        print("✅ PDF extractor working")
        return True
    except Exception as e:
        print(f"❌ PDF extractor error: {e}")
        return False

def test_config_manager():
    """Test config manager"""
    print("Testing config manager...")
    
    try:
        from docs2app.core.config import ConfigManager
        config = ConfigManager('config.yaml')
        provider = config.get_active_ai_provider()
        assert provider in ['ollama', 'openai', 'azure']
        print(f"✅ Config manager working (active provider: {provider})")
        return True
    except Exception as e:
        print(f"❌ Config manager error: {e}")
        return False

def test_document_segmenter():
    """Test document segmenter"""
    print("Testing document segmenter...")
    
    try:
        from docs2app.analyzers.document_segmenter import DocumentSegmenter
        segmenter = DocumentSegmenter()
        # Test basic text segmentation
        text = "This is a test document. It has multiple sentences."
        sections = segmenter.segment_document(text)
        print(f"✅ Document segmenter working (found {len(sections)} sections)")
        return True
    except Exception as e:
        print(f"❌ Document segmenter error: {e}")
        return False

def test_cli_help():
    """Test CLI help command"""
    print("Testing CLI help...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "main.py", "--help"], 
                              capture_output=True, text=True)
        if result.returncode == 0 and "Docs2App" in result.stdout:
            print("✅ CLI help working")
            return True
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Docs2App functionality tests...\n")
    
    tests = [
        test_imports,
        test_pdf_extractor,
        test_config_manager,
        test_document_segmenter,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Empty line for readability
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The project is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())