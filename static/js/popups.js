// Professional Pop-ups for Lost & Found Website

// Home Page Pop-up
setTimeout(() => {
    if (!localStorage.getItem('homeVisited')) {
        const popup = document.getElementById('homeWelcomePopup');
        if (popup) {
            popup.style.display = 'flex';
            localStorage.setItem('homeVisited', 'true');
        }
    }
}, 2000);

function closeHomePopup() {
    document.getElementById('homeWelcomePopup').style.display = 'none';
}

// User Dashboard Pop-up
function showUserDashboardTip() {
    if (!localStorage.getItem('userDashboardTip')) {
        setTimeout(() => {
            showTooltip('💡 Tip: Use notifications to track when your lost items are found!', 'info');
            localStorage.setItem('userDashboardTip', 'true');
        }, 1000);
    }
}

// Admin Dashboard Pop-up
function showAdminDashboardTip() {
    if (!localStorage.getItem('adminDashboardTip')) {
        setTimeout(() => {
            showTooltip('🔧 Admin Tip: Use the matching system to help reunite items with owners!', 'admin');
            localStorage.setItem('adminDashboardTip', 'true');
        }, 1500);
    }
}

// Report Form Success Pop-up
function showReportSuccess(type) {
    const popup = document.createElement('div');
    popup.className = 'success-popup';
    popup.innerHTML = `
        <div class="success-content">
            <div class="success-icon">${type === 'lost' ? '🔍' : '🎯'}</div>
            <h3>${type === 'lost' ? 'Lost Item Reported!' : 'Found Item Reported!'}</h3>
            <p>Thank you for using our system. We'll notify you of any matches!</p>
            <button onclick="closeSuccessPopup()" class="btn btn-secondary">Continue</button>
        </div>
    `;
    document.body.appendChild(popup);
    
    setTimeout(() => {
        popup.style.display = 'flex';
    }, 100);
}

function closeSuccessPopup() {
    const popup = document.querySelector('.success-popup');
    if (popup) {
        popup.remove();
    }
}

// Notification Pop-up
function showNotificationTip() {
    if (!localStorage.getItem('notificationTip')) {
        setTimeout(() => {
            showTooltip('📧 New notifications appear here when matches are found!', 'notification');
            localStorage.setItem('notificationTip', 'true');
        }, 800);
    }
}

// Generic Tooltip Function
function showTooltip(message, type) {
    const tooltip = document.createElement('div');
    tooltip.className = `tooltip tooltip-${type}`;
    tooltip.innerHTML = `
        <div class="tooltip-content">
            <span class="tooltip-close" onclick="closeTooltip(this)">&times;</span>
            <p>${message}</p>
        </div>
    `;
    document.body.appendChild(tooltip);
    
    setTimeout(() => {
        tooltip.style.display = 'block';
    }, 100);
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        if (tooltip.parentNode) {
            tooltip.remove();
        }
    }, 5000);
}

function closeTooltip(element) {
    element.closest('.tooltip').remove();
}

// Match Found Celebration
function showMatchCelebration() {
    const celebration = document.createElement('div');
    celebration.className = 'match-celebration';
    celebration.innerHTML = `
        <div class="celebration-content">
            <div class="celebration-animation">
                <div class="confetti"></div>
                <div class="confetti"></div>
                <div class="confetti"></div>
            </div>
            <h2>🎉 Match Found! 🎉</h2>
            <p>Great news! We found a potential match for the item.</p>
            <button onclick="closeCelebration()" class="btn">Awesome!</button>
        </div>
    `;
    document.body.appendChild(celebration);
    
    setTimeout(() => {
        celebration.style.display = 'flex';
    }, 100);
}

function closeCelebration() {
    const celebration = document.querySelector('.match-celebration');
    if (celebration) {
        celebration.remove();
    }
}