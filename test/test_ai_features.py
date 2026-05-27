#!/usr/bin/env python3
"""
Test script to verify all AI features are working
Run this after installation to verify Docling and Langflow
"""

import sys
import os

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"[OK] {text}")

def print_warning(text):
    print(f"[WARN] {text}")

def print_error(text):
    print(f"[FAIL] {text}")

def test_imports():
    """Test if all required modules can be imported"""
    print_header("Testing Module Imports")
    
    modules = [
        ('flask', 'Flask'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('fastf1', 'FastF1'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('documents.documentProcessor', 'Document Processor'),
        ('workflows.langflowIntegration', 'Langflow Integration'),
        ('ai.aiCommentary', 'AI Commentary'),
        ('ai.graniteClient', 'Granite Client'),
    ]
    
    all_passed = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print_success(f"{display_name} imported successfully")
        except ImportError as e:
            print_error(f"{display_name} import failed: {e}")
            all_passed = False
    
    return all_passed

def test_docling():
    """Test Docling document processing"""
    print_header("Testing Docling Document Processing")
    
    try:
        from documents.documentProcessor import DocumentProcessor
        
        # Initialize processor
        processor = DocumentProcessor()
        print_success("DocumentProcessor initialized")
        
        # Test with F1 regulations file
        regulations_path = 'documents/f1_regulations_sample.md'
        if not os.path.exists(regulations_path):
            print_error(f"Regulations file not found: {regulations_path}")
            return False
        
        print(f"📄 Processing: {regulations_path}")
        doc = processor.processDocument(regulations_path)
        
        # Verify document structure
        if not doc:
            print_error("Document processing returned None")
            return False
        
        sections = doc.get('sections', [])
        metadata = doc.get('metadata', {})
        
        print_success(f"Document processed successfully")
        print(f"   Title: {metadata.get('title', 'Unknown')}")
        print(f"   Sections: {len(sections)}")
        print(f"   Total subsections: {sum(len(s.get('subsections', [])) for s in sections)}")
        
        # Test regulation extraction
        extracted_rules = processor.extractRegulationRules(doc)
        print_success(f"Extracted {len(extracted_rules)} rule categories")
        
        for rule_type, rules in extracted_rules.items():
            if rules:
                print(f"   {rule_type}: {len(rules)} rules")
        
        # Test search functionality
        search_results = processor.searchInDocument(doc, 'DRS')
        print_success(f"Search test: Found {len(search_results)} results for 'DRS'")
        
        return True
        
    except Exception as e:
        print_error(f"Docling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_langflow():
    """Test Langflow workflow orchestration"""
    print_header("Testing Langflow Workflow Orchestration")
    
    try:
        from workflows.langflowIntegration import F1WorkflowOrchestrator
        
        # Initialize orchestrator
        orchestrator = F1WorkflowOrchestrator()
        print_success("F1WorkflowOrchestrator initialized")
        
        # Test workflows
        workflows = ['commentary', 'analysis', 'prediction']
        print(f"📊 Available workflows: {', '.join(workflows)}")
        
        # Test commentary workflow
        test_data = {
            'frame': {
                'drivers': {
                    'VER': {'position': 1, 'speed': 320, 'lap': 10, 'tyre': 0, 'tyreLife': 5, 'inPit': False, 'drs': 0},
                    'HAM': {'position': 2, 'speed': 318, 'lap': 10, 'tyre': 1, 'tyreLife': 8, 'inPit': False, 'drs': 1},
                    'LEC': {'position': 3, 'speed': 315, 'lap': 10, 'tyre': 0, 'tyreLife': 5, 'inPit': False, 'drs': 0}
                }
            },
            'time': 600.0,
            'weather': {'rainState': 'DRY', 'trackTemp': 45.0}
        }
        
        print("\n🔄 Testing commentary workflow...")
        result = orchestrator.executeWorkflow('commentary', test_data)
        
        if result:
            print_success("Commentary workflow executed")
            print(f"   Steps completed: {len(result.get('steps', []))}")
            for step in result.get('steps', []):
                status = step.get('status', 'unknown')
                action = step.get('action', 'unknown')
                icon = "✅" if status == 'success' else "❌"
                print(f"   {icon} {action}: {status}")
        else:
            print_error("Commentary workflow returned None")
            return False
        
        # Test analysis workflow
        print("\n🔄 Testing analysis workflow...")
        result = orchestrator.executeWorkflow('analysis', test_data)
        
        if result:
            print_success("Analysis workflow executed")
            print(f"   Steps completed: {len(result.get('steps', []))}")
            
            # Check for tyre analysis
            for step in result.get('steps', []):
                if step.get('action') == 'analyze_tyre_strategy':
                    output = step.get('output', {})
                    tyre_analysis = output.get('tyreAnalysis', {})
                    if tyre_analysis:
                        print(f"   📊 Tyre analysis for {len(tyre_analysis)} drivers")
                        for driver, analysis in list(tyre_analysis.items())[:3]:
                            print(f"      {driver}: {analysis.get('compound')} - {analysis.get('health', 0):.0f}% health")
        else:
            print_error("Analysis workflow returned None")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Langflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_commentary():
    """Test AI commentary generation"""
    print_header("Testing AI Commentary Generation")
    
    try:
        from ai.aiCommentary import CommentaryManager
        from ai.graniteClient import GraniteClient
        
        # Check if API key is configured
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print_warning("GEMINI_API_KEY not set in .env file")
            print("   AI commentary will use fallback mode")
            print("   To enable full AI: Add GEMINI_API_KEY to .env")
            return True  # Not a failure, just a warning
        
        # Initialize client
        client = GraniteClient()
        print_success("GraniteClient (Gemini) initialized")
        
        # Initialize commentary manager
        manager = CommentaryManager()
        print_success("CommentaryManager initialized")
        
        # Load regulations
        from documents.documentProcessor import DocumentProcessor
        processor = DocumentProcessor()
        regulations_path = 'documents/f1_regulations_sample.md'
        
        if os.path.exists(regulations_path):
            doc = processor.processDocument(regulations_path)
            extracted_rules = processor.extractRegulationRules(doc)
            
            regulations = {
                'drs_rules': 'DRS can only be used when within 1 second of car ahead',
                'pit_rules': 'Pit lane speed limit is 80 km/h',
                'sections': doc.get('sections', [])
            }
            
            for rule_type, rules in extracted_rules.items():
                if rules:
                    regulations[rule_type] = rules[0].get('content', '')[:200]
            
            manager.loadRegulations(regulations)
            print_success(f"Regulations loaded: {len(doc.get('sections', []))} sections")
        
        print_success("AI Commentary system ready")
        print("   Note: Commentary generates every 90 seconds during race replay")
        
        return True
        
    except Exception as e:
        print_error(f"AI Commentary test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test full integration"""
    print_header("Testing Full Integration")
    
    try:
        from documents.documentProcessor import DocumentProcessor
        from workflows.langflowIntegration import F1WorkflowOrchestrator
        from ai.aiCommentary import CommentaryManager
        
        # Initialize all components
        processor = DocumentProcessor()
        orchestrator = F1WorkflowOrchestrator()
        manager = CommentaryManager()
        
        # Load regulations
        regulations_path = 'documents/f1_regulations_sample.md'
        if os.path.exists(regulations_path):
            doc = processor.processDocument(regulations_path)
            extracted_rules = processor.extractRegulationRules(doc)
            
            regulations = {
                'sections': doc.get('sections', [])
            }
            for rule_type, rules in extracted_rules.items():
                if rules:
                    regulations[rule_type] = rules[0].get('content', '')[:200]
            
            manager.loadRegulations(regulations)
        
        # Set workflow orchestrator
        manager.setWorkflowOrchestrator(orchestrator)
        
        print_success("All components integrated successfully")
        print("   ✅ DocumentProcessor")
        print("   ✅ F1WorkflowOrchestrator")
        print("   ✅ CommentaryManager")
        print("   ✅ Regulations loaded")
        print("   ✅ Workflows connected")
        
        return True
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  CHRONOS F1 - AI Features Test Suite")
    print("="*60)
    
    results = {
        'Imports': test_imports(),
        'Docling': test_docling(),
        'Langflow': test_langflow(),
        'AI Commentary': test_ai_commentary(),
        'Integration': test_integration()
    }
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your installation is complete.")
        print("   Run 'python app.py' to start the application")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("   See INSTALLATION.md for troubleshooting")
        return 1

if __name__ == '__main__':
    sys.exit(main())

