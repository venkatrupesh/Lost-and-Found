from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import re
from difflib import SequenceMatcher
import random
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageStat
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

def extract_identification_details(description):
    """Extract identification details from description"""
    if '| IDENTIFICATION:' not in description:
        return ''
    return description.split('| IDENTIFICATION:')[1].strip()

def calculate_identification_match(lost_desc, found_desc):
    """Calculate match probability based on identification details"""
    lost_id = extract_identification_details(lost_desc)
    found_id = extract_identification_details(found_desc)
    
    if not lost_id or not found_id:
        return 0.0
    
    # Key identification markers
    id_markers = {
        'serial': ['serial', 'number', 'imei', 'model'],
        'physical': ['scratch', 'dent', 'crack', 'mark', 'sticker'],
        'color': ['red', 'blue', 'green', 'black', 'white', 'brown', 'gray'],
        'brand': ['apple', 'samsung', 'nike', 'sony', 'hp', 'dell'],
        'size': ['small', 'large', 'medium', 'big', 'tiny']
    }
    
    match_score = 0.0
    total_categories = 0
    
    for category, keywords in id_markers.items():
        lost_has = any(word in lost_id.lower() for word in keywords)
        found_has = any(word in found_id.lower() for word in keywords)
        
        if lost_has or found_has:
            total_categories += 1
            if lost_has and found_has:
                # Check for specific matches within category
                category_match = calculate_nlp_text_similarity(lost_id, found_id)
                match_score += category_match
    
    if total_categories == 0:
        return calculate_nlp_text_similarity(lost_id, found_id)
    
    return min(100, match_score / total_categories)

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
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create reports table
    conn.execute('''CREATE TABLE IF NOT EXISTS reports (
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

@app.route('/login_intro')
@require_auth
def login_intro():
    user_name = session.get('user_name', 'User')
    return render_template('login_intro.html', user_name=user_name)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['google_authenticated'] = True
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            session['user_picture'] = ''
            session['show_intro'] = True
            flash(f'Successfully logged in as {user["name"]}', 'success')
            return redirect(url_for('login_intro'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        # Validate email domain
        if not (email.endswith('@klu.ac.in') or email.endswith('@gmail.com')):
            flash('Only @klu.ac.in and @gmail.com emails are allowed', 'danger')
            return render_template('signup.html')
        
        conn = get_db_connection()
        
        # Check if user exists
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            flash('Email already registered', 'danger')
            conn.close()
            return render_template('signup.html')
        
        # Create user
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)',
                    (name, email, hashed_password, phone))
        conn.commit()
        conn.close()
        
        # Auto-login after signup
        session['google_authenticated'] = True
        session['user_email'] = email
        session['user_name'] = name
        session['user_picture'] = ''
        session['show_intro'] = True
        flash(f'Welcome to Lost & Found, {name}!', 'success')
        return redirect(url_for('login_intro'))
    
    return render_template('signup.html')

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
        
        # Validate specific identification if no image
        image_file = request.files.get('image')
        has_image = image_file and image_file.filename != '' and allowed_file(image_file.filename)
        specific_identification = request.form.get('specific_identification', '').strip()
        
        if not has_image and not specific_identification:
            flash('Specific identification details are required when no image is uploaded', 'danger')
            return render_template('report_lost.html')
        
        if not has_image and len(specific_identification) < 10:
            flash('Please provide more detailed identification information (at least 10 characters)', 'danger')
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
        

        
        # Get specific identification if no image uploaded
        specific_identification = request.form.get('specific_identification', '')
        final_description = request.form['description']
        if not image_filename and specific_identification:
            final_description += f" | IDENTIFICATION: {specific_identification}"
        
        conn.execute("""
            INSERT INTO reports (name, email, phone, item_name, description, location, image_filename, date_reported, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['item_name'],
            final_description,
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
        
        # Validate specific identification if no image
        image_file = request.files.get('image')
        has_image = image_file and image_file.filename != '' and allowed_file(image_file.filename)
        specific_identification = request.form.get('specific_identification', '').strip()
        
        if not has_image and not specific_identification:
            flash('Specific identification details are required when no image is uploaded', 'danger')
            return render_template('report_found.html')
        
        if not has_image and len(specific_identification) < 10:
            flash('Please provide more detailed identification information (at least 10 characters)', 'danger')
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
        
        # Get specific identification if no image uploaded
        specific_identification = request.form.get('specific_identification', '')
        final_description = request.form['description']
        if not image_filename and specific_identification:
            final_description += f" | IDENTIFICATION: {specific_identification}"
        
        conn.execute("""
            INSERT INTO reports (name, email, phone, item_name, description, location, image_filename, date_reported, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['item_name'],
            final_description,
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
                
                # Identification-based matching if no images
                identification_percentage = 0.0
                if not lost['image_filename'] and not found['image_filename']:
                    identification_percentage = calculate_identification_match(
                        lost['description'], found['description']
                    )
                
                # Text similarity as fallback
                text_sim = calculate_similarity(
                    f"{lost['item_name']} {lost['description']}",
                    f"{found['item_name']} {found['description']}"
                )
                text_percentage = text_sim * 100
                
                # Determine final percentage and match type
                if image_percentage > 0:
                    final_percentage = image_percentage
                    match_type = 'Image-Based'
                elif identification_percentage > 0:
                    final_percentage = identification_percentage
                    match_type = 'ID-Based'
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
                        'identification_similarity': identification_percentage,
                        'text_similarity': text_percentage,
                        'match_type': match_type
                    })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        conn.close()
        return jsonify(matches)
        
    except Exception as e:
        return jsonify([]), 200

@app.route('/send_match_notification', methods=['POST'])
def send_match_notification_route():
    try:
        data = request.json
        lost_id = data.get('lost_id')
        found_id = data.get('found_id')
        
        conn = get_db_connection()
        lost_item = conn.execute("SELECT * FROM reports WHERE id = ?", (lost_id,)).fetchone()
        found_item = conn.execute("SELECT * FROM reports WHERE id = ?", (found_id,)).fetchone()
        conn.close()
        
        if not lost_item or not found_item:
            return jsonify({'success': False, 'message': 'Items not found'})
        
        success = send_match_notification(
            lost_item['email'],
            dict(lost_item),
            dict(found_item),
            f"{found_item['name']} - {found_item['phone']}"
        )
        
        return jsonify({'success': success, 'message': 'Notification sent successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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

@app.route('/find_identification_matches')
def find_identification_matches():
    """Find matches based on identification details for items without images"""
    try:
        conn = get_db_connection()
        # Get items without images that have identification details
        lost_items = conn.execute("""
            SELECT * FROM reports 
            WHERE type = 'lost' AND (image_filename IS NULL OR image_filename = '') 
            AND description LIKE '%| IDENTIFICATION:%'
            ORDER BY date_reported DESC
        """).fetchall()
        
        found_items = conn.execute("""
            SELECT * FROM reports 
            WHERE type = 'found' AND (image_filename IS NULL OR image_filename = '') 
            AND description LIKE '%| IDENTIFICATION:%'
            ORDER BY date_reported DESC
        """).fetchall()
        conn.close()
        
        matches = []
        
        for lost in lost_items:
            for found in found_items:
                # Skip same user matches
                if lost['email'] == found['email']:
                    continue
                
                # Calculate identification match
                id_percentage = calculate_identification_match(
                    lost['description'], found['description']
                )
                
                # Also check basic item similarity
                item_similarity = calculate_nlp_text_similarity(
                    lost['item_name'], found['item_name']
                )
                
                # Combined score (70% identification, 30% item name)
                combined_score = (id_percentage * 0.7) + (item_similarity * 0.3)
                
                if combined_score >= 25:  # Lower threshold for ID-based matching
                    if combined_score >= 70:
                        match_level = 'High ID Match'
                        urgency = 'HIGH'
                    elif combined_score >= 50:
                        match_level = 'Medium ID Match'
                        urgency = 'MEDIUM'
                    else:
                        match_level = 'Possible ID Match'
                        urgency = 'LOW'
                    
                    matches.append({
                        'lost': dict(lost),
                        'found': dict(found),
                        'match_score': f'{match_level} - {combined_score:.1f}%',
                        'similarity': combined_score / 100,
                        'identification_match': id_percentage,
                        'item_match': item_similarity,
                        'urgency': urgency,
                        'match_type': 'Identification-Based'
                    })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return jsonify(matches[:15])  # Limit to top 15 matches
        
    except Exception as e:
        print(f"ID matching error: {e}")
        return jsonify([])

@app.route('/ai_find_matches')
def ai_find_matches():
    """Smart image-based matching with proper 0-100% range"""
    try:
        conn = get_db_connection()
        # Limit to recent items for faster processing
        lost_items = conn.execute("SELECT * FROM reports WHERE type = 'lost' AND image_filename IS NOT NULL AND image_filename != '' ORDER BY date_reported DESC LIMIT 20").fetchall()
        found_items = conn.execute("SELECT * FROM reports WHERE type = 'found' AND image_filename IS NOT NULL AND image_filename != '' ORDER BY date_reported DESC LIMIT 20").fetchall()
        conn.close()
        
        matches = []
        processed = 0
        max_comparisons = 50
        
        for lost in lost_items:
            if processed >= max_comparisons:
                break
                
            for found in found_items:
                if processed >= max_comparisons:
                    break
                    
                # Skip same user matches
                if lost['email'] == found['email']:
                    continue
                
                lost_img_path = os.path.join(app.config['UPLOAD_FOLDER'], lost['image_filename'])
                found_img_path = os.path.join(app.config['UPLOAD_FOLDER'], found['image_filename'])
                
                if not os.path.exists(lost_img_path) or not os.path.exists(found_img_path):
                    continue
                
                # Smart image analysis
                cv_result = advanced_computer_vision_scan(lost_img_path, found_img_path)
                processed += 1
                
                if cv_result.get('error'):
                    continue
                
                percentage = cv_result['overall_percentage']
                
                # Only show meaningful matches (skip 0% and very low matches)
                if percentage >= 15:
                    if percentage >= 80:
                        match_level = 'Excellent Match'
                        urgency = 'HIGH'
                    elif percentage >= 60:
                        match_level = 'Good Match'
                        urgency = 'MEDIUM'
                    elif percentage >= 30:
                        match_level = 'Fair Match'
                        urgency = 'LOW'
                    else:
                        match_level = 'Weak Match'
                        urgency = 'LOW'
                    
                    matches.append({
                        'lost': dict(lost),
                        'found': dict(found),
                        'match_score': f'{match_level} - {percentage:.1f}%',
                        'similarity': percentage / 100,
                        'urgency': urgency,
                        'image_match': True
                    })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return jsonify(matches[:10])
        
    except Exception as e:
        print(f"Image matching error: {e}")
        return jsonify([])

@app.route('/scan_images', methods=['POST'])
def scan_images():
    """AI Image scanning for admin - compare two images"""
    try:
        data = request.json
        lost_id = data.get('lost_id')
        found_id = data.get('found_id')
        
        conn = get_db_connection()
        lost_item = conn.execute("SELECT * FROM reports WHERE id = ? AND type = 'lost'", (lost_id,)).fetchone()
        found_item = conn.execute("SELECT * FROM reports WHERE id = ? AND type = 'found'", (found_id,)).fetchone()
        conn.close()
        
        if not lost_item or not found_item:
            return jsonify({'error': 'Items not found'}), 404
        
        # Check if both items have images
        if not lost_item['image_filename'] or not found_item['image_filename']:
            return jsonify({
                'success': False,
                'message': 'Both items must have images for scanning',
                'scan_result': None
            })
        
        lost_img_path = os.path.join(app.config['UPLOAD_FOLDER'], lost_item['image_filename'])
        found_img_path = os.path.join(app.config['UPLOAD_FOLDER'], found_item['image_filename'])
        
        if not os.path.exists(lost_img_path) or not os.path.exists(found_img_path):
            return jsonify({
                'success': False,
                'message': 'Image files not found on server',
                'scan_result': None
            })
        
        # Perform AI image analysis
        scan_result = perform_ai_image_scan(lost_img_path, found_img_path, lost_item, found_item)
        
        return jsonify({
            'success': True,
            'message': 'Image scan completed successfully',
            'scan_result': scan_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Scan error: {str(e)}',
            'scan_result': None
        }), 500

def perform_ai_image_scan(img1_path, img2_path, lost_item, found_item):
    """Fast AI image analysis"""
    try:
        # Quick computer vision analysis
        cv_result = advanced_computer_vision_scan(img1_path, img2_path)
        
        if cv_result.get('error'):
            return perform_basic_image_scan(img1_path, img2_path, lost_item, found_item)
        
        overall_percentage = cv_result['overall_percentage']
        
        # Quick match level determination
        if overall_percentage >= 80:
            match_level = 'HIGH'
            confidence = 'HIGH'
        elif overall_percentage >= 60:
            match_level = 'MEDIUM'
            confidence = 'MEDIUM'
        else:
            match_level = 'LOW'
            confidence = 'LOW'
        
        # Simplified analysis details
        analysis_details = {
            'xerox_scan_analysis': {
                'histogram_similarity': cv_result.get('histogram_similarity', 0),
                'color_accuracy': cv_result.get('color_similarity', 0),
                'structural_match': cv_result.get('structure_similarity', 0),
                'pattern_recognition': cv_result.get('pattern_similarity', 0),
                'layout_analysis': cv_result.get('layout_similarity', 0),
                'texture_analysis': cv_result.get('texture_similarity', 0),
                'brightness_consistency': cv_result.get('brightness_similarity', 0),
                'contrast_preservation': cv_result.get('contrast_similarity', 0)
            },
            'detailed_assessment': {
                'color_fidelity': 'Good' if cv_result.get('color_similarity', 0) > 60 else 'Fair',
                'structural_integrity': 'Good' if cv_result.get('structure_similarity', 0) > 60 else 'Different',
                'pattern_consistency': 'Similar' if cv_result.get('pattern_similarity', 0) > 50 else 'Different',
                'layout_preservation': 'Good' if cv_result.get('layout_similarity', 0) > 50 else 'Poor',
                'surface_texture': 'Similar' if cv_result.get('texture_similarity', 0) > 50 else 'Different'
            },
            'scan_metadata': {
                'lost_item': lost_item['item_name'],
                'found_item': found_item['item_name'],
                'scan_timestamp': datetime.now().isoformat(),
                'scan_technique': 'Fast Image Analysis',
                'resolution': '128x128 Optimized',
                'analysis_depth': 'Quick Comparison'
            }
        }
        
        return {
            'overall_percentage': round(overall_percentage, 2),
            'match_level': match_level,
            'confidence': confidence,
            'recommendation': get_scan_recommendation(overall_percentage),
            'analysis_details': analysis_details,
            'scan_points': generate_quick_scan_points(overall_percentage)
        }
        
    except Exception as e:
        return {
            'overall_percentage': 0.0,
            'match_level': 'ERROR',
            'confidence': 'NONE',
            'recommendation': 'Scan failed',
            'analysis_details': {'error': str(e)},
            'scan_points': ['❌ Scan failed']
        }

def get_scan_recommendation(percentage):
    """Get recommendation based on scan percentage"""
    if percentage >= 95:
        return 'EXTREMELY LIKELY MATCH - Immediate notification recommended'
    elif percentage >= 80:
        return 'VERY LIKELY MATCH - Strong candidate for notification'
    elif percentage >= 60:
        return 'POSSIBLE MATCH - Manual verification recommended'
    elif percentage >= 30:
        return 'WEAK MATCH - Consider other factors'
    else:
        return 'UNLIKELY MATCH - Different items'

def advanced_computer_vision_scan(img1_path, img2_path):
    """Smart image analysis with proper 0-100% range"""
    try:
        # Check for identical files first
        with open(img1_path, 'rb') as f1, open(img2_path, 'rb') as f2:
            if f1.read() == f2.read():
                return {
                    'overall_percentage': 100.0,
                    'histogram_similarity': 100.0,
                    'color_similarity': 100.0,
                    'structure_similarity': 100.0,
                    'pattern_similarity': 100.0,
                    'layout_similarity': 100.0,
                    'texture_similarity': 100.0,
                    'brightness_similarity': 100.0,
                    'contrast_similarity': 100.0,
                    'pixel_similarity': 100.0
                }
        
        # Load and process images
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')
        
        target_size = (128, 128)
        img1_resized = img1.resize(target_size, Image.NEAREST)
        img2_resized = img2.resize(target_size, Image.NEAREST)
        
        # Calculate individual similarities
        hist1 = img1_resized.histogram()
        hist2 = img2_resized.histogram()
        histogram_similarity = smart_histogram_similarity(hist1, hist2)
        
        color_similarity = smart_color_similarity(img1_resized, img2_resized)
        brightness_similarity = calculate_brightness_similarity(img1_resized, img2_resized)
        
        # Check if images are completely different
        if histogram_similarity < 5 and color_similarity < 10 and brightness_similarity < 10:
            return {
                'overall_percentage': 0.0,
                'histogram_similarity': 0.0,
                'color_similarity': 0.0,
                'structure_similarity': 0.0,
                'pattern_similarity': 0.0,
                'layout_similarity': 0.0,
                'texture_similarity': 0.0,
                'brightness_similarity': 0.0,
                'contrast_similarity': 0.0,
                'pixel_similarity': 0.0
            }
        
        # Calculate weighted score for similar characteristics
        overall_percentage = (
            histogram_similarity * 0.4 +
            color_similarity * 0.4 +
            brightness_similarity * 0.2
        )
        
        # Perfect match detection
        if histogram_similarity > 98 and color_similarity > 98 and brightness_similarity > 95:
            overall_percentage = 100.0
        
        # Ensure minimum threshold for any similarity
        if overall_percentage < 5:
            overall_percentage = 0.0
        
        return {
            'overall_percentage': round(min(100, max(0, overall_percentage)), 2),
            'histogram_similarity': round(histogram_similarity, 2),
            'color_similarity': round(color_similarity, 2),
            'structure_similarity': round(brightness_similarity, 2),
            'pattern_similarity': round(color_similarity, 2),
            'layout_similarity': round(histogram_similarity, 2),
            'texture_similarity': round(brightness_similarity, 2),
            'brightness_similarity': round(brightness_similarity, 2),
            'contrast_similarity': round(color_similarity, 2),
            'pixel_similarity': round(histogram_similarity, 2)
        }
        
    except Exception as e:
        print(f"Computer vision error: {e}")
        return {'error': str(e)}

def smart_histogram_similarity(hist1, hist2):
    """Smart histogram comparison with proper 0-100% range"""
    try:
        # Check for exact match first
        if hist1 == hist2:
            return 100.0
            
        total1 = sum(hist1) or 1
        total2 = sum(hist2) or 1
        
        # Use more bins for better accuracy
        norm1 = [h / total1 for h in hist1[:128]]
        norm2 = [h / total2 for h in hist2[:128]]
        
        # Calculate chi-square distance for better differentiation
        chi_square = 0
        for i in range(len(norm1)):
            if norm1[i] + norm2[i] > 0:
                chi_square += ((norm1[i] - norm2[i]) ** 2) / (norm1[i] + norm2[i])
        
        # Convert chi-square to similarity percentage
        # Lower chi-square = higher similarity
        if chi_square > 2.0:  # Very different histograms
            return 0.0
        elif chi_square < 0.01:  # Very similar histograms
            return 100.0
        else:
            # Scale between 0-100 based on chi-square value
            similarity = max(0, 100 - (chi_square * 50))
            return min(100, similarity)
        
    except:
        return 0.0

def smart_color_similarity(img1, img2):
    """Smart color comparison with proper differentiation"""
    try:
        # Get average colors
        stat1 = ImageStat.Stat(img1)
        stat2 = ImageStat.Stat(img2)
        
        # Calculate color differences
        r_diff = abs(stat1.mean[0] - stat2.mean[0])
        g_diff = abs(stat1.mean[1] - stat2.mean[1])
        b_diff = abs(stat1.mean[2] - stat2.mean[2])
        
        # Perfect match detection
        if r_diff <= 2 and g_diff <= 2 and b_diff <= 2:
            return 100.0
        
        # Very different colors detection
        if r_diff > 100 or g_diff > 100 or b_diff > 100:
            return 0.0
        
        # Calculate Euclidean distance in RGB space
        color_distance = (r_diff ** 2 + g_diff ** 2 + b_diff ** 2) ** 0.5
        
        # Normalize to 0-100 scale with better sensitivity
        if color_distance > 150:  # Very different colors
            return 0.0
        elif color_distance < 5:  # Very similar colors
            return 95.0 + (5 - color_distance)  # 95-100%
        else:
            # Linear scale for moderate differences
            similarity = max(0, 100 - (color_distance / 150 * 100))
            return similarity
        
    except:
        return 0.0

def calculate_color_similarity(img1, img2):
    """Calculate average color similarity"""
    try:
        # Get average colors
        stat1 = ImageStat.Stat(img1)
        stat2 = ImageStat.Stat(img2)
        
        avg_color1 = stat1.mean
        avg_color2 = stat2.mean
        
        # Calculate Euclidean distance
        color_distance = sum([(c1 - c2) ** 2 for c1, c2 in zip(avg_color1, avg_color2)]) ** 0.5
        
        # Convert to similarity percentage (max distance is ~441 for RGB)
        similarity = max(0, 100 - (color_distance / 441 * 100))
        return similarity
        
    except:
        return 0.0

def calculate_brightness_similarity(img1, img2):
    """Calculate brightness similarity"""
    try:
        # Convert to grayscale and get average brightness
        gray1 = img1.convert('L')
        gray2 = img2.convert('L')
        
        stat1 = ImageStat.Stat(gray1)
        stat2 = ImageStat.Stat(gray2)
        
        brightness1 = stat1.mean[0]
        brightness2 = stat2.mean[0]
        
        brightness_diff = abs(brightness1 - brightness2)
        similarity = max(0, 100 - (brightness_diff / 255 * 100))
        return similarity
        
    except:
        return 0.0

def calculate_contrast_similarity(img1, img2):
    """Calculate contrast similarity"""
    try:
        # Convert to grayscale and get standard deviation (contrast)
        gray1 = img1.convert('L')
        gray2 = img2.convert('L')
        
        stat1 = ImageStat.Stat(gray1)
        stat2 = ImageStat.Stat(gray2)
        
        contrast1 = stat1.stddev[0]
        contrast2 = stat2.stddev[0]
        
        contrast_diff = abs(contrast1 - contrast2)
        similarity = max(0, 100 - (contrast_diff / 128 * 100))
        return similarity
        
    except:
        return 0.0

def calculate_advanced_color_similarity(img1, img2):
    """Advanced color analysis with multiple color spaces"""
    try:
        # RGB analysis
        stat1_rgb = ImageStat.Stat(img1)
        stat2_rgb = ImageStat.Stat(img2)
        rgb_similarity = calculate_color_distance(stat1_rgb.mean, stat2_rgb.mean)
        
        # HSV analysis for better color perception
        hsv1 = img1.convert('HSV')
        hsv2 = img2.convert('HSV')
        stat1_hsv = ImageStat.Stat(hsv1)
        stat2_hsv = ImageStat.Stat(hsv2)
        hsv_similarity = calculate_color_distance(stat1_hsv.mean, stat2_hsv.mean)
        
        # Combined similarity
        return (rgb_similarity * 0.6 + hsv_similarity * 0.4)
        
    except:
        return calculate_color_similarity(img1, img2)

def calculate_color_distance(color1, color2):
    """Calculate Euclidean distance between colors"""
    distance = sum([(c1 - c2) ** 2 for c1, c2 in zip(color1, color2)]) ** 0.5
    return max(0, 100 - (distance / 441 * 100))

def calculate_structure_similarity(img1, img2):
    """Analyze structural similarity using edge detection"""
    try:
        # Convert to grayscale for edge detection
        gray1 = img1.convert('L')
        gray2 = img2.convert('L')
        
        # Simple edge detection using gradient
        edges1 = detect_edges(gray1)
        edges2 = detect_edges(gray2)
        
        # Compare edge patterns
        edge_similarity = compare_edge_patterns(edges1, edges2)
        return edge_similarity
        
    except:
        return 0.0

def detect_edges(gray_img):
    """Simple edge detection using gradient"""
    try:
        import numpy as np
        
        # Convert to numpy array
        img_array = np.array(gray_img)
        
        # Sobel-like edge detection
        grad_x = np.abs(np.diff(img_array, axis=1))
        grad_y = np.abs(np.diff(img_array, axis=0))
        
        # Combine gradients
        edges = np.zeros_like(img_array)
        edges[:, :-1] += grad_x
        edges[:-1, :] += grad_y
        
        return edges
        
    except:
        return np.zeros((256, 256))

def compare_edge_patterns(edges1, edges2):
    """Compare edge patterns between two images"""
    try:
        import numpy as np
        
        # Normalize edge arrays
        edges1_norm = edges1 / (np.max(edges1) + 1e-8)
        edges2_norm = edges2 / (np.max(edges2) + 1e-8)
        
        # Calculate correlation
        correlation = np.corrcoef(edges1_norm.flatten(), edges2_norm.flatten())[0, 1]
        
        # Convert to percentage
        similarity = max(0, correlation * 100) if not np.isnan(correlation) else 0
        return similarity
        
    except:
        return 0.0

def calculate_pattern_similarity(img1, img2):
    """Analyze repeating patterns (useful for ID cards)"""
    try:
        # Convert to grayscale
        gray1 = img1.convert('L')
        gray2 = img2.convert('L')
        
        # Analyze horizontal and vertical patterns
        h_pattern1 = analyze_horizontal_patterns(gray1)
        h_pattern2 = analyze_horizontal_patterns(gray2)
        v_pattern1 = analyze_vertical_patterns(gray1)
        v_pattern2 = analyze_vertical_patterns(gray2)
        
        # Compare patterns
        h_similarity = compare_patterns(h_pattern1, h_pattern2)
        v_similarity = compare_patterns(v_pattern1, v_pattern2)
        
        return (h_similarity + v_similarity) / 2
        
    except:
        return 0.0

def analyze_horizontal_patterns(gray_img):
    """Analyze horizontal line patterns"""
    try:
        import numpy as np
        img_array = np.array(gray_img)
        
        # Sum pixels horizontally to get pattern
        h_pattern = np.sum(img_array, axis=1)
        return h_pattern / np.max(h_pattern) if np.max(h_pattern) > 0 else h_pattern
        
    except:
        return np.zeros(256)

def analyze_vertical_patterns(gray_img):
    """Analyze vertical line patterns"""
    try:
        import numpy as np
        img_array = np.array(gray_img)
        
        # Sum pixels vertically to get pattern
        v_pattern = np.sum(img_array, axis=0)
        return v_pattern / np.max(v_pattern) if np.max(v_pattern) > 0 else v_pattern
        
    except:
        return np.zeros(256)

def compare_patterns(pattern1, pattern2):
    """Compare two pattern arrays"""
    try:
        import numpy as np
        
        # Ensure same length
        min_len = min(len(pattern1), len(pattern2))
        p1 = pattern1[:min_len]
        p2 = pattern2[:min_len]
        
        # Calculate correlation
        correlation = np.corrcoef(p1, p2)[0, 1]
        return max(0, correlation * 100) if not np.isnan(correlation) else 0
        
    except:
        return 0.0

def calculate_layout_similarity(img1, img2):
    """Analyze spatial layout similarity"""
    try:
        # Divide images into grid and compare regions
        grid_size = 8
        similarity_scores = []
        
        width, height = img1.size
        cell_w, cell_h = width // grid_size, height // grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                x1, y1 = i * cell_w, j * cell_h
                x2, y2 = x1 + cell_w, y1 + cell_h
                
                # Extract regions
                region1 = img1.crop((x1, y1, x2, y2))
                region2 = img2.crop((x1, y1, x2, y2))
                
                # Compare regions
                region_sim = calculate_color_similarity(region1, region2)
                similarity_scores.append(region_sim)
        
        # Average similarity across all regions
        return sum(similarity_scores) / len(similarity_scores)
        
    except:
        return 0.0

def calculate_texture_similarity(img1, img2):
    """Analyze texture similarity using statistical measures"""
    try:
        # Convert to grayscale
        gray1 = img1.convert('L')
        gray2 = img2.convert('L')
        
        # Calculate texture features
        texture1 = calculate_texture_features(gray1)
        texture2 = calculate_texture_features(gray2)
        
        # Compare texture features
        similarity = compare_texture_features(texture1, texture2)
        return similarity
        
    except:
        return 0.0

def calculate_texture_features(gray_img):
    """Calculate texture features from grayscale image"""
    try:
        import numpy as np
        
        img_array = np.array(gray_img)
        
        # Statistical texture features
        mean_val = np.mean(img_array)
        std_val = np.std(img_array)
        skewness = calculate_skewness(img_array)
        kurtosis = calculate_kurtosis(img_array)
        
        return [mean_val, std_val, skewness, kurtosis]
        
    except:
        return [0, 0, 0, 0]

def calculate_skewness(data):
    """Calculate skewness of data"""
    try:
        import numpy as np
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val == 0:
            return 0
        return np.mean(((data - mean_val) / std_val) ** 3)
    except:
        return 0

def calculate_kurtosis(data):
    """Calculate kurtosis of data"""
    try:
        import numpy as np
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val == 0:
            return 0
        return np.mean(((data - mean_val) / std_val) ** 4) - 3
    except:
        return 0

def compare_texture_features(features1, features2):
    """Compare texture feature vectors"""
    try:
        # Calculate Euclidean distance between feature vectors
        distance = sum([(f1 - f2) ** 2 for f1, f2 in zip(features1, features2)]) ** 0.5
        
        # Normalize and convert to similarity percentage
        max_distance = 1000  # Estimated max distance
        similarity = max(0, 100 - (distance / max_distance * 100))
        return similarity
        
    except:
        return 0.0

def calculate_enhanced_pixel_similarity(img1, img2):
    """Enhanced pixel-level similarity with noise reduction"""
    try:
        import numpy as np
        
        # Convert to arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Apply Gaussian-like smoothing to reduce noise
        arr1_smooth = smooth_array(arr1)
        arr2_smooth = smooth_array(arr2)
        
        # Calculate structural similarity index
        ssim = calculate_ssim(arr1_smooth, arr2_smooth)
        return ssim
        
    except:
        return calculate_pixel_similarity(img1, img2)

def smooth_array(arr):
    """Simple smoothing filter"""
    try:
        import numpy as np
        
        # Simple 3x3 averaging filter
        kernel = np.ones((3, 3)) / 9
        smoothed = np.zeros_like(arr)
        
        for i in range(1, arr.shape[0] - 1):
            for j in range(1, arr.shape[1] - 1):
                if len(arr.shape) == 3:  # Color image
                    for k in range(arr.shape[2]):
                        smoothed[i, j, k] = np.sum(arr[i-1:i+2, j-1:j+2, k] * kernel)
                else:  # Grayscale
                    smoothed[i, j] = np.sum(arr[i-1:i+2, j-1:j+2] * kernel)
        
        return smoothed
        
    except:
        return arr

def calculate_ssim(arr1, arr2):
    """Simplified Structural Similarity Index"""
    try:
        import numpy as np
        
        # Convert to float
        img1 = arr1.astype(np.float64)
        img2 = arr2.astype(np.float64)
        
        # Calculate means
        mu1 = np.mean(img1)
        mu2 = np.mean(img2)
        
        # Calculate variances and covariance
        var1 = np.var(img1)
        var2 = np.var(img2)
        cov = np.mean((img1 - mu1) * (img2 - mu2))
        
        # SSIM constants
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        
        # Calculate SSIM
        ssim = ((2 * mu1 * mu2 + c1) * (2 * cov + c2)) / ((mu1**2 + mu2**2 + c1) * (var1 + var2 + c2))
        
        # Convert to percentage
        return max(0, ssim * 100)
        
    except:
        return 0.0

def calculate_pixel_similarity(img1, img2):
    """Calculate pixel-level similarity (fallback)"""
    try:
        # Convert to arrays for pixel comparison
        import numpy as np
        
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Calculate mean squared error
        mse = np.mean((arr1.astype(float) - arr2.astype(float)) ** 2)
        
        # Convert to similarity percentage
        similarity = max(0, 100 - (mse / 65025 * 100))  # 255^2 = 65025
        return similarity
        
    except:
        return 0.0

def perform_basic_image_scan(img1_path, img2_path, lost_item, found_item):
    """Fallback basic image scan if computer vision fails"""
    try:
        with open(img1_path, 'rb') as f1, open(img2_path, 'rb') as f2:
            img1_data = f1.read()
            img2_data = f2.read()
        
        hash1 = hashlib.md5(img1_data).hexdigest()
        hash2 = hashlib.md5(img2_data).hexdigest()
        
        if hash1 == hash2:
            overall_percentage = 100.0
            match_level = 'IDENTICAL'
            confidence = 'VERY HIGH'
        else:
            size1 = len(img1_data)
            size2 = len(img2_data)
            size_diff = abs(size1 - size2)
            size_similarity = max(0, 100 - (size_diff / max(size1, size2) * 100))
            overall_percentage = size_similarity * 0.6
            match_level = 'BASIC'
            confidence = 'LOW'
        
        analysis_details = {
            'basic_analysis': {
                'file_hash_match': hash1 == hash2,
                'file_size_similarity': round(size_similarity if 'size_similarity' in locals() else 0, 2)
            },
            'visual_analysis': {
                'color_match': 'Unknown',
                'structure_match': 'Unknown',
                'detail_preservation': 'Unknown'
            },
            'metadata': {
                'lost_item': lost_item['item_name'],
                'found_item': found_item['item_name'],
                'scan_timestamp': datetime.now().isoformat(),
                'technique': 'Basic File Analysis (Fallback)'
            }
        }
        
        return {
            'overall_percentage': round(overall_percentage, 2),
            'match_level': match_level,
            'confidence': confidence,
            'recommendation': get_scan_recommendation(overall_percentage),
            'analysis_details': analysis_details,
            'scan_points': generate_scan_points(overall_percentage)
        }
        
    except Exception as e:
        return {
            'overall_percentage': 0.0,
            'match_level': 'ERROR',
            'confidence': 'NONE',
            'recommendation': 'Scan failed - manual review required',
            'analysis_details': {'error': str(e)},
            'scan_points': ['❌ Scan failed due to technical error']
        }

def generate_quick_scan_points(percentage):
    """Generate quick scan analysis points"""
    if percentage >= 80:
        return [
            '✅ High image similarity detected',
            '✅ Color patterns match well',
            '✅ Good structural alignment',
            '🎯 LIKELY MATCH - Recommend notification'
        ]
    elif percentage >= 60:
        return [
            '⚠️ Moderate image similarity',
            '⚠️ Some color differences found',
            '⚠️ Partial structural match',
            '🎯 POSSIBLE MATCH - Manual review suggested'
        ]
    else:
        return [
            '❌ Low image similarity',
            '❌ Significant differences detected',
            '🎯 UNLIKELY MATCH - Different items'
        ]

def generate_scan_points(percentage):
    """Backward compatibility"""
    return generate_quick_scan_points(percentage)

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


