// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#dc3545';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showAlert('Please fill in all required fields', 'danger');
            }
        });
    });
    
    // Email validation
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        field.addEventListener('blur', function() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (this.value && !emailRegex.test(this.value)) {
                this.style.borderColor = '#dc3545';
                showAlert('Please enter a valid email address', 'danger');
            } else {
                this.style.borderColor = '#ddd';
            }
        });
    });
    
    // Phone validation
    const phoneFields = document.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        field.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9+\-\s]/g, '');
        });
    });
});

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function loadMyReports() {
    window.location.href = '/my_reports';
}

function loadMyNotifications() {
    window.location.href = '/my_notifications';
}

function loadMyRewards() {
    window.location.href = '/my_rewards';
}

function showImageModal(imageSrc) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        cursor: pointer;
    `;
    
    const img = document.createElement('img');
    img.src = imageSrc;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    `;
    
    modal.appendChild(img);
    document.body.appendChild(modal);
    
    modal.onclick = () => modal.remove();
}

function giveReward(finderEmail, finderName, itemName, giverEmail, giverName, buttonElement) {
    // Check if reward already given
    fetch('/check_reward_given', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            finder_email: finderEmail,
            item_name: itemName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.already_given) {
            showAlert('Reward already given for this item!', 'warning');
            if (buttonElement) {
                buttonElement.disabled = true;
                buttonElement.textContent = '✓ Reward Given';
                buttonElement.style.background = '#6B7280';
            }
            return;
        }
        
        const tokens = prompt('How many tokens would you like to give? (1-100):');
        const message = prompt('Optional message for the finder:') || '';
        
        if (tokens && tokens > 0 && tokens <= 100) {
            fetch('/give_reward', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    finder_email: finderEmail,
                    finder_name: finderName,
                    giver_email: giverEmail,
                    giver_name: giverName,
                    tokens: parseInt(tokens),
                    item_name: itemName,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Reward sent successfully!', 'success');
                    if (buttonElement) {
                        buttonElement.disabled = true;
                        buttonElement.textContent = '✓ Reward Given';
                        buttonElement.style.background = '#6B7280';
                    }
                } else {
                    showAlert(data.message || 'Failed to send reward', 'danger');
                }
            })
            .catch(error => {
                console.error('Error sending reward:', error);
                showAlert('Error sending reward', 'danger');
            });
        } else {
            showAlert('Please enter a valid number of tokens (1-100)', 'danger');
        }
    })
    .catch(error => {
        console.error('Error checking reward status:', error);
    });
}

function markNotificationAsRead(notificationId) {
    fetch(`/mark_notification_read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update badge count
            if (typeof loadNotificationCount === 'function') {
                loadNotificationCount();
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

// Admin Dashboard Functions
function loadAllReports() {
    fetch('/admin_reports')
        .then(response => response.json())
        .then(data => {
            displayReports(data);
        })
        .catch(error => {
            console.error('Error loading reports:', error);
            showAlert('Error loading reports', 'danger');
        });
}

function displayReports(reports) {
    const container = document.getElementById('reports-container');
    if (!container) return;
    
    if (reports.length === 0) {
        container.innerHTML = '<p class="loading">No reports found.</p>';
        return;
    }
    
    // Sort reports by date (first come first serve)
    reports.sort((a, b) => new Date(a.date_reported) - new Date(b.date_reported));
    
    let html = `
        <div style="margin-bottom: 15px; padding: 10px; background: #e3f2fd; border-radius: 8px;">
            <strong>📅 Reports sorted by submission time (First Come First Serve)</strong>
        </div>
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Image</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Item</th>
                    <th>Type</th>
                    <th>Date & Time</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    reports.forEach(report => {
        const imageHtml = report.image_filename ? 
            `<img src="/static/uploads/${report.image_filename}" alt="Item image" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; cursor: pointer;" onclick="showImageModal('/static/uploads/${report.image_filename}')" />` : 
            '<span style="color: #64748b; font-size: 12px;">No image</span>';
        
        const reportDate = new Date(report.date_reported);
        const dateTimeString = reportDate.toLocaleDateString() + ' ' + reportDate.toLocaleTimeString();
        
        html += `
            <tr>
                <td>${report.id}</td>
                <td>${imageHtml}</td>
                <td>${report.name}</td>
                <td>${report.email}</td>
                <td>${report.phone}</td>
                <td>${report.item_name}</td>
                <td><span class="badge ${report.type === 'lost' ? 'badge-danger' : 'badge-success'}">${report.type}</span></td>
                <td style="font-size: 12px; white-space: nowrap;">${dateTimeString}</td>
                <td>${report.status}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function findMatches() {
    const container = document.getElementById('matches-container');
    if (!container) return;
    
    container.innerHTML = '<p class="loading">Finding matches...</p>';
    
    fetch('/find_matches')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayMatches(Array.isArray(data) ? data : []);
        })
        .catch(error => {
            console.error('Error finding matches:', error);
            container.innerHTML = '<p class="loading">Error loading matches</p>';
            showAlert('Error finding matches', 'danger');
        });
}

function displayMatches(matches) {
    const container = document.getElementById('matches-container');
    if (!container) return;
    
    // Ensure matches is an array
    if (!Array.isArray(matches)) {
        matches = [];
    }
    
    // Store matches globally
    currentMatches = matches;
    
    if (matches.length === 0) {
        container.innerHTML = '<p class="loading">No matches found.</p>';
        return;
    }
    
    let html = '';
    matches.forEach((match, index) => {
        const lostImage = match.lost.image_filename ? 
            `<img src="/static/uploads/${match.lost.image_filename}" alt="Lost item" style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; margin: 10px 0; cursor: pointer;" onclick="showImageModal('/static/uploads/${match.lost.image_filename}')" />` : 
            '<div style="width: 120px; height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">No Image</div>';
        
        const foundImage = match.found.image_filename ? 
            `<img src="/static/uploads/${match.found.image_filename}" alt="Found item" style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; margin: 10px 0; cursor: pointer;" onclick="showImageModal('/static/uploads/${match.found.image_filename}')" />` : 
            '<div style="width: 120px; height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">No Image</div>';
        
        html += `
            <div class="match-card">
                <div class="match-header">🎯 Match ${index + 1} - ${match.match_score}</div>
                <div class="item-details">
                    <div>
                        <h4>Lost Item</h4>
                        ${lostImage}
                        <p><strong>Reporter:</strong> ${match.lost.name}</p>
                        <p><strong>Email:</strong> ${match.lost.email}</p>
                        <p><strong>Item:</strong> ${match.lost.item_name}</p>
                        <p><strong>Description:</strong> ${match.lost.description}</p>
                    </div>
                    <div>
                        <h4>Found Item</h4>
                        ${foundImage}
                        <p><strong>Finder:</strong> ${match.found.name}</p>
                        <p><strong>Email:</strong> ${match.found.email}</p>
                        <p><strong>Item:</strong> ${match.found.item_name}</p>
                        <p><strong>Description:</strong> ${match.found.description}</p>
                    </div>
                </div>
                <button class="btn" onclick="sendNotification(${index})">
                    📧 Send Notification
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

let currentMatches = [];

function sendNotification(matchIndex) {
    if (!currentMatches[matchIndex]) {
        showAlert('Match not found', 'danger');
        return;
    }
    
    const match = currentMatches[matchIndex];
    
    fetch('/send_notification', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            lost_item: match.lost,
            found_item: match.found
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMatchCelebration();
            showAlert('Notification sent successfully!', 'success');
        } else {
            showAlert('Failed to send notification', 'danger');
        }
    })
    .catch(error => {
        console.error('Error sending notification:', error);
        showAlert('Error sending notification', 'danger');
    });
}
// Enhanced AI matching functions
function findAIMatches() {
    const container = document.getElementById('matches-container');
    if (!container) return;
    
    container.innerHTML = '<p class="loading">🤖 AI is analyzing matches with image recognition and urgency priority...</p>';
    
    fetch('/ai_find_matches')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayAIMatches(data);
        })
        .catch(error => {
            console.error('Error finding AI matches:', error);
            container.innerHTML = `<p class="loading">Error: ${error.message}</p>`;
            showAlert('Error finding AI matches: ' + error.message, 'danger');
        });
}

function displayAIMatches(matches) {
    const container = document.getElementById('matches-container');
    if (!container) return;
    
    currentMatches = matches;
    
    if (matches.length === 0) {
        container.innerHTML = '<p class="loading">No AI matches found.</p>';
        return;
    }
    
    let html = '';
    matches.forEach((match, index) => {
        const urgencyColor = {
            'CRITICAL': '#ff1744',
            'HIGH': '#ff5722', 
            'MEDIUM': '#ff9800',
            'LOW': '#4caf50'
        };
        
        const lostImage = match.lost.image_filename ? 
            `<img src="/static/uploads/${match.lost.image_filename}" alt="Lost item" style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; margin: 10px 0; cursor: pointer;" onclick="showImageModal('/static/uploads/${match.lost.image_filename}')" />` : 
            '<div style="width: 120px; height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">No Image</div>';
        
        const foundImage = match.found.image_filename ? 
            `<img src="/static/uploads/${match.found.image_filename}" alt="Found item" style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; margin: 10px 0; cursor: pointer;" onclick="showImageModal('/static/uploads/${match.found.image_filename}')" />` : 
            '<div style="width: 120px; height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">No Image</div>';
        
        html += `
            <div class="match-card ai-match">
                <div class="match-header">
                    🤖 AI Match ${index + 1} - ${match.match_score}
                    <span class="urgency-badge" style="background: ${urgencyColor[match.urgency]};">
                        ⚡ ${match.urgency}
                    </span>
                    ${match.image_match ? '<span class="image-match-badge">📷 Image Match</span>' : ''}
                </div>
                <div class="item-details">
                    <div>
                        <h4>Lost Item (${match.lost.urgency_score}% urgency)</h4>
                        ${lostImage}
                        <p><strong>Reporter:</strong> ${match.lost.name}</p>
                        <p><strong>Email:</strong> ${match.lost.email}</p>
                        <p><strong>Item:</strong> ${match.lost.item_name}</p>
                        <p><strong>Description:</strong> ${match.lost.description}</p>
                        <p><strong>Hours passed:</strong> ${Math.round((new Date() - new Date(match.lost.date_reported)) / 3600000)}h</p>
                    </div>
                    <div>
                        <h4>Found Item</h4>
                        ${foundImage}
                        <p><strong>Finder:</strong> ${match.found.name}</p>
                        <p><strong>Email:</strong> ${match.found.email}</p>
                        <p><strong>Item:</strong> ${match.found.item_name}</p>
                        <p><strong>Description:</strong> ${match.found.description}</p>
                    </div>
                </div>
                <button class="btn" onclick="sendNotification(${index})" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    🚀 Send AI-Powered Notification
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function loadUrgentItems() {
    fetch('/admin_reports')
        .then(response => response.json())
        .then(data => {
            // Filter urgent items
            const urgentItems = data.filter(item => 
                item.urgency_level && ['CRITICAL', 'HIGH'].includes(item.urgency_level)
            ).sort((a, b) => b.urgency_score - a.urgency_score);
            
            displayUrgentItems(urgentItems);
        })
        .catch(error => {
            console.error('Error loading urgent items:', error);
            showAlert('Error loading urgent items', 'danger');
        });
}

function displayUrgentItems(items) {
    const container = document.getElementById('reports-container');
    if (!container) return;
    
    if (items.length === 0) {
        container.innerHTML = '<p class="loading">No urgent items found.</p>';
        return;
    }
    
    let html = '<h3>⚡ Urgent Items Requiring Immediate Attention</h3>';
    
    items.forEach(item => {
        const urgencyColor = item.urgency_level === 'CRITICAL' ? '#ff1744' : '#ff5722';
        const imageHtml = item.image_filename ? 
            `<img src="/static/uploads/${item.image_filename}" alt="Item image" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px; cursor: pointer;" onclick="showImageModal('/static/uploads/${item.image_filename}')" />` : 
            '<span style="color: #64748b;">No image</span>';
        
        html += `
            <div class="urgent-item-card" style="border-left: 5px solid ${urgencyColor}; margin: 10px 0; padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <h4>${item.item_name} 
                            <span style="background: ${urgencyColor}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                                ${item.urgency_level} - ${item.urgency_score}%
                            </span>
                        </h4>
                        <p><strong>Reporter:</strong> ${item.name} (${item.email})</p>
                        <p><strong>Description:</strong> ${item.description}</p>
                        <p><strong>Location:</strong> ${item.location}</p>
                        <p><strong>Reported:</strong> ${new Date(item.date_reported).toLocaleString()}</p>
                    </div>
                    <div style="margin-left: 20px;">
                        ${imageHtml}
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}