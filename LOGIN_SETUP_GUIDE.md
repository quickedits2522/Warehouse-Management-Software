# 🔐 Login & Role-Based Access Control - Setup Guide

## Overview
The Warehouse Management System now includes a secure login page with role-based access control. Users must authenticate before accessing the system, and their permissions are determined by their assigned role.

## 🎨 Design
- **Theme**: Matches the existing blue/indigo color scheme
- **Style**: Modern, clean login interface with smooth animations
- **Responsive**: Works across different screen sizes

## 👥 User Roles & Permissions

### 1. **Admin** (Full Access)
   - ✅ Dashboard: All cards visible
   - ✅ Inventory Management
   - ✅ Shipments Management (View, Edit, Delete)
   - ✅ User Management (Add, Edit, Delete)
   - ✅ Database Management
   - ✅ Profit & Loss Reports
   - ✅ Settings
   - ✅ Add Orders

### 2. **Manager** (Management Access)
   - ✅ Dashboard: Inventory, Shipments, Users, Revenue cards
   - ✅ Inventory Management
   - ✅ Shipments Management (View, Edit)
   - ✅ User Management (Add, Edit, Delete)
   - ✅ Profit & Loss Reports
   - ✅ Settings
   - ✅ Add Orders
   - ❌ Database Management (Admin only)
   - ❌ Delete Shipments

### 3. **Sales** (Sales Operations)
   - ✅ Dashboard: Inventory, Shipments cards
   - ✅ Inventory Management (View)
   - ✅ Shipments (View only)
   - ✅ Add Orders
   - ❌ User Management
   - ❌ Database Management
   - ❌ Settings
   - ❌ Profit & Loss Reports

### 4. **Shipping** (Logistics)
   - ✅ Dashboard: Shipments card only
   - ✅ Shipments Management (View, Edit)
   - ❌ Inventory Management
   - ❌ User Management
   - ❌ Database Management
   - ❌ Settings
   - ❌ Add Orders
   - ❌ Profit & Loss Reports

## 🔑 Default Login Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Admin

### Test Accounts (Created for demonstration)
- **Manager**
  - Username: `manager`
  - Password: `manager123`
  
- **Sales**
  - Username: `sales`
  - Password: `sales123`
  
- **Shipping**
  - Username: `shipping`
  - Password: `shipping123`

## 📝 How to Add New Users

### Method 1: Direct Database Insert
```sql
INSERT INTO LOGIN (Username, Password, Role, UserID) 
VALUES ('newuser', SHA2('password123', 256), 'Admin', NULL);
```

### Method 2: Python Script
```python
import hashlib
import mysql.connector

# Connect to database
mycon = mysql.connector.connect(
    user="wmsuser",
    passwd="mysql",
    host="localhost",
    database="WMS"
)
mycursor = mycon.cursor()

# Hash password
password = hashlib.sha256("password123".encode()).hexdigest()

# Insert new user
mycursor.execute(
    "INSERT INTO LOGIN (Username, Password, Role, UserID) VALUES (%s, %s, %s, %s)",
    ("newuser", password, "Manager", None)
)
mycon.commit()
```

## 🗄️ Database Schema

### LOGIN Table
```sql
CREATE TABLE LOGIN (
    LoginID int PRIMARY KEY AUTO_INCREMENT,
    Username varchar(50) UNIQUE NOT NULL,
    Password varchar(255) NOT NULL,      -- SHA256 hashed
    Role ENUM('Admin', 'Manager', 'Sales', 'Shipping') NOT NULL,
    UserID int,                          -- Optional FK to USER table
    FOREIGN KEY (UserID) REFERENCES USER(UserID) ON DELETE CASCADE
);
```

## 🔒 Security Features

1. **Password Hashing**: All passwords are stored as SHA256 hashes
2. **Session Management**: Cookie-based sessions with Flask
3. **Route Protection**: Decorators enforce role-based access
4. **Automatic Logout**: Users can logout anytime
5. **Unauthorized Access Handling**: Redirects to dashboard with error message

## 🎯 Features Implemented

- ✅ Professional login page matching theme
- ✅ Username + Password authentication
- ✅ Four role types: Admin, Manager, Sales, Shipping
- ✅ Role-based dashboard visibility
- ✅ Route-level access control
- ✅ Session management
- ✅ Logout functionality
- ✅ User info displayed in header
- ✅ Flash messages for errors/success
- ✅ Default admin account auto-created

## 🚀 How to Start the Application

1. **Ensure MySQL is running**:
   ```bash
   sudo supervisorctl status mysql
   ```

2. **Start the Flask application**:
   ```bash
   sudo supervisorctl start flask_app
   ```

3. **Access the application**:
   - URL: `http://localhost:5000`
   - Login with admin credentials

4. **Check logs if needed**:
   ```bash
   tail -f /var/log/supervisor/flask_app.out.log
   tail -f /var/log/supervisor/flask_app.err.log
   ```

## 🔄 Changing Passwords

To change a user's password:

```sql
UPDATE LOGIN 
SET Password = SHA2('new_password', 256) 
WHERE Username = 'username';
```

## ⚠️ Important Notes

1. **First Time Setup**: On first run, the application automatically:
   - Creates all required database tables
   - Inserts a default admin account (username: admin, password: admin123)

2. **Password Security**: Always change the default admin password in production

3. **Database Connection**: The app uses:
   - User: `wmsuser`
   - Password: `mysql`
   - Database: `WMS`

4. **Session Duration**: Sessions persist until explicit logout or browser closure

## 🎨 UI Elements

### Login Page
- Blue gradient background matching main theme
- Centered login card with shadow
- Company logo display
- Username and password fields
- Animated hover effects
- Error/success message display

### Dashboard Header
- Company name/logo
- User info with role badge
- Add Order button
- Settings button
- Red logout button

## 📱 Responsive Design
The login page and dashboard are fully responsive and work on:
- Desktop (1920x1080 and above)
- Tablets (768px - 1024px)
- Mobile devices (320px - 767px)

## 🔍 Testing the System

Test each role by logging in with different credentials and verifying:
1. Correct dashboard cards are visible
2. Accessing allowed routes works
3. Accessing restricted routes redirects to dashboard
4. Logout works correctly
5. Login with wrong credentials shows error

---

**System Status**: ✅ Fully Operational
**Last Updated**: October 29, 2025
