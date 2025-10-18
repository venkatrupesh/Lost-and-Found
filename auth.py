from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from validators import EmailValidator, PhoneValidator, OTPService
import sqlite3
from datetime import datetime, timedelta
import hashlib

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form['email']
        
        # Validate email
        email_valid, email_msg = EmailValidator.full_email_validation(email)
        if not email_valid:
            flash(f'Validation Error: {email_msg}', 'danger')
            return render_template('verify_email.html')
        
        # Generate and send OTP
        otp = OTPService.generate_otp()
        
        # Store OTP in session with expiry
        session['verification_otp'] = otp
        session['verification_email'] = email
        session['otp_expiry'] = (datetime.now() + timedelta(hours=1)).isoformat()
        
        # Send OTP email (this also verifies Gmail account exists)
        if OTPService.send_verification_email(email, otp):
            flash('Verification code sent to your email', 'success')
            return redirect(url_for('auth.confirm_otp'))
        else:
            if email.endswith('@gmail.com'):
                flash('Gmail account does not exist or cannot receive emails', 'danger')
            else:
                flash('Failed to send verification email', 'danger')
    
    return render_template('verify_email.html')

@auth_bp.route('/confirm_otp', methods=['GET', 'POST'])
def confirm_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        
        # Check if OTP session exists
        if 'verification_otp' not in session:
            flash('No verification in progress', 'danger')
            return redirect(url_for('auth.verify_email'))
        
        # Check OTP expiry
        expiry_time = datetime.fromisoformat(session['otp_expiry'])
        if datetime.now() > expiry_time:
            flash('Verification code expired', 'danger')
            session.pop('verification_otp', None)
            return redirect(url_for('auth.verify_email'))
        
        # Verify OTP
        if entered_otp == session['verification_otp']:
            session['email_verified'] = True
            session['verified_email'] = session['verification_email']
            flash('Email verified successfully!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid verification code', 'danger')
    
    return render_template('confirm_otp.html')

@auth_bp.route('/check_access')
def check_access():
    """Middleware to check if user has verified email"""
    if 'email_verified' not in session:
        flash('Please verify your email first', 'warning')
        return redirect(url_for('auth.verify_email'))
    return redirect(url_for('user_dashboard'))