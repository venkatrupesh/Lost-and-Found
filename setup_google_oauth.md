# Google OAuth Setup Instructions

## Current Error: "Access blocked: smart classroom note generator's request is invalid"

### Problem:
Your OAuth credentials are configured for a different project/domain.

### Solution:

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Select Project**: "smart classroom note generator" or create new one

3. **OAuth Consent Screen**:
   - Go to APIs & Services → OAuth consent screen
   - Application name: "Lost & Found System"
   - Add test user: rushirupesh578@gmail.com
   - Authorized domains: localhost

4. **Credentials Configuration**:
   - Go to APIs & Services → Credentials
   - Click your OAuth 2.0 Client ID
   - Add Authorized redirect URIs:
     * http://localhost:5000/callback/google
     * http://127.0.0.1:5000/callback/google
   
   - Add Authorized JavaScript origins:
     * http://localhost:5000
     * http://127.0.0.1:5000

5. **Save Changes** and try again

### Your Current Credentials:
- Client ID: [Set in .env file]
- Client Secret: [Set in .env file]

### Test URL:
http://localhost:5000/login/google