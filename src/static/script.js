// Global variables
let uploadedFiles = [];
let conversationHistory = [];

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const ragToggle = document.getElementById('ragToggle');
const clearChat = document.getElementById('clearChat');
const refreshStats = document.getElementById('refreshStats');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const charCount = document.getElementById('charCount');
const toastContainer = document.getElementById('toastContainer');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadSystemStats();
    
    // Remove welcome message when first document is uploaded
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'block';
    }
});

// Event Listeners
function initializeEventListeners() {
    // File upload events
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Chat events
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    messageInput.addEventListener('input', updateCharCount);
    
    // Control events
    clearChat.addEventListener('click', clearChatHistory);
    refreshStats.addEventListener('click', loadSystemStats);
}

// File Upload Functions
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    processFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    processFiles(files);
}

function processFiles(files) {
    const allowedTypes = ['pdf', 'docx', 'pptx', 'csv', 'txt', 'md'];
    
    files.forEach(file => {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            showToast(`File type .${fileExtension} is not supported`, 'error');
            return;
        }
        
        if (file.size > 16 * 1024 * 1024) { // 16MB limit
            showToast(`File ${file.name} is too large (max 16MB)`, 'error');
            return;
        }
        
        uploadFile(file);
    });
}

async function uploadFile(file) {
    const fileId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Add file to UI immediately
    addFileToList(file, fileId, 'processing');
    
    // Hide welcome message
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading('Uploading and processing document...');
        
        const response = await fetch('/api/chatbot/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            updateFileStatus(fileId, 'success');
            uploadedFiles.push({
                id: fileId,
                name: file.name,
                metadata: result.metadata,
                trace_id: result.trace_id
            });
            showToast(`Successfully processed ${file.name}`, 'success');
            loadSystemStats();
        } else {
            updateFileStatus(fileId, 'error');
            showToast(`Error processing ${file.name}: ${result.error}`, 'error');
        }
    } catch (error) {
        updateFileStatus(fileId, 'error');
        showToast(`Network error uploading ${file.name}`, 'error');
        console.error('Upload error:', error);
    } finally {
        hideLoading();
    }
}

function addFileToList(file, fileId, status) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = `file-${fileId}`;
    
    const fileIcon = getFileIcon(file.name);
    
    fileItem.innerHTML = `
        <div class="file-info">
            <i class="fas ${fileIcon} file-icon"></i>
            <span class="file-name">${file.name}</span>
        </div>
        <span class="file-status ${status}" id="status-${fileId}">
            ${status === 'processing' ? 'Processing...' : status}
        </span>
    `;
    
    fileList.appendChild(fileItem);
}

function updateFileStatus(fileId, status) {
    const statusElement = document.getElementById(`status-${fileId}`);
    if (statusElement) {
        statusElement.className = `file-status ${status}`;
        statusElement.textContent = status === 'success' ? 'Ready' : 'Error';
    }
}

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'pdf': 'fa-file-pdf',
        'docx': 'fa-file-word',
        'pptx': 'fa-file-powerpoint',
        'csv': 'fa-file-csv',
        'txt': 'fa-file-alt',
        'md': 'fa-file-alt'
    };
    return iconMap[extension] || 'fa-file';
}

// Chat Functions
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    messageInput.value = '';
    updateCharCount();
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const response = await fetch('/api/chatbot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                use_rag: ragToggle.checked
            })
        });
        
        const result = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (response.ok) {
            addMessageToChat(result.response, 'bot', result.sources);
            conversationHistory.push({
                query: message,
                response: result.response,
                sources: result.sources,
                trace_id: result.trace_id
            });
            loadSystemStats();
        } else {
            addMessageToChat(`Error: ${result.error}`, 'bot');
            showToast('Error processing message', 'error');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessageToChat('Network error. Please try again.', 'bot');
        showToast('Network error', 'error');
        console.error('Chat error:', error);
    }
}

function addMessageToChat(content, sender, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    let messageHTML = `<div class="message-content">${content}</div>`;
    
    if (sources && sources.length > 0) {
        messageHTML += `
            <div class="message-sources">
                <h4><i class="fas fa-link"></i> Sources:</h4>
                ${sources.map(source => `
                    <div class="source-item">
                        <span class="source-name">
                            <i class="fas ${getFileIcon(source.file_name)}"></i>
                            ${source.file_name}
                        </span>
                        <span class="source-score">Score: ${source.relevance_score || 'N/A'}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    messageDiv.innerHTML = messageHTML;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = typingId;
    typingDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-circle-notch fa-spin"></i> Thinking...
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typingElement = document.getElementById(typingId);
    if (typingElement) {
        typingElement.remove();
    }
}

function updateCharCount() {
    const count = messageInput.value.length;
    charCount.textContent = `${count}/500`;
    
    if (count > 450) {
        charCount.style.color = '#f56565';
    } else if (count > 400) {
        charCount.style.color = '#ed8936';
    } else {
        charCount.style.color = '#718096';
    }
}

async function clearChatHistory() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/chatbot/clear', {
            method: 'POST'
        });
        
        if (response.ok) {
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <i class="fas fa-robot"></i>
                    <p>Chat history cleared. Ask me anything about your documents!</p>
                </div>
            `;
            conversationHistory = [];
            showToast('Chat history cleared', 'success');
            loadSystemStats();
        } else {
            showToast('Error clearing chat history', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
        console.error('Clear chat error:', error);
    }
}

// System Stats Functions
async function loadSystemStats() {
    try {
        const response = await fetch('/api/chatbot/stats');
        const stats = await response.json();
        
        if (response.ok) {
            document.getElementById('docCount').textContent = uploadedFiles.length;
            document.getElementById('convCount').textContent = conversationHistory.length;
            document.getElementById('vectorCount').textContent = 
                `${stats.vector_store?.total_documents || 0} chunks`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Utility Functions
function showLoading(text = 'Processing...') {
    loadingText.textContent = text;
    loadingOverlay.classList.add('show');
}

function hideLoading() {
    loadingOverlay.classList.remove('show');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas ${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);
}

function getToastIcon(type) {
    const iconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return iconMap[type] || 'fa-info-circle';
}

