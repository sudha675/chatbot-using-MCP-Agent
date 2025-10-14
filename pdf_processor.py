# pdf_processor.py
import PyPDF2
import re
import os
from typing import List, Dict, Tuple
import base64
import io

class PDFProcessor:
    """Handles PDF reading, extraction, and analysis"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def extract_text_from_pdf(self, pdf_data: str) -> Dict:
        """
        Extract text from PDF base64 data or file path
        Returns: Dictionary with text content and metadata
        """
        try:
            # Handle base64 data
            if pdf_data.startswith('data:application/pdf;base64,'):
                pdf_data = pdf_data.split(',')[1]
            
            pdf_bytes = base64.b64decode(pdf_data)
            
            # Check file size
            if len(pdf_bytes) > self.max_file_size:
                return {
                    'success': False,
                    'error': f'File too large. Maximum size is {self.max_file_size // 1024 // 1024}MB'
                }
            
            # Read PDF
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract metadata
            metadata = {
                'pages': len(pdf_reader.pages),
                'author': pdf_reader.metadata.get('/Author', 'Unknown'),
                'title': pdf_reader.metadata.get('/Title', 'Unknown'),
                'subject': pdf_reader.metadata.get('/Subject', 'Unknown'),
            }
            
            # Extract text from all pages
            full_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
            
            return {
                'success': True,
                'text': full_text.strip(),
                'metadata': metadata,
                'summary': self.generate_summary(full_text),
                'key_points': self.extract_key_points(full_text)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading PDF: {str(e)}'
            }
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a concise summary of the PDF content"""
        # Simple summary generation - you can enhance this with AI
        sentences = re.split(r'[.!?]+', text)
        
        # Remove very short sentences and clean up
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first few meaningful sentences as summary
        summary = ' '.join(sentences[:3])
        
        if len(summary) > max_length:
            summary = summary[:max_length] + '...'
            
        return summary
    
    def extract_key_points(self, text: str, max_points: int = 10) -> List[str]:
        """Extract key points from PDF text"""
        key_points = []
        
        # Look for bullet points, numbered lists, and important sections
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip very short lines
            if len(line) < 20:
                continue
                
            # Look for bullet points or numbered items
            if (line.startswith('•') or 
                line.startswith('-') or 
                re.match(r'^\d+\.', line) or
                re.match(r'^[A-Z][a-z]+:', line) or
                any(keyword in line.lower() for keyword in [
                    'important', 'key', 'summary', 'conclusion', 
                    'recommendation', 'finding', 'result'
                ])):
                
                key_points.append(line)
                
            # Stop if we have enough points
            if len(key_points) >= max_points:
                break
        
        # If no structured points found, extract important sentences
        if not key_points:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
            key_points = sentences[:max_points]
        
        return key_points
    
    def analyze_pdf_structure(self, text: str) -> Dict:
        """Analyze PDF structure and content type"""
        lines = text.split('\n')
        
        analysis = {
            'has_headings': False,
            'has_lists': False,
            'has_tables': False,
            'content_type': 'unknown',
            'estimated_word_count': len(text.split())
        }
        
        # Check for headings (lines in all caps or with specific patterns)
        heading_patterns = [
            r'^[A-Z][A-Z\s]{10,}$',  # All caps with spaces
            r'^\d+\.\s+[A-Z]',       # Numbered headings
            r'^[IVX]+\.\s+[A-Z]',    # Roman numeral headings
        ]
        
        for line in lines:
            if any(re.match(pattern, line.strip()) for pattern in heading_patterns):
                analysis['has_headings'] = True
            
            if line.strip().startswith(('•', '-', '*')) or re.match(r'^\d+\.', line.strip()):
                analysis['has_lists'] = True
        
        # Determine content type based on keywords
        text_lower = text.lower()
        if any(word in text_lower for word in ['research', 'study', 'methodology', 'results']):
            analysis['content_type'] = 'research_paper'
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms', 'conditions']):
            analysis['content_type'] = 'legal_document'
        elif any(word in text_lower for word in ['invoice', 'receipt', 'payment', 'total']):
            analysis['content_type'] = 'financial_document'
        elif any(word in text_lower for word in ['resume', 'cv', 'experience', 'skills']):
            analysis['content_type'] = 'resume'
        else:
            analysis['content_type'] = 'general_document'
        
        return analysis
    
    def format_pdf_report(self, extraction_result: Dict) -> str:
        """Format PDF analysis into a readable report"""
        if not extraction_result['success']:
            return f"❌ Error: {extraction_result['error']}"
        
        report = f"""
📄 **PDF ANALYSIS REPORT**

**Document Information:**
• Pages: {extraction_result['metadata']['pages']}
• Title: {extraction_result['metadata']['title']}
• Author: {extraction_result['metadata']['author']}
• Content Type: {extraction_result.get('structure', {}).get('content_type', 'Unknown')}

**Summary:**
{extraction_result['summary']}

**Key Points:**
"""
        
        for i, point in enumerate(extraction_result['key_points'][:8], 1):
            report += f"{i}. {point}\n"
        
        report += f"\n**Word Count:** {extraction_result.get('structure', {}).get('estimated_word_count', 'Unknown')}"
        
        return report

# Test the PDF Processor
if __name__ == "__main__":
    processor = PDFProcessor()
    
    # Test with a sample (you would need an actual PDF file for real testing)
    print("🧪 Testing PDF Processor...")
    
    # This is a mock test - in real usage, you'd provide actual PDF data
    test_result = {
        'success': True,
        'text': "This is a sample PDF content for testing purposes.",
        'metadata': {'pages': 5, 'author': 'Test Author', 'title': 'Test Document'},
        'summary': "Sample summary of the test document.",
        'key_points': ['First key point', 'Second important finding', 'Third recommendation']
    }
    
    report = processor.format_pdf_report(test_result)
    print(report)