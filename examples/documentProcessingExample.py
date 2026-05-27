"""
Document Processing Example
Demonstrates how to use Docling for F1 documents
"""
import sys
sys.path.append('..')

from documents.documentProcessor import DocumentProcessor, F1RegulationsProcessor


def exampleBasicProcessing():
    """Basic document processing"""
    print("\n" + "="*60)
    print("Example 1: Basic Document Processing")
    print("="*60)
    
    processor = DocumentProcessor()
    
    if not processor.doclingAvailable:
        print("\n⚠️ Docling not installed")
        print("Install with: pip install docling")
        return
    
    print("\nDocling is ready!")
    print("\nTo process a document:")
    print("  doc_data = processor.processDocument('path/to/document.pdf')")
    print("\nSupported formats: PDF, DOCX, PPTX, HTML, Markdown")


def exampleSearchDocument():
    """Search in processed document"""
    print("\n" + "="*60)
    print("Example 2: Search in Document")
    print("="*60)
    
    processor = DocumentProcessor()
    
    # Example document data (simulated)
    exampleDoc = {
        'filePath': 'FIA_Regulations_2024.pdf',
        'text': 'Full document text here...',
        'sections': [
            {
                'title': 'DRS REGULATIONS',
                'content': 'The DRS (Drag Reduction System) may only be activated in designated zones when a driver is within one second of the car ahead.'
            },
            {
                'title': 'TYRE REGULATIONS',
                'content': 'Each driver must use at least two different tyre compounds during a dry race.'
            },
            {
                'title': 'SAFETY CAR PROCEDURES',
                'content': 'When the safety car is deployed, all drivers must reduce speed and maintain position.'
            }
        ]
    }
    
    # Search for DRS rules
    print("\nSearching for 'DRS'...")
    results = processor.searchInDocument(exampleDoc, 'DRS')
    
    for result in results:
        print(f"\nSection: {result['section']}")
        print(f"Relevance: {result['relevance']}")
        print(f"Content: {result['content'][:200]}...")


def exampleF1Regulations():
    """F1-specific regulations processing"""
    print("\n" + "="*60)
    print("Example 3: F1 Regulations Processor")
    print("="*60)
    
    f1Processor = F1RegulationsProcessor()
    
    print("\nF1 Regulations Processor initialized")
    print("\nUsage:")
    print("  # Load regulations")
    print("  regs = f1Processor.loadRegulations('FIA_2024_Regulations.pdf')")
    print("")
    print("  # Check specific regulation")
    print("  drs_rules = f1Processor.checkRegulation('DRS', 'FIA_2024_Regulations.pdf')")
    print("")
    print("  # Extract technical specs")
    print("  specs = f1Processor.extractTechnicalSpecs(regs)")


def exampleTechnicalSpecs():
    """Extract technical specifications"""
    print("\n" + "="*60)
    print("Example 4: Extract Technical Specifications")
    print("="*60)
    
    f1Processor = F1RegulationsProcessor()
    
    # Example document with technical content
    exampleDoc = {
        'text': """
        The engine must be a 1.6 liter V6 turbocharged power unit.
        Maximum RPM is limited to 15,000.
        The car must weigh at least 798 kg including the driver.
        Maximum downforce is regulated by wing dimensions.
        Tyre pressure must be maintained within specified limits.
        The wheelbase must not exceed 3600mm.
        """
    }
    
    specs = f1Processor.extractTechnicalSpecs(exampleDoc)
    
    print("\nExtracted Technical Specifications:")
    for category, items in specs.items():
        if items:
            print(f"\n{category.upper()}:")
            for item in items[:3]:  # Show first 3 items
                print(f"  - {item}")


def exampleCaching():
    """Document caching demonstration"""
    print("\n" + "="*60)
    print("Example 5: Document Caching")
    print("="*60)
    
    processor = DocumentProcessor(cacheDir="example_cache")
    
    print("\nDocument caching is automatic!")
    print("\nFirst time processing a document:")
    print("  - Processes the entire document")
    print("  - Saves to cache")
    print("  - Takes 1-10 seconds")
    print("\nSubsequent loads:")
    print("  - Loads from cache")
    print("  - Instant (< 1 second)")
    print(f"\nCache directory: {processor.cacheDir}")


def exampleRealWorldUsage():
    """Real-world usage scenario"""
    print("\n" + "="*60)
    print("Example 6: Real-World Usage Scenario")
    print("="*60)
    
    print("\nScenario: Processing F1 Race Report")
    print("\nStep 1: Process the document")
    print("  processor = DocumentProcessor()")
    print("  report = processor.processDocument('Bahrain_GP_2024_Report.pdf')")
    print("\nStep 2: Extract key information")
    print("  winner = processor.searchInDocument(report, 'race winner')")
    print("  incidents = processor.searchInDocument(report, 'incident')")
    print("  penalties = processor.searchInDocument(report, 'penalty')")
    print("\nStep 3: Use in your application")
    print("  # Display race summary")
    print("  # Show incidents timeline")
    print("  # Analyze penalties")


def main():
    print("="*60)
    print("DOCUMENT PROCESSING EXAMPLES")
    print("="*60)
    print("\nThese examples demonstrate document processing with Docling.")
    
    try:
        exampleBasicProcessing()
        exampleSearchDocument()
        exampleF1Regulations()
        exampleTechnicalSpecs()
        exampleCaching()
        exampleRealWorldUsage()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED!")
        print("="*60)
        print("\nTo use with real documents:")
        print("1. Install Docling: pip install docling")
        print("2. Place your PDF/DOCX files in the project")
        print("3. Process them using the examples above")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
