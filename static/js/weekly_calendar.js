/**
 * Weekly Attendance Calendar Component
 * 
 * This component replaces the existing FullCalendar implementation with a custom
 * weekly view that shows detailed daily attendance information including:
 * - Present/Absent status
 * - Shift type
 * - Morning/Evening thumb timings
 * - Calculated delays and early departures
 */

class WeeklyAttendanceCalendar {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            staffId: options.staffId || null,
            isAdminView: options.isAdminView || false,
            ...options
        };
        
        this.currentWeekStart = this.getWeekStart(new Date());
        this.weeklyData = [];
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Weekly calendar container not found');
            return;
        }
        
        this.render();
        this.loadWeeklyData();
    }
    
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
        return new Date(d.setDate(diff));
    }
    
    formatDate(date) {
        return date.toISOString().split('T')[0];
    }
    
    render() {
        const weekStart = new Date(this.currentWeekStart);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        
        this.container.innerHTML = `
            <div class="weekly-calendar">
                <div class="calendar-header">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="btn-group" role="group">
                            <button class="btn btn-outline-primary btn-sm" id="prevWeek" title="Previous Week (Left Arrow)">
                                <i class="bi bi-chevron-left"></i> Previous
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" id="todayWeek" title="Go to Current Week">
                                <i class="bi bi-calendar-today"></i> Today
                            </button>
                        </div>
                        <div class="text-center">
                            <h5 class="mb-0">
                                Week of ${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}
                            </h5>
                            <small class="text-muted">${weekStart.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</small>
                        </div>
                        <button class="btn btn-outline-primary btn-sm" id="nextWeek" title="Next Week (Right Arrow)">
                            Next <i class="bi bi-chevron-right"></i>
                        </button>
                    </div>
                </div>
                <div class="calendar-body">
                    <div class="row" id="weeklyGrid">
                        <div class="col-12">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Loading weekly attendance...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners for navigation
        document.getElementById('prevWeek').addEventListener('click', () => {
            this.navigateWeek(-1);
        });

        document.getElementById('nextWeek').addEventListener('click', () => {
            this.navigateWeek(1);
        });

        document.getElementById('todayWeek').addEventListener('click', () => {
            this.goToCurrentWeek();
        });

        // Add keyboard navigation support
        this.addKeyboardNavigation();
    }
    
    navigateWeek(direction) {
        const newWeekStart = new Date(this.currentWeekStart);
        newWeekStart.setDate(newWeekStart.getDate() + (direction * 7));
        this.currentWeekStart = newWeekStart;
        
        this.render();
        this.loadWeeklyData();
    }
    
    loadWeeklyData() {
        const weekStartStr = this.formatDate(this.currentWeekStart);
        let url = `/get_weekly_attendance?week_start=${weekStartStr}`;
        
        if (this.options.staffId) {
            url += `&staff_id=${this.options.staffId}`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.weeklyData = data.weekly_data;
                    this.renderWeeklyGrid(data);
                } else {
                    this.showError(data.error || 'Failed to load weekly data');
                }
            })
            .catch(error => {
                console.error('Error loading weekly data:', error);
                this.showError('Failed to load weekly attendance data');
            });
    }
    
    renderWeeklyGrid(data) {
        const grid = document.getElementById('weeklyGrid');
        
        let html = '<div class="table-responsive">';
        html += '<table class="table table-bordered weekly-attendance-table">';
        html += '<thead class="table-light">';
        html += '<tr>';
        
        // Header row with day names
        data.weekly_data.forEach(day => {
            const isToday = day.date === new Date().toISOString().split('T')[0];
            const headerClass = isToday ? 'bg-primary text-white' : '';
            html += `<th class="text-center ${headerClass}">${day.day_name}<br><small>${new Date(day.date).toLocaleDateString()}</small></th>`;
        });
        
        html += '</tr>';
        html += '</thead>';
        html += '<tbody>';
        html += '<tr>';
        
        // Data cells for each day
        data.weekly_data.forEach(day => {
            html += '<td class="day-cell">';
            html += this.renderDayCell(day);
            html += '</td>';
        });
        
        html += '</tr>';
        html += '</tbody>';
        html += '</table>';
        html += '</div>';
        
        grid.innerHTML = html;
    }
    
    renderDayCell(dayData) {
        let html = '<div class="day-content">';

        // Present/Absent/On Duty status
        let statusClass = 'text-danger'; // Default for absent
        if (dayData.present_status === 'Present') {
            statusClass = 'text-success';
        } else if (dayData.present_status === 'On Duty') {
            statusClass = 'text-info';
        }
        html += `<div class="status-badge"><strong class="${statusClass}">${dayData.present_status}</strong></div>`;

        // Handle On Duty status display
        if (dayData.present_status === 'On Duty') {
            html += `<div class="on-duty-info">`;
            html += `<div class="duty-type"><small class="text-info"><strong>Type:</strong> ${dayData.on_duty_type}</small></div>`;
            if (dayData.on_duty_location && dayData.on_duty_location !== 'Not specified') {
                html += `<div class="duty-location"><small class="text-muted"><strong>Location:</strong> ${dayData.on_duty_location}</small></div>`;
            }
            if (dayData.on_duty_purpose) {
                const truncatedPurpose = dayData.on_duty_purpose.length > 30 ?
                    dayData.on_duty_purpose.substring(0, 30) + '...' :
                    dayData.on_duty_purpose;
                html += `<div class="duty-purpose"><small class="text-secondary" title="${dayData.on_duty_purpose}"><strong>Purpose:</strong> ${truncatedPurpose}</small></div>`;
            }
            html += `</div>`;
        } else {
            // Shift type and timing (only for regular attendance)
            html += `<div class="shift-info">`;
            html += `<div class="shift-type"><small class="text-muted">${dayData.shift_type_display}</small></div>`;
            if (dayData.shift_start_time && dayData.shift_end_time) {
                html += `<div class="shift-timing"><small class="text-primary"><strong>Shift:</strong> ${dayData.shift_start_time} - ${dayData.shift_end_time}</small></div>`;
            }
            html += `</div>`;
        }

        if (dayData.present_status === 'Present') {
            // Morning thumb timing
            if (dayData.morning_thumb) {
                html += `<div class="timing-section">`;
                html += `<div class="timing-info">`;
                html += `<span class="timing-label">Morning Thumb:</span>`;
                html += `<span class="timing-value">${dayData.morning_thumb}</span>`;
                html += `</div>`;

                // Arrived soon information (early arrival)
                if (dayData.arrived_soon_info) {
                    html += `<div class="arrived-soon-info">`;
                    html += `<small class="text-success"><i class="bi bi-clock-fill"></i> ${dayData.arrived_soon_info}</small>`;
                    html += `</div>`;
                }

                // Delay information with detailed timing
                if (dayData.delay_info) {
                    html += `<div class="delay-info">`;
                    html += `<small class="text-warning"><i class="bi bi-clock-fill"></i> ${dayData.delay_info}</small>`;
                    html += `</div>`;
                }
                html += `</div>`;
            }

            // Evening thumb timing
            if (dayData.evening_thumb) {
                html += `<div class="timing-section">`;
                html += `<div class="timing-info">`;
                html += `<span class="timing-label">Evening Thumb:</span>`;
                html += `<span class="timing-value">${dayData.evening_thumb}</span>`;
                html += `</div>`;

                // Left soon information with detailed timing
                if (dayData.left_soon_info) {
                    html += `<div class="left-soon-info">`;
                    html += `<small class="text-info"><i class="bi bi-clock-fill"></i> ${dayData.left_soon_info}</small>`;
                    html += `</div>`;
                }
                html += `</div>`;
            }

            // Overtime information
            if (dayData.overtime_in || dayData.overtime_out) {
                html += `<div class="overtime-section">`;
                html += `<div class="overtime-header"><small class="text-secondary"><strong>Overtime:</strong></small></div>`;
                if (dayData.overtime_in) {
                    html += `<div class="overtime-timing"><small>In: ${dayData.overtime_in}</small></div>`;
                }
                if (dayData.overtime_out) {
                    html += `<div class="overtime-timing"><small>Out: ${dayData.overtime_out}</small></div>`;
                }
                html += `</div>`;
            }
        }

        html += '</div>';
        return html;
    }
    
    showError(message) {
        const grid = document.getElementById('weeklyGrid');
        grid.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${message}
                </div>
            </div>
        `;
    }
    
    // Public method to refresh data
    refresh() {
        this.loadWeeklyData();
    }
    
    // Public method to navigate to specific week
    goToWeek(date) {
        this.currentWeekStart = this.getWeekStart(date);
        this.render();
        this.loadWeeklyData();
    }
    
    // Public method to go to current week
    goToCurrentWeek() {
        this.goToWeek(new Date());
    }

    // Add keyboard navigation support
    addKeyboardNavigation() {
        // Remove existing listener if it exists
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
        }

        this.keyboardHandler = (event) => {
            // Only handle keyboard events when the calendar container is focused or visible
            if (!this.container.closest('.modal')?.classList.contains('show') &&
                !document.activeElement?.closest('.weekly-calendar')) {
                return;
            }

            switch (event.key) {
                case 'ArrowLeft':
                    event.preventDefault();
                    this.navigateWeek(-1);
                    break;
                case 'ArrowRight':
                    event.preventDefault();
                    this.navigateWeek(1);
                    break;
                case 'Home':
                    event.preventDefault();
                    this.goToCurrentWeek();
                    break;
                case 'r':
                case 'R':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.refresh();
                    }
                    break;
            }
        };

        document.addEventListener('keydown', this.keyboardHandler);
    }

    // Cleanup method to remove event listeners
    destroy() {
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
        }
    }
}

// CSS styles for the weekly calendar
const weeklyCalendarStyles = `
<style>
.weekly-calendar {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.weekly-attendance-table {
    margin-bottom: 0;
}

.weekly-attendance-table th {
    vertical-align: middle;
    padding: 12px 8px;
    font-weight: 600;
}

.day-cell {
    vertical-align: top;
    padding: 12px 8px;
    min-height: 200px;
    width: 14.28%; /* 100% / 7 days */
}

.day-content {
    min-height: 180px;
}

.status-badge {
    margin-bottom: 8px;
    font-size: 14px;
}

.shift-info {
    margin-bottom: 10px;
}

.shift-type {
    margin-bottom: 4px;
    font-size: 12px;
}

.shift-timing {
    font-size: 11px;
    margin-bottom: 6px;
}

.timing-section {
    margin-bottom: 8px;
    padding: 4px 0;
    border-bottom: 1px solid #f0f0f0;
}

.timing-section:last-of-type {
    border-bottom: none;
}

.timing-info {
    margin-bottom: 4px;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.timing-label {
    font-size: 11px;
    color: #6c757d;
    font-weight: 600;
}

.timing-value {
    font-size: 12px;
    font-weight: 500;
    color: #495057;
}

.arrived-soon-info, .delay-info, .left-soon-info {
    margin-top: 4px;
    padding: 3px 6px;
    border-radius: 4px;
    background-color: rgba(255, 193, 7, 0.1);
    border-left: 3px solid #ffc107;
}

.arrived-soon-info {
    background-color: rgba(25, 135, 84, 0.1);
    border-left-color: #198754;
}

.left-soon-info {
    background-color: rgba(13, 202, 240, 0.1);
    border-left-color: #0dcaf0;
}

.overtime-section {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #dee2e6;
}

.overtime-header {
    margin-bottom: 4px;
}

.overtime-timing {
    font-size: 11px;
    margin-bottom: 2px;
    color: #6c757d;
}

.weekly-attendance-table td:hover {
    background-color: #f8f9fa;
}

@media (max-width: 768px) {
    .day-cell {
        min-height: 150px;
        padding: 8px 4px;
    }
    
    .day-content {
        min-height: 130px;
    }
    
    .timing-info {
        font-size: 12px;
    }
}
</style>
`;

// Inject styles into the document
if (!document.getElementById('weekly-calendar-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'weekly-calendar-styles';
    styleElement.innerHTML = weeklyCalendarStyles;
    document.head.appendChild(styleElement);
}
