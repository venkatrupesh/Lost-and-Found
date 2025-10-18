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
    
    // Set up logout functionality (use global logout to always go to login)
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof logout === 'function') {
                logout();
            } else {
                localStorage.removeItem('currentUser');
                localStorage.removeItem('isLoggedIn');
                sessionStorage.removeItem('currentUser');
                window.location.href = '../auth/login.html';
            }
        });
    }
    
    // Add styles for notification indicator
    const style = document.createElement('style');
    style.textContent = `
        .notification-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: #ff4757;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        .item-image {
            position: relative;
        }
    `;
    document.head.appendChild(style);
    
    // Display user's name in the welcome message
    const welcomeUserName = document.getElementById('welcomeUserName');
    if (welcomeUserName) {
        // Get user data from various sources with fallbacks
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        // Use the user's full name from registration, or name from currentUser, or userName from localStorage, or default to 'User'
        welcomeUserName.textContent = userData.fullName || currentUser.name || localStorage.getItem('userName') || 'User';
    }
    
    // Load user's items
    loadUserItems(currentUser.id);
    
    // Set up tab switching
    setupTabs();
});

function loadUserItems(userId) {
    if (!userId) {
        console.error('No user ID provided');
        return;
    }
    
    // Get items from localStorage and filter by current user
    const lostItems = JSON.parse(localStorage.getItem('lostItems') || '[]')
        .filter(item => item.userId === userId)
        .sort((a, b) => new Date(b.dateReported || b.createdAt) - new Date(a.dateReported || a.createdAt));
        
    const foundItems = JSON.parse(localStorage.getItem('foundItems') || '[]')
        .filter(item => item.userId === userId)
        .sort((a, b) => new Date(b.dateReported || b.createdAt) - new Date(a.dateReported || a.createdAt));
    
    console.log('Loading items for user:', userId);
    console.log('Lost items:', lostItems);
    console.log('Found items:', foundItems);
    
    // Update stats
    document.getElementById('totalLost').textContent = lostItems.length;
    document.getElementById('totalFound').textContent = foundItems.length;
    document.getElementById('totalResolved').textContent = 
        lostItems.filter(item => item.status === 'found').length + 
        foundItems.filter(item => item.status === 'claimed').length;
    
    // Display items
    displayItems('lost-items-container', lostItems, 'lost');
    displayItems('found-items-container', foundItems, 'found');
    
    // Update notifications count
    updateNotificationsCount(lostItems, foundItems);
}

function displayItems(containerId, items, type) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-${type === 'lost' ? 'search' : 'box-open'}"></i>
                <h3>No ${type} items found</h3>
                <p>You haven't reported any ${type} items yet.</p>
                <a href="../items/report-${type}.html" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Report a ${type === 'lost' ? 'Lost' : 'Found'} Item
                </a>
            </div>
        `;
        return;
    }
    
    // Create a grid container for the items
    container.innerHTML = `
        <div class="items-grid">
            ${items.map(item => createItemCard(item, type)).join('')}
        </div>
    `;
    
    // Add event listeners for status updates and view details
    items.forEach(item => {
        const statusBtn = document.getElementById(`status-btn-${item.id}`);
        if (statusBtn) {
            statusBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                updateItemStatus(item.id, type);
            });
        }
        
        // Make entire item clickable
        const itemElement = document.getElementById(`item-${item.id}`);
        if (itemElement) {
            itemElement.addEventListener('click', () => viewItemDetails(item.id, type));
            itemElement.style.cursor = 'pointer';
            
            // Add hover effect
            itemElement.addEventListener('mouseenter', () => {
                itemElement.style.transform = 'translateY(-5px)';
                itemElement.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.15)';
            });
            
            itemElement.addEventListener('mouseleave', () => {
                itemElement.style.transform = '';
                itemElement.style.boxShadow = '';
            });
        }
    });
}

function createItemCard(item, type) {
    const isResolved = type === 'lost' ? item.status === 'found' : item.status === 'claimed';
    const statusText = type === 'lost' ? 
        (isResolved ? 'Found' : 'Still Looking') : 
        (isResolved ? 'Claimed' : 'Not Claimed');
    
    // Format the date
    const date = new Date(item.dateLost || item.dateFound || item.createdAt);
    const formattedDate = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Get the first image or use a placeholder
    const itemImage = item.images && item.images.length > 0 ? 
        `<img src="${item.images[0]}" alt="${item.itemName || 'Item image'}" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\'no-image\'><i class=\'fas fa-image\'></i></div>'">` : 
        `<div class="no-image"><i class="fas fa-image"></i></div>`;
    
    // Get status icon and color
    const statusIcon = isResolved ? 'check-circle' : type === 'lost' ? 'search' : 'box';
    const statusClass = isResolved ? 'resolved' : 'active';
    
    // Get category icon
    const categoryIcon = getCategoryIcon(item.category);
    
    // Check if there are notifications for this item
    const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const hasNotifications = currentUser && notifications.some(notif => 
        notif.userId === currentUser.id && 
        notif.itemId === item.id && 
        !notif.read
    );
    
    // Add notification indicator if there are unread notifications
    const notificationIndicator = hasNotifications ? 
        `<div class="notification-indicator"><i class="fas fa-bell"></i></div>` : '';
    
    return `
        <div class="dashboard-item" id="item-${item.id}">
            <div class="item-image">
                ${itemImage}
                ${notificationIndicator}
            </div>
            <div class="item-details">
                <div class="item-header">
                    <h3>${item.itemName || 'Unnamed Item'}</h3>
                    <span class="status-badge ${statusClass}">
                        <i class="fas fa-${statusIcon}"></i>
                        ${statusText}
                    </span>
                </div>
                <p class="item-category">
                    <i class="fas fa-${categoryIcon}"></i> 
                    ${item.category || 'Uncategorized'}
                </p>
                <p class="item-description">${item.description || 'No description provided.'}</p>
                <div class="item-meta">
                    <span><i class="far fa-calendar"></i> ${formattedDate}</span>
                    <span><i class="fas fa-map-marker-alt"></i> ${item.location || 'Location not specified'}</span>
                </div>
                <div class="item-actions">
                    <button id="status-btn-${item.id}" class="btn btn-sm ${isResolved ? 'btn-outline' : 'btn-primary'}">
                        <i class="fas fa-${isResolved ? 'undo' : type === 'lost' ? 'check' : 'check-double'}"></i>
                        ${isResolved ? 'Reopen' : 'Mark as ' + (type === 'lost' ? 'Found' : 'Claimed')}
                    </button>
                    <button onclick="event.stopPropagation(); viewItemDetails('${item.id}', '${type}');" class="btn btn-sm btn-outline">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        </div>
    `;
}

function getCategoryIcon(category) {
    if (!category) return 'tag';
    
    const categoryIcons = {
        'electronics': 'laptop',
        'phone': 'mobile-alt',
        'laptop': 'laptop',
        'wallet': 'wallet',
        'keys': 'key',
        'bag': 'briefcase',
        'clothing': 'tshirt',
        'accessories': 'glasses',
        'documents': 'file-alt',
        'jewelry': 'gem',
        'books': 'book',
        'stationery': 'pen-fancy',
        'sports': 'futbol',
        'toys': 'gamepad',
        'other': 'tag'
    };
    
    const lowerCategory = category.toLowerCase();
    for (const [key, icon] of Object.entries(categoryIcons)) {
        if (lowerCategory.includes(key)) {
            return icon;
        }
    }
    
    return 'tag';
}

function updateItemStatus(itemId, type) {
    const storageKey = type === 'lost' ? 'lostItems' : 'foundItems';
    const items = JSON.parse(localStorage.getItem(storageKey) || '[]');
    const itemIndex = items.findIndex(item => item.id === itemId);
    
    if (itemIndex === -1) {
        showToast('Item not found', 'error');
        return;
    }
    
    const item = items[itemIndex];
    const wasResolved = type === 'lost' ? item.status === 'found' : item.status === 'claimed';
    
    // Toggle status
    if (type === 'lost') {
        item.status = wasResolved ? 'searching' : 'found';
    } else {
        item.status = wasResolved ? 'unclaimed' : 'claimed';
    }
    
    // Update timestamps
    if (!wasResolved) {
        item.resolvedAt = new Date().toISOString();
    } else {
        delete item.resolvedAt;
    }
    
    // Save back to localStorage
    items[itemIndex] = item;
    localStorage.setItem(storageKey, JSON.stringify(items));
    
    // Show success message
    const action = wasResolved ? 'reopened' : type === 'lost' ? 'marked as found' : 'marked as claimed';
    showToast(`Item ${action} successfully`, 'success');
    
    // Reload items
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    if (currentUser) {
        loadUserItems(currentUser.id);
    }
    
    // Update notifications
    const lostItems = JSON.parse(localStorage.getItem('lostItems') || '[]');
    const foundItems = JSON.parse(localStorage.getItem('foundItems') || '[]');
    updateNotificationsCount(lostItems, foundItems);
}

function updateNotificationsCount(lostItems, foundItems) {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    if (!currentUser) return;
    
    // Count unresolved items for the current user
    const unresolvedLost = lostItems.filter(item => 
        item.userId === currentUser.id && item.status !== 'found'
    ).length;
    
    const unresolvedFound = foundItems.filter(item => 
        item.userId === currentUser.id && item.status !== 'claimed'
    ).length;
    
    // Get admin notifications for this user
    const notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
    const unreadNotifications = notifications.filter(notif => 
        notif.userId === currentUser.id && !notif.read
    ).length;
    
    // Update the notifications badge
    const notificationsBadge = document.getElementById('notificationsCount');
    const totalNotifications = unresolvedLost + unresolvedFound + unreadNotifications;
    
    if (notificationsBadge) {
        notificationsBadge.textContent = totalNotifications;
        notificationsBadge.style.display = totalNotifications > 0 ? 'flex' : 'none';
    }
    
    // Update the resolved count in stats
    const resolvedCount = document.getElementById('totalResolved');
    if (resolvedCount) {
        const totalResolved = 
            lostItems.filter(item => item.status === 'found').length +
            foundItems.filter(item => item.status === 'claimed').length;
        resolvedCount.textContent = totalResolved;
    }
}

function viewItemDetails(itemId, type) {
    // Store the item ID and type to view details
    sessionStorage.setItem('viewingItem', JSON.stringify({ id: itemId, type }));
    // Navigate to item details page
    window.location.href = `details.html`;
}

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const targetPane = document.getElementById(button.getAttribute('data-tab'));
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
}

// Show toast notification
function showToast(message, type = 'info', duration = 3000) {
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

// Make functions available globally
window.viewItemDetails = viewItemDetails;
