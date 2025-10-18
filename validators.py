import re
import dns.resolver
import smtplib
from email.mime.text import MIMEText
from flask import current_app
import random
import string
import requests
import json

class EmailValidator:
    @staticmethod
    def is_authorized_domain(email):
        """Check if email domain is authorized"""
        domain = email.split('@')[1].lower()
        authorized_domains = current_app.config.get('AUTHORIZED_EMAIL_DOMAINS', [])
        return domain in authorized_domains
    
    @staticmethod
    def verify_google_account(email):
        """Verify Gmail account using Google's password reset check"""
        if not email.endswith('@gmail.com'):
            return True
        
        try:
            # Method 1: Check Google account recovery page
            recovery_url = "https://accounts.google.com/signin/recovery"
            data = {'Email': email}
            
            response = requests.post(recovery_url, data=data, timeout=10, allow_redirects=False)
            
            # If account exists, Google redirects or shows specific response
            if response.status_code in [200, 302]:
                # Check response content for account existence indicators
                if 'doesn\'t match' in response.text or 'not found' in response.text:
                    return False
                return True
            
            # Method 2: Simple SMTP check for Gmail
            import smtplib
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.ehlo()
            
            # Try to initiate mail to the address
            code, message = server.rcpt(email)
            server.quit()
            
            # Gmail returns 250 for valid addresses
            return code == 250
            
        except Exception as e:
            print(f"Gmail verification error: {e}")
            # Fallback: Send OTP and let user verify
            return True
    
    @staticmethod
    def validate_email_format(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def check_mx_record(email):
        """Check if email domain has valid MX record"""
        try:
            domain = email.split('@')[1]
            dns.resolver.resolve(domain, 'MX')
            return True
        except:
            return False
    
    @staticmethod
    def verify_email_exists(email):
        """Verify if email actually exists (SMTP check)"""
        try:
            domain = email.split('@')[1]
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(mx_records[0].exchange)
            
            server = smtplib.SMTP(mx_record, 25, timeout=10)
            server.helo()
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            return code == 250
        except:
            return False
    
    @staticmethod
    def full_email_validation(email):
        """Complete email validation with Google account check"""
        if not EmailValidator.validate_email_format(email):
            return False, "Invalid email format"
        
        if not EmailValidator.is_authorized_domain(email):
            return False, "Only @klu.ac.in and @gmail.com emails allowed"
        
        if not EmailValidator.check_mx_record(email):
            return False, "Email domain does not exist"
        
        # Gmail verification through OTP (most reliable method)
        if email.endswith('@gmail.com'):
            # For Gmail, we verify by sending OTP - if it bounces, account doesn't exist
            return True, "Gmail will be verified via OTP"
        else:
            if not EmailValidator.verify_email_exists(email):
                return False, "Email address does not exist"
        
        return True, "Email is valid"

class PhoneValidator:
    @staticmethod
    def validate_indian_mobile(phone):
        """Validate Indian mobile number (10 digits, starts with 6-9)"""
        phone = re.sub(r'[^\d]', '', phone)  # Remove non-digits
        pattern = current_app.config.get('PHONE_REGEX', r'^[6-9]\d{9}$')
        
        if not re.match(pattern, phone):
            return False, "Invalid mobile number. Must be 10 digits starting with 6-9"
        
        return True, "Valid mobile number"

class OTPService:
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def send_verification_email(email, otp):
        """Send OTP via email"""
        try:
            from flask_mail import Message
            from extensions import mail
            
            msg = Message(
                subject='Email Verification - Lost & Found',
                recipients=[email],
                body=f'''
Your verification code is: {otp}

This code will expire in 1 hour.

If you didn't request this verification, please ignore this email.

Best regards,
Lost & Found Team
                '''
            )
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Email sending error: {e}")
            return False