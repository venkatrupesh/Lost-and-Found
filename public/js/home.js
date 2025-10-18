// Sample data for recently found items (in a real app, this would come from an API)
const sampleItems = [
    {
        id: 1,
        title: 'Black Wallet Found',
        category: 'Wallet',
        location: 'Main Building, Room 101',
        date: '2023-11-10',
        image: 'https://images.unsplash.com/photo-1541643600914-78f084ea7f6e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
        type: 'found'
    },
    {
        id: 2,
        title: 'Silver Laptop',
        category: 'Electronics',
        location: 'Library, 2nd Floor',
        date: '2023-11-09',
        image: 'https://images.unsplash.com/photo-1496181133205-80b16566e1cd?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
        type: 'lost'
    },
    {
        id: 3,
        title: 'Gold Earrings',
        category: 'Jewelry',
        location: 'Cafeteria',
        date: '2023-11-08',
        image: 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
        type: 'found'
    },
    {
        id: 4,
        title: 'Water Bottle - Blue',
        category: 'Accessories',
        location: 'Gym',
        date: '2023-11-07',
        image: 'https://images.unsplash.com/photo-1589985270828-15f25a0e8268?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
        type: 'lost'
    },
    {
        id: 5,
        title: 'Black Backpack',
        category: 'Bag',
        location: 'Auditorium',
        date: '2023-11-06',
        image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
        type: 'found'
    },
    {
        id: 6,
        title: 'Wireless Headphones',
        category: 'Electronics',
        location: 'Bus Stop',
        date: '2023-11-05',
        image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
        type: 'lost'
    }
];

// Function to create item card HTML
const createItemCard = (item) => {
    return `
        <div class="item-card animate-on-scroll" data-id="${item.id}">
            <div class="item-image">
                <img src="${item.image}" alt="${item.title}">
                <div class="item-category">${item.category}</div>
            </div>
            <div class="item-info">
                <h3 class="item-title">${item.title}</h3>
                <div class="item-meta">
                    <span><i class="fas fa-map-marker-alt"></i> ${item.location}</span>
                    <span><i class="far fa-calendar-alt"></i> ${formatDate(item.date)}</span>
                </div>
                <a href="pages/items/item-details.html?id=${item.id}" class="btn btn-outline" style="margin-top: 15px; display: inline-block;">View Details</a>
            </div>
        </div>
    `;
};

// Format date to readable format
const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
};

// Function to load recent items
const loadRecentItems = () => {
    const container = document.getElementById('recentItems');
    if (!container) return;
    
    // Sort items by date (newest first) and take first 6
    const recentItems = [...sampleItems]
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 6);
    
    // Clear loading state if any
    container.innerHTML = '';
    
    // Add items to the container
    recentItems.forEach(item => {
        container.innerHTML += createItemCard(item);
    });
};

// Function to handle search
const handleSearch = (query) => {
    if (!query.trim()) {
        loadRecentItems();
        return;
    }
    
    const container = document.getElementById('recentItems');
    if (!container) return;
    
    const searchTerm = query.toLowerCase();
    const filteredItems = sampleItems.filter(item => 
        item.title.toLowerCase().includes(searchTerm) ||
        item.category.toLowerCase().includes(searchTerm) ||
        item.location.toLowerCase().includes(searchTerm)
    );
    
    container.innerHTML = '';
    
    if (filteredItems.length === 0) {
        container.innerHTML = `
            <div class="no-results" style="grid-column: 1 / -1; text-align: center; padding: 40px 0;">
                <i class="fas fa-search" style="font-size: 3rem; color: #ccc; margin-bottom: 20px;"></i>
                <h3>No items found</h3>
                <p>We couldn't find any items matching "${query}"</p>
            </div>
        `;
    } else {
        filteredItems.forEach(item => {
            container.innerHTML += createItemCard(item);
        });
    }
};

// Check authentication status and update UI
function updateAuthUI() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const authLinks = document.querySelector('.auth-links');
    const userMenu = document.querySelector('.user-menu');
    const dashboardLink = document.querySelector('.dashboard-link');
    
    if (currentUser) {
        if (authLinks) authLinks.style.display = 'none';
        if (userMenu) userMenu.style.display = 'flex';
        if (dashboardLink) dashboardLink.style.display = 'inline-flex';
        
        // Set up logout button if it exists
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                localStorage.removeItem('currentUser');
                window.location.reload();
            });
        }
    } else {
        if (authLinks) authLinks.style.display = 'flex';
        if (userMenu) userMenu.style.display = 'none';
        if (dashboardLink) dashboardLink.style.display = 'none';
    }
}

// Initialize the home page
document.addEventListener('DOMContentLoaded', () => {
    // Update authentication UI
    updateAuthUI();
    
    // Load recent items
    loadRecentItems();
    
    // Add event listener to search form
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('searchQuery').value.trim();
            if (query) {
                handleSearch(query);
            }
        });
    }
    
    // Add event listener to quick action buttons
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.getAttribute('data-action');
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            
            // If user is not logged in, redirect to login page with return URL
            if (!currentUser && (action === 'report-lost' || action === 'report-found')) {
                localStorage.setItem('redirectAfterLogin', `pages/items/${action}.html`);
                window.location.href = 'pages/auth/login.html';
                return;
            }
            
            // Navigate to the appropriate page
            if (action === 'report-lost') {
                window.location.href = 'pages/items/report-lost.html';
            } else if (action === 'report-found') {
                window.location.href = 'pages/items/report-found.html';
            } else if (action === 'browse') {
                window.location.href = 'pages/items/browse.html';
            }
        });
    });
    
    // Add click handler for dashboard link
    const dashboardLink = document.querySelector('.dashboard-link');
    if (dashboardLink) {
        dashboardLink.addEventListener('click', function(e) {
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            if (!currentUser) {
                e.preventDefault();
                localStorage.setItem('redirectAfterLogin', 'pages/dashboard/index.html');
                window.location.href = 'pages/auth/login.html';
            }
        });
    }
});

// Add event listener for search input to show live results
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length === 0) {
            loadRecentItems();
            return;
        }
        
        // Add delay to prevent too many searches while typing
        searchTimeout = setTimeout(() => {
            handleSearch(query);
        }, 300);
    });
}
