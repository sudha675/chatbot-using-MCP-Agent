import re
from datetime import datetime
from typing import List, Dict

class LangChainConversationMemory:
    """Simplified conversation memory system."""
    
    def __init__(self, max_history=10):
        self.max_history = max_history
        self.conversation_history = []
        self.current_topics = set()
        
    def add_interaction(self, user_message: str, assistant_response: str, tool_used: str = None):
        topics = self._extract_topics(user_message + " " + assistant_response)
        self.current_topics.update(topics)
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'assistant_response': assistant_response,
            'tool_used': tool_used,
            'topics': list(topics)
        }
        self.conversation_history.append(interaction)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    def _extract_topics(self, text: str) -> set:
        topics = set()
        topic_patterns = {
            'programming': ['java', 'python', 'javascript', 'c++', 'programming', 'code'],
            'ai': ['ai', 'artificial intelligence', 'machine learning'],
            'weather': ['weather', 'temperature', 'forecast'],
            'news': ['news', 'headlines', 'current events'],
            'email': ['email', 'send email', 'gmail'],
            'image': ['image', 'picture', 'photo'],
        }
        text_lower = text.lower()
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.add(topic)
        return topics
    
    def get_conversation_context(self) -> str:
        if not self.conversation_history:
            return "No previous conversation."
        context = "=== CONVERSATION HISTORY ===\n"
        for i, interaction in enumerate(self.conversation_history[-3:], 1):
            context += f"Exchange {i}:\n  User: {interaction['user_message']}\n"
            preview = interaction['assistant_response'][:150] + "..." if len(interaction['assistant_response']) > 150 else interaction['assistant_response']
            context += f"  Assistant: {preview}\n"
            if interaction['tool_used']:
                context += f"  Tool Used: {interaction['tool_used']}\n"
            context += "\n"
        return context
    
    def is_follow_up_question(self, current_message: str) -> bool:
        if len(self.conversation_history) < 1:
            return False
        last = self.conversation_history[-1]
        last_user = last['user_message'].lower()
        current = current_message.lower()
        indicators = ['it', 'that', 'this', 'how about', 'what about', 'more about']
        has_indicator = any(ind in current for ind in indicators)
        last_topics = set(last.get('topics', []))
        current_topics = self._extract_topics(current_message)
        topics_related = len(last_topics.intersection(current_topics)) > 0
        return has_indicator or topics_related
    
    def clear_memory(self):
        self.conversation_history.clear()
        self.current_topics.clear()
    
    def get_conversation_summary(self) -> str:
        total = len(self.conversation_history)
        topics = list(self.current_topics)
        return f"Conversation Summary:\n- Total interactions: {total}\n- Recent topics: {', '.join(topics) if topics else 'None'}\n- Memory usage: {total}/{self.max_history}"