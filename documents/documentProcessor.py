"""
Document Processor using Docling
Process F1 regulations, race reports, and historical documents
"""
from typing import Dict, List, Optional
import json
import os
import re


class DocumentProcessor:
    def __init__(self, cacheDir: str = "document_cache"):
        self.cacheDir = cacheDir
        self.ensureCacheDir()
        
        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
            self.doclingAvailable = True
            print("✅ Docling initialized successfully")
        except ImportError:
            print("⚠️ Docling not installed. Using built-in markdown processor")
            self.doclingAvailable = False
            self.converter = None
    
    def ensureCacheDir(self):
        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)
    
    def processDocument(self, filePath: str) -> Optional[Dict]:
        """Process document with Docling or fallback to markdown parser"""
        if not self.doclingAvailable:
            return self._processMarkdownDocument(filePath)
        
        try:
            cacheFile = self._getCachePath(filePath)
            if os.path.exists(cacheFile):
                print(f"📦 Loading from cache: {cacheFile}")
                with open(cacheFile, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            print(f"📄 Processing document with Docling: {filePath}")
            result = self.converter.convert(filePath)
            
            structuredData = {
                'filePath': filePath,
                'text': result.document.export_to_text(),
                'markdown': result.document.export_to_markdown(),
                'metadata': {
                    'numPages': len(result.document.pages) if hasattr(result.document, 'pages') else 0,
                    'title': self._extractTitle(result.document),
                },
                'sections': self._extractSections(result.document)
            }
            
            # Cache the result
            with open(cacheFile, 'w', encoding='utf-8') as f:
                json.dump(structuredData, f, indent=2)
            
            print(f"✅ Document processed: {len(structuredData['sections'])} sections found")
            return structuredData
            
        except Exception as e:
            print(f"⚠️ Docling processing failed: {e}, falling back to markdown parser")
            return self._processMarkdownDocument(filePath)
    
    def _processMarkdownDocument(self, filePath: str) -> Dict:
        """Fallback: Process markdown documents without Docling"""
        try:
            print(f"📝 Processing markdown document: {filePath}")
            
            if not os.path.exists(filePath):
                print(f"❌ File not found: {filePath}")
                return self._createEmptyDocument(filePath)
            
            with open(filePath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first # heading)
            titleMatch = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = titleMatch.group(1) if titleMatch else os.path.basename(filePath)
            
            # Extract sections using shared method
            sections = self._extractSectionsFromMarkdown(content)
            
            structuredData = {
                'filePath': filePath,
                'text': content,
                'markdown': content,
                'metadata': {
                    'numPages': 1,
                    'title': title,
                    'sections_count': len(sections)
                },
                'sections': sections
            }
            
            print(f"✅ Markdown processed: {len(sections)} sections, {sum(len(s.get('subsections', [])) for s in sections)} subsections")
            return structuredData
            
        except Exception as e:
            print(f"❌ Error processing markdown: {e}")
            return self._createEmptyDocument(filePath)
    
    def _createEmptyDocument(self, filePath: str) -> Dict:
        """Create empty document structure"""
        return {
            'filePath': filePath,
            'text': '',
            'markdown': '',
            'metadata': {
                'numPages': 0,
                'title': os.path.basename(filePath),
                'error': 'Document could not be processed'
            },
            'sections': []
        }
    
    def _getCachePath(self, filePath: str) -> str:
        filename = os.path.basename(filePath)
        cacheName = f"{filename}.json"
        return os.path.join(self.cacheDir, cacheName)
    
    def _extractTitle(self, document) -> str:
        try:
            if hasattr(document, 'title'):
                return document.title
            text = document.export_to_text()
            lines = text.split('\n')
            return lines[0] if lines else "Untitled"
        except:
            return "Untitled"
    
    def _extractSections(self, document) -> List[Dict]:
        """Extract sections from Docling document object"""
        try:
            # Get markdown from document
            markdown = document.export_to_markdown()
            
            # Use our markdown parser to extract sections
            return self._extractSectionsFromMarkdown(markdown)
        except Exception as e:
            print(f"⚠️ Section extraction failed: {e}")
            return []
    
    def _extractSectionsFromMarkdown(self, markdown: str) -> List[Dict]:
        """Extract sections from markdown text"""
        sections = []
        
        # Extract sections (## headings)
        sectionPattern = r'^##\s+(.+?)$\n(.*?)(?=^##\s+|\Z)'
        matches = re.finditer(sectionPattern, markdown, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            sectionTitle = match.group(1).strip()
            sectionContent = match.group(2).strip()
            
            # Extract subsections (### headings)
            subsections = []
            subsectionPattern = r'^###\s+(.+?)$\n(.*?)(?=^###\s+|\Z)'
            submatches = re.finditer(subsectionPattern, sectionContent, re.MULTILINE | re.DOTALL)
            
            for submatch in submatches:
                subsections.append({
                    'title': submatch.group(1).strip(),
                    'content': submatch.group(2).strip()
                })
            
            sections.append({
                'title': sectionTitle,
                'content': sectionContent,
                'subsections': subsections
            })
        
        return sections
    
    def _fallbackProcessor(self, filePath: str) -> Dict:
        """Legacy fallback - now redirects to markdown processor"""
        return self._processMarkdownDocument(filePath)
    
    def searchInDocument(self, documentData: Dict, query: str) -> List[Dict]:
        """Search for query in document sections"""
        results = []
        queryLower = query.lower()
        
        for section in documentData.get('sections', []):
            sectionTitle = section.get('title', '')
            content = section.get('content', '').lower()
            
            if queryLower in content or queryLower in sectionTitle.lower():
                # Calculate relevance score
                relevance = content.count(queryLower)
                
                # Extract relevant snippet
                contentLines = section.get('content', '').split('\n')
                relevantLines = [line for line in contentLines if queryLower in line.lower()]
                snippet = '\n'.join(relevantLines[:3])  # First 3 relevant lines
                
                results.append({
                    'section': sectionTitle,
                    'content': snippet if snippet else section.get('content', '')[:300],
                    'relevance': relevance,
                    'subsections': len(section.get('subsections', []))
                })
            
            # Also search subsections
            for subsection in section.get('subsections', []):
                subContent = subsection.get('content', '').lower()
                if queryLower in subContent:
                    results.append({
                        'section': f"{sectionTitle} > {subsection.get('title', '')}",
                        'content': subsection.get('content', '')[:300],
                        'relevance': subContent.count(queryLower),
                        'subsections': 0
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results
    
    def extractRegulationRules(self, documentData: Dict) -> Dict:
        """Extract specific F1 regulation rules from document"""
        rules = {
            'drs_rules': [],
            'pit_rules': [],
            'tyre_rules': [],
            'safety_car_rules': [],
            'penalty_rules': [],
            'flag_rules': []
        }
        
        keywords = {
            'drs_rules': ['drs', 'drag reduction', 'rear wing'],
            'pit_rules': ['pit', 'pit lane', 'pit stop'],
            'tyre_rules': ['tyre', 'tire', 'compound', 'pressure'],
            'safety_car_rules': ['safety car', 'sc', 'vsc', 'virtual safety'],
            'penalty_rules': ['penalty', 'time penalty', 'grid penalty'],
            'flag_rules': ['flag', 'yellow flag', 'red flag', 'blue flag']
        }
        
        for section in documentData.get('sections', []):
            sectionTitle = section.get('title', '').lower()
            sectionContent = section.get('content', '')
            
            # Check which category this section belongs to
            for ruleType, terms in keywords.items():
                if any(term in sectionTitle for term in terms):
                    rules[ruleType].append({
                        'title': section.get('title', ''),
                        'content': sectionContent[:500]  # First 500 chars
                    })
            
            # Also check subsections
            for subsection in section.get('subsections', []):
                subTitle = subsection.get('title', '').lower()
                subContent = subsection.get('content', '')
                
                for ruleType, terms in keywords.items():
                    if any(term in subTitle for term in terms):
                        rules[ruleType].append({
                            'title': f"{section.get('title', '')} > {subsection.get('title', '')}",
                            'content': subContent[:500]
                        })
        
        return rules


class F1RegulationsProcessor:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.regulationsCache = {}
    
    def loadRegulations(self, regulationsFile: str) -> Dict:
        if regulationsFile in self.regulationsCache:
            return self.regulationsCache[regulationsFile]
        
        docData = self.processor.processDocument(regulationsFile)
        self.regulationsCache[regulationsFile] = docData
        return docData
    
    def checkRegulation(self, query: str, regulationsFile: str) -> List[Dict]:
        docData = self.loadRegulations(regulationsFile)
        return self.processor.searchInDocument(docData, query)
    
    def extractTechnicalSpecs(self, documentData: Dict) -> Dict:
        specs = {
            'engine': [],
            'aerodynamics': [],
            'tyres': [],
            'dimensions': [],
            'weight': []
        }
        
        keywords = {
            'engine': ['engine', 'power unit', 'rpm', 'horsepower'],
            'aerodynamics': ['downforce', 'drag', 'wing', 'diffuser'],
            'tyres': ['tyre', 'tire', 'compound', 'pressure'],
            'dimensions': ['length', 'width', 'height', 'wheelbase'],
            'weight': ['weight', 'mass', 'kg', 'minimum weight']
        }
        
        text = documentData.get('text', '').lower()
        
        for category, terms in keywords.items():
            for term in terms:
                if term in text:
                    sentences = text.split('.')
                    for sentence in sentences:
                        if term in sentence:
                            specs[category].append(sentence.strip())
        
        return specs
