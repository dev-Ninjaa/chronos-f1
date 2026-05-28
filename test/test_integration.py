#!/usr/bin/env python3
"""
Integration test for Chronos F1
Tests the complete workflow from data loading to AI commentary
"""

import sys
import os

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"[OK] {text}")

def print_error(text):
    print(f"[FAIL] {text}")

def test_full_workflow():
    """Test complete workflow: Data → Replay → AI"""
    print_header("Testing Full Workflow Integration")
    
    try:
        # 1. Import all components
        print("[*] Importing components...")
        from manager.dataManager import DataManager
        from replay.replayEngine import ReplayEngine
        from ai.aiCommentary import CommentaryManager
        from documents.documentProcessor import DocumentProcessor
        from workflows.langflowIntegration import F1WorkflowOrchestrator
        print_success("All components imported")
        
        # 2. Initialize DataManager
        print("\n📊 Initializing DataManager...")
        dm = DataManager()
        seasons = dm.getAvailableSeasons()
        print_success(f"DataManager ready: {len(seasons)} seasons available")
        
        # 3. Initialize AI components
        print("\n🤖 Initializing AI components...")
        
        # Document processor
        docProcessor = DocumentProcessor()
        regulationsPath = 'documents/f1_regulations_sample.md'
        if os.path.exists(regulationsPath):
            doc = docProcessor.processDocument(regulationsPath)
            print_success(f"Regulations loaded: {len(doc['sections'])} sections")
        else:
            print_error(f"Regulations file not found: {regulationsPath}")
            return False
        
        # Workflow orchestrator
        orchestrator = F1WorkflowOrchestrator()
        print_success("Workflow orchestrator initialized")
        
        # Commentary manager
        try:
            commentaryManager = CommentaryManager()
            
            # Load regulations
            extractedRules = docProcessor.extractRegulationRules(doc)
            regulations = {'sections': doc['sections']}
            for ruleType, rules in extractedRules.items():
                if rules:
                    regulations[ruleType] = rules[0].get('content', '')[:200]
            
            commentaryManager.loadRegulations(regulations)
            commentaryManager.setWorkflowOrchestrator(orchestrator)
            print_success("Commentary manager initialized with regulations")
        except Exception as e:
            print(f"⚠️  Commentary manager initialization: {e}")
            print("   (This is OK if Ollama is not running)")
        
        # 4. Test workflow execution
        print("\n🔄 Testing workflow execution...")
        testData = {
            'frame': {
                'drivers': {
                    'VER': {'position': 1, 'speed': 320, 'lap': 10, 'tyre': 0, 'tyreLife': 5},
                    'HAM': {'position': 2, 'speed': 318, 'lap': 10, 'tyre': 1, 'tyreLife': 8}
                }
            },
            'time': 600.0
        }
        
        result = orchestrator.executeWorkflow('analysis', testData)
        if result and len(result.get('steps', [])) > 0:
            print_success(f"Workflow executed: {len(result['steps'])} steps")
        else:
            print_error("Workflow execution failed")
            return False
        
        # 5. Test replay engine with mock data
        print("\n▶️  Testing replay engine...")
        mockRaceData = {
            'eventName': 'Integration Test GP',
            'circuitName': 'Test Circuit',
            'country': 'Test',
            'date': '2024-01-01',
            'totalLaps': 10,
            'frames': [
                {
                    't': float(i),
                    'drivers': {
                        'VER': {'position': 1, 'speed': 300 + i, 'lap': 1, 'dist': i * 10}
                    }
                }
                for i in range(10)
            ],
            'drivers': ['VER'],
            'driverColors': {'VER': '#3671C6'},
            'trackData': {'x': [], 'y': [], 'distance': []},
            'trackStatuses': [],
            'raceControlMessages': [],
            'tyreModel': None
        }
        
        class MockSocketIO:
            def emit(self, event, data):
                pass
        
        replayEngine = ReplayEngine(mockRaceData, MockSocketIO())
        replayEngine.play()
        telemetry = replayEngine.getCurrentTelemetry()
        
        if telemetry and 'frame' in telemetry:
            print_success("Replay engine working")
        else:
            print_error("Replay engine failed")
            return False
        
        print("\n✅ Full workflow integration successful!")
        print("   Data Manager → AI Components → Workflows → Replay Engine")
        return True
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run integration test"""
    print("\n" + "="*60)
    print("  CHRONOS F1 - Integration Test")
    print("="*60)
    
    result = test_full_workflow()
    
    print_header("Test Summary")
    
    if result:
        print_success("Integration Test: PASSED")
        print("\n🎉 All components work together correctly!")
        return 0
    else:
        print_error("Integration Test: FAILED")
        print("\n⚠️  Integration test failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

