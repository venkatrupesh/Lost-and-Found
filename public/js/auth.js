// Function to validate KLU email
function isValidKLUEmail(email) {
    return email.endsWith('@klu.ac.in');
}

// Function to check authentication status
function checkAuthStatus() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    
    // Get all elements that should be visible only when logged in
    const authElements = document.querySelectorAll('.auth-required');
    // Get all elements that should be visible only when logged out
    const guestElements = document.querySelectorAll('.guest-only');
    
    if (isLoggedIn && currentUser.id) {
        // User is logged in
        authElements.forEach(el => el.style.display = '');
        guestElements.forEach(el => el.style.display = 'none');
        
        // Update user name if element exists
        const userNameElement = document.getElementById('userName');
        if (userNameElement) {
            userNameElement.textContent = currentUser.name || 'User';
        }
    } else {
        // User is not logged in
        authElements.forEach(el => el.style.display = 'none');
        guestElements.forEach(el => el.style.display = '');
        
        // Redirect to login page if on a protected page
        const currentPath = window.location.pathname;
        if (currentPath.includes('/dashboard/') || 
            currentPath.includes('/items/report-') ||
            currentPath.includes('/profile/')) {
            window.location.href = '../../pages/auth/login.html';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Check which form exists on the page
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const emailInput = document.getElementById('email');

    // Add email validation on input
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const errorElement = document.getElementById('emailError');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        });
    }

    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            // Basic validation
            if (!email || !password) {
                showError('Please fill in all fields');
                return;
            }
            
            // Validate KLU email
            if (!isValidKLUEmail(email)) {
                showError('Please use your KLU email address (@klu.ac.in)');
                return;
            }
            
            // Get stored user data (in a real app, this would be verified on the server)
            const userData = JSON.parse(localStorage.getItem('userData') || '{}');
            
            // Check if user exists and password matches
            if (userData && userData.email === email) {
                // Set authentication state
                localStorage.setItem('isLoggedIn', 'true');
                localStorage.setItem('currentUser', JSON.stringify({
                    id: 'user-' + Date.now(),
                    name: userData.fullName || userData.email.split('@')[0]
                }));
                
                // Redirect to dashboard
                window.location.href = '../../pages/dashboard/';
            } else {
                showError('Invalid email or password');
            }
        });
    }

    // Handle registration form submission
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fullName = document.getElementById('fullName').value.trim();
            const email = document.getElementById('email').value.trim().toLowerCase();
            const phone = document.getElementById('phone').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            // Basic validation
            if (!fullName || !email || !phone || !password || !confirmPassword) {
                showError('Please fill in all fields');
                return;
            }
            
            // Validate KLU email
            if (!isValidKLUEmail(email)) {
                showError('Please use your KLU email address (@klu.ac.in)');
                return;
            }
            
            if (password !== confirmPassword) {
                showError('Passwords do not match');
                return;
            }
            
            if (password.length < 8) {
                showError('Password must be at least 8 characters long');
                return;
            }
            
            // Check for password strength requirements
            const hasUppercase = /[A-Z]/.test(password);
            const hasLowercase = /[a-z]/.test(password);
            const hasNumber = /[0-9]/.test(password);
            const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
            
            if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
                showError('Password must include uppercase, lowercase, number, and special character');
                return;
            }
            
            // Check if user already exists
            const existingUser = JSON.parse(localStorage.getItem('userData') || '{}');
            if (existingUser && existingUser.email === email) {
                showError('An account with this email already exists');
                return;
            }
            
            // Create user data object
            const userData = {
                id: 'user-' + Date.now(),
                fullName,
                email,
                phone,
                password, // In a real app, this would be hashed
                createdAt: new Date().toISOString()
            };
            
            // Store user data (in a real app, this would be on the server)
            localStorage.setItem('userData', JSON.stringify(userData));
            
            // Auto-login after registration
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('currentUser', JSON.stringify({
                id: userData.id,
                name: userData.fullName
            }));
            
            // Redirect to dashboard
            window.location.href = '../../pages/dashboard/';
        });
    }
    
    // Function to show error messages
    function showError(message) {
        // Check if there's already an error message and remove it
        const existingError = document.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = '#e53e3e';
        errorDiv.style.marginBottom = '1rem';
        errorDiv.style.padding = '0.5rem';
        errorDiv.style.backgroundColor = '#fff5f5';
        errorDiv.style.borderRadius = '4px';
        errorDiv.style.borderLeft = '3px solid #e53e3e';
        errorDiv.textContent = message;
        
        // Insert the error message at the top of the form
        const form = loginForm || registerForm;
        form.insertBefore(errorDiv, form.firstChild);
        
        // Scroll to the error message
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
