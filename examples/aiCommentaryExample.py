"""
AI Commentary Example
Demonstrates how to use the AI commentary system
"""
import sys
sys.path.append('..')

from ai.aiCommentary import CommentaryManager, AICommentary
from ai.graniteClient import GraniteClient


def exampleBasicCommentary():
    """Basic commentary generation"""
    print("\n" + "="*60)
    print("Example 1: Basic Commentary Generation")
    print("="*60)
    
    manager = CommentaryManager()
    
    # Simulate race frame
    frame = {
        't': 150.0,
        'drivers': {
            'VER': {'position': 1, 'speed': 320.5, 'lap': 8, 'drs': 0, 'inPit': False},
            'HAM': {'position': 2, 'speed': 318.0, 'lap': 8, 'drs': 1, 'inPit': False},
            'LEC': {'position': 3, 'speed': 315.0, 'lap': 8, 'drs': 0, 'inPit': False}
        },
        'weather': {
            'rainState': 'DRY',
            'trackTemp': 45.0,
            'airTemp': 30.0
        }
    }
    
    commentary = manager.generateForFrame(frame)
    print(f"\nCommentary: {commentary}")


def exampleEventDetection():
    """Event detection and commentary"""
    print("\n" + "="*60)
    print("Example 2: Event Detection")
    print("="*60)
    
    manager = CommentaryManager()
    
    # Frame 1: Normal racing
    frame1 = {
        't': 200.0,
        'drivers': {
            'VER': {'position': 1, 'speed': 310.0, 'lap': 10, 'drs': 0, 'inPit': False},
            'HAM': {'position': 2, 'speed': 308.0, 'lap': 10, 'drs': 0, 'inPit': False}
        },
        'weather': {'rainState': 'DRY', 'trackTemp': 42.0, 'airTemp': 28.0}
    }
    
    # Frame 2: HAM activates DRS
    frame2 = {
        't': 201.0,
        'drivers': {
            'VER': {'position': 1, 'speed': 310.0, 'lap': 10, 'drs': 0, 'inPit': False},
            'HAM': {'position': 2, 'speed': 315.0, 'lap': 10, 'drs': 1, 'inPit': False}
        },
        'weather': {'rainState': 'DRY', 'trackTemp': 42.0, 'airTemp': 28.0}
    }
    
    # Frame 3: HAM overtakes VER
    frame3 = {
        't': 202.0,
        'drivers': {
            'HAM': {'position': 1, 'speed': 318.0, 'lap': 10, 'drs': 1, 'inPit': False},
            'VER': {'position': 2, 'speed': 310.0, 'lap': 10, 'drs': 0, 'inPit': False}
        },
        'weather': {'rainState': 'DRY', 'trackTemp': 42.0, 'airTemp': 28.0}
    }
    
    print("\nFrame 1 (Normal racing):")
    commentary1 = manager.generateForFrame(frame1, None)
    print(f"  {commentary1}")
    
    print("\nFrame 2 (DRS activated):")
    commentary2 = manager.generateForFrame(frame2, frame1)
    print(f"  {commentary2}")
    
    print("\nFrame 3 (Overtake!):")
    commentary3 = manager.generateForFrame(frame3, frame2)
    print(f"  {commentary3}")


def examplePitStop():
    """Pit stop commentary"""
    print("\n" + "="*60)
    print("Example 3: Pit Stop Commentary")
    print("="*60)
    
    manager = CommentaryManager()
    
    # Before pit stop
    frame1 = {
        't': 500.0,
        'drivers': {
            'LEC': {'position': 3, 'speed': 305.0, 'lap': 15, 'drs': 0, 'inPit': False}
        },
        'weather': {'rainState': 'DRY', 'trackTemp': 40.0, 'airTemp': 27.0}
    }
    
    # During pit stop
    frame2 = {
        't': 502.0,
        'drivers': {
            'LEC': {'position': 3, 'speed': 80.0, 'lap': 15, 'drs': 0, 'inPit': True}
        },
        'weather': {'rainState': 'DRY', 'trackTemp': 40.0, 'airTemp': 27.0}
    }
    
    print("\nBefore pit stop:")
    commentary1 = manager.generateForFrame(frame1, None)
    print(f"  {commentary1}")
    
    print("\nDuring pit stop:")
    commentary2 = manager.generateForFrame(frame2, frame1)
    print(f"  {commentary2}")


def exampleGraniteClient():
    """Direct Granite client usage"""
    print("\n" + "="*60)
    print("Example 4: Direct Granite Client Usage")
    print("="*60)
    
    client = GraniteClient()
    
    if not client.isAvailable():
        print("\n⚠️ Ollama not running. Start with: ollama serve")
        return
    
    print(f"\nAvailable models: {client.listModels()}")
    
    # Generate custom text
    prompt = "Describe an exciting F1 overtake in one sentence."
    print(f"\nPrompt: {prompt}")
    
    response = client.generate(prompt, maxTokens=100)
    print(f"Response: {response}")


def exampleCommentaryHistory():
    """Track commentary history"""
    print("\n" + "="*60)
    print("Example 5: Commentary History")
    print("="*60)
    
    manager = CommentaryManager()
    
    # Generate multiple commentaries
    frames = [
        {'t': 100, 'drivers': {'VER': {'position': 1, 'speed': 310, 'lap': 5, 'drs': 0, 'inPit': False}}, 'weather': {'rainState': 'DRY', 'trackTemp': 40, 'airTemp': 25}},
        {'t': 110, 'drivers': {'VER': {'position': 1, 'speed': 315, 'lap': 5, 'drs': 1, 'inPit': False}}, 'weather': {'rainState': 'DRY', 'trackTemp': 40, 'airTemp': 25}},
        {'t': 120, 'drivers': {'VER': {'position': 1, 'speed': 320, 'lap': 6, 'drs': 0, 'inPit': False}}, 'weather': {'rainState': 'DRY', 'trackTemp': 41, 'airTemp': 26}},
    ]
    
    prevFrame = None
    for frame in frames:
        commentary = manager.generateForFrame(frame, prevFrame)
        if commentary:
            print(f"\nTime {frame['t']}s: {commentary}")
        prevFrame = frame
    
    # Get history
    history = manager.getCommentaryHistory()
    print(f"\n\nTotal commentaries generated: {len(history)}")
    print("\nHistory:")
    for item in history:
        print(f"  [{item['time']:.1f}s] {item['event']}: {item['text']}")


def main():
    print("="*60)
    print("AI COMMENTARY EXAMPLES")
    print("="*60)
    print("\nThese examples demonstrate the AI commentary system.")
    print("Make sure Ollama is running with: ollama serve")
    print("And the model is installed: ollama pull granite3-dense:8b")
    
    try:
        exampleBasicCommentary()
        exampleEventDetection()
        examplePitStop()
        exampleGraniteClient()
        exampleCommentaryHistory()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is running: ollama serve")
        print("2. Model is installed: ollama pull granite3-dense:8b")


if __name__ == "__main__":
    main()
