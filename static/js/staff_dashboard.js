document.addEventListener('DOMContentLoaded', function() {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }
    // Initialize attendance chart with real data
    const ctx = document.getElementById('attendanceChart')?.getContext('2d');
    if (ctx) {
        fetch('/get_attendance_summary')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const attendanceChart = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Present', 'Absent', 'Late', 'Leave'],
                            datasets: [{
                                data: [data.present, data.absent, data.late, data.leave],
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

                    // Update counts
                    document.getElementById('presentDays').textContent = data.present;
                    document.getElementById('absentDays').textContent = data.absent;
                    document.getElementById('lateDays').textContent = data.late;
                    document.getElementById('leaveDays').textContent = data.leave;
                }
            });
    }

    // Removed biometric authentication UI elements (no longer needed)

    // Removed biometric authentication functions (no longer needed)



    // Global variables for biometric verification
    let isVerificationInProgress = false;

    // Load today's attendance status on page load
    loadTodayAttendanceStatus();

    // Start automatic polling for device verifications
    startDevicePolling();

    // Removed device status check (no longer needed)

    function loadTodayAttendanceStatus() {
        fetch('/get_today_attendance_status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateAttendanceDisplay(data.attendance);
                    // Removed verification history and available actions (no longer needed)
                }
            })
            .catch(error => {
                console.error('Error loading attendance status:', error);
            });
    }

    function updateAttendanceDisplay(attendance) {
        const currentStatus = document.getElementById('currentStatus');
        const timeIn = document.getElementById('timeIn');
        const timeOut = document.getElementById('timeOut');
        const workStatus = document.getElementById('workStatus');
        const totalHours = document.getElementById('totalHours');

        // Update today's status widget
        const todayStatusText = document.getElementById('todayStatusText');
        const todayCheckIn = document.getElementById('todayCheckIn');
        const todayCheckOut = document.getElementById('todayCheckOut');

        if (attendance) {
            timeIn.textContent = attendance.time_in || '--:--:--';
            timeOut.textContent = attendance.time_out || '--:--:--';

            // Update today's status widget
            todayCheckIn.textContent = attendance.time_in || '--:--';
            todayCheckOut.textContent = attendance.time_out || '--:--';

            // Calculate total hours worked
            let totalHoursText = '--:--';
            if (attendance.time_in && attendance.time_out) {
                const timeInDate = new Date(`2000-01-01 ${attendance.time_in}`);
                const timeOutDate = new Date(`2000-01-01 ${attendance.time_out}`);
                const diffMs = timeOutDate - timeInDate;
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                totalHoursText = `${diffHours}:${diffMinutes.toString().padStart(2, '0')}`;
            }
            totalHours.textContent = totalHoursText;

            // Update status based on attendance
            let statusText, statusClass, todayStatusClass, workStatusText;
            if (attendance.time_out) {
                statusText = 'Work Complete';
                statusClass = 'text-success';
                todayStatusClass = 'text-success';
                todayStatusText.textContent = '✅ Work Complete';
                workStatusText = 'Checked Out';
            } else if (attendance.time_in) {
                statusText = 'Checked In';
                statusClass = 'text-primary';
                todayStatusClass = 'text-primary';
                todayStatusText.textContent = '🟢 Checked In';
                workStatusText = 'Working';
            } else {
                statusText = 'Not Marked';
                statusClass = 'text-secondary';
                todayStatusClass = 'text-secondary';
                todayStatusText.textContent = '⚪ Not Marked';
                workStatusText = 'Not Checked In';
            }

            currentStatus.textContent = statusText;
            currentStatus.className = statusClass;
            todayStatusText.className = todayStatusClass;
            workStatus.textContent = workStatusText;
        } else {
            currentStatus.textContent = 'Not Marked';
            currentStatus.className = 'text-secondary';
            timeIn.textContent = '--:--:--';
            timeOut.textContent = '--:--:--';
            workStatus.textContent = 'Not Checked In';
            totalHours.textContent = '--:--';

            // Update today's status widget
            todayStatusText.textContent = '⚪ Not Marked';
            todayStatusText.className = 'text-secondary';
            todayCheckIn.textContent = '--:--';
            todayCheckOut.textContent = '--:--';
        }
    }

    // Removed verification history and available actions functions (no longer needed)

    function startDevicePolling() {
        // Poll for new device verifications every 30 seconds
        setInterval(() => {
            pollForDeviceVerifications();
        }, 30000);

        // Also poll immediately
        pollForDeviceVerifications();
    }

    function pollForDeviceVerifications() {
        fetch('/get_latest_device_verifications?since_minutes=1')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.verifications.length > 0) {
                    // Check if any verification is for the current user
                    const currentUserId = getCurrentUserId(); // We'll need to implement this
                    const userVerifications = data.verifications.filter(v => v.user_id === currentUserId);

                    if (userVerifications.length > 0) {
                        // Reload attendance status when new verification detected
                        setTimeout(() => {
                            loadTodayAttendanceStatus();
                        }, 1000);
                    }
                }
            })
            .catch(error => {
                console.error('Error polling for device verifications:', error);
            });
    }

    // Removed showVerificationSuccess function (no longer needed)

    function getCurrentUserId() {
        // Extract user ID from session or page data
        // For now, we'll try to get it from the page context
        // This should be set when the page loads
        return window.currentStaffId || null;
    }

    // Removed checkDeviceStatus function (no longer needed)

    // Apply leave
    const submitLeave = document.getElementById('submitLeave');
    submitLeave?.addEventListener('click', function () {
        const leaveType = document.getElementById('leaveType').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const reason = document.getElementById('leaveReason').value;

        if (!leaveType || !startDate || !endDate || !reason) {
            alert('Please fill all fields');
            return;
        }

        fetch('/apply_leave', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `leave_type=${leaveType}&start_date=${startDate}&end_date=${endDate}&reason=${encodeURIComponent(reason)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Leave application submitted successfully');
                    bootstrap.Modal.getInstance(document.getElementById('applyLeaveModal')).hide();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to submit leave application');
                }
            });
    });

    // Apply on duty
    const submitOnDuty = document.getElementById('submitOnDuty');
    submitOnDuty?.addEventListener('click', function () {
        const form = document.getElementById('onDutyForm');
        const formData = new FormData(form);

        // Basic validation
        const dutyType = formData.get('duty_type');
        const startDate = formData.get('start_date');
        const endDate = formData.get('end_date');
        const purpose = formData.get('purpose');

        if (!dutyType || !startDate || !endDate || !purpose) {
            alert('Please fill all required fields');
            return;
        }

        // Check if end date is after start date
        if (new Date(endDate) < new Date(startDate)) {
            alert('End date must be after or equal to start date');
            return;
        }

        fetch('/apply_on_duty', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || 'On-duty application submitted successfully');
                    bootstrap.Modal.getInstance(document.getElementById('applyOnDutyModal')).hide();
                    form.reset();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to submit on-duty application');
                }
            })
            .catch(error => {
                console.error('Error submitting on-duty application:', error);
                alert('Error submitting on-duty application');
            });
    });

    // Apply permission
    const submitPermission = document.getElementById('submitPermission');
    submitPermission?.addEventListener('click', function () {
        const form = document.getElementById('permissionForm');
        const formData = new FormData(form);

        // Basic validation
        const permissionType = formData.get('permission_type');
        const permissionDate = formData.get('permission_date');
        const startTime = formData.get('start_time');
        const endTime = formData.get('end_time');
        const reason = formData.get('reason');

        if (!permissionType || !permissionDate || !startTime || !endTime || !reason) {
            alert('Please fill all required fields');
            return;
        }

        // Check if end time is after start time
        if (startTime >= endTime) {
            alert('End time must be after start time');
            return;
        }

        fetch('/apply_permission', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || 'Permission application submitted successfully');
                    bootstrap.Modal.getInstance(document.getElementById('applyPermissionModal')).hide();
                    form.reset();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to submit permission application');
                }
            })
            .catch(error => {
                console.error('Error submitting permission application:', error);
                alert('Error submitting permission application');
            });
    });

    // Updated download report with date selection
// Updated download report with date selection
document.getElementById('downloadReportBtn')?.addEventListener('click', function() {
    const startDate = prompt('Enter start date (YYYY-MM-DD):');
    if (!startDate) return;

    const endDate = prompt('Enter end date (YYYY-MM-DD):');
    if (!endDate) return;

    fetch(`/export_staff_report?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_report_${startDate}_to_${endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
});



    function formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    }









});
