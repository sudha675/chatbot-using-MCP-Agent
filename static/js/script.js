// Global variables
let currentConversationId = null;
let currentFile = null;

// Initialize when document is ready
$(document).ready(function() {
    initializeChat();
    setupEventListeners();
    checkSystemStatus();
});

function initializeChat() {
    // Start a new conversation
    startNewConversation();
    
    // Show welcome screen
    $('#welcome-screen').show();
    $('#chat-container').hide();
}

function setupEventListeners() {
    // Send message on button click
    $('#send-btn').on('click', sendMessage);
    
    // Send message on Enter key (but allow Shift+Enter for new line)
    $('#message-input').on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Enable/disable send button based on input
    $('#message-input').on('input', function() {
        const hasText = $(this).val().trim().length > 0;
        const hasFile = currentFile !== null;
        $('#send-btn').prop('disabled', !(hasText || hasFile));
    });
    
    // File upload handling
    $('#file-upload-btn').on('click', function() {
        $('#file-input').click();
    });
    
    $('#file-input').on('change', function(e) {
        handleFileSelect(e.target.files[0]);
    });
    
    // Remove file
    $('#remove-file-btn').on('click', function() {
        clearFileSelection();
    });
    
    // New chat button
    $('#new-chat-btn').on('click', startNewConversation);
    
    // System status button
    $('#system-status-btn').on('click', showSystemStatus);
    
    // Quick action cards
    $('.quick-action-card').on('click', function() {
        const action = $(this).data('action');
        handleQuickAction(action);
    });
    
    // Modal close buttons
    $('.modal-close').on('click', function() {
        $(this).closest('.modal').hide();
    });
    
    // Close modal when clicking outside
    $(window).on('click', function(e) {
        $('.modal').each(function() {
            if (e.target === this) {
                $(this).hide();
            }
        });
    });
    
    // Auto-resize textarea
    $('#message-input').on('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

function startNewConversation() {
    $.post('/new_chat')
        .done(function(data) {
            currentConversationId = data.conversation_id;
            $('#chat-messages').empty();
            $('#welcome-screen').show();
            $('#chat-container').hide();
            clearFileSelection();
            $('#message-input').val('');
            $('#send-btn').prop('disabled', true);
        })
        .fail(function() {
            showError('Failed to start new conversation');
        });
}

function sendMessage() {
    const message = $('#message-input').val().trim();
    
    if (!message && !currentFile) {
        return;
    }
    
    // Hide welcome screen on first message
    if ($('#welcome-screen').is(':visible')) {
        $('#welcome-screen').hide();
        $('#chat-container').show();
    }
    
    // Add user message to chat
    addMessage('user', message);
    
    // Clear input and reset height
    $('#message-input').val('');
    $('#message-input').height('auto');
    $('#send-btn').prop('disabled', true);
    
    // Show loading
    showLoading();
    
    // Prepare request data
    const requestData = {
        message: message,
        conversation_id: currentConversationId
    };
    
    // Add file data if present
    if (currentFile) {
        requestData.file_path = currentFile.path;
        requestData.file_type = currentFile.type;
    }
    
    // Send request
    $.ajax({
        url: '/chat',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(requestData),
        success: function(data) {
            hideLoading();
            if (data.response) {
                addMessage('assistant', data.response);
                currentConversationId = data.conversation_id;
            } else {
                showError('No response received');
            }
            clearFileSelection();
        },
        error: function(xhr, status, error) {
            hideLoading();
            showError('Failed to send message: ' + (xhr.responseJSON?.error || error));
        }
    });
}

function handleFileSelect(file) {
    if (!file) return;
    
    // Check file type
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'ppt', 'pptx'];
    
    if (!allowedExtensions.includes(fileExtension)) {
        showError('File type not allowed. Please select a PDF, image, or PowerPoint file.');
        return;
    }
    
    // Check file size (16MB limit)
    if (file.size > 16 * 1024 * 1024) {
        showError('File too large. Please select a file smaller than 16MB.');
        return;
    }
    
    // Upload file
    const formData = new FormData();
    formData.append('file', file);
    
    showLoading('Uploading file...');
    
    $.ajax({
        url: '/upload_file',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(data) {
            hideLoading();
            if (data.status === 'success') {
                currentFile = {
                    name: data.filename,
                    path: data.file_path,
                    type: data.file_type,
                    size: data.file_size
                };
                showFilePreview();
                $('#send-btn').prop('disabled', false);
            } else {
                showError(data.error || 'File upload failed');
            }
        },
        error: function(xhr, status, error) {
            hideLoading();
            showError('File upload failed: ' + (xhr.responseJSON?.error || error));
        }
    });
}

function handleQuickAction(action) {
    let message = '';
    
    switch(action) {
        case 'weather':
            message = 'What is the current weather in London?';
            break;
        case 'news':
            message = 'What are the latest news headlines?';
            break;
        case 'email':
            message = 'Send a test email to test@example.com with subject "Test" and content "This is a test email from the chatbot"';
            break;
        case 'pdf':
            message = 'Can you read and summarize a PDF document for me?';
            break;
        case 'image':
            message = 'What can you see in this image?';
            break;
        case 'calculator':
            message = 'Calculate 25 * 40 + 15';
            break;
    }
    
    if (message) {
        $('#message-input').val(message);
        $('#send-btn').prop('disabled', false);
        // Optionally auto-send for quick actions
        // sendMessage();
    }
}

function showFilePreview() {
    if (currentFile) {
        $('#file-preview-name').text(currentFile.name);
        $('#file-preview').show();
    }
}

function clearFileSelection() {
    currentFile = null;
    $('#file-input').val('');
    $('#file-preview').hide();
    $('#send-btn').prop('disabled', $('#message-input').val().trim().length === 0);
}

function addMessage(role, content) {
    const avatar = role === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';
    
    const messageClass = role === 'user' ? 'message-user' : 'message-assistant';
    
    // Format content with line breaks
    const formattedContent = content.replace(/\n/g, '<br>');
    
    const messageHtml = `
        <div class="message ${messageClass}">
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content">
                ${formattedContent}
            </div>
        </div>
    `;
    
    $('#chat-messages').append(messageHtml);
    
    // Scroll to bottom
    $('#chat-container').scrollTop($('#chat-container')[0].scrollHeight);
}

function showLoading(text = 'AI is thinking...') {
    $('.loading-text').text(text);
    $('#loading').show();
}

function hideLoading() {
    $('#loading').hide();
}

function showError(message) {
    const errorHtml = `
        <div class="message message-assistant">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content" style="color: #ef4444;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        </div>
    `;
    
    $('#chat-messages').append(errorHtml);
    $('#chat-container').scrollTop($('#chat-container')[0].scrollHeight);
}

function checkSystemStatus() {
    $.get('/system_status')
        .done(function(data) {
            updateSystemStatus(data.components);
        })
        .fail(function() {
            // Silently fail for status check
        });
}

function updateSystemStatus(components) {
    // You can use this to update any status indicators if needed
    console.log('System status:', components);
}

function showSystemStatus() {
    $.get('/system_status')
        .done(function(data) {
            let statusHtml = '';
            
            for (const [component, status] of Object.entries(data.components)) {
                let statusClass = 'status-success';
                if (status.includes('❌')) statusClass = 'status-error';
                else if (status.includes('⚠️')) statusClass = 'status-warning';
                
                statusHtml += `
                    <div class="status-item">
                        <span class="status-name">${component.replace('_', ' ').toUpperCase()}</span>
                        <span class="status-value ${statusClass}">${status}</span>
                    </div>
                `;
            }
            
            $('#status-content').html(statusHtml);
            $('#system-status-modal').show();
        })
        .fail(function() {
            $('#status-content').html('<p style="color: #ef4444; text-align: center;">Failed to load system status</p>');
            $('#system-status-modal').show();
        });
}

// Drag and drop support
$(document).on('dragenter', function(e) {
    e.preventDefault();
    e.stopPropagation();
});

$(document).on('dragover', function(e) {
    e.preventDefault();
    e.stopPropagation();
});

$(document).on('drop', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.originalEvent.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});