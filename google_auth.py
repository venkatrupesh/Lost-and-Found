from flask import Blueprint, redirect, url_for, session, request, flash
import json
import requests
from urllib.parse import urlencode

google_auth = Blueprint('google_auth', __name__)

@google_auth.route('/login/google')
def google_login():
    """Redirect to Google OAuth"""
    from flask import current_app
    
    client_id = current_app.config.get('GOOGLE_OAUTH_CLIENT_ID')
    redirect_uri = 'http://127.0.0.1:5000/callback'
    
    google_auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode({
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'select_account'
    })
    
    return redirect(google_auth_url)

@google_auth.route('/callback')
def google_callback():
    """Handle Google OAuth callback"""
    from flask import current_app
    
    code = request.args.get('code')
    if not code:
        flash('Google authentication failed', 'danger')
        return redirect(url_for('index'))
    
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': current_app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
        'client_secret': current_app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://127.0.0.1:5000/callback'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, headers=headers)
        print(f"Token response status: {token_response.status_code}")
        print(f"Token response: {token_response.text}")
        
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            error_msg = token_json.get('error_description', 'Unknown error')
            flash(f'Failed to get access token: {error_msg}', 'danger')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Token exchange error: {e}")
        flash('Authentication failed - please try again', 'danger')
        return redirect(url_for('index'))
    
    # Get user info
    user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token_json['access_token']}"
    user_response = requests.get(user_info_url)
    user_info = user_response.json()
    
    # Validate email domain
    email = user_info.get('email', '')
    if not (email.endswith('@gmail.com') or email.endswith('@klu.ac.in')):
        flash('Only @gmail.com and @klu.ac.in accounts are allowed', 'danger')
        return redirect(url_for('index'))
    
    # Store user session (temporary - expires when browser closes)
    from flask import session
    session.permanent = False
    session['google_authenticated'] = True
    session['user_email'] = email
    session['user_name'] = user_info.get('name', '')
    session['user_picture'] = user_info.get('picture', '')
    
    flash(f'Successfully signed in as {email}', 'success')
    return redirect(url_for('user_dashboard'))

@google_auth.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('index'))