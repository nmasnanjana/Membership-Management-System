# 📋 Membership Management System (MMS)

A comprehensive Django-based web application for managing members, meetings, and attendance tracking with QR code support and detailed reporting capabilities.

![Django](https://img.shields.io/badge/Django-4.2.5-green.svg)
![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

### 👥 Member Management
- **Member Registration**: Register new members with complete profile information
- **Member Profiles**: Store member details including:
  - Personal information (name, address, date of birth)
  - Contact details (phone number, account number)
  - Profile pictures (optional)
  - Guardian information
  - Active/Inactive status
  - Club roles (President, Secretary, Treasury, Vice roles, Committee Member)
- **Member Roles**: 
  - Assign roles to members (superuser only)
  - Unique role enforcement (only one person per main/sub role)
  - Role display with special symbols (crown, star, users icon)
  - Dashboard widgets showing members by role
- **QR Code Generation**: Automatic QR code generation for each member
- **Member Viewing & Editing**: View and update member information
- **Member Reports**: Generate detailed attendance reports per member
- **Automatic Deactivation**: Members missing 3 consecutive meetings are automatically deactivated

### 📅 Meeting Management
- **Meeting Creation**: Create and manage meetings with dates and fees
- **Meeting History**: View all past and upcoming meetings
- **Duplicate Prevention**: Validation to prevent duplicate meeting dates

### ✅ Attendance Tracking
- **Mark Attendance**: Record member attendance for meetings (single or bulk)
- **Bulk Attendance Marking**: Mark attendance for multiple members at once
- **Attendance Status**: Track both attendance and fee payment status
- **Fee Payment**: Members can pay fees even if absent (flexible payment system)
- **View by Date**: View attendance records for specific meeting dates
- **Edit Attendance**: Update attendance records after marking (superuser only)
- **Permission System**: Normal staff can only mark new attendance; only superusers can edit/delete
- **Auto-save**: Bulk marking auto-saves data in browser for recovery
- **Duplicate Prevention**: Prevent duplicate attendance entries
- **Quick Actions**: "Mark All Present" button for faster marking

### 📊 Dashboard & Analytics
- **Statistics Overview**: 
  - Total members (active/passive)
  - Total meetings
  - Latest meeting attendance count
  - Annual attendance trends
- **Finance Widget**: 
  - Total collected fees (all paid fees)
  - Amount to receive (attended but unpaid fees)
- **Member Roles Display**: 
  - Main roles (President, Secretary, Treasury)
  - Vice roles (Vice President, Vice Secretary, Vice Treasury)
  - Committee members
- **Visual Charts**: Interactive attendance charts using Chart.js
- **Progress Indicators**: Visual representation of active vs passive members
- **Automatic Member Deactivation**: Members missing 3 consecutive meetings are automatically deactivated

### 📤 Data Export
- **Excel Export**: Export member details to Excel
- **Attendance Reports**: Export attendance reports by meeting or member
- **Formatted Data**: Well-structured Excel files with proper headers

### 🔐 User Management & Security
- **Staff Registration**: Register staff members (superuser only)
- **Authentication**: Secure login/logout system
- **Session Management**: 6-hour session timeout with activity extension
- **Password Management**: Change password and reset functionality
- **Profile Management**: Edit user profiles
- **Role-Based Access Control (RBAC)**: 
  - Different permissions for staff and superusers
  - Normal staff: Can mark new attendance, cannot edit existing
  - Superusers: Full access including edit/delete operations
- **Site Security**: All pages require authentication; login screen is first thing users see
- **OWASP Top 10 Security**: 
  - Security headers middleware
  - Rate limiting for login attempts
  - Account lockout after failed attempts
  - Enhanced password validators
  - Secure session and CSRF cookies
  - File upload validation
  - Input sanitization and XSS/SQL injection detection
  - Security logging

### 🔍 QR Code Scanner
- **QR Code Scanning**: Scan member QR codes to quickly view member profiles
- **Optimized Performance**: 
  - Duplicate scan prevention (2-second cooldown)
  - Smart camera selection (prefers back camera on mobile)
  - Optimized scan period for faster detection
- **Error Handling**: Clear messages for camera permission issues
- **Manual Entry**: Option to enter member ID manually if scanning fails
- **Quick Access**: Fast member lookup using QR codes

---

## 🛠️ Technology Stack

- **Backend Framework**: Django 4.2.5
- **Database**: MySQL (configured via environment variables)
- **Frontend**: 
  - Bootstrap 5
  - Chart.js (for analytics)
  - DataTables (for data display)
  - SB Admin 2 (dashboard theme)
- **Python Libraries**:
  - `django-crispy-forms` - Form rendering
  - `crispy-bootstrap5` - Bootstrap 5 integration
  - `qrcode[pil]` - QR code generation
  - `Pillow` - Image processing
  - `openpyxl` - Excel file generation
  - `python-decouple` - Environment variable management
  - `PyMySQL` - MySQL database connector for Python
  - `PyMySQL` - MySQL database connector for Python

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Membership-Management-System
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**On Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Note**: For production, set `DEBUG=False` and use a secure `SECRET_KEY`.

### 6. Run Migrations

```bash
python manage.py migrate
```

**Important**: Before running migrations, make sure:
1. MySQL server is running
2. Database is created: `CREATE DATABASE membership_db;` (or your configured DB_NAME)
3. Database user has proper permissions

Then run migrations:
```bash
python manage.py migrate
```

This will create all database tables in your MySQL database.

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Collect Static Files (Optional)

```bash
python manage.py collectstatic
```

### 9. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

---

## 📖 Usage Guide

### Accessing the Application

1. **Login**: Navigate to `http://127.0.0.1:8000/login/` and login with your superuser credentials
2. **Dashboard**: After login, you'll be redirected to the dashboard with system statistics

### Managing Members

1. **Register Member**: 
   - Navigate to "Members" → "Register Member"
   - Fill in member details and upload profile picture
   - QR code will be automatically generated

2. **View Members**: 
   - Go to "Members" → "List Members"
   - Click on a member to view details

3. **Edit Member**: 
   - From member list, click edit
   - Update information and save

4. **Generate QR Code**: 
   - View member profile
   - QR code is automatically generated on registration
   - Can be regenerated if needed

### Managing Meetings

1. **Create Meeting** (Superuser only):
   - Navigate to "Meetings" → "Add Meeting"
   - Enter meeting date and fee
   - Save meeting

2. **View Meetings**: 
   - Go to "Meetings" → "List Meetings"
   - View all meetings with dates and fees

### Marking Attendance

1. **Single Attendance Marking**:
   - Go to "Attendance Marking"
   - Select meeting date and member
   - Mark attendance status (Present/Absent)
   - Mark fee payment status (Paid/Not Paid) - can pay even if absent
   - Save

2. **Bulk Attendance Marking**:
   - Go to "Bulk Mark Attendance"
   - Select meeting from dropdown
   - See all active members in a searchable table
   - Mark present/absent and fee status for multiple members
   - Use "Mark All Present" for quick action
   - Auto-save feature prevents data loss
   - Submit all at once

3. **View Attendance**:
   - Go to "Attendance" → Select a date
   - View all attendance records for that meeting
   - Edit or delete records (Superuser only)
   - Normal staff can only view, cannot edit existing records

4. **Permissions**:
   - **Normal Staff**: Can mark new attendance only
   - **Superusers**: Can mark, edit, and delete attendance

### Generating Reports

1. **Member Attendance Report**:
   - View member profile
   - Click "Attendance Report"
   - View detailed attendance history
   - Export to Excel if needed

2. **Export Data**:
   - Member details export (Superuser only)
   - Attendance report export by meeting
   - Member-specific attendance export

### QR Code Scanning

1. **Scan QR Code**:
   - Navigate to "QR Scan" (requires login)
   - Point camera at member's QR code
   - Scanner automatically detects and redirects to member profile
   - Or enter member ID manually
   - Optimized for mobile devices with back camera preference
   - Duplicate scan prevention (2-second cooldown)

---

## 📁 Project Structure

```
Membership-Management-System/
│
├── app/                          # Main application
│   ├── migrations/               # Database migrations
│   ├── static/                   # Static files (CSS, JS, images)
│   ├── templates/                # HTML templates
│   │   ├── attendance/          # Attendance templates
│   │   ├── member/               # Member templates
│   │   ├── meeting/              # Meeting templates
│   │   ├── staff/                # Staff templates
│   │   └── ...
│   ├── admin.py                  # Django admin configuration
│   ├── forms.py                  # Form definitions
│   ├── models.py                 # Database models
│   ├── urls.py                   # URL routing
│   ├── utils.py                  # Utility functions
│   ├── views.py                  # Main views
│   ├── views_attendance.py       # Attendance views
│   ├── views_member.py           # Member views
│   ├── views_meeting.py          # Meeting views
│   └── views_staff.py            # Staff views
│
├── mms/                          # Django project settings
│   ├── settings.py               # Project settings
│   ├── urls.py                   # Root URL configuration
│   └── wsgi.py                   # WSGI configuration
│
├── static/                       # Static files directory
├── media/                         # Media files (uploaded images)
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (create this)
└── README.md                     # This file
```

---

## 🗄️ Database Models

### Member
- `member_id` (Primary Key)
- Personal information (name, address, DOB)
- Contact details (phone, account number)
- Profile picture (optional) and QR code
- Active status (automatically deactivated after 3 missed meetings)
- Member role (President, Secretary, Treasury, Vice roles, Committee Member, or None)
- Join date
- Updated timestamp

### MeetingInfo
- `meeting_id` (Primary Key)
- `meeting_date`
- `meeting_fee`

### MemberAttendance
- `attendance_id` (Primary Key)
- `meeting_date` (ForeignKey to MeetingInfo)
- `member_id` (ForeignKey to Member)
- `attendance_status` (Present/Absent)
- `attendance_fee_status` (Paid/Not Paid) - Can be paid even if absent
- `attendance_created_at`
- `attendance_updated_at`
- Unique constraint on (meeting_date, member_id) to prevent duplicates

---

## 🔗 Key URLs

- `/` - Dashboard (requires login)
- `/login/` - Staff login
- `/logout/` - Logout
- `/member/list/` - List all members (requires login)
- `/member/register/` - Register new member (requires login)
- `/member/view/<member_id>/` - View member details (requires login)
- `/member/edit/<member_id>/` - Edit member (requires login)
- `/meeting/list/` - List all meetings (superuser only)
- `/meeting/add/` - Add new meeting (superuser only)
- `/attendance/mark/` - Mark attendance (single) (requires login)
- `/attendance/bulk/` - Bulk attendance marking (requires login)
- `/attendance/date/all` - View all attendance dates (requires login)
- `/attendance/date/<meeting_id>` - View attendance for specific meeting (requires login)
- `/qr_scan/` - QR code scanner (requires login)

---

## 🔒 Security Features

- **Authentication**: Django's built-in authentication system with 6-hour session timeout
- **Authorization**: Role-based access control (Staff/Superuser)
- **Site-Wide Protection**: All pages require authentication; login screen is first thing users see
- **CSRF Protection**: Enabled by default with secure cookie settings
- **Secure Settings**: Environment-based configuration
- **Input Validation**: Form validation and data sanitization
- **SQL Injection Protection**: Django ORM protection
- **XSS Protection**: Input sanitization and validation
- **File Upload Security**: 
  - File type validation (MIME type checking)
  - File size limits
  - Content scanning
  - Filename sanitization
- **Rate Limiting**: Login attempt rate limiting
- **Account Lockout**: Temporary lockout after multiple failed login attempts
- **Security Headers**: 
  - Content Security Policy (CSP)
  - X-Frame-Options
  - X-Content-Type-Options
  - HSTS (HTTP Strict Transport Security)
- **Security Logging**: All security events are logged
- **Session Security**: 
  - Secure cookies (HTTPS in production)
  - HttpOnly cookies
  - SameSite protection
  - Session expires on browser close

---

## 🧪 Testing

To run the Django test suite:

```bash
python manage.py test
```

---

## 🐛 Troubleshooting

### Common Issues

1. **Database errors**: Run `python manage.py migrate`
2. **Static files not loading**: Run `python manage.py collectstatic`
3. **Import errors**: Ensure virtual environment is activated and dependencies are installed
4. **Permission errors**: Check file permissions for `media/` directory

### Debug Mode

For development, ensure `DEBUG=True` in your `.env` file. For production, always set `DEBUG=False`.

---

## 📝 Notes

- The system uses MySQL database (configured via .env file)
- Database credentials are stored in `.env` file (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- Make sure MySQL server is running and database is created before running migrations
- Media files are stored in the `media/` directory
- QR codes are automatically generated in PNG format
- Excel exports use the `.xlsx` format
- Session timeout is set to 6 hours (can be adjusted in settings)
- Automatic member deactivation runs via Django signals (no cron jobs needed)
- Bulk attendance marking includes auto-save feature (data saved in browser)
- All pages require authentication - site is fully secured
- Normal staff can only mark new attendance; superusers have full access

---

## 👤 Author

**Anjana Narasinghe**

- Project started: 2023
- System: Membership Management System

---

## 📄 License

This project is open source and available for use and modification.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---

## 🙏 Acknowledgments

- Django Framework
- Bootstrap Team
- Chart.js
- All open-source contributors

---

## 📞 Support

For support, please open an issue in the repository or contact the project maintainer.

---

**Made with ❤️ using Django**
