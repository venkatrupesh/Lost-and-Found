document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let messages = [];
    let currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    
    // Function to load messages from localStorage
    function fetchMessages() {
        try {
            // Get user messages
            const storedMessages = localStorage.getItem('messages') || '[]';
            const userMessages = JSON.parse(storedMessages);
            
            // Get admin messages
            const storedAdminMessages = localStorage.getItem('adminMessages') || '[]';
            const adminMessages = JSON.parse(storedAdminMessages);
            
            // Combine both message types
            messages = [...userMessages, ...adminMessages];
            
            // Filter messages based on user and visibility settings
            const filteredMessages = filterMessages(messages);
            
            // Display messages
            displayMessages(filteredMessages);
        } catch (error) {
            console.error('Error loading messages:', error);
            // Show no messages if there's an error
            displayMessages([]);
        }
    }
    
    // Function to filter messages based on user and visibility settings
    function filterMessages(allMessages) {
        // For now, show all messages to all users
        // In a real app, you might want to filter based on recipient groups
        return allMessages;
    }
    
    // Function to display messages in the UI
    function displayMessages(messagesToShow) {
        const messagesContainer = document.getElementById('adminMessagesContainer');
        if (!messagesContainer) return;
        
        if (messagesToShow.length === 0) {
            messagesContainer.innerHTML = `
                <div class="no-messages">
                    <i class="fas fa-envelope-open"></i>
                    <p>No messages from admin at this time.</p>
                </div>
            `;
            return;
        }
        
        // Sort messages by date (newest first)
        messagesToShow.sort((a, b) => {
            // Pin important messages to top if specified
            if (a.pinToTop && !b.pinToTop) return -1;
            if (!a.pinToTop && b.pinToTop) return 1;
            // Then sort by date
            return new Date(b.created_at) - new Date(a.created_at);
        });
        
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
            
            let typeClass = '';
            let typeIcon = '';
            
            switch(message.type) {
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
                    typeIcon = 'check-circle';
                    break;
                default:
                    typeClass = 'info';
                    typeIcon = 'info-circle';
            }
            
            // Get recipient info
            let recipientInfo = '';
            if (message.recipient === 'all') {
                recipientInfo = `Sent to: All Users (${message.targetUsers ? message.targetUsers.length : 0} recipients)`;
            } else if (message.recipient === 'lost-reporters') {
                recipientInfo = `Sent to: Users who reported Lost Items (${message.targetUsers ? message.targetUsers.length : 0} recipients)`;
            } else if (message.recipient === 'found-reporters') {
                recipientInfo = `Sent to: Users who reported Found Items (${message.targetUsers ? message.targetUsers.length : 0} recipients)`;
            } else if (message.email) {
                recipientInfo = `Sent to: ${message.email}`;
            }

            return `
                <div class="message-card ${typeClass} ${message.isImportant ? 'important' : ''}" id="message-${message.id}">
                    <div class="message-header">
                        <div class="message-type">
                            <i class="fas fa-${typeIcon}"></i> ${message.type.charAt(0).toUpperCase() + message.type.slice(1)}
                        </div>
                        <div class="message-date">${formattedDate}</div>
                        ${message.pinToTop ? '<div class="pinned-badge"><i class="fas fa-thumbtack"></i> Pinned</div>' : ''}
                    </div>
                    <div class="message-title">${message.title}</div>
                    <div class="message-content">${message.content.replace(/\n/g, '<br>')}</div>
                    <div class="message-meta" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; font-size: 0.9rem; color: #6c757d;">
                        <div>${recipientInfo}</div>
                        <div>From: ${message.created_by === 'admin' ? 'Administrator' : message.created_by}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        messagesContainer.innerHTML = messagesHTML;
    }
    
    // Add message section to the page if it doesn't exist
    function createMessageSection() {
        // Check if the section already exists
        if (document.getElementById('adminMessagesSection')) return;
        
        // Create the section
        const section = document.createElement('section');
        section.id = 'adminMessagesSection';
        section.className = 'container';
        section.innerHTML = `
            <div class="section-header">
                <h2><i class="fas fa-envelope"></i> Messages & Announcements</h2>
                <p>Important updates from administrators</p>
            </div>
            <div id="adminMessagesContainer" class="messages-container">
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading messages...</p>
                </div>
            </div>
        `;
        
        // Find the appropriate place to insert the section
        const reportsContainer = document.querySelector('.reports-container');
        if (reportsContainer) {
            reportsContainer.parentNode.insertBefore(section, reportsContainer);
        } else {
            // Fallback - add to the main content area
            const mainContent = document.querySelector('main');
            if (mainContent) {
                mainContent.appendChild(section);
            }
        }
    }
    
    // Initialize the page
    function init() {
        createMessageSection();
        fetchMessages();
    }
    
    // Start the initialization
    init();
});