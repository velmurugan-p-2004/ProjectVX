# salary_calculator.py
"""
Comprehensive Salary Calculator for VishnoRex Attendance System

This module calculates salaries based on various attendance factors:
- Present days (full pay)
- Absent days (deductions)
- On duty days (full pay)
- Permission/Leave days (based on leave type)
- Arrived soon bonus (early arrival incentive)
- Left soon deductions (early departure penalty)
- Overtime calculations
- Late arrival penalties
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_db
import calendar


class SalaryCalculator:
    """Comprehensive salary calculation system"""
    
    def __init__(self):
        # Default salary calculation rules (can be configured per organization)
        self.salary_rules = {
            'early_arrival_bonus_per_hour': 50.0,  # Bonus for arriving early
            'early_departure_penalty_per_hour': 100.0,  # Penalty for leaving early
            'late_arrival_penalty_per_hour': 75.0,  # Penalty for being late
            'absent_day_deduction_rate': 1.0,  # Full day salary deduction
            'half_day_threshold_hours': 4.0,  # Minimum hours for half day
            'overtime_rate_multiplier': 1.5,  # 1.5x regular rate for overtime
            'on_duty_rate': 1.0,  # Full pay for on duty days
            'permission_deduction_rate': 0.0,  # No deduction for approved permissions
            'sick_leave_rate': 1.0,  # Full pay for sick leave (up to limit)
            'casual_leave_rate': 1.0,  # Full pay for casual leave
            'earned_leave_rate': 1.0,  # Full pay for earned leave
            'maternity_leave_rate': 1.0,  # Full pay for maternity leave
            'unpaid_leave_rate': 0.0,  # No pay for unpaid leave
        }

    def _get_db_connection(self):
        """Get database connection"""
        return get_db()

    def calculate_monthly_salary(self, staff_id: int, year: int, month: int) -> Dict:
        """Calculate comprehensive monthly salary for a staff member"""
        try:
            # Get staff details
            staff_info = self._get_staff_info(staff_id)
            if not staff_info:
                return {'success': False, 'error': 'Staff not found'}
            
            # Get attendance data for the month
            attendance_data = self._get_monthly_attendance(staff_id, year, month)
            
            # Get leave data for the month
            leave_data = self._get_monthly_leaves(staff_id, year, month)
            
            # Calculate working days in month
            working_days = self._get_working_days_in_month(year, month)
            
            # Perform salary calculations
            salary_breakdown = self._calculate_salary_breakdown(
                staff_info, attendance_data, leave_data, working_days, year, month
            )
            
            return {
                'success': True,
                'staff_info': staff_info,
                'salary_breakdown': salary_breakdown,
                'calculation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_staff_info(self, staff_id: int) -> Optional[Dict]:
        """Get staff information including salary details"""
        db = self._get_db_connection()
        staff = db.execute('''
            SELECT s.*, 
                   sc.name as school_name,
                   s.basic_salary,
                   s.hra,
                   s.transport_allowance,
                   s.other_allowances,
                   s.pf_deduction,
                   s.esi_deduction,
                   s.professional_tax,
                   s.other_deductions
            FROM staff s
            LEFT JOIN schools sc ON s.school_id = sc.id
            WHERE s.id = ?
        ''', (staff_id,)).fetchone()
        
        if staff:
            return dict(staff)
        return None
    
    def _get_monthly_attendance(self, staff_id: int, year: int, month: int) -> List[Dict]:
        """Get detailed attendance data for the month"""
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"

        db = self._get_db_connection()
        attendance = db.execute('''
            SELECT date, status, time_in, time_out,
                   late_duration_minutes, early_departure_minutes,
                   overtime_in, overtime_out, on_duty_type, on_duty_location,
                   on_duty_purpose
            FROM attendance
            WHERE staff_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (staff_id, start_date, end_date)).fetchall()
        
        return [dict(row) for row in attendance]
    
    def _get_monthly_leaves(self, staff_id: int, year: int, month: int) -> List[Dict]:
        """Get leave applications for the month"""
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"

        db = self._get_db_connection()
        leaves = db.execute('''
            SELECT leave_type, start_date, end_date, status, reason
            FROM leave_applications
            WHERE staff_id = ? AND status = 'approved'
            AND ((start_date BETWEEN ? AND ?) OR (end_date BETWEEN ? AND ?)
                 OR (start_date <= ? AND end_date >= ?))
            ORDER BY start_date
        ''', (staff_id, start_date, end_date, start_date, end_date, start_date, end_date)).fetchall()
        
        return [dict(row) for row in leaves]
    
    def _get_working_days_in_month(self, year: int, month: int) -> int:
        """Calculate working days in month (excluding weekends)"""
        total_days = calendar.monthrange(year, month)[1]
        working_days = 0
        
        for day in range(1, total_days + 1):
            date_obj = datetime(year, month, day)
            # Exclude Sundays (weekday 6)
            if date_obj.weekday() != 6:
                working_days += 1
        
        return working_days
    
    def _calculate_salary_breakdown(self, staff_info: Dict, attendance_data: List[Dict], 
                                  leave_data: List[Dict], working_days: int, 
                                  year: int, month: int) -> Dict:
        """Calculate detailed salary breakdown"""
        
        # Basic salary components
        basic_salary = float(staff_info.get('basic_salary', 0))
        hra = float(staff_info.get('hra', 0))
        transport_allowance = float(staff_info.get('transport_allowance', 0))
        other_allowances = float(staff_info.get('other_allowances', 0))
        
        # Calculate per-day salary
        gross_salary = basic_salary + hra + transport_allowance + other_allowances
        per_day_salary = gross_salary / working_days if working_days > 0 else 0
        per_hour_salary = per_day_salary / 8  # Assuming 8-hour work day
        
        # Initialize counters
        present_days = 0
        absent_days = 0
        on_duty_days = 0
        leave_days = 0
        half_days = 0
        
        # Bonus and penalty calculations
        early_arrival_bonus = 0.0
        early_departure_penalty = 0.0
        late_arrival_penalty = 0.0
        overtime_pay = 0.0
        
        # Process attendance data
        attendance_summary = self._process_attendance_data(
            attendance_data, per_hour_salary, staff_info
        )
        
        present_days = attendance_summary['present_days']
        absent_days = attendance_summary['absent_days']
        on_duty_days = attendance_summary['on_duty_days']
        early_arrival_bonus = attendance_summary['early_arrival_bonus']
        early_departure_penalty = attendance_summary['early_departure_penalty']
        late_arrival_penalty = attendance_summary['late_arrival_penalty']
        overtime_pay = attendance_summary['overtime_pay']
        
        # Process leave data
        leave_summary = self._process_leave_data(leave_data, per_day_salary, year, month)
        leave_days = leave_summary['total_leave_days']
        leave_pay = leave_summary['leave_pay']
        
        # Calculate final amounts
        present_pay = present_days * per_day_salary
        on_duty_pay = on_duty_days * per_day_salary * self.salary_rules['on_duty_rate']
        absent_deduction = absent_days * per_day_salary * self.salary_rules['absent_day_deduction_rate']
        
        # Total earnings
        total_earnings = (
            present_pay + 
            on_duty_pay + 
            leave_pay + 
            early_arrival_bonus + 
            overtime_pay
        )
        
        # Total deductions
        pf_deduction = float(staff_info.get('pf_deduction', 0))
        esi_deduction = float(staff_info.get('esi_deduction', 0))
        professional_tax = float(staff_info.get('professional_tax', 0))
        other_deductions = float(staff_info.get('other_deductions', 0))
        
        total_deductions = (
            absent_deduction +
            early_departure_penalty +
            late_arrival_penalty +
            pf_deduction +
            esi_deduction +
            professional_tax +
            other_deductions
        )
        
        # Net salary
        net_salary = total_earnings - total_deductions
        
        return {
            'calculation_period': f"{calendar.month_name[month]} {year}",
            'working_days': working_days,
            'per_day_salary': round(per_day_salary, 2),
            'per_hour_salary': round(per_hour_salary, 2),
            
            # Attendance summary
            'attendance_summary': {
                'present_days': present_days,
                'absent_days': absent_days,
                'on_duty_days': on_duty_days,
                'leave_days': leave_days,
                'half_days': half_days
            },
            
            # Earnings breakdown
            'earnings': {
                'basic_salary': basic_salary,
                'hra': hra,
                'transport_allowance': transport_allowance,
                'other_allowances': other_allowances,
                'present_pay': round(present_pay, 2),
                'on_duty_pay': round(on_duty_pay, 2),
                'leave_pay': round(leave_pay, 2),
                'early_arrival_bonus': round(early_arrival_bonus, 2),
                'overtime_pay': round(overtime_pay, 2),
                'total_earnings': round(total_earnings, 2)
            },
            
            # Deductions breakdown
            'deductions': {
                'absent_deduction': round(absent_deduction, 2),
                'early_departure_penalty': round(early_departure_penalty, 2),
                'late_arrival_penalty': round(late_arrival_penalty, 2),
                'pf_deduction': pf_deduction,
                'esi_deduction': esi_deduction,
                'professional_tax': professional_tax,
                'other_deductions': other_deductions,
                'total_deductions': round(total_deductions, 2)
            },
            
            # Final calculation
            'net_salary': round(net_salary, 2),
            'salary_rules_applied': self.salary_rules
        }
    
    def _process_attendance_data(self, attendance_data: List[Dict], 
                               per_hour_salary: float, staff_info: Dict) -> Dict:
        """Process attendance data for salary calculations"""
        present_days = 0
        absent_days = 0
        on_duty_days = 0
        early_arrival_bonus = 0.0
        early_departure_penalty = 0.0
        late_arrival_penalty = 0.0
        overtime_pay = 0.0
        
        # Get shift information for the staff
        shift_info = self._get_staff_shift_info(staff_info['id'])
        
        for record in attendance_data:
            if record['status'] == 'present':
                present_days += 1
                
                # Calculate early arrival bonus
                if record['time_in'] and shift_info:
                    early_minutes = self._calculate_early_arrival_minutes(
                        record['time_in'], shift_info['start_time']
                    )
                    if early_minutes > 0:
                        early_hours = early_minutes / 60
                        early_arrival_bonus += early_hours * self.salary_rules['early_arrival_bonus_per_hour']
                
                # Calculate early departure penalty
                if record['time_out'] and shift_info:
                    early_departure_minutes = self._calculate_early_departure_minutes(
                        record['time_out'], shift_info['end_time']
                    )
                    if early_departure_minutes > 0:
                        early_hours = early_departure_minutes / 60
                        early_departure_penalty += early_hours * self.salary_rules['early_departure_penalty_per_hour']
                
                # Calculate late arrival penalty
                if record['late_duration_minutes'] and record['late_duration_minutes'] > 0:
                    late_hours = record['late_duration_minutes'] / 60
                    late_arrival_penalty += late_hours * self.salary_rules['late_arrival_penalty_per_hour']
                
                # Calculate overtime pay
                overtime_hours = self._calculate_overtime_hours(record['overtime_in'], record['overtime_out'])
                if overtime_hours > 0:
                    overtime_pay += overtime_hours * per_hour_salary * self.salary_rules['overtime_rate_multiplier']
                    
            elif record['status'] == 'on_duty':
                on_duty_days += 1
                
            elif record['status'] == 'absent':
                absent_days += 1
        
        return {
            'present_days': present_days,
            'absent_days': absent_days,
            'on_duty_days': on_duty_days,
            'early_arrival_bonus': early_arrival_bonus,
            'early_departure_penalty': early_departure_penalty,
            'late_arrival_penalty': late_arrival_penalty,
            'overtime_pay': overtime_pay
        }
    
    def _process_leave_data(self, leave_data: List[Dict], per_day_salary: float, 
                          year: int, month: int) -> Dict:
        """Process leave data for salary calculations"""
        total_leave_days = 0
        leave_pay = 0.0
        
        for leave in leave_data:
            leave_type = leave['leave_type'].lower()

            # Calculate days from start_date and end_date
            start_date = datetime.strptime(leave['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(leave['end_date'], '%Y-%m-%d').date()

            # Only count days within the requested month
            month_start = datetime(year, month, 1).date()
            month_end = datetime(year, month, calendar.monthrange(year, month)[1]).date()

            # Adjust dates to be within the month
            actual_start = max(start_date, month_start)
            actual_end = min(end_date, month_end)

            if actual_start <= actual_end:
                days = (actual_end - actual_start).days + 1

                # Apply leave rate based on type
                if leave_type in ['sick_leave', 'sl']:
                    rate = self.salary_rules['sick_leave_rate']
                elif leave_type in ['casual_leave', 'cl']:
                    rate = self.salary_rules['casual_leave_rate']
                elif leave_type in ['earned_leave', 'el']:
                    rate = self.salary_rules['earned_leave_rate']
                elif leave_type in ['maternity_leave', 'ml']:
                    rate = self.salary_rules['maternity_leave_rate']
                elif leave_type == 'permission':
                    rate = self.salary_rules['permission_deduction_rate']
                else:
                    rate = self.salary_rules['unpaid_leave_rate']

                total_leave_days += days
                leave_pay += days * per_day_salary * rate
        
        return {
            'total_leave_days': total_leave_days,
            'leave_pay': leave_pay
        }
    
    def _get_staff_shift_info(self, staff_id: int) -> Optional[Dict]:
        """Get shift information for staff member"""
        try:
            db = self._get_db_connection()
            # Try to get shift info from staff table only (shifts table may not exist)
            staff = db.execute('''
                SELECT shift_type
                FROM staff
                WHERE id = ?
            ''', (staff_id,)).fetchone()

            if staff and staff['shift_type']:
                # Return default shift info based on shift type
                return {
                    'shift_type': staff['shift_type'],
                    'start_time': '09:00:00',
                    'end_time': '17:00:00',
                    'grace_period_minutes': 10
                }
        except:
            pass

        # Default shift if not found or error
        return {
            'shift_type': 'general',
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'grace_period_minutes': 10
        }
    
    def _calculate_early_arrival_minutes(self, actual_time: str, shift_start: str) -> int:
        """Calculate minutes of early arrival"""
        try:
            actual = datetime.strptime(actual_time, '%H:%M:%S').time()
            shift = datetime.strptime(shift_start, '%H:%M:%S').time()
            
            actual_dt = datetime.combine(datetime.today(), actual)
            shift_dt = datetime.combine(datetime.today(), shift)
            
            if actual_dt < shift_dt:
                return int((shift_dt - actual_dt).total_seconds() / 60)
            return 0
        except:
            return 0
    
    def _calculate_early_departure_minutes(self, actual_time: str, shift_end: str) -> int:
        """Calculate minutes of early departure"""
        try:
            actual = datetime.strptime(actual_time, '%H:%M:%S').time()
            shift = datetime.strptime(shift_end, '%H:%M:%S').time()
            
            actual_dt = datetime.combine(datetime.today(), actual)
            shift_dt = datetime.combine(datetime.today(), shift)
            
            if actual_dt < shift_dt:
                return int((shift_dt - actual_dt).total_seconds() / 60)
            return 0
        except:
            return 0

    def _calculate_overtime_hours(self, overtime_in: str, overtime_out: str) -> float:
        """Calculate overtime hours from overtime_in and overtime_out times"""
        try:
            if not overtime_in or not overtime_out:
                return 0.0

            overtime_in_time = datetime.strptime(overtime_in, '%H:%M:%S').time()
            overtime_out_time = datetime.strptime(overtime_out, '%H:%M:%S').time()

            overtime_in_dt = datetime.combine(datetime.today(), overtime_in_time)
            overtime_out_dt = datetime.combine(datetime.today(), overtime_out_time)

            # Handle overnight overtime
            if overtime_out_dt < overtime_in_dt:
                overtime_out_dt += timedelta(days=1)

            overtime_duration = overtime_out_dt - overtime_in_dt
            return overtime_duration.total_seconds() / 3600  # Convert to hours
        except:
            return 0.0

    def generate_salary_report(self, staff_id: int, year: int, month: int) -> Dict:
        """Generate a comprehensive salary report"""
        salary_data = self.calculate_monthly_salary(staff_id, year, month)
        
        if not salary_data['success']:
            return salary_data
        
        # Add additional report information
        report_data = salary_data.copy()
        report_data['report_generated_at'] = datetime.now().isoformat()
        report_data['report_type'] = 'Monthly Salary Report'
        
        return report_data
    
    def update_salary_rules(self, new_rules: Dict) -> Dict:
        """Update salary calculation rules"""
        try:
            self.salary_rules.update(new_rules)
            return {'success': True, 'message': 'Salary rules updated successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
