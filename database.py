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
            status TEXT CHECK(status IN ('present', 'absent', 'late', 'leave', 'left_soon', 'on_duty', 'holiday')),
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

        # Create holidays table for comprehensive holiday management
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            holiday_name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            holiday_type TEXT CHECK(holiday_type IN ('institution_wide', 'department_specific')) NOT NULL DEFAULT 'institution_wide',
            description TEXT,
            departments TEXT,  -- JSON array of department names for department-specific holidays
            is_recurring BOOLEAN DEFAULT 0,
            recurring_type TEXT CHECK(recurring_type IN ('yearly', 'monthly', 'weekly')),
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (created_by) REFERENCES admins(id)
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


def get_institution_timings():
    """
    Get institution-wide check-in and check-out times from database.
    Returns dynamic timings if set, otherwise returns default times.
    
    Returns:
        dict: {
            'checkin_time': datetime.time object,
            'checkout_time': datetime.time object,
            'is_custom': bool (True if custom timings are set)
        }
    """
    import datetime
    
    try:
        db = get_db()
        
        # Check if institution_settings table exists
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='institution_settings'
        """)
        
        if not cursor.fetchone():
            # Return default timings if table doesn't exist
            return {
                'checkin_time': datetime.time(9, 0),   # 9:00 AM
                'checkout_time': datetime.time(17, 0), # 5:00 PM
                'is_custom': False
            }
        
        # Fetch current institution timings
        cursor = db.execute("""
            SELECT setting_name, setting_value 
            FROM institution_settings 
            WHERE setting_name IN ('checkin_time', 'checkout_time')
        """)
        
        settings = dict(cursor.fetchall())
        
        if not settings or len(settings) < 2:
            # Return default timings if no custom settings found
            return {
                'checkin_time': datetime.time(9, 0),   # 9:00 AM
                'checkout_time': datetime.time(17, 0), # 5:00 PM
                'is_custom': False
            }
        
        # Parse time strings and return as time objects
        checkin_str = settings.get('checkin_time', '09:00')
        checkout_str = settings.get('checkout_time', '17:00')
        
        # Convert string to time object (format: HH:MM)
        checkin_time = datetime.datetime.strptime(checkin_str, '%H:%M').time()
        checkout_time = datetime.datetime.strptime(checkout_str, '%H:%M').time()
        
        return {
            'checkin_time': checkin_time,
            'checkout_time': checkout_time,
            'is_custom': True
        }
        
    except Exception as e:
        print(f"Error getting institution timings: {e}")
        # Return default timings on error
        return {
            'checkin_time': datetime.time(9, 0),   # 9:00 AM
            'checkout_time': datetime.time(17, 0), # 5:00 PM
            'is_custom': False
        }


def calculate_attendance_status(check_time, verification_type='check-in', grace_minutes=10, date_obj=None, department=None):
    """
    Calculate attendance status based on institution timings, considering holidays.

    Args:
        check_time (datetime.time): Time when staff checked in/out
        verification_type (str): 'check-in' or 'check-out'
        grace_minutes (int): Grace period in minutes for late arrival
        date_obj (datetime.date, optional): Date to check for holidays
        department (str, optional): Department for department-specific holidays

    Returns:
        str: Attendance status ('present', 'late', 'early_departure', 'holiday')
    """
    import datetime

    # Check if the date is a holiday
    if date_obj is None:
        date_obj = datetime.date.today()

    if is_holiday(date_obj, department):
        return 'holiday'

    timings = get_institution_timings()

    if verification_type == 'check-in':
        # Calculate grace period cutoff
        checkin_dt = datetime.datetime.combine(datetime.date.today(), timings['checkin_time'])
        grace_cutoff = checkin_dt + datetime.timedelta(minutes=grace_minutes)
        grace_cutoff_time = grace_cutoff.time()

        return 'late' if check_time > grace_cutoff_time else 'present'

    elif verification_type == 'check-out':
        # For check-out, consider early departure
        return 'early_departure' if check_time < timings['checkout_time'] else 'present'

    else:
        return 'present'


def calculate_standard_working_hours_per_month():
    """
    Calculate standard working hours per month based on institution timing configuration.

    Returns:
        dict: {
            'daily_hours': float,
            'monthly_hours': float,
            'working_days_per_month': int
        }
    """
    import datetime
    import calendar

    try:
        # Get institution timings
        timings = get_institution_timings()
        checkin_time = timings['checkin_time']
        checkout_time = timings['checkout_time']

        # Calculate daily working hours
        checkin_dt = datetime.datetime.combine(datetime.date.today(), checkin_time)
        checkout_dt = datetime.datetime.combine(datetime.date.today(), checkout_time)

        # Handle overnight shifts (if checkout is before checkin)
        if checkout_dt < checkin_dt:
            checkout_dt += datetime.timedelta(days=1)

        daily_hours = (checkout_dt - checkin_dt).total_seconds() / 3600

        # Calculate working days per month (excluding Sundays and holidays)
        # Use current month as reference
        now = datetime.datetime.now()
        total_days = calendar.monthrange(now.year, now.month)[1]
        working_days = 0

        for day in range(1, total_days + 1):
            date_obj = datetime.date(now.year, now.month, day)
            # Exclude Sundays (weekday 6) and holidays
            if date_obj.weekday() != 6 and not is_holiday(date_obj):
                working_days += 1

        monthly_hours = daily_hours * working_days

        return {
            'daily_hours': daily_hours,
            'monthly_hours': monthly_hours,
            'working_days_per_month': working_days
        }

    except Exception as e:
        print(f"Error calculating standard working hours: {e}")
        # Return default values (8 hours/day, 26 working days/month)
        return {
            'daily_hours': 8.0,
            'monthly_hours': 208.0,  # 8 * 26
            'working_days_per_month': 26
        }


def calculate_hourly_rate(base_monthly_salary):
    """
    Calculate hourly rate from base monthly salary using institution timing configuration.

    Args:
        base_monthly_salary (float): Base monthly salary amount

    Returns:
        dict: {
            'hourly_rate': float,
            'daily_rate': float,
            'standard_monthly_hours': float,
            'standard_daily_hours': float
        }
    """
    try:
        base_salary = float(base_monthly_salary)
        if base_salary <= 0:
            return {
                'hourly_rate': 0.0,
                'daily_rate': 0.0,
                'standard_monthly_hours': 0.0,
                'standard_daily_hours': 0.0
            }

        # Get standard working hours
        working_hours = calculate_standard_working_hours_per_month()

        # Calculate rates
        hourly_rate = base_salary / working_hours['monthly_hours'] if working_hours['monthly_hours'] > 0 else 0
        daily_rate = base_salary / working_hours['working_days_per_month'] if working_hours['working_days_per_month'] > 0 else 0

        return {
            'hourly_rate': round(hourly_rate, 2),
            'daily_rate': round(daily_rate, 2),
            'standard_monthly_hours': working_hours['monthly_hours'],
            'standard_daily_hours': working_hours['daily_hours']
        }

    except Exception as e:
        print(f"Error calculating hourly rate: {e}")
        return {
            'hourly_rate': 0.0,
            'daily_rate': 0.0,
            'standard_monthly_hours': 0.0,
            'standard_daily_hours': 0.0
        }


def is_holiday(date_obj, department=None, school_id=None):
    """
    Check if a given date is a holiday.

    Args:
        date_obj (datetime.date): Date to check
        department (str, optional): Department name for department-specific holidays
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        bool: True if the date is a holiday, False otherwise
    """
    import json
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return False

        db = get_db()

        # Check for institution-wide holidays
        institution_holidays = db.execute('''
            SELECT * FROM holidays
            WHERE school_id = ?
            AND holiday_type = 'institution_wide'
            AND is_active = 1
            AND ? BETWEEN start_date AND end_date
        ''', (school_id, date_obj.isoformat())).fetchall()

        if institution_holidays:
            return True

        # Check for department-specific holidays if department is provided
        if department:
            dept_holidays = db.execute('''
                SELECT * FROM holidays
                WHERE school_id = ?
                AND holiday_type = 'department_specific'
                AND is_active = 1
                AND ? BETWEEN start_date AND end_date
            ''', (school_id, date_obj.isoformat())).fetchall()

            for holiday in dept_holidays:
                if holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            return True
                    except (json.JSONDecodeError, TypeError):
                        continue

        return False

    except Exception as e:
        print(f"Error checking holiday status: {e}")
        return False


def get_holidays(school_id=None, start_date=None, end_date=None, department=None):
    """
    Get holidays for a school within a date range.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        department (str, optional): Filter by department for department-specific holidays

    Returns:
        list: List of holiday records
    """
    import json
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return []

        db = get_db()

        # Build query conditions
        conditions = ['school_id = ?', 'is_active = 1']
        params = [school_id]

        if start_date:
            conditions.append('end_date >= ?')
            params.append(start_date)

        if end_date:
            conditions.append('start_date <= ?')
            params.append(end_date)

        query = f'''
            SELECT * FROM holidays
            WHERE {' AND '.join(conditions)}
            ORDER BY start_date ASC
        '''

        holidays = db.execute(query, params).fetchall()

        # Filter department-specific holidays if department is specified
        if department:
            filtered_holidays = []
            for holiday in holidays:
                if holiday['holiday_type'] == 'institution_wide':
                    filtered_holidays.append(holiday)
                elif holiday['holiday_type'] == 'department_specific' and holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            filtered_holidays.append(holiday)
                    except (json.JSONDecodeError, TypeError):
                        continue
            return filtered_holidays

        return holidays

    except Exception as e:
        print(f"Error getting holidays: {e}")
        return []


def create_holiday(holiday_data):
    """
    Create a new holiday.

    Args:
        holiday_data (dict): Holiday information including name, dates, type, etc.

    Returns:
        dict: Result with success status and holiday_id or error message
    """
    import json
    from flask import session, has_request_context

    try:
        # Handle session data - use provided values or get from session
        if 'school_id' in holiday_data:
            school_id = holiday_data['school_id']
        elif has_request_context():
            school_id = session.get('school_id')
        else:
            return {'success': False, 'message': 'School ID required'}

        if 'created_by' in holiday_data:
            created_by = holiday_data['created_by']
        elif has_request_context():
            created_by = session.get('user_id')
        else:
            created_by = 1  # Default for testing

        if not school_id:
            return {'success': False, 'message': 'Invalid session or school ID'}

        db = get_db()

        # Validate required fields
        required_fields = ['holiday_name', 'start_date', 'end_date', 'holiday_type']
        for field in required_fields:
            if not holiday_data.get(field):
                return {'success': False, 'error': f'Missing required field: {field}'}

        # Prepare departments JSON
        departments_json = None
        if holiday_data.get('departments') and holiday_data['holiday_type'] == 'department_specific':
            departments_json = json.dumps(holiday_data['departments'])

        # Insert holiday
        cursor = db.execute('''
            INSERT INTO holidays (
                school_id, holiday_name, start_date, end_date, holiday_type,
                description, departments, is_recurring, recurring_type, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            school_id,
            holiday_data['holiday_name'],
            holiday_data['start_date'],
            holiday_data['end_date'],
            holiday_data['holiday_type'],
            holiday_data.get('description', ''),
            departments_json,
            holiday_data.get('is_recurring', 0),
            holiday_data.get('recurring_type'),
            created_by
        ))

        db.commit()

        return {
            'success': True,
            'holiday_id': cursor.lastrowid,
            'message': 'Holiday created successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_holiday(holiday_id, holiday_data):
    """
    Update an existing holiday.

    Args:
        holiday_id (int): Holiday ID to update
        holiday_data (dict): Updated holiday information

    Returns:
        dict: Result with success status and message
    """
    import json
    from flask import session, has_request_context

    try:
        # Handle session data - use provided values or get from session
        if 'school_id' in holiday_data:
            school_id = holiday_data['school_id']
        elif has_request_context():
            school_id = session.get('school_id')
        else:
            return {'success': False, 'message': 'School ID required'}

        if not school_id:
            return {'success': False, 'message': 'Invalid session or school ID'}

        db = get_db()

        # Check if holiday exists and belongs to the school
        existing_holiday = db.execute('''
            SELECT * FROM holidays WHERE id = ? AND school_id = ?
        ''', (holiday_id, school_id)).fetchone()

        if not existing_holiday:
            return {'success': False, 'error': 'Holiday not found'}

        # Prepare departments JSON
        departments_json = None
        if holiday_data.get('departments') and holiday_data.get('holiday_type') == 'department_specific':
            departments_json = json.dumps(holiday_data['departments'])

        # Update holiday
        db.execute('''
            UPDATE holidays SET
                holiday_name = ?,
                start_date = ?,
                end_date = ?,
                holiday_type = ?,
                description = ?,
                departments = ?,
                is_recurring = ?,
                recurring_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (
            holiday_data.get('holiday_name', existing_holiday['holiday_name']),
            holiday_data.get('start_date', existing_holiday['start_date']),
            holiday_data.get('end_date', existing_holiday['end_date']),
            holiday_data.get('holiday_type', existing_holiday['holiday_type']),
            holiday_data.get('description', existing_holiday['description']),
            departments_json,
            holiday_data.get('is_recurring', existing_holiday['is_recurring']),
            holiday_data.get('recurring_type', existing_holiday['recurring_type']),
            holiday_id,
            school_id
        ))

        db.commit()

        return {
            'success': True,
            'message': 'Holiday updated successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_holiday(holiday_id):
    """
    Delete a holiday (soft delete by setting is_active to 0).

    Args:
        holiday_id (int): Holiday ID to delete

    Returns:
        dict: Result with success status and message
    """
    from flask import session

    try:
        school_id = session.get('school_id')

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Check if holiday exists and belongs to the school
        existing_holiday = db.execute('''
            SELECT * FROM holidays WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (holiday_id, school_id)).fetchone()

        if not existing_holiday:
            return {'success': False, 'error': 'Holiday not found'}

        # Soft delete holiday
        db.execute('''
            UPDATE holidays SET
                is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (holiday_id, school_id))

        db.commit()

        return {
            'success': True,
            'message': 'Holiday deleted successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_departments_list(school_id=None):
    """
    Get list of departments for the school.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        list: List of department names
    """
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return []

        db = get_db()

        # Get unique departments from staff table
        departments = db.execute('''
            SELECT DISTINCT department FROM staff
            WHERE school_id = ? AND department IS NOT NULL AND department != ''
            ORDER BY department ASC
        ''', (school_id,)).fetchall()

        return [dept['department'] for dept in departments]

    except Exception as e:
        print(f"Error getting departments list: {e}")
        return []
