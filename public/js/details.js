document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    if (!currentUser) {
        // Store the current URL to redirect back after login
        localStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = '../auth/login.html';
        return;
    }
    
    // Update the navigation to show user is logged in
    const authLinks = document.querySelector('.auth-links');
    const userMenu = document.querySelector('.user-menu');
    const dashboardLink = document.querySelector('.dashboard-link');
    
    if (authLinks) authLinks.style.display = 'none';
    if (userMenu) userMenu.style.display = 'flex';
    if (dashboardLink) dashboardLink.style.display = 'inline-flex';
    
    // Set up logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('currentUser');
            localStorage.removeItem('isLoggedIn');
            sessionStorage.removeItem('currentUser');
            window.location.href = '../auth/login.html';
        });
    }
    
    // Get the item ID and type from sessionStorage
    const viewingItem = JSON.parse(sessionStorage.getItem('viewingItem') || '{}');
    if (!viewingItem.id || !viewingItem.type) {
        showError('No item selected for viewing');
        return;
    }
    
    // Load item details
    loadItemDetails(viewingItem.id, viewingItem.type);
    
    // Load notifications related to this item
    loadItemNotifications(viewingItem.id, currentUser.id);
    
    // Update notifications count
    updateNotificationsCount();
});

function loadItemDetails(itemId, itemType) {
    const storageKey = itemType === 'lost' ? 'lostItems' : 'foundItems';
    const items = JSON.parse(localStorage.getItem(storageKey) || '[]');
    const item = items.find(item => item.id === itemId);
    
    if (!item) {
        showError('Item not found');
        return;
    }
    
    const container = document.getElementById('itemDetailsContainer');
    if (!container) return;
    
    // Determine status display
    let statusText, statusClass, statusIcon;
    if (itemType === 'lost') {
        statusText = item.status === 'found' ? 'Found' : 'Searching';
        statusClass = item.status === 'found' ? 'status-found' : 'status-searching';
        statusIcon = item.status === 'found' ? 'check-circle' : 'search';
    } else {
        statusText = item.status === 'claimed' ? 'Claimed' : 'Unclaimed';
        statusClass = item.status === 'claimed' ? 'status-claimed' : 'status-unclaimed';
        statusIcon = item.status === 'claimed' ? 'check-double' : 'box-open';
    }
    
    // Format dates
    const reportedDate = new Date(item.dateReported || item.createdAt);
    const formattedReportedDate = reportedDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
    
    const itemDate = new Date(itemType === 'lost' ? (item.dateLost || item.createdAt) : (item.dateFound || item.createdAt));
    const formattedItemDate = itemDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Get category icon
    const categoryIcon = getCategoryIcon(item.category);
    
    // Create HTML for item details
    container.innerHTML = `
        <div class="card">
            <div class="item-header">
                <div class="item-title">
                    <h1>${item.itemName || 'Unnamed Item'}</h1>
                    <span class="status-badge ${statusClass}">
                        <i class="fas fa-${statusIcon}"></i>
                        ${statusText}
                    </span>
                </div>
                <a href="../dashboard/index.html" class="btn btn-outline">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
            
            ${item.images && item.images.length > 0 ? `
                <div class="item-images">
                    ${item.images.map(img => `<img src="${img}" alt="${item.itemName}" class="item-image">`).join('')}
                </div>
            ` : ''}
            
            <div class="item-details">
                <div class="detail-section">
                    <div class="detail-group">
                        <span class="detail-label">Category</span>
                        <div class="detail-value">
                            <i class="fas fa-${categoryIcon}"></i> ${item.category || 'Uncategorized'}
                        </div>
                    </div>
                    
                    <div class="detail-group">
                        <span class="detail-label">Description</span>
                        <div class="detail-value">${item.description || 'No description provided.'}</div>
                    </div>
                    
                    <div class="detail-group">
                        <span class="detail-label">Location</span>
                        <div class="detail-value">
                            <i class="fas fa-map-marker-alt"></i> ${item.location || 'Location not specified'}
                        </div>
                    </div>
                    
                    <div class="detail-group">
                        <span class="detail-label">Date ${itemType === 'lost' ? 'Lost' : 'Found'}</span>
                        <div class="detail-value">
                            <i class="far fa-calendar"></i> ${formattedItemDate}
                        </div>
                    </div>
                    
                    <div class="detail-group">
                        <span class="detail-label">Date Reported</span>
                        <div class="detail-value">
                            <i class="far fa-calendar-check"></i> ${formattedReportedDate}
                        </div>
                    </div>
                </div>
                
                ${item.contactInfo ? `
                    <div class="detail-section">
                        <h3>Contact Information</h3>
                        <div class="detail-group">
                            <span class="detail-label">Name</span>
                            <div class="detail-value">${item.contactInfo.name || 'Not provided'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <span class="detail-label">Email</span>
                            <div class="detail-value">${item.contactInfo.email || 'Not provided'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <span class="detail-label">Phone</span>
                            <div class="detail-value">${item.contactInfo.phone || 'Not provided'}</div>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function loadItemNotifications(itemId, userId) {
    const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    
    // Filter notifications for this item and user
    const itemNotifications = notifications.filter(notif => 
        notif.itemId === itemId && notif.userId === userId
    );
    
    const container = document.getElementById('notificationsContainer');
    if (!container) return;
    
    if (itemNotifications.length === 0) {
        container.innerHTML = `
            <div class="no-notifications">
                <i class="fas fa-bell-slash"></i>
                <p>No notifications for this item yet.</p>
            </div>
        `;
        return;
    }
    
    // Sort notifications by date (newest first)
    itemNotifications.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    // Mark all as read
    itemNotifications.forEach(notif => {
        if (!notif.read) {
            notif.read = true;
            // Find and update in the original array
            const index = notifications.findIndex(n => n.id === notif.id);
            if (index !== -1) {
                notifications[index].read = true;
            }
        }
    });
    
    // Save updated notifications back to localStorage
    localStorage.setItem('notifications', JSON.stringify(notifications));
    
    // Display notifications
    container.innerHTML = itemNotifications.map(notif => {
        const date = new Date(notif.date);
        const formattedDate = date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="notification-card" id="notification-${notif.id}">
                <div class="notification-header">
                    <div class="notification-title">${notif.title}</div>
                    <div class="notification-date">${formattedDate}</div>
                </div>
                <div class="notification-message">${notif.message}</div>
                ${notif.collectionLocation ? `
                    <div class="notification-location">
                        <strong>Collection Location:</strong> ${notif.collectionLocation}
                    </div>
                ` : ''}
                <div class="notification-actions">
                    <button class="btn btn-sm btn-outline" onclick="dismissNotification('${notif.id}')">
                        <i class="fas fa-check"></i> Acknowledge
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function dismissNotification(notificationId) {
    const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    const index = notifications.findIndex(notif => notif.id === notificationId);
    
    if (index !== -1) {
        // Remove the notification from the array
        notifications.splice(index, 1);
        localStorage.setItem('notifications', JSON.stringify(notifications));
        
        // Remove the notification card from the DOM
        const card = document.getElementById(`notification-${notificationId}`);
        if (card) {
            card.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => {
                card.remove();
                
                // Check if there are no more notifications
                const container = document.getElementById('notificationsContainer');
                if (container && container.children.length === 0) {
                    container.innerHTML = `
                        <div class="no-notifications">
                            <i class="fas fa-bell-slash"></i>
                            <p>No notifications for this item yet.</p>
                        </div>
                    `;
                }
            }, 300);
        }
        
        // Show success message
        showToast('Notification dismissed', 'success');
        
        // Update notifications count
        updateNotificationsCount();
    }
}

function updateNotificationsCount() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    if (!currentUser) return;
    
    const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    
    // Count unread notifications for the current user
    const unreadCount = notifications.filter(notif => 
        notif.userId === currentUser.id && !notif.read
    ).length;
    
    // Update the notifications badge
    const notificationsBadge = document.getElementById('notificationsCount');
    if (notificationsBadge) {
        notificationsBadge.textContent = unreadCount;
        notificationsBadge.style.display = unreadCount > 0 ? 'flex' : 'none';
    }
}

function getCategoryIcon(category) {
    const categoryIcons = {
        'Electronics': 'laptop',
        'Clothing': 'tshirt',
        'Accessories': 'glasses',
        'Books': 'book',
        'Documents': 'file-alt',
        'Keys': 'key',
        'Wallet': 'wallet',
        'Bag': 'briefcase',
        'Other': 'box'
    };
    
    return categoryIcons[category] || 'box';
}

function showError(message) {
    const container = document.getElementById('itemDetailsContainer');
    if (container) {
        container.innerHTML = `
            <div class="card error-card">
                <i class="fas fa-exclamation-circle"></i>
                <h2>Error</h2>
                <p>${message}</p>
                <a href="../dashboard/index.html" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
        `;
    }
    
    // Hide notifications section
    const notificationSection = document.getElementById('notificationSection');
    if (notificationSection) {
        notificationSection.style.display = 'none';
    }
    
    // Show error toast
    displayToast(message, 'error');
}

// Display toast notification using the existing showToast function
function displayToast(message, type = 'info', duration = 3000) {
    // Check if showToast function exists globally
    if (typeof window.showToast === 'function') {
        window.showToast(message, type, duration);
    } else {
        // Fallback if showToast is not available
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Create a simple alert for critical messages
        if (type === 'error') {
            alert(message);
        }
    }
}

// Make functions available globally
window.dismissNotification = dismissNotification;