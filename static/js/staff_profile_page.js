document.addEventListener('DOMContentLoaded', function() {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }

    // Initialize attendance summary chart
    const ctx = document.getElementById('attendanceSummaryChart')?.getContext('2d');
    if (ctx) {
        const presentDays = parseInt(document.querySelector('.bg-success h4').textContent) || 0;
        const absentDays = parseInt(document.querySelector('.bg-danger h4').textContent) || 0;
        const lateDays = parseInt(document.querySelector('.bg-warning h4').textContent) || 0;
        const leaveDays = parseInt(document.querySelector('.bg-info h4').textContent) || 0;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent', 'Late', 'Leave'],
                datasets: [{
                    data: [presentDays, absentDays, lateDays, leaveDays],
                    backgroundColor: [
                        '#198754',
                        '#dc3545',
                        '#ffc107',
                        '#0dcaf0'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Initialize weekly attendance calendar
    const weeklyCalendarEl = document.getElementById('weeklyAttendanceCalendar');
    if (weeklyCalendarEl) {
        // Initialize the weekly calendar component
        const weeklyCalendar = new WeeklyAttendanceCalendar('weeklyAttendanceCalendar', {
            isAdminView: false
        });

        // Store reference for potential future use
        window.weeklyAttendanceCalendar = weeklyCalendar;
    }

    // Edit Profile functionality
    document.getElementById('saveProfileBtn')?.addEventListener('click', function() {
        const form = document.getElementById('editProfileForm');
        const formData = new FormData(form);

        fetch('/staff/update_profile', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Profile updated successfully!');
                bootstrap.Modal.getInstance(document.getElementById('editProfileModal')).hide();
                location.reload(); // Reload to show updated information
            } else {
                alert(data.error || 'Failed to update profile');
            }
        })
        .catch(error => {
            console.error('Error updating profile:', error);
            alert('Error updating profile');
        });
    });

    // Change Password functionality
    document.getElementById('changePasswordBtn')?.addEventListener('click', function() {
        const form = document.getElementById('changePasswordForm');
        const formData = new FormData(form);

        // Validate passwords match
        const newPassword = formData.get('new_password');
        const confirmPassword = formData.get('confirm_password');

        if (newPassword !== confirmPassword) {
            alert('New passwords do not match');
            return;
        }

        fetch('/staff/change_password', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Password changed successfully!');
                bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
                form.reset();
            } else {
                alert(data.error || 'Failed to change password');
            }
        })
        .catch(error => {
            console.error('Error changing password:', error);
            alert('Error changing password');
        });
    });

    // Apply Leave functionality
    document.getElementById('submitLeave')?.addEventListener('click', function() {
        const form = document.getElementById('leaveForm');
        const formData = new FormData(form);

        // Basic validation
        const leaveType = formData.get('leave_type');
        const startDate = formData.get('start_date');
        const endDate = formData.get('end_date');
        const reason = formData.get('reason');

        if (!leaveType || !startDate || !endDate || !reason) {
            alert('Please fill all fields');
            return;
        }

        // Check if end date is after start date
        if (new Date(endDate) < new Date(startDate)) {
            alert('End date must be after start date');
            return;
        }

        fetch('/apply_leave', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Leave application submitted successfully!');
                bootstrap.Modal.getInstance(document.getElementById('applyLeaveModal')).hide();
                form.reset();
                location.reload(); // Reload to show new leave application
            } else {
                alert(data.error || 'Failed to submit leave application');
            }
        })
        .catch(error => {
            console.error('Error submitting leave:', error);
            alert('Error submitting leave application');
        });
    });

    // Set minimum date for leave application to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('startDate')?.setAttribute('min', today);
    document.getElementById('endDate')?.setAttribute('min', today);

    // Update end date minimum when start date changes
    document.getElementById('startDate')?.addEventListener('change', function() {
        const endDateInput = document.getElementById('endDate');
        if (endDateInput) {
            endDateInput.setAttribute('min', this.value);
            if (endDateInput.value && endDateInput.value < this.value) {
                endDateInput.value = this.value;
            }
        }
    });
});
