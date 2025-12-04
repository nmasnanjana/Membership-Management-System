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
  - Profile pictures
  - Guardian information
  - Active/Inactive status
- **QR Code Generation**: Automatic QR code generation for each member
- **Member Viewing & Editing**: View and update member information
- **Member Reports**: Generate detailed attendance reports per member

### 📅 Meeting Management
- **Meeting Creation**: Create and manage meetings with dates and fees
- **Meeting History**: View all past and upcoming meetings
- **Duplicate Prevention**: Validation to prevent duplicate meeting dates

### ✅ Attendance Tracking
- **Mark Attendance**: Record member attendance for meetings
- **Attendance Status**: Track both attendance and fee payment status
- **View by Date**: View attendance records for specific meeting dates
- **Edit Attendance**: Update attendance records after marking
- **Duplicate Prevention**: Prevent duplicate attendance entries

### 📊 Dashboard & Analytics
- **Statistics Overview**: 
  - Total members (active/passive)
  - Total meetings
  - Latest meeting attendance count
  - Annual attendance trends
- **Visual Charts**: Interactive attendance charts using Chart.js
- **Progress Indicators**: Visual representation of active vs passive members

### 📤 Data Export
- **Excel Export**: Export member details to Excel
- **Attendance Reports**: Export attendance reports by meeting or member
- **Formatted Data**: Well-structured Excel files with proper headers

### 🔐 User Management
- **Staff Registration**: Register staff members (superuser only)
- **Authentication**: Secure login/logout system
- **Password Management**: Change password and reset functionality
- **Profile Management**: Edit user profiles
- **Role-Based Access**: Different permissions for staff and superusers

### 🔍 QR Code Scanner
- **QR Code Scanning**: Scan member QR codes to quickly view member profiles
- **Quick Access**: Fast member lookup using QR codes

---

## 🛠️ Technology Stack

- **Backend Framework**: Django 4.2.5
- **Database**: SQLite (development) / PostgreSQL (production-ready)
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

This will create the database tables automatically (SQLite database will be created as `db.sqlite3`).

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

1. **Mark Attendance**:
   - Go to "Attendance Marking"
   - Select meeting date and member
   - Mark attendance status (Present/Absent)
   - Mark fee payment status (Paid/Not Paid)
   - Save

2. **View Attendance**:
   - Go to "Attendance" → Select a date
   - View all attendance records for that meeting
   - Edit or delete records (Superuser only)

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
   - Navigate to "QR Scan"
   - Enter member ID or scan QR code
   - View member profile instantly

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
├── db.sqlite3                     # SQLite database (auto-generated)
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
- Profile picture and QR code
- Active status
- Join date

### MeetingInfo
- `meeting_id` (Primary Key)
- `meeting_date`
- `meeting_fee`

### MemberAttendance
- `attendance_id` (Primary Key)
- `meeting_date` (ForeignKey to MeetingInfo)
- `member_id` (ForeignKey to Member)
- `attendance_status` (Present/Absent)
- `attendance_fee_status` (Paid/Not Paid)
- `attendance_created_at`

---

## 🔗 Key URLs

- `/` - Dashboard
- `/login/` - Staff login
- `/logout/` - Logout
- `/member/list/` - List all members
- `/member/register/` - Register new member
- `/member/view/<member_id>/` - View member details
- `/member/edit/<member_id>/` - Edit member
- `/meeting/list/` - List all meetings
- `/meeting/add/` - Add new meeting
- `/attendance/mark/` - Mark attendance
- `/attendance/date/all` - View all attendance dates
- `/qr_scan/` - QR code scanner

---

## 🔒 Security Features

- **Authentication**: Django's built-in authentication system
- **Authorization**: Role-based access control (Staff/Superuser)
- **CSRF Protection**: Enabled by default
- **Secure Settings**: Environment-based configuration
- **Input Validation**: Form validation and data sanitization
- **SQL Injection Protection**: Django ORM protection

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

- The system uses SQLite by default for development
- For production, consider using PostgreSQL or MySQL
- Media files are stored in the `media/` directory
- QR codes are automatically generated in PNG format
- Excel exports use the `.xlsx` format

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
