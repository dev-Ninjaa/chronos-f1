"""
Workflow Orchestration Example
Demonstrates how to use Langflow for AI workflows
"""
import sys
sys.path.append('..')

from workflows.langflowIntegration import F1WorkflowOrchestrator, WorkflowBuilder, LangflowClient


def exampleBasicWorkflow():
    """Basic workflow execution"""
    print("\n" + "="*60)
    print("Example 1: Basic Workflow Execution")
    print("="*60)
    
    orchestrator = F1WorkflowOrchestrator()
    
    # Sample race data
    raceData = {
        'drivers': {
            'VER': {'position': 1, 'speed': 315, 'inPit': False, 'drs': 0},
            'HAM': {'position': 2, 'speed': 312, 'inPit': False, 'drs': 1},
            'LEC': {'position': 3, 'speed': 310, 'inPit': True, 'drs': 0}
        },
        'weather': {'rainState': 'DRY', 'trackTemp': 42.0, 'airTemp': 28.0},
        't': 250.0
    }
    
    print("\nExecuting commentary workflow...")
    result = orchestrator.executeWorkflow('commentary', raceData)
    
    print(f"\nWorkflow: {result['workflow']}")
    print(f"Steps executed: {len(result['steps'])}")
    
    for step in result['steps']:
        print(f"\n  Step: {step['action']}")
        print(f"  Status: {step['status']}")


def exampleAnalysisWorkflow():
    """Race analysis workflow"""
    print("\n" + "="*60)
    print("Example 2: Race Analysis Workflow")
    print("="*60)
    
    orchestrator = F1WorkflowOrchestrator()
    
    analysisData = {
        'raceId': 'Bahrain_2024',
        'drivers': ['VER', 'HAM', 'LEC'],
        'laps': 57,
        'pitStops': {
            'VER': [{'lap': 15, 'duration': 2.3}],
            'HAM': [{'lap': 18, 'duration': 2.5}],
            'LEC': [{'lap': 12, 'duration': 2.4}, {'lap': 35, 'duration': 2.6}]
        }
    }
    
    print("\nExecuting analysis workflow...")
    result = orchestrator.executeWorkflow('analysis', analysisData)
    
    print(f"\nAnalysis completed!")
    print(f"Steps: {len(result['steps'])}")


def examplePredictionWorkflow():
    """Race prediction workflow"""
    print("\n" + "="*60)
    print("Example 3: Race Prediction Workflow")
    print("="*60)
    
    orchestrator = F1WorkflowOrchestrator()
    
    predictionData = {
        'circuit': 'Monaco',
        'weather': 'DRY',
        'qualifyingResults': {
            'VER': 1,
            'LEC': 2,
            'HAM': 3
        },
        'historicalData': {
            'VER': {'wins': 3, 'podiums': 5},
            'LEC': {'wins': 2, 'podiums': 4},
            'HAM': {'wins': 1, 'podiums': 3}
        }
    }
    
    print("\nExecuting prediction workflow...")
    result = orchestrator.executeWorkflow('prediction', predictionData)
    
    print(f"\nPrediction completed!")


def exampleCustomWorkflow():
    """Build custom workflow"""
    print("\n" + "="*60)
    print("Example 4: Custom Workflow Builder")
    print("="*60)
    
    builder = WorkflowBuilder()
    
    workflow = (builder
        .setName("Pit Stop Strategy")
        .setDescription("Analyze optimal pit stop timing")
        .addStep("load_race_data", {})
        .addStep("analyze_tyre_wear", {'compound': 'SOFT'})
        .addStep("calculate_pit_window", {'targetLap': 20})
        .addStep("generate_recommendation", {})
        .build()
    )
    
    print(f"\nCustom Workflow Created:")
    print(f"  Name: {workflow['name']}")
    print(f"  Description: {workflow['description']}")
    print(f"  Steps: {len(workflow['steps'])}")
    
    for i, step in enumerate(workflow['steps'], 1):
        print(f"\n  Step {i}: {step['action']}")
        print(f"    Params: {step['params']}")


def exampleLangflowClient():
    """Langflow client usage"""
    print("\n" + "="*60)
    print("Example 5: Langflow Client")
    print("="*60)
    
    client = LangflowClient()
    
    if client.isAvailable():
        print("\n✅ Langflow is running")
        print(f"   Base URL: {client.baseUrl}")
        
        # Create a flow
        flowId = client.createCommentaryFlow()
        print(f"\n✅ Flow created: {flowId}")
    else:
        print("\n⚠️ Langflow not running")
        print("   Start with: langflow run")
        print("   Then access: http://localhost:7860")


def exampleComplexWorkflow():
    """Complex multi-step workflow"""
    print("\n" + "="*60)
    print("Example 6: Complex Multi-Step Workflow")
    print("="*60)
    
    builder = WorkflowBuilder()
    
    workflow = (builder
        .setName("Complete Race Analysis")
        .setDescription("Full race analysis with AI commentary")
        .addStep("load_race_data", {'year': 2024, 'round': 1})
        .addStep("extract_telemetry", {})
        .addStep("detect_events", {'eventTypes': ['overtake', 'pit_stop', 'crash']})
        .addStep("analyze_strategy", {})
        .addStep("generate_commentary", {'style': 'exciting'})
        .addStep("create_highlights", {'topN': 5})
        .addStep("generate_report", {'format': 'markdown'})
        .build()
    )
    
    print(f"\nComplex Workflow:")
    print(f"  Name: {workflow['name']}")
    print(f"  Total Steps: {len(workflow['steps'])}")
    
    print("\n  Workflow Pipeline:")
    for i, step in enumerate(workflow['steps'], 1):
        print(f"    {i}. {step['action']}")


def exampleEventDrivenWorkflow():
    """Event-driven workflow"""
    print("\n" + "="*60)
    print("Example 7: Event-Driven Workflow")
    print("="*60)
    
    orchestrator = F1WorkflowOrchestrator()
    
    # Simulate different race events
    events = [
        {'type': 'overtake', 'driver': 'HAM', 'overtaken': 'VER', 'lap': 15},
        {'type': 'pit_stop', 'driver': 'LEC', 'lap': 18, 'duration': 2.4},
        {'type': 'fastest_lap', 'driver': 'VER', 'lap': 25, 'time': 92.3}
    ]
    
    print("\nProcessing race events:")
    for event in events:
        print(f"\n  Event: {event['type']}")
        print(f"  Driver: {event['driver']}")
        
        # Execute workflow based on event type
        if event['type'] == 'overtake':
            data = {'event': event, 'drivers': {}}
            result = orchestrator.executeWorkflow('commentary', data)
            print(f"  Commentary generated: {result['steps'][-1]['status']}")


def main():
    print("="*60)
    print("WORKFLOW ORCHESTRATION EXAMPLES")
    print("="*60)
    print("\nThese examples demonstrate AI workflow orchestration.")
    
    try:
        exampleBasicWorkflow()
        exampleAnalysisWorkflow()
        examplePredictionWorkflow()
        exampleCustomWorkflow()
        exampleLangflowClient()
        exampleComplexWorkflow()
        exampleEventDrivenWorkflow()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED!")
        print("="*60)
        print("\nTo use Langflow:")
        print("1. Install: pip install langflow")
        print("2. Start: langflow run")
        print("3. Open: http://localhost:7860")
        print("4. Build visual workflows in the UI")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
