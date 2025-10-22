# langchain_memory.py
import time
import re
import json
from typing import List, Dict, Any
from datetime import datetime

class LangChainConversationMemory:
    """Simplified conversation memory system (No LangChain dependencies)"""
    
    def __init__(self, max_history=10):
        self.max_history = max_history
        self.conversation_history = []
        self.current_topics = set()
        
    def add_interaction(self, user_message: str, assistant_response: str, tool_used: str = None):
        """Add interaction to memory"""
        # Extract topics
        topics = self._extract_topics(user_message + " " + assistant_response)
        self.current_topics.update(topics)
        
        # Store interaction
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'assistant_response': assistant_response,
            'tool_used': tool_used,
            'topics': list(topics)
        }
        
        self.conversation_history.append(interaction)
        
        # Keep within limit
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    def _extract_topics(self, text: str) -> set:
        """Extract main topics from text"""
        topics = set()
        
        topic_patterns = {
            'programming': ['java', 'python', 'javascript', 'c++', 'programming', 'code', 'developer', 
                           'switch', 'case', 'if-else', 'function', 'class', 'object', 'variable'],
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network'],
            'technology': ['technology', 'tech', 'software', 'computer', 'digital', 'programming'],
            'science': ['science', 'scientific', 'research', 'experiment'],
            'weather': ['weather', 'temperature', 'climate', 'forecast'],
            'news': ['news', 'headlines', 'current events', 'breaking'],
            'education': ['education', 'learn', 'study', 'teaching', 'school'],
            'business': ['business', 'company', 'industry', 'market'],
            'health': ['health', 'medical', 'medicine', 'doctor'],
            'email': ['email', 'send email', 'gmail', 'outlook', 'mail'],
            'pdf': ['pdf', 'document', 'file', 'read pdf'],
            'calculation': ['calculate', 'math', 'equation', 'solve'],
            'image': ['image', 'picture', 'photo', 'analyze this', 'what is in this image'],
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.add(topic)
        
        return topics
    
    def get_conversation_context(self) -> str:
        """Get formatted context for the AI"""
        if not self.conversation_history:
            return "No previous conversation."
        
        context = "=== CONVERSATION HISTORY ===\n"
        for i, interaction in enumerate(self.conversation_history[-3:], 1):
            context += f"Exchange {i}:\n"
            context += f"  User: {interaction['user_message']}\n"
            response_preview = interaction['assistant_response'][:150] + "..." if len(interaction['assistant_response']) > 150 else interaction['assistant_response']
            context += f"  Assistant: {response_preview}\n"
            if interaction['tool_used']:
                context += f"  Tool Used: {interaction['tool_used']}\n"
            context += "\n"
        
        return context
    
    def is_follow_up_question(self, current_message: str) -> bool:
        """Check if current message is a follow-up"""
        if len(self.conversation_history) < 1:
            return False
        
        last_interaction = self.conversation_history[-1]
        last_user_msg = last_interaction['user_message'].lower()
        current_msg = current_message.lower()
        
        follow_up_indicators = [
            'it', 'that', 'this', 'those', 'these',
            'how about', 'what about', 'and what', 'also',
            'in that case', 'following that', 'regarding',
            'more about', 'tell me more', 'explain further'
        ]
        
        has_follow_up_indicators = any(indicator in current_msg for indicator in follow_up_indicators)
        
        previous_topics = set(last_interaction.get('topics', []))
        current_topics = self._extract_topics(current_msg)
        topics_related = len(previous_topics.intersection(current_topics)) > 0
        
        return has_follow_up_indicators or topics_related
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.conversation_history.clear()
        self.current_topics.clear()
        print("Conversation memory cleared")
    
    def get_conversation_summary(self) -> str:
        """Get conversation summary"""
        total_interactions = len(self.conversation_history)
        topics = list(self.current_topics)
        
        summary = f"""
Conversation Summary:
- Total interactions: {total_interactions}
- Recent topics: {', '.join(topics) if topics else 'None yet'}
- Memory usage: {len(self.conversation_history)}/{self.max_history} exchanges stored
"""
        return summary
    
    def get_conversation_history(self) -> List[Dict]:
        """Get raw conversation history"""
        return self.conversation_history.copy()
    
    def get_last_interaction(self) -> Dict:
        """Get the last interaction"""
        if self.conversation_history:
            return self.conversation_history[-1]
        return {}