class OllamaChatbot {
    constructor() {
        this.currentSessionId = 'default';
        this.isConnected = false;
        this.eventSource = null;
        this.init();
    }

    init() {
        this.checkStatus();
        this.setupEventListeners();
        this.loadSessions();
        this.setupSSE();
    }

    setupEventListeners() {
        // Send message
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // New session
        document.getElementById('new-session-btn').addEventListener('click', () => this.showNewSessionModal());
        document.getElementById('create-session-btn').addEventListener('click', () => this.createNewSession());
        document.getElementById('cancel-session-btn').addEventListener('click', () => this.hideNewSessionModal());

        // Session management
        document.getElementById('clear-chat-btn').addEventListener('click', () => this.clearChat());
        document.getElementById('delete-session-btn').addEventListener('click', () => this.deleteSession());
    }

    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.updateStatus(data.ollama_available && data.model_available);
            
            if (!data.ollama_available) {
                this.showError('Ollama is not available. Please make sure Ollama is installed and running.');
            } else if (!data.model_available) {
                this.showError(`Model ${data.model_name} is not available. Please pull it with: ollama pull ${data.model_name}`);
            }
        } catch (error) {
            this.updateStatus(false);
            this.showError('Cannot connect to server');
        }
    }

    updateStatus(connected) {
        this.isConnected = connected;
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (connected) {
            indicator.style.color = '#48bb78';
            text.textContent = 'Connected to Ollama';
            text.style.color = '#48bb78';
        } else {
            indicator.style.color = '#f56565';
            text.textContent = 'Disconnected';
            text.style.color = '#f56565';
        }
    }

    setupSSE() {
        this.eventSource = new EventSource('/api/stream');
        
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'chunk':
                    this.appendChunk(data.content, data.session_id);
                    break;
                case 'complete':
                    this.completeResponse(data);
                    break;
                case 'error':
                    this.showError(data.content);
                    break;
                case 'ping':
                    // Keep connection alive
                    break;
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.showError('Connection lost. Reconnecting...');
            setTimeout(() => this.setupSSE(), 5000);
        };
    }

    async sendMessage() {
        if (!this.isConnected) {
            this.showError('Not connected to Ollama');
            return;
        }

        const input = document.getElementById('message-input');
        const message = input.value.trim();

        if (!message) return;

        // Clear input
        input.value = '';

        // Add user message to chat
        this.addMessage('user', message, this.currentSessionId);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.currentSessionId
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.showError('Failed to send message: ' + error.message);
        }
    }

    addMessage(role, content, sessionId) {
        if (sessionId !== this.currentSessionId) return;

        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    appendChunk(content, sessionId) {
        if (sessionId !== this.currentSessionId) return;

        this.hideTypingIndicator();
        
        const messagesContainer = document.getElementById('chat-messages');
        let lastMessage = messagesContainer.lastChild;

        // If last message is not from assistant, create new one
        if (!lastMessage || !lastMessage.classList.contains('assistant')) {
            this.addMessage('assistant', content, sessionId);
            return;
        }

        // Append to existing assistant message
        const contentDiv = lastMessage.querySelector('.message-content');
        contentDiv.textContent += content;

        // Update timestamp
        const timeDiv = lastMessage.querySelector('.message-time');
        timeDiv.textContent = new Date().toLocaleTimeString();

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    completeResponse(data) {
        this.hideTypingIndicator();
        document.getElementById('response-time').textContent = `Response time: ${data.response_time.toFixed(2)}s`;
        
        // Reload sessions to update message counts
        this.loadSessions();
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.textContent = 'AI is thinking...';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            const data = await response.json();
            
            this.renderSessions(data.sessions);
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    renderSessions(sessions) {
        const sessionsList = document.getElementById('sessions-list');
        sessionsList.innerHTML = '';

        sessions.forEach(session => {
            const sessionDiv = document.createElement('div');
            sessionDiv.className = `session-item ${session.session_id === this.currentSessionId ? 'active' : ''}`;
            sessionDiv.innerHTML = `
                <div class="session-name">${session.name}</div>
                <div class="session-meta">
                    ${session.message_count} messages<br>
                    ${new Date(session.created_at).toLocaleDateString()}
                </div>
            `;

            sessionDiv.addEventListener('click', () => this.switchSession(session.session_id, session.name));
            sessionsList.appendChild(sessionDiv);
        });
    }

    async switchSession(sessionId, sessionName) {
        this.currentSessionId = sessionId;
        document.getElementById('current-session-name').textContent = sessionName;
        
        // Reload sessions to update active state
        this.loadSessions();
        
        // Load session history
        await this.loadSessionHistory(sessionId);
    }

    async loadSessionHistory(sessionId) {
        try {
            const response = await fetch(`/api/history/${sessionId}`);
            const data = await response.json();
            
            this.renderChatHistory(data.history);
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    renderChatHistory(history) {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = '';

        history.forEach(exchange => {
            this.addMessage('user', exchange.user, this.currentSessionId);
            this.addMessage('assistant', exchange.assistant, this.currentSessionId);
        });
    }

    showNewSessionModal() {
        document.getElementById('new-session-modal').style.display = 'block';
        document.getElementById('session-name-input').value = '';
        document.getElementById('session-name-input').focus();
    }

    hideNewSessionModal() {
        document.getElementById('new-session-modal').style.display = 'none';
    }

    async createNewSession() {
        const nameInput = document.getElementById('session-name-input');
        const sessionName = nameInput.value.trim() || `Session_${Date.now()}`;

        try {
            const response = await fetch('/api/session/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: sessionName })
            });

            if (response.ok) {
                const data = await response.json();
                this.hideNewSessionModal();
                this.switchSession(data.session_id, data.name);
                this.loadSessions();
            } else {
                throw new Error('Failed to create session');
            }
        } catch (error) {
            this.showError('Failed to create session: ' + error.message);
        }
    }

    async clearChat() {
        if (!confirm('Are you sure you want to clear the chat history?')) return;

        try {
            const response = await fetch(`/api/history/${this.currentSessionId}/clear`, {
                method: 'POST'
            });

            if (response.ok) {
                this.renderChatHistory([]);
            } else {
                throw new Error('Failed to clear chat');
            }
        } catch (error) {
            this.showError('Failed to clear chat: ' + error.message);
        }
    }

    async deleteSession() {
        if (this.currentSessionId === 'default') {
            alert('Cannot delete the default session');
            return;
        }

        if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) return;

        try {
            const response = await fetch(`/api/session/${this.currentSessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // Switch to default session
                this.switchSession('default', 'Default Session');
                this.loadSessions();
            } else {
                throw new Error('Failed to delete session');
            }
        } catch (error) {
            this.showError('Failed to delete session: ' + error.message);
        }
    }

    showError(message) {
        // Simple error display - you might want to use a more sophisticated notification system
        console.error('Error:', message);
        alert('Error: ' + message);
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new OllamaChatbot();
});