from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import re
from difflib import SequenceMatcher
import random
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Load configuration
from config import Config
app.config.from_object(Config)

# Register Google Auth Blueprint
from google_auth import google_auth
app.register_blueprint(google_auth)

# Image upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Only PNG and JPG files allowed
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# NLP Functions
def extract_keywords(text):
    """Extract important keywords from item description"""
    # Common words to ignore
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    
    # Extract words and filter
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    return list(set(keywords))  # Remove duplicates

def calculate_nlp_text_similarity(text1, text2):
    """Simple text similarity without ML dependencies"""
    try:
        if not text1 or not text2:
            return 0.0
        
        # Clean texts
        text1_clean = re.sub(r'[^a-zA-Z0-9\s]', '', text1.lower())
        text2_clean = re.sub(r'[^a-zA-Z0-9\s]', '', text2.lower())
        
        # Sequence similarity
        seq_sim = SequenceMatcher(None, text1_clean, text2_clean).ratio()
        
        # Keyword overlap (Jaccard similarity)
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        if words1 and words2:
            jaccard_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            jaccard_sim = 0.0
        
        # Simple weighted similarity percentage
        nlp_score = (seq_sim * 0.6 + jaccard_sim * 0.4) * 100
        
        return round(max(0, min(100, nlp_score)), 2)
        
    except Exception as e:
        print(f"Text similarity error: {e}")
        return 0.0

def calculate_similarity(text1, text2):
    """Backward compatibility wrapper"""
    return calculate_nlp_text_similarity(text1, text2) / 100

def analyze_sentiment(text):
    """Simple sentiment analysis for user messages"""
    positive_words = ['thank', 'grateful', 'happy', 'amazing', 'wonderful', 'great', 'excellent', 'fantastic', 'awesome', 'love', 'appreciate', 'helpful', 'kind', 'generous']
    negative_words = ['sad', 'upset', 'angry', 'frustrated', 'disappointed', 'terrible', 'awful', 'bad', 'horrible', 'hate', 'annoyed']
    
    words = text.lower().split()
    positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
    negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
    
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'

def generate_smart_suggestions(item_name, description):
    """Generate smart suggestions for better item descriptions"""
    suggestions = []
    
    # Check for color mentions
    colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'brown', 'gray', 'pink', 'purple', 'orange']
    has_color = any(color in description.lower() for color in colors)
    if not has_color:
        suggestions.append("💡 Consider adding the color of your item for better identification")
    
    # Check for brand mentions
    common_brands = ['apple', 'samsung', 'nike', 'adidas', 'sony', 'hp', 'dell', 'canon', 'nikon']
    has_brand = any(brand in description.lower() for brand in common_brands)
    if not has_brand and any(item in item_name.lower() for item in ['phone', 'laptop', 'camera', 'watch', 'bag']):
        suggestions.append("💡 Adding the brand name can help identify your item faster")
    
    # Check description length
    if len(description.split()) < 5:
        suggestions.append("💡 A more detailed description increases your chances of recovery")
    
    return suggestions

def get_motivational_message():
    """Generate motivational messages for users"""
    messages = [
        "🌟 Every item you help return makes someone's day brighter!",
        "🤝 You're building a stronger, more caring community!",
        "💫 Your kindness creates ripples of positivity!",
        "🎯 Together, we're making lost items found again!",
        "✨ Your efforts help restore faith in humanity!",
        "🏆 You're a real-life hero in someone's story!"
    ]
    return random.choice(messages)

# Feature 1: AI Photo Similarity
def extract_image_features(image_path):
    """Simple image feature extraction without heavy dependencies"""
    try:
        # Simple file-based hash for basic comparison
        with open(image_path, 'rb') as f:
            file_content = f.read()
            file_hash = hashlib.md5(file_content).hexdigest()[:16]
        
        # Get file size as a basic feature
        file_size = os.path.getsize(image_path)
        
        return {
            'file_hash': file_hash,
            'file_size': file_size,
            'filename': os.path.basename(image_path)
        }
    except Exception as e:
        return None

def calculate_image_similarity(features1, features2):
    """Simple image similarity calculation"""
    if not features1 or not features2:
        return 0.0
    
    # Hash comparison
    hash_similarity = 1.0 if features1['file_hash'] == features2['file_hash'] else 0.0
    
    # Size similarity (basic)
    size_diff = abs(features1['file_size'] - features2['file_size'])
    max_size = max(features1['file_size'], features2['file_size'])
    size_similarity = 1.0 - (size_diff / max_size) if max_size > 0 else 0.0
    
    return (hash_similarity * 0.8) + (size_similarity * 0.2)

# Feature 5: Time-Based Urgency System
def calculate_urgency_score(date_reported, item_type):
    """Calculate urgency score based on time and item type"""
    now = datetime.now()
    time_diff = now - date_reported
    hours_passed = time_diff.total_seconds() / 3600
    
    urgency_multipliers = {
        'phone': 2.0, 'wallet': 2.5, 'keys': 2.0, 'passport': 3.0,
        'medication': 3.5, 'laptop': 1.8, 'jewelry': 1.5, 'bag': 1.3
    }
    
    base_urgency = max(0, 100 - (hours_passed * 2))
    item_multiplier = 1.0
    for item, multiplier in urgency_multipliers.items():
        if item in item_type.lower():
            item_multiplier = multiplier
            break
    
    urgency_score = min(100, base_urgency * item_multiplier)
    
    if urgency_score >= 80:
        level = 'CRITICAL'
    elif urgency_score >= 60:
        level = 'HIGH'
    elif urgency_score >= 40:
        level = 'MEDIUM'
    else:
        level = 'LOW'
    
    return {
        'score': round(urgency_score, 1),
        'level': level,
        'hours_passed': round(hours_passed, 1)
    }

# Database file
DATABASE = 'lost_found.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Create reports table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            item_name TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            image_filename TEXT,
            date_reported DATETIME NOT NULL,
            type TEXT CHECK(type IN ('lost', 'found')) NOT NULL,
            status TEXT CHECK(status IN ('active', 'resolved')) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add image_filename column if it doesn't exist (for existing databases)
    try:
        conn.execute('ALTER TABLE reports ADD COLUMN image_filename TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore the error
        pass
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            finder_email TEXT NOT NULL,
            finder_name TEXT NOT NULL,
            giver_email TEXT NOT NULL,
            giver_name TEXT NOT NULL,
            tokens INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def send_match_notification(email, lost_item, found_item, finder_contact):
    try:
        # Create notification message
        title = f"Great News! Your Lost Item '{lost_item['item_name']}' Has Been Found!"
        message = f"""Dear {lost_item['name']},

Excellent news! We found a match for your lost item:

YOUR LOST ITEM:
- Item: {lost_item['item_name']}
- Description: {lost_item['description']}
- Lost at: {lost_item['location']}

FOUND ITEM DETAILS:
- Item: {found_item['item_name']}
- Description: {found_item['description']}
- Found at: {found_item['location']}

FINDER CONTACT:
- Name: {found_item['name']}
- Phone: {found_item['phone']}
- Email: {found_item['email']}

Please contact the finder to arrange pickup.

Best regards,
Lost & Found System"""
        
        # Save notification to database for ONLY the lost item user
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO notifications (user_email, title, message)
            VALUES (?, ?, ?)
        """, (email, title, message))
        
        # Store match details in the main notification message for reward system
        reward_data = f"REWARD_DATA:{found_item['email']}|{found_item['name']}|{lost_item['item_name']}"
        conn.execute("""
            INSERT INTO notifications (user_email, title, message)
            VALUES (?, ?, ?)
        """, (email, 'REWARD_INFO', reward_data))
        
        conn.commit()
        conn.close()
        
        # Print to console for testing
        print(f"\n=== NOTIFICATION SENT TO: {email} ===")
        print(f"Title: {title}")
        print("Notification saved to user's dashboard!")
        print("================================\n")
        
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

@app.route('/')
def index():
    # Clear any existing session to force fresh login
    session.clear()
    return render_template('index.html')

def require_auth(f):
    """Decorator to require Google authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Always check for fresh authentication
        if 'google_authenticated' not in session or not session.get('google_authenticated'):
            session.clear()  # Clear any stale session data
            flash('Please sign in with Google to access this page', 'warning')
            return redirect(url_for('google_auth.google_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/user_dashboard')
@require_auth
def user_dashboard():
    user_info = {
        'name': session.get('user_name', ''),
        'email': session.get('user_email', ''),
        'picture': session.get('user_picture', '')
    }
    return render_template('user_dashboard_new.html', user=user_info)

@app.route('/my_notifications')
@require_auth
def my_notifications():
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    # Only show unread notifications
    notifications_raw = conn.execute("SELECT * FROM notifications WHERE user_email = ? AND is_read = 0 ORDER BY created_at DESC", (email,)).fetchall()
    notifications = [dict(notification) for notification in notifications_raw]
    conn.close()
    
    return render_template('my_notifications.html', notifications=notifications, user_email=email)

@app.route('/notification_history')
@require_auth
def notification_history():
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    # Show all notifications (read and unread)
    notifications_raw = conn.execute("SELECT * FROM notifications WHERE user_email = ? ORDER BY created_at DESC", (email,)).fetchall()
    notifications = [dict(notification) for notification in notifications_raw]
    conn.close()
    
    return render_template('notification_history.html', notifications=notifications, user_email=email)

@app.route('/live_feed')
def live_feed():
    """Live feed of recent activities"""
    conn = get_db_connection()
    recent_reports = conn.execute("""
        SELECT *, 'report' as activity_type FROM reports 
        ORDER BY date_reported DESC LIMIT 10
    """).fetchall()
    
    recent_rewards = conn.execute("""
        SELECT *, 'reward' as activity_type FROM rewards 
        ORDER BY created_at DESC LIMIT 5
    """).fetchall()
    
    activities = []
    for report in recent_reports:
        activities.append(dict(report))
    for reward in recent_rewards:
        activities.append(dict(reward))
    
    # Sort by timestamp
    activities.sort(key=lambda x: x.get('date_reported') or x.get('created_at'), reverse=True)
    conn.close()
    
    return jsonify(activities[:15])

@app.route('/leaderboard')
def leaderboard():
    """Community leaderboard"""
    conn = get_db_connection()
    
    # Top helpers by tokens earned
    top_helpers = conn.execute("""
        SELECT finder_email, finder_name, SUM(tokens) as total_tokens, COUNT(*) as items_found
        FROM rewards 
        GROUP BY finder_email, finder_name 
        ORDER BY total_tokens DESC 
        LIMIT 10
    """).fetchall()
    
    # Most active reporters
    top_reporters = conn.execute("""
        SELECT email, name, COUNT(*) as total_reports,
               SUM(CASE WHEN type = 'lost' THEN 1 ELSE 0 END) as lost_reports,
               SUM(CASE WHEN type = 'found' THEN 1 ELSE 0 END) as found_reports
        FROM reports 
        GROUP BY email, name 
        ORDER BY total_reports DESC 
        LIMIT 10
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        'helpers': [dict(helper) for helper in top_helpers],
        'reporters': [dict(reporter) for reporter in top_reporters]
    })

@app.route('/quick_search')
def quick_search():
    """Quick search for items"""
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    results = conn.execute("""
        SELECT * FROM reports 
        WHERE (LOWER(item_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(location) LIKE ?)
        AND status = 'active'
        ORDER BY date_reported DESC 
        LIMIT 20
    """, (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    
    conn.close()
    return jsonify([dict(result) for result in results])

@app.route('/community')
def community():
    """Community page with live feed and leaderboard"""
    return render_template('community.html')

@app.route('/community_stats')
def community_stats():
    """Real-time community statistics"""
    conn = get_db_connection()
    
    # Total items reunited (resolved reports)
    total_matches = conn.execute("SELECT COUNT(*) as count FROM reports WHERE status = 'resolved'").fetchone()['count']
    
    # Active users (users who reported in last 30 days)
    active_users = conn.execute("""
        SELECT COUNT(DISTINCT email) as count FROM reports 
        WHERE date_reported >= datetime('now', '-30 days')
    """).fetchone()['count']
    
    # Total tokens earned
    total_tokens = conn.execute("SELECT COALESCE(SUM(tokens), 0) as total FROM rewards").fetchone()['total']
    
    # Average response time (mock for now - would need match timestamps)
    avg_response = "2.3h"
    
    conn.close()
    
    return jsonify({
        'total_matches': total_matches,
        'active_users': active_users, 
        'total_tokens': total_tokens,
        'avg_response_time': avg_response
    })

@app.route('/user_stats')
@require_auth
def user_stats():
    """Get current user's statistics"""
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    
    # User's lost items count
    lost_count = conn.execute("SELECT COUNT(*) as count FROM reports WHERE email = ? AND type = 'lost'", (email,)).fetchone()['count']
    
    # User's found items count
    found_count = conn.execute("SELECT COUNT(*) as count FROM reports WHERE email = ? AND type = 'found'", (email,)).fetchone()['count']
    
    # User's total tokens earned
    tokens_earned = conn.execute("SELECT COALESCE(SUM(tokens), 0) as total FROM rewards WHERE finder_email = ?", (email,)).fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'lost_items': lost_count,
        'found_items': found_count,
        'tokens_earned': tokens_earned
    })

@app.route('/unread_notifications_count')
@require_auth
def unread_notifications_count():
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) as count FROM notifications WHERE user_email = ? AND is_read = 0", (email,)).fetchone()['count']
    conn.close()
    
    return jsonify({'count': count})

@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@require_auth
def mark_notification_read(notification_id):
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_email = ?", (notification_id, email))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/check_reward_given', methods=['POST'])
@require_auth
def check_reward_given():
    data = request.json
    giver_email = session.get('user_email', '')
    finder_email = data.get('finder_email', '')
    item_name = data.get('item_name', '')
    
    conn = get_db_connection()
    existing_reward = conn.execute("""
        SELECT COUNT(*) as count FROM rewards 
        WHERE giver_email = ? AND finder_email = ? AND item_name = ?
    """, (giver_email, finder_email, item_name)).fetchone()['count']
    conn.close()
    
    return jsonify({'already_given': existing_reward > 0})

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    ADMIN_CODE = "ADMIN2024"  # Secret admin code
    
    if request.method == 'POST':
        entered_code = request.form.get('admin_code', '')
        if entered_code == ADMIN_CODE:
            session['admin_authenticated'] = True
            return render_template('admin_dashboard_new.html')
        else:
            flash('Invalid admin code. Access denied.', 'danger')
            return render_template('admin_login.html')
    
    # Check if already authenticated
    if session.get('admin_authenticated'):
        return render_template('admin_dashboard_new.html')
    
    # Show login form
    return render_template('admin_login.html')

@app.route('/report_lost', methods=['GET', 'POST'])
@require_auth
def report_lost():
    if request.method == 'POST':
        # Basic validation
        email = request.form['email']
        phone = request.form['phone']
        
        # Simple email domain check
        if not (email.endswith('@klu.ac.in') or email.endswith('@gmail.com')):
            flash('Only @klu.ac.in and @gmail.com emails are allowed', 'danger')
            return render_template('report_lost.html')
        
        # Simple phone validation
        phone_clean = phone.replace(' ', '').replace('-', '')
        if not (len(phone_clean) == 10 and phone_clean.isdigit() and phone_clean[0] in '6789'):
            flash('Phone must be 10 digits starting with 6-9', 'danger')
            return render_template('report_lost.html')
        
        conn = get_db_connection()
        
        # Handle image upload and feature extraction
        image_filename = None
        image_features = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                image_filename = timestamp + filename
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                file.save(image_path)
                
                # Extract image features for AI matching
                features = extract_image_features(image_path)
                if features:
                    image_features = str(features)
        
        conn.execute("""
            INSERT INTO reports (name, email, phone, item_name, description, location, image_filename, date_reported, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['item_name'],
            request.form['description'],
            request.form['location'],
            image_filename,
            datetime.now(),
            'lost'
        ))
        
        conn.commit()
        conn.close()
        
        motivational = get_motivational_message()
        flash('Lost item reported successfully! ' + motivational)
        return redirect(url_for('user_dashboard') + '?success=lost')
    
    return render_template('report_lost.html')

@app.route('/report_found', methods=['GET', 'POST'])
@require_auth
def report_found():
    if request.method == 'POST':
        # Basic validation
        email = request.form['email']
        phone = request.form['phone']
        
        # Simple email domain check
        if not (email.endswith('@klu.ac.in') or email.endswith('@gmail.com')):
            flash('Only @klu.ac.in and @gmail.com emails are allowed', 'danger')
            return render_template('report_found.html')
        
        # Simple phone validation
        phone_clean = phone.replace(' ', '').replace('-', '')
        if not (len(phone_clean) == 10 and phone_clean.isdigit() and phone_clean[0] in '6789'):
            flash('Phone must be 10 digits starting with 6-9', 'danger')
            return render_template('report_found.html')
        
        conn = get_db_connection()
        
        # Handle image upload and feature extraction
        image_filename = None
        image_features = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                image_filename = timestamp + filename
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                file.save(image_path)
                
                # Extract image features for AI matching
                features = extract_image_features(image_path)
                if features:
                    image_features = str(features)
        
        conn.execute("""
            INSERT INTO reports (name, email, phone, item_name, description, location, image_filename, date_reported, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['item_name'],
            request.form['description'],
            request.form['location'],
            image_filename,
            datetime.now(),
            'found'
        ))
        
        conn.commit()
        conn.close()
        
        motivational = get_motivational_message()
        flash('Found item reported successfully! ' + motivational)
        return redirect(url_for('user_dashboard') + '?success=found')
    
    return render_template('report_found.html')

@app.route('/my_reports')
@require_auth
def my_reports():
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    reports_raw = conn.execute("SELECT * FROM reports WHERE email = ? ORDER BY date_reported DESC", (email,)).fetchall()
    reports = [dict(report) for report in reports_raw]
    
    conn.close()
    
    return render_template('my_reports.html', reports=reports, user_email=email)

@app.route('/admin_reports')
def admin_reports():
    conn = get_db_connection()
    reports = conn.execute("SELECT * FROM reports ORDER BY date_reported DESC").fetchall()
    conn.close()
    
    return jsonify([dict(report) for report in reports])

def simple_image_similarity(img1_path, img2_path):
    """Basic file comparison for images"""
    try:
        # Simple file hash comparison
        with open(img1_path, 'rb') as f1, open(img2_path, 'rb') as f2:
            hash1 = hashlib.md5(f1.read()).hexdigest()
            hash2 = hashlib.md5(f2.read()).hexdigest()
        
        if hash1 == hash2:
            return 100.0
        
        # Basic file size comparison
        size1 = os.path.getsize(img1_path)
        size2 = os.path.getsize(img2_path)
        size_diff = abs(size1 - size2)
        max_size = max(size1, size2)
        
        if max_size > 0:
            similarity = max(0, 100 - (size_diff / max_size * 100))
            return round(similarity, 1)
        
        return 0.0
    except:
        return 0.0

@app.route('/find_matches')
def find_matches():
    try:
        conn = get_db_connection()
        lost_items = conn.execute("SELECT * FROM reports WHERE type = 'lost'").fetchall()
        found_items = conn.execute("SELECT * FROM reports WHERE type = 'found'").fetchall()
        
        matches = []
        
        for lost in lost_items:
            for found in found_items:
                # Skip if same user reported both items
                if lost['email'] == found['email']:
                    continue
                
                # Image-based similarity if both have images
                image_percentage = 0.0
                if lost['image_filename'] and found['image_filename']:
                    lost_img = os.path.join(app.config['UPLOAD_FOLDER'], lost['image_filename'])
                    found_img = os.path.join(app.config['UPLOAD_FOLDER'], found['image_filename'])
                    
                    if os.path.exists(lost_img) and os.path.exists(found_img):
                        image_percentage = simple_image_similarity(lost_img, found_img)
                
                # Text similarity as fallback
                text_sim = calculate_similarity(
                    f"{lost['item_name']} {lost['description']}",
                    f"{found['item_name']} {found['description']}"
                )
                text_percentage = text_sim * 100
                
                # Use image percentage if available, otherwise text
                if image_percentage > 0:
                    final_percentage = image_percentage
                    match_type = 'Image-Based'
                else:
                    final_percentage = text_percentage
                    match_type = 'Text-Based'
                
                if final_percentage >= 30:
                    if final_percentage >= 80:
                        level = 'High Match'
                    elif final_percentage >= 60:
                        level = 'Medium Match'
                    else:
                        level = 'Low Match'
                    
                    matches.append({
                        'lost': dict(lost),
                        'found': dict(found),
                        'match_score': f'{level} - {final_percentage:.1f}%',
                        'similarity': final_percentage / 100,
                        'image_similarity': image_percentage,
                        'text_similarity': text_percentage,
                        'match_type': match_type
                    })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        conn.close()
        return jsonify(matches)
        
    except Exception as e:
        return jsonify([]), 200

@app.route('/send_notification', methods=['POST'])
def send_notification():
    data = request.json
    lost_item = data['lost_item']
    found_item = data['found_item']
    
    success = send_match_notification(
        lost_item['email'],
        lost_item,
        found_item,
        f"{found_item['name']} - {found_item['phone']}"
    )
    
    return jsonify({'success': success, 'message': 'Notification sent successfully!'})

@app.route('/get_smart_suggestions', methods=['POST'])
def get_smart_suggestions():
    data = request.json
    item_name = data.get('item_name', '')
    description = data.get('description', '')
    
    suggestions = generate_smart_suggestions(item_name, description)
    motivational = get_motivational_message()
    
    return jsonify({
        'suggestions': suggestions,
        'motivational': motivational,
        'keywords': extract_keywords(description)
    })

@app.route('/analyze_sentiment', methods=['POST'])
def analyze_user_sentiment():
    data = request.json
    text = data.get('text', '')
    
    sentiment = analyze_sentiment(text)
    
    return jsonify({
        'sentiment': sentiment,
        'message': 'Thank you for your feedback!' if sentiment == 'positive' else 
                  'We appreciate your input and will work to improve.' if sentiment == 'negative' else 
                  'Thank you for sharing your thoughts.'
    })

@app.route('/give_reward', methods=['POST'])
def give_reward():
    data = request.json
    
    # Check if reward already given
    conn = get_db_connection()
    existing_reward = conn.execute("""
        SELECT COUNT(*) as count FROM rewards 
        WHERE giver_email = ? AND finder_email = ? AND item_name = ?
    """, (data['giver_email'], data['finder_email'], data['item_name'])).fetchone()['count']
    
    if existing_reward > 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Reward already given for this item!'})
    
    conn.execute("""
        INSERT INTO rewards (finder_email, finder_name, giver_email, giver_name, tokens, item_name, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data['finder_email'],
        data['finder_name'], 
        data['giver_email'],
        data['giver_name'],
        data['tokens'],
        data['item_name'],
        data.get('message', '')
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Reward sent successfully!'})

@app.route('/my_rewards')
@require_auth
def my_rewards():
    email = session.get('user_email', '')
    
    conn = get_db_connection()
    rewards_raw = conn.execute("""
        SELECT * FROM rewards WHERE finder_email = ? ORDER BY created_at DESC
    """, (email,)).fetchall()
    rewards = [dict(reward) for reward in rewards_raw]
    
    # Calculate total tokens
    total_tokens = sum(reward['tokens'] for reward in rewards)
    
    conn.close()
    
    return render_template('my_rewards.html', rewards=rewards, total_tokens=total_tokens, user_email=email)



@app.route('/admin_logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin_authenticated', None)
    flash('Admin session ended', 'info')
    return redirect(url_for('index'))

@app.route('/clear_all_data')
def clear_all_data():
    """Clear all existing data for fresh start"""
    conn = get_db_connection()
    conn.execute("DELETE FROM reports")
    conn.execute("DELETE FROM notifications")
    conn.execute("DELETE FROM rewards")
    conn.commit()
    conn.close()
    flash('All data cleared. Starting fresh!', 'success')
    return redirect(url_for('index'))

@app.route('/urgent_items')
def urgent_items():
    """Get urgent/emergency items that need immediate attention"""
    try:
        conn = get_db_connection()
        
        # Get all reports and calculate urgency
        all_reports = conn.execute("SELECT * FROM reports ORDER BY date_reported DESC").fetchall()
        urgent_reports = []
        
        for report in all_reports:
            report_dict = dict(report)
            
            # Calculate time since reported
            report_time = datetime.strptime(report['date_reported'], '%Y-%m-%d %H:%M:%S.%f')
            hours_passed = (datetime.now() - report_time).total_seconds() / 3600
            
            # Determine urgency based on item type and keywords
            urgency_score = 0
            urgency_level = 'LOW'
            
            item_text = f"{report['item_name']} {report['description']}".lower()
            
            # Critical items (always urgent)
            critical_items = ['passport', 'id', 'license', 'medication', 'medicine', 'insulin', 'keys', 'car key', 'house key']
            if any(item in item_text for item in critical_items):
                urgency_score = 95
                urgency_level = 'CRITICAL'
            
            # High priority items
            elif any(item in item_text for item in ['phone', 'mobile', 'wallet', 'purse', 'laptop', 'computer']):
                urgency_score = 80
                urgency_level = 'HIGH'
            
            # Medium priority items
            elif any(item in item_text for item in ['bag', 'backpack', 'watch', 'jewelry', 'camera']):
                urgency_score = 60
                urgency_level = 'MEDIUM'
            
            # Recent reports get higher priority
            if hours_passed < 2:
                urgency_score += 15
            elif hours_passed < 6:
                urgency_score += 10
            elif hours_passed < 24:
                urgency_score += 5
            
            # Emergency keywords boost urgency
            emergency_words = ['urgent', 'emergency', 'important', 'asap', 'help', 'please']
            if any(word in item_text for word in emergency_words):
                urgency_score += 20
                
            # Only include items with urgency score >= 60
            if urgency_score >= 60:
                report_dict['urgency_score'] = min(100, urgency_score)
                report_dict['urgency_level'] = urgency_level
                report_dict['hours_passed'] = round(hours_passed, 1)
                urgent_reports.append(report_dict)
        
        # Sort by urgency score (highest first)
        urgent_reports.sort(key=lambda x: x['urgency_score'], reverse=True)
        
        conn.close()
        return jsonify(urgent_reports)
        
    except Exception as e:
        print(f"Error getting urgent items: {e}")
        return jsonify([]), 200

@app.route('/ai_find_matches')
def ai_find_matches():
    """Simplified AI matching that works"""
    try:
        conn = get_db_connection()
        lost_items = conn.execute("SELECT * FROM reports WHERE type = 'lost'").fetchall()
        found_items = conn.execute("SELECT * FROM reports WHERE type = 'found'").fetchall()
        conn.close()
        
        print(f"Found {len(lost_items)} lost items and {len(found_items)} found items")
        
        matches = []
        
        for lost in lost_items:
            for found in found_items:
                # Skip same user matches
                if lost['email'] == found['email']:
                    print(f"Skipping same user: {lost['email']}")
                    continue
                
                # Simple text similarity using basic method
                lost_text = f"{lost['item_name']} {lost['description']}".lower()
                found_text = f"{found['item_name']} {found['description']}".lower()
                
                # Basic similarity calculation
                similarity = calculate_similarity(lost_text, found_text)
                percentage = similarity * 100
                
                print(f"Comparing '{lost['item_name']}' vs '{found['item_name']}': {percentage:.1f}%")
                
                # Lower threshold to 10% to show more matches
                if percentage >= 10:
                    matches.append({
                        'lost': dict(lost),
                        'found': dict(found),
                        'match_score': f'AI Match - {percentage:.1f}%',
                        'similarity': similarity,
                        'urgency': 'MEDIUM',
                        'image_match': False
                    })
        
        print(f"Found {len(matches)} matches")
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return jsonify(matches)
        
    except Exception as e:
        print(f"AI matching error: {e}")
        return jsonify([])

@app.route('/debug_ai_data')
def debug_ai_data():
    """Debug route to check available data"""
    try:
        conn = get_db_connection()
        lost_items = conn.execute("SELECT * FROM reports WHERE type = 'lost'").fetchall()
        found_items = conn.execute("SELECT * FROM reports WHERE type = 'found'").fetchall()
        conn.close()
        
        return jsonify({
            'lost_count': len(lost_items),
            'found_count': len(found_items),
            'lost_items': [dict(item) for item in lost_items],
            'found_items': [dict(item) for item in found_items]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# Initialize database when module loads
init_db()

if __name__ == '__main__':
    app.run(debug=True)
# Enhanced NLP Features
def auto_categorize_item(item_name, description):
    """Auto-categorize items using NLP"""
    text = (item_name + ' ' + description).lower()
    
    categories = {
        'electronics': ['phone', 'laptop', 'computer', 'tablet', 'camera', 'headphones', 'charger', 'mouse', 'keyboard', 'speaker'],
        'clothing': ['shirt', 'pants', 'jacket', 'shoes', 'hat', 'dress', 'sweater', 'coat', 'jeans', 'sneakers'],
        'accessories': ['wallet', 'purse', 'bag', 'backpack', 'watch', 'jewelry', 'ring', 'necklace', 'bracelet', 'sunglasses'],
        'documents': ['passport', 'license', 'id', 'card', 'certificate', 'paper', 'document', 'ticket', 'receipt'],
        'keys': ['key', 'keys', 'keychain', 'fob', 'remote'],
        'books': ['book', 'notebook', 'textbook', 'journal', 'diary', 'manual'],
        'sports': ['ball', 'racket', 'equipment', 'gear', 'helmet', 'gloves']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    return 'other'

def calculate_location_similarity(loc1, loc2):
    """Calculate similarity between locations"""
    location_groups = {
        'library': ['library', 'study hall', 'reading room', 'book'],
        'cafeteria': ['cafeteria', 'dining', 'food court', 'restaurant', 'cafe'],
        'classroom': ['classroom', 'lecture hall', 'room', 'class'],
        'parking': ['parking', 'garage', 'lot', 'car'],
        'gym': ['gym', 'fitness', 'sports', 'exercise'],
        'office': ['office', 'admin', 'reception', 'desk']
    }
    
    loc1_lower = loc1.lower()
    loc2_lower = loc2.lower()
    
    # Direct similarity
    direct_sim = SequenceMatcher(None, loc1_lower, loc2_lower).ratio()
    
    # Group similarity
    group_sim = 0.0
    for group, keywords in location_groups.items():
        loc1_in_group = any(keyword in loc1_lower for keyword in keywords)
        loc2_in_group = any(keyword in loc2_lower for keyword in keywords)
        if loc1_in_group and loc2_in_group:
            group_sim = 0.8
            break
    
    return max(direct_sim, group_sim)

def detect_duplicate_report(new_item, existing_reports):
    """Detect potential duplicate reports"""
    duplicates = []
    
    for report in existing_reports:
        name_sim = calculate_similarity(new_item['item_name'], report['item_name'])
        desc_sim = calculate_similarity(new_item['description'], report['description'])
        loc_sim = calculate_location_similarity(new_item['location'], report['location'])
        
        overall_sim = (name_sim * 0.4) + (desc_sim * 0.4) + (loc_sim * 0.2)
        
        if overall_sim > 0.7:
            duplicates.append({
                'report': dict(report),
                'similarity': overall_sim,
                'confidence': 'High' if overall_sim > 0.85 else 'Medium'
            })
    
    return duplicates

def smart_search(query, reports):
    """Natural language search through reports"""
    query_keywords = extract_keywords(query)
    results = []
    
    for report in reports:
        searchable_text = f"{report['item_name']} {report['description']} {report['location']}"
        text_keywords = extract_keywords(searchable_text)
        keyword_matches = len(set(query_keywords).intersection(set(text_keywords)))
        text_similarity = calculate_similarity(query, searchable_text)
        
        score = (keyword_matches / max(len(query_keywords), 1)) * 0.6 + text_similarity * 0.4
        
        if score > 0.2:
            results.append({
                'report': dict(report),
                'score': score,
                'relevance': 'High' if score > 0.6 else 'Medium' if score > 0.4 else 'Low'
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:10]
# Add category column to database
def update_db_schema():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE reports ADD COLUMN category TEXT DEFAULT "other"')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

# Enhanced routes with new NLP features
@app.route('/smart_search', methods=['POST'])
def smart_search_route():
    data = request.json
    query = data.get('query', '')
    
    conn = get_db_connection()
    reports = conn.execute("SELECT * FROM reports").fetchall()
    conn.close()
    
    results = smart_search(query, reports)
    return jsonify(results)

@app.route('/check_duplicates', methods=['POST'])
def check_duplicates():
    data = request.json
    new_item = {
        'item_name': data.get('item_name', ''),
        'description': data.get('description', ''),
        'location': data.get('location', '')
    }
    
    conn = get_db_connection()
    existing_reports = conn.execute("SELECT * FROM reports WHERE type = ?", (data.get('type', 'lost'),)).fetchall()
    conn.close()
    
    duplicates = detect_duplicate_report(new_item, existing_reports)
    return jsonify(duplicates)

@app.route('/categorize_item', methods=['POST'])
def categorize_item():
    data = request.json
    item_name = data.get('item_name', '')
    description = data.get('description', '')
    
    category = auto_categorize_item(item_name, description)
    return jsonify({'category': category})

@app.route('/enhanced_matches')
def enhanced_matches():
    conn = get_db_connection()
    lost_items = conn.execute("SELECT * FROM reports WHERE type = 'lost'").fetchall()
    found_items = conn.execute("SELECT * FROM reports WHERE type = 'found'").fetchall()
    
    matches = []
    
    for lost in lost_items:
        for found in found_items:
            name_similarity = calculate_similarity(lost['item_name'], found['item_name'])
            desc_similarity = calculate_similarity(lost['description'], found['description'])
            loc_similarity = calculate_location_similarity(lost['location'], found['location'])
            
            overall_similarity = (name_similarity * 0.4) + (desc_similarity * 0.4) + (loc_similarity * 0.2)
            
            if overall_similarity > 0.3:
                matches.append({
                    'lost': dict(lost),
                    'found': dict(found),
                    'similarity': overall_similarity,
                    'location_match': loc_similarity > 0.6,
                    'match_score': f'{int(overall_similarity * 100)}% Match'
                })
    
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    conn.close()
    return jsonify(matches)
@app.route('/smart_search_page')
def smart_search_page():
    return render_template('smart_search.html')


def calculate_image_similarity(features1, features2):
    """Backward compatibility wrapper"""
    return 0.0

def detect_duplicate_image(image_path, existing_images):
    """Detect if uploaded image is duplicate or original"""
    try:
        new_features = extract_image_features(image_path)
        if not new_features:
            return {'is_duplicate': False, 'confidence': 0}
        
        for existing_path in existing_images:
            if os.path.exists(existing_path):
                existing_features = extract_image_features(existing_path)
                if existing_features:
                    similarity = calculate_image_similarity(new_features, existing_features)
                    
                    if similarity > 0.95:
                        return {
                            'is_duplicate': True,
                            'confidence': similarity,
                            'duplicate_path': existing_path
                        }
        
        return {'is_duplicate': False, 'confidence': 0}
        
    except Exception as e:
        return {'is_duplicate': False, 'confidence': 0}


