def check_gmail_account_exists(email):
    """
    Simple method: Send OTP email and check if it delivers successfully
    If Gmail account doesn't exist, email will bounce back
    """
    
    if not email.endswith('@gmail.com'):
        return True  # Not Gmail, skip check
    
    try:
        # Try to send OTP email
        from validators import OTPService
        otp = OTPService.generate_otp()
        
        # If this succeeds, Gmail account exists
        # If this fails, Gmail account doesn't exist
        success = OTPService.send_verification_email(email, otp)
        
        if success:
            return True, "Gmail account exists - OTP sent successfully"
        else:
            return False, "Gmail account does not exist - email bounced"
            
    except Exception as e:
        return False, f"Gmail verification failed: {str(e)}"

# How it works in the website:
# 1. User enters: john123@gmail.com
# 2. System tries to send OTP email
# 3. If Gmail account exists → Email delivers → User gets OTP
# 4. If Gmail account doesn't exist → Email bounces → Error message shown
# 5. Only users who receive OTP can proceed