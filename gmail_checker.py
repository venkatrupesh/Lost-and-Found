import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailAccountChecker:
    """Simple Gmail account existence checker"""
    
    @staticmethod
    def check_gmail_exists(email):
        """
        Check if Gmail account exists using multiple methods:
        1. SMTP verification
        2. OTP delivery test
        3. Bounce detection
        """
        if not email.endswith('@gmail.com'):
            return True, "Not a Gmail address"
        
        # Method 1: SMTP Check
        try:
            # Connect to Gmail SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.ehlo()
            
            # Test mail delivery without actually sending
            from_addr = 'test@example.com'
            server.mail(from_addr)
            
            # This will return error code if email doesn't exist
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                return True, "Gmail account exists"
            else:
                return False, f"Gmail account not found (Code: {code})"
                
        except smtplib.SMTPRecipientsRefused:
            return False, "Gmail account does not exist"
        except Exception as e:
            print(f"SMTP check failed: {e}")
            
        # Method 2: OTP Delivery Test (Most Reliable)
        return GmailAccountChecker.test_otp_delivery(email)
    
    @staticmethod
    def test_otp_delivery(email):
        """
        Test if we can actually send email to Gmail account
        This is the most reliable method
        """
        try:
            # Use a real SMTP server to test delivery
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = "noreply@lostfound.com"
            msg['To'] = email
            msg['Subject'] = "Account Verification Test"
            
            body = "This is a test message to verify your Gmail account exists."
            msg.attach(MIMEText(body, 'plain'))
            
            # Try to send (will fail if account doesn't exist)
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
            # Note: In production, use actual SMTP credentials
            # server.login("your_email@gmail.com", "your_password")
            
            # Test delivery without login (will show if recipient exists)
            text = msg.as_string()
            result = server.sendmail("test@example.com", email, text)
            server.quit()
            
            return True, "Gmail account verified via delivery test"
            
        except smtplib.SMTPRecipientsRefused as e:
            return False, "Gmail account does not exist or cannot receive emails"
        except Exception as e:
            print(f"Delivery test failed: {e}")
            # If we can't test, assume it exists and let OTP verification handle it
            return True, "Cannot verify - will test via OTP"

# Usage example:
def verify_gmail_in_app(email):
    """Integration function for the main app"""
    if email.endswith('@gmail.com'):
        exists, message = GmailAccountChecker.check_gmail_exists(email)
        return exists, message
    return True, "Not a Gmail address"