// DOM Elements
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');
const navbar = document.querySelector('.navbar');
const body = document.body;

// Toggle mobile menu
if (hamburger) {
    hamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
        document.body.classList.toggle('nav-open');
        
        if (navLinks.classList.contains('active')) {
            // Disable scroll when mobile menu is open
            body.style.overflow = 'hidden';
            // Close menu when clicking outside
            document.addEventListener('click', closeMenuOnClickOutside);
        } else {
            body.style.overflow = '';
            document.removeEventListener('click', closeMenuOnClickOutside);
        }
    });
}

// Close menu when clicking outside
function closeMenuOnClickOutside(e) {
    if (!navLinks.contains(e.target) && !hamburger.contains(e.target)) {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
        body.style.overflow = '';
        document.removeEventListener('click', closeMenuOnClickOutside);
    }
}

// Close mobile menu when clicking on a nav link
const navItems = document.querySelectorAll('.nav-links a');
navItems.forEach(link => {
    link.addEventListener('click', () => {
        if (hamburger && hamburger.classList.contains('active')) {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            body.style.overflow = '';
            document.removeEventListener('click', closeMenuOnClickOutside);
        }
    });
});

// Add active class to current page in navigation
function setActiveNavItem() {
    const currentLocation = location.pathname;
    const menuItems = document.querySelectorAll('.nav-links a');
    
    menuItems.forEach(item => {
        // Remove active class from all items
        item.classList.remove('active');
        
        // Check if the link's path matches the current URL
        const itemPath = new URL(item.href).pathname;
        if (itemPath === currentLocation || 
            (currentLocation.startsWith(itemPath) && itemPath !== '/')) {
            item.classList.add('active');
        }
    });
}

// Call on page load and when the URL changes (for SPA-like navigation)
document.addEventListener('DOMContentLoaded', setActiveNavItem);
window.addEventListener('popstate', setActiveNavItem);

// Enhanced smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');
        
        // Skip empty or invalid hashes
        if (targetId === '#' || targetId === '') {
            e.preventDefault();
            return;
        }
        
        // Handle internal links
        if (targetId.startsWith('#')) {
            e.preventDefault();
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                // Close mobile menu if open
                if (hamburger && hamburger.classList.contains('active')) {
                    hamburger.classList.remove('active');
                    navLinks.classList.remove('active');
                    body.style.overflow = '';
                }
                
                // Calculate the scroll position, accounting for fixed header
                const headerOffset = 90;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                // Smooth scroll to the target
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
                
                // Update URL without page jump
                if (history.pushState) {
                    history.pushState(null, null, targetId);
                } else {
                    location.hash = targetId;
                }
            }
        }
    });
});

// Intersection Observer for scroll animations
const animateOnScroll = () => {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                // Unobserve after animation starts to improve performance
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
};

// Initialize animations on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add animation class to elements that should animate on scroll
    const animatedElements = [
        ...document.querySelectorAll('.feature-card'),
        ...document.querySelectorAll('.item-card'),
        ...document.querySelectorAll('.stat-item'),
        ...document.querySelectorAll('.section-header')
    ];
    
    animatedElements.forEach((element, index) => {
        element.style.setProperty('--animation-delay', `${index * 0.1}s`);
        element.classList.add('animate-on-scroll');
    });
    
    // Initialize scroll animations
    if ('IntersectionObserver' in window) {
        animateOnScroll();
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animatedElements.forEach(element => {
            element.classList.add('animated');
        });
    }
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Initialize navbar state
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    }
});

// Form validation helper
const validateForm = (formId) => {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
            
            // Add error message if not already present
            if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('error-message')) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error-message';
                errorMsg.textContent = 'This field is required';
                errorMsg.style.color = 'var(--danger-color)';
                errorMsg.style.fontSize = '0.8rem';
                errorMsg.style.marginTop = '5px';
                input.parentNode.insertBefore(errorMsg, input.nextSibling);
            }
        } else {
            input.classList.remove('error');
            const errorMsg = input.nextElementSibling;
            if (errorMsg && errorMsg.classList.contains('error-message')) {
                errorMsg.remove();
            }
        }
    });
    
    return isValid;
};

// Add event listeners to all forms with validation
const forms = document.querySelectorAll('form[data-validate]');
forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        if (!validateForm(this.id)) {
            e.preventDefault();
        }
    });
});

// Helper function to show toast messages
const showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Trigger reflow
    toast.offsetHeight;
    
    // Add show class
    toast.classList.add('show');
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
};

// Add toast styles if not already present
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        .toast-success {
            background-color: var(--success-color);
        }
        
        .toast-error {
            background-color: var(--danger-color);
        }
        
        .toast-warning {
            background-color: var(--warning-color);
            color: #000;
        }
    `;
    document.head.appendChild(style);
}

// Check if user is logged in and update UI accordingly
function checkAuthStatus() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const authLinks = document.getElementById('authLinks');
    const userMenu = document.getElementById('userMenu');
    const dashboardLinks = document.querySelectorAll('.dashboard-link');
    
    if (isLoggedIn) {
        const userName = localStorage.getItem('userName') || 'User';
        const userNameElements = document.querySelectorAll('#userName');
        
        // Update all userName elements on the page
        userNameElements.forEach(element => {
            element.textContent = userName;
        });
        
        // Show user menu and hide auth links
        if (authLinks) authLinks.style.display = 'none';
        if (userMenu) userMenu.style.display = 'flex';
        dashboardLinks.forEach(link => {
            link.style.display = 'flex';
        });
        
        // Update report buttons to go directly to forms
        reportButtons.forEach(btn => {
            const action = btn.getAttribute('data-action');
            if (action) {
                btn.href = `pages/items/report-${action}.html`;
                btn.onclick = null; // Remove any click handlers
            }
        });
    } else {
        // User is not logged in
        if (loginLink) loginLink.style.display = 'block';
        if (registerLink) registerLink.style.display = 'block';
        if (userMenu) userMenu.style.display = 'none';
        if (dashboardLink) dashboardLink.style.display = 'none';
        
        // Hide all navigation items except Home
        navItems.forEach(item => {
            if (!item.href.includes('index.html')) {
                item.style.display = 'none';
            } else {
                item.style.display = 'block';
            }
        });
        
        // Update report buttons to redirect to login
        reportButtons.forEach(btn => {
            const action = btn.getAttribute('data-action');
            if (action) {
                btn.href = 'pages/auth/login.html';
                btn.onclick = function(e) {
                    e.preventDefault();
                    localStorage.setItem('redirectAfterLogin', `pages/items/report-${action}.html`);
                    window.location.href = 'pages/auth/login.html';
                };
            }
        });
    }
}

// Add logout functionality
function setupLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
}

// Call checkAuthStatus when the page loads
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    setupLogout();
    
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

// Handle logout
function logout() {
    // Clear user data
    localStorage.removeItem('currentUser');
    localStorage.removeItem('isLoggedIn');
    sessionStorage.removeItem('currentUser');
    
    // Always redirect to login.html under the public folder, regardless of current page
    const path = window.location.pathname.replace(/\\/g, '/');
    const pubIdx = path.indexOf('/public/');
    if (pubIdx !== -1) {
        const base = path.substring(0, pubIdx + '/public/'.length);
        window.location.href = base + 'pages/auth/login.html';
    } else {
        // Fallback for relative navigation when not under /public/
        window.location.href = 'pages/auth/login.html';
    }
}
