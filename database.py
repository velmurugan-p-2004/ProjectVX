# database.py
import sqlite3
from flask import g
import os

DATABASE = 'vishnorex.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db(app):
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # --- Table creation ---
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            staff_id TEXT NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            gender TEXT,
            date_of_birth DATE,
            date_of_joining DATE,
            photo_data TEXT,
            shift_type TEXT DEFAULT 'general',
            basic_salary DECIMAL(10,2) DEFAULT 0.00,
            hra DECIMAL(10,2) DEFAULT 0.00,
            transport_allowance DECIMAL(10,2) DEFAULT 0.00,
            other_allowances DECIMAL(10,2) DEFAULT 0.00,
            pf_deduction DECIMAL(10,2) DEFAULT 0.00,
            esi_deduction DECIMAL(10,2) DEFAULT 0.00,
            professional_tax DECIMAL(10,2) DEFAULT 0.00,
            other_deductions DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, staff_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_in TIME,
            time_out TIME,
            overtime_in TIME,
            overtime_out TIME,
            work_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            status TEXT CHECK(status IN ('present', 'absent', 'late', 'leave', 'left_soon', 'on_duty')),
            notes TEXT,
            on_duty_type TEXT,
            on_duty_location TEXT,
            on_duty_purpose TEXT,
            late_duration_minutes INTEGER DEFAULT 0,
            early_departure_minutes INTEGER DEFAULT 0,
            shift_start_time TIME,
            shift_end_time TIME,
            regularization_requested BOOLEAN DEFAULT 0,
            regularization_status TEXT CHECK(regularization_status IN ('pending', 'approved', 'rejected')),
            regularization_reason TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(staff_id, date)
        )
        ''')

        # Create biometric verification log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            verification_type TEXT CHECK(verification_type IN ('check-in', 'check-out', 'overtime-in', 'overtime-out')) NOT NULL,
            verification_time DATETIME NOT NULL,
            device_ip TEXT,
            biometric_method TEXT CHECK(biometric_method IN ('fingerprint', 'face', 'card', 'password')),
            verification_status TEXT CHECK(verification_status IN ('success', 'failed', 'retry')) DEFAULT 'success',
            notes TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            leave_type TEXT CHECK(leave_type IN ('CL', 'SL', 'EL', 'ML')),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create department shift mappings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS department_shift_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            default_shift_type TEXT NOT NULL CHECK(default_shift_type IN ('general', 'morning', 'evening', 'night')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department)
        )
        ''')

        # Create on-duty applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS on_duty_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            duty_type TEXT CHECK(duty_type IN ('Official Work', 'Training', 'Meeting', 'Conference', 'Field Work', 'Other')) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            location TEXT,
            purpose TEXT NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            admin_remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create permission applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permission_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            permission_type TEXT CHECK(permission_type IN ('Personal Work', 'Medical', 'Emergency', 'Family Function', 'Other')) NOT NULL,
            permission_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_hours DECIMAL(4,2),
            reason TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            admin_remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create shift definitions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shift_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_type TEXT NOT NULL UNIQUE,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            grace_period_minutes INTEGER DEFAULT 10,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create attendance regularization requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_regularization_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            request_type TEXT CHECK(request_type IN ('late_arrival', 'early_departure')) NOT NULL,
            original_time TIME NOT NULL,
            expected_time TIME NOT NULL,
            duration_minutes INTEGER NOT NULL,
            staff_reason TEXT,
            admin_reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (attendance_id) REFERENCES attendance(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create comprehensive notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('admin', 'staff', 'company_admin')),
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info' CHECK(notification_type IN ('info', 'success', 'warning', 'danger')),
            action_url TEXT,
            is_read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create notification logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_type TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT,
            status TEXT NOT NULL CHECK(status IN ('sent', 'failed', 'pending')),
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # --- Safe column additions ---
        def ensure_column_exists(table, column_def, column_name):
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

        ensure_column_exists('schools', 'logo_url TEXT', 'logo_url')
        ensure_column_exists('schools', 'is_hidden BOOLEAN DEFAULT 0', 'is_hidden')
        ensure_column_exists('staff', 'photo_url TEXT', 'photo_url')
        ensure_column_exists('staff', 'password_hash TEXT', 'password_hash')
        ensure_column_exists('staff', 'shift_type TEXT DEFAULT "general"', 'shift_type')

        # Add new staff fields for enhanced staff management
        ensure_column_exists('staff', 'first_name TEXT', 'first_name')
        ensure_column_exists('staff', 'last_name TEXT', 'last_name')
        ensure_column_exists('staff', 'date_of_birth DATE', 'date_of_birth')
        ensure_column_exists('staff', 'date_of_joining DATE', 'date_of_joining')
        ensure_column_exists('staff', 'destination TEXT', 'destination')
        ensure_column_exists('staff', 'gender TEXT CHECK(gender IN ("Male", "Female", "Other"))', 'gender')

        # Enhanced attendance tracking columns
        ensure_column_exists('attendance', 'late_duration_minutes INTEGER DEFAULT 0', 'late_duration_minutes')
        ensure_column_exists('attendance', 'early_departure_minutes INTEGER DEFAULT 0', 'early_departure_minutes')
        ensure_column_exists('attendance', 'shift_start_time TIME', 'shift_start_time')
        ensure_column_exists('attendance', 'shift_end_time TIME', 'shift_end_time')
        ensure_column_exists('attendance', 'regularization_requested BOOLEAN DEFAULT 0', 'regularization_requested')
        ensure_column_exists('attendance', 'regularization_status TEXT CHECK(regularization_status IN ("pending", "approved", "rejected")) DEFAULT NULL', 'regularization_status')
        ensure_column_exists('attendance', 'regularization_reason TEXT', 'regularization_reason')

        # Create cloud-related tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            verification_type TEXT NOT NULL,
            punch_code INTEGER DEFAULT 0,
            status INTEGER DEFAULT 0,
            verify_method INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT DEFAULT 'ZK_BIOMETRIC',
            local_ip TEXT,
            local_port INTEGER DEFAULT 4370,
            cloud_enabled BOOLEAN DEFAULT TRUE,
            sync_interval INTEGER DEFAULT 30,
            last_sync TIMESTAMP,
            status TEXT DEFAULT 'unknown',
            organization_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            sync_type TEXT NOT NULL,
            records_count INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            sync_started_at TIMESTAMP,
            sync_completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            organization_id TEXT NOT NULL,
            permissions TEXT DEFAULT 'read',
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMP,
            last_used_at TIMESTAMP,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Initialize default shift definitions
        cursor.execute('SELECT COUNT(*) FROM shift_definitions')
        if cursor.fetchone()[0] == 0:
            # Insert default shift types as per requirements
            cursor.execute('''
                INSERT INTO shift_definitions (shift_type, start_time, end_time, grace_period_minutes, description)
                VALUES
                ('general', '09:20:00', '16:30:00', 10, 'General Shift: 9:20 AM - 4:30 PM'),
                ('overtime', '09:20:00', '17:30:00', 10, 'Overtime Shift: 9:20 AM - 5:30 PM')
            ''')

        db.commit()
