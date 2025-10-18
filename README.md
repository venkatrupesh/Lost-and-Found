<<<<<<< HEAD
# Lost & Found Website

A modern web application for managing lost and found items with separate user and admin dashboards.

## Features

### User Dashboard
- Report lost items with detailed descriptions
- Report found items to help others
- View personal reports and track status
- Clean, responsive UI design

### Admin Dashboard
- View all submitted reports (lost and found)
- Automatic matching system between lost and found items
- Email notifications for matches
- Comprehensive reporting system

## Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Email**: SMTP for notifications

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Email (Optional)
For email notifications, update the email settings in app.py:
```python
# Update these with your email credentials
server.login('your_email@gmail.com', 'your_app_password')
```

### 3. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## Usage

### For Users
1. Go to User Dashboard
2. Report lost or found items using the forms
3. View your reports by entering your email
4. Receive email notifications when matches are found

### For Admins
1. Go to Admin Dashboard
2. View all reports from all users
3. Use the matching system to find potential matches
4. Send notifications to users when matches are found

## File Structure
```
lost-and-found/
├── app.py                 # Main Flask application
├── database.sql           # Database schema
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── main.js       # JavaScript functionality
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── user_dashboard.html
    ├── admin_dashboard.html
    ├── report_lost.html
    ├── report_found.html
    └── my_reports.html
```

## Features Implemented

✅ Clean, modern UI design with gradient backgrounds
✅ Responsive design for mobile and desktop
✅ User dashboard with report forms
✅ Admin dashboard with all reports view
✅ Automatic matching system
✅ Email notifications for matches
✅ Form validation and error handling
✅ MySQL database integration
✅ Report tracking and status management

## Security Notes
- Remember to use environment variables for sensitive data
- Update email credentials before deployment
- Use HTTPS in production
- Implement proper authentication for admin dashboard
=======
# lost-and-found
never lost again 
>>>>>>> 1c6ca1e078e246ddf8ed72134707b30c158f180d
