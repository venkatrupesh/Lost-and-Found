document.addEventListener('DOMContentLoaded', function() {
    // Check if user is admin, redirect if not
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    if (!currentUser || !currentUser.isAdmin) {
        window.location.href = '../index.html';
        return;
    }
    
    // Initialize variables
    const messagesList = document.getElementById('messagesList');
    const messagesFilter = document.getElementById('messagesFilter');
    const searchInput = document.getElementById('searchMessages');
    const userDropdown = document.getElementById('specificUser');
    const isSendMessagePage = window.location.pathname.includes('send-message.html');
    
    // Check if we're on the send-message page
    if (isSendMessagePage) {
        setupMessageForm();
    }
    
    // Initialize variables
    let messages = [];
    let users = [];
    
    // Get DOM elements
    const messageForm = document.getElementById('messageForm');
    // messagesList is already defined above, removing duplicate declaration
    const targetUsersSelect = document.getElementById('targetUsers');
    
    // Function to fetch messages from the server
    async function fetchMessages() {
        try {
            const response = await fetch('/api/admin/messages');
            if (!response.ok) {
                throw new Error('Failed to fetch messages');
            }
            
            messages = await response.json();
            displayMessages(messages);
        } catch (error) {
            console.error('Error fetching messages:', error);
            // If API is not available, try to get messages from localStorage
            messages = JSON.parse(localStorage.getItem('adminMessages') || '[]');
            displayMessages(messages);
        }
    }
    
    // Function to fetch users
    function fetchUsers() {
        // In a real app, this would be an API call
        // For now, we'll get users from localStorage
        const storedUsers = JSON.parse(localStorage.getItem('users') || '[]');
        users = storedUsers;
        
        // Populate target users dropdown
        populateUserDropdown();
    }
    
    // Function to populate user dropdown
    function populateUserDropdown() {
        if (!targetUsersSelect) return;
        
        // Clear existing options except 'All Users'
        while (targetUsersSelect.options.length > 1) {
            targetUsersSelect.remove(1);
        }
        
        // Add user options
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.name} (${user.email})`;
            targetUsersSelect.appendChild(option);
        });
    }
    
    // Function to set up message form handling
    function setupMessageForm() {
        const messageForm = document.getElementById('messageForm');
        const titleInput = document.getElementById('messageTitle');
        const contentInput = document.getElementById('messageContent');
        const titleCount = document.getElementById('titleCount');
        const contentCount = document.getElementById('contentCount');
        const previewBtn = document.getElementById('previewBtn');
        const previewSection = document.getElementById('previewSection');
        const messagePreview = document.getElementById('messagePreview');
        
        // Character counters
        if (titleInput && titleCount) {
            titleInput.addEventListener('input', () => {
                titleCount.textContent = titleInput.value.length;
            });
        }
        
        if (contentInput && contentCount) {
            contentInput.addEventListener('input', () => {
                contentCount.textContent = contentInput.value.length;
            });
        }
        
        // Preview button
        if (previewBtn && previewSection && messagePreview) {
            previewBtn.addEventListener('click', function() {
                const messageType = document.querySelector('input[name="messageType"]:checked').value;
                const title = titleInput.value.trim();
                const content = contentInput.value.trim();
                const isImportant = document.getElementById('isImportant').checked;
                
                if (!title || !content) {
                    alert('Please fill in both title and content to preview the message.');
                    return;
                }
                
                // Format the preview
                let typeClass = '';
                let typeIcon = '';
                
                switch(messageType) {
                    case 'announcement':
                        typeClass = 'announcement';
                        typeIcon = 'bullhorn';
                        break;
                    case 'lost':
                        typeClass = 'lost';
                        typeIcon = 'search';
                        break;
                    case 'found':
                        typeClass = 'found';
                        typeIcon = 'box';
                        break;
                    default:
                        typeClass = 'info';
                        typeIcon = 'info-circle';
                }
                
                const now = new Date();
                const formattedDate = now.toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                messagePreview.className = `message-card ${typeClass}`;
                messagePreview.innerHTML = `
                    <div class="message-header">
                        <div class="message-type">
                            <i class="fas fa-${typeIcon}"></i>
                            <span>${messageType.charAt(0).toUpperCase() + messageType.slice(1)}</span>
                        </div>
                        ${isImportant ? '<span class="important-badge"><i class="fas fa-exclamation-circle"></i> Important</span>' : ''}
                    </div>
                    <h3>${title}</h3>
                    <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
                    <div class="message-meta">
                        <span>Created: ${formattedDate}</span>
                        <span>By: Admin</span>
                    </div>
                `;
                
                previewSection.style.display = 'block';
                previewSection.scrollIntoView({ behavior: 'smooth' });
            });
        }
        
        // Form submission
        if (messageForm) {
            messageForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const title = titleInput.value.trim();
                const content = contentInput.value.trim();
                const messageType = document.querySelector('input[name="messageType"]:checked').value;
                const recipientType = document.querySelector('input[name="recipientType"]:checked').value;
                const isImportant = document.getElementById('isImportant').checked;
                const pinToTop = document.getElementById('pinToTop').checked;
                
                // Validate form
                if (!title || !content) {
                    alert('Please fill in all required fields.');
                    return;
                }
                
                // Create message object
                const messageData = {
                    id: 'msg-' + Date.now(),
                    title: title,
                    content: content,
                    type: messageType,
                    recipientType: recipientType,
                    isImportant: isImportant,
                    pinToTop: pinToTop,
                    created_at: new Date().toISOString(),
                    created_by: currentUser.id || 'admin'
                };
                
                // Save to localStorage
                const adminMessages = JSON.parse(localStorage.getItem('adminMessages') || '[]');
                adminMessages.unshift(messageData);
                localStorage.setItem('adminMessages', JSON.stringify(adminMessages));
                
                // Show success message
                alert('Message sent successfully!');
                
                // Reset form
                messageForm.reset();
                if (titleCount) titleCount.textContent = '0';
                if (contentCount) contentCount.textContent = '0';
                if (previewSection) previewSection.style.display = 'none';
            });
        }
    }
    
    // Function to display messages
    function displayMessages(messagesToShow) {
        if (!messagesList) return;
        
        if (messagesToShow.length === 0) {
            messagesList.innerHTML = `
                <div class="no-messages">
                    <i class="fas fa-envelope-open"></i>
                    <p>No messages created yet.</p>
                </div>
            `;
            return;
        }
        
        // Sort messages by date (newest first)
        messagesToShow.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        // Generate HTML for messages
        const messagesHTML = messagesToShow.map(message => {
            const date = new Date(message.created_at);
            const formattedDate = date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            return `
                <div class="message-card" id="message-${message.id}">
                    <span class="message-type ${message.type}">${message.type.charAt(0).toUpperCase() + message.type.slice(1)}</span>
                    <h3>${message.title}</h3>
                    <p>${message.content}</p>
                    <div class="message-meta">
                        <span>Created: ${formattedDate}</span>
                        <div class="message-actions">
                            <button onclick="editMessage('${message.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button onclick="deleteMessage('${message.id}')" class="delete" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        messagesList.innerHTML = messagesHTML;
    }
    
    // Function to create a new message
    async function createMessage(messageData) {
        try {
            const response = await fetch('/api/admin/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(messageData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to create message');
            }
            
            const newMessage = await response.json();
            
            // Update local messages array and display
            messages.unshift(newMessage);
            displayMessages(messages);
            
            // Also update localStorage for offline functionality
            const storedMessages = JSON.parse(localStorage.getItem('adminMessages') || '[]');
            storedMessages.unshift(newMessage);
            localStorage.setItem('adminMessages', JSON.stringify(storedMessages));
            
            // Show success message
            showToast('Message created successfully', 'success');
            
            return newMessage;
        } catch (error) {
            console.error('Error creating message:', error);
            
            // Fallback for offline mode
            const newMessage = {
                ...messageData,
                id: generateId(),
                created_at: new Date().toISOString()
            };
            
            // Update local messages array and display
            messages.unshift(newMessage);
            displayMessages(messages);
            
            // Also update localStorage
            const storedMessages = JSON.parse(localStorage.getItem('adminMessages') || '[]');
            storedMessages.unshift(newMessage);
            localStorage.setItem('adminMessages', JSON.stringify(storedMessages));
            
            showToast('Message saved locally (offline mode)', 'warning');
            
            return newMessage;
        }
    }
    
    // Function to delete a message
    window.deleteMessage = async function(messageId) {
        if (!confirm('Are you sure you want to delete this message?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/messages/${messageId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete message');
            }
            
            // Remove from local array
            messages = messages.filter(msg => msg.id !== messageId);
            displayMessages(messages);
            
            // Also update localStorage
            const storedMessages = JSON.parse(localStorage.getItem('adminMessages') || '[]');
            const updatedMessages = storedMessages.filter(msg => msg.id !== messageId);
            localStorage.setItem('adminMessages', JSON.stringify(updatedMessages));
            
            showToast('Message deleted successfully', 'success');
        } catch (error) {
            console.error('Error deleting message:', error);
            
            // Fallback for offline mode
            messages = messages.filter(msg => msg.id !== messageId);
            displayMessages(messages);
            
            // Also update localStorage
            const storedMessages = JSON.parse(localStorage.getItem('adminMessages') || '[]');
            const updatedMessages = storedMessages.filter(msg => msg.id !== messageId);
            localStorage.setItem('adminMessages', JSON.stringify(updatedMessages));
            
            showToast('Message deleted locally (offline mode)', 'warning');
        }
    };
    
    // Function to edit a message (placeholder for now)
    window.editMessage = function(messageId) {
        alert('Edit functionality will be implemented in a future update.');
    };
    
    // Helper function to generate a unique ID
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }
    
    // Show toast notification
    function showToast(message, type = 'info', duration = 3000) {
        // Add toast styles if they don't exist
        if (!document.querySelector('style[data-id="toast-styles"]')) {
            const style = document.createElement('style');
            style.setAttribute('data-id', 'toast-styles');
            style.textContent = `
                .toast {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    padding: 10px 15px;
                    border-radius: 4px;
                    color: white;
                    font-size: 14px;
                    z-index: 1000;
                    opacity: 0;
                    transform: translateY(20px);
                    transition: opacity 0.3s, transform 0.3s;
                    display: flex;
                    align-items: center;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                }
                .toast.show {
                    opacity: 1;
                    transform: translateY(0);
                }
                .toast-info {
                    background-color: #2196F3;
                }
                .toast-success {
                    background-color: #4CAF50;
                }
                .toast-warning {
                    background-color: #FF9800;
                }
                .toast-error {
                    background-color: #F44336;
                }
            `;
            document.head.appendChild(style);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Hide and remove toast after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, duration);
    }
    
    // Handle form submission
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const title = document.getElementById('messageTitle').value;
            const content = document.getElementById('messageContent').value;
            const type = document.getElementById('messageType').value;
            const isPublic = document.getElementById('isPublic').checked;
            const createNotifications = document.getElementById('createNotifications').checked;
            
            // Get target users
            const targetUsers = [];
            if (targetUsersSelect) {
                const selectedOptions = Array.from(targetUsersSelect.selectedOptions);
                if (!selectedOptions.some(option => option.value === 'all')) {
                    selectedOptions.forEach(option => {
                        if (option.value !== 'all') {
                            targetUsers.push(option.value);
                        }
                    });
                }
            }
            
            // Create message data
            const messageData = {
                title,
                content,
                type,
                is_public: isPublic,
                target_users: targetUsers,
                create_notifications: createNotifications
            };
            
            // Send message
            createMessage(messageData).then(() => {
                // Reset form
                messageForm.reset();
                document.getElementById('isPublic').checked = true;
                document.getElementById('createNotifications').checked = true;
            });
        });
    }
    
    // Initialize the page
    fetchMessages();
    fetchUsers();
});