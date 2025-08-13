document.addEventListener('DOMContentLoaded', function () {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }
document.getElementById('schoolSearch')?.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const rows = document.querySelectorAll('.table tbody tr');
    
    rows.forEach(row => {
        const schoolName = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
        row.style.display = schoolName.includes(searchTerm) ? '' : 'none';
    });
});

    // Delete school
    document.querySelectorAll('.delete-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const schoolId = this.getAttribute('data-school-id');
            const schoolName = this.closest('tr').querySelector('td:nth-child(1)').textContent;

            if (!confirm(`Are you sure you want to delete ${schoolName}? This action cannot be undone.`)) {
                return;
            }

            fetch('/delete_school', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `school_id=${schoolId}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('School deleted successfully');
                        location.reload();
                    } else {
                        alert(data.error || 'Failed to delete school');
                    }
                });
        });
    });

    // Hide school
    document.querySelectorAll('.hide-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const row = this.closest('tr');
            const schoolId = this.getAttribute('data-school-id');
            const schoolName = row.querySelector('td:nth-child(1)').textContent;

            if (!confirm(`Are you sure you want to toggle visibility for ${schoolName}?`)) {
                return;
            }

            fetch('/toggle_school_visibility', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `school_id=${schoolId}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`School visibility updated successfully`);
                        location.reload();
                    } else {
                        alert(data.error || 'Failed to update school visibility');
                    }
                });
        });
    });

    // Add new school
    const saveSchool = document.getElementById('saveSchool');
    saveSchool.addEventListener('click', function () {
        const schoolName = document.getElementById('schoolName').value;
        const schoolAddress = document.getElementById('schoolAddress').value;
        const schoolEmail = document.getElementById('schoolEmail').value;
        const schoolPhone = document.getElementById('schoolPhone').value;

        const adminUsername = document.getElementById('adminUsername').value;
        const adminPassword = document.getElementById('adminPassword').value;
        const adminFullName = document.getElementById('adminFullName').value;
        const adminEmail = document.getElementById('adminEmail').value;

        if (!schoolName || !adminUsername || !adminPassword || !adminFullName) {
            alert('School Name and Admin details are required');
            return;
        }

        fetch('/add_school', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `name=${encodeURIComponent(schoolName)}&address=${encodeURIComponent(schoolAddress)}&contact_email=${schoolEmail}&contact_phone=${schoolPhone}&admin_username=${adminUsername}&admin_password=${encodeURIComponent(adminPassword)}&admin_full_name=${encodeURIComponent(adminFullName)}&admin_email=${adminEmail}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('School added successfully');
                    bootstrap.Modal.getInstance(document.getElementById('addSchoolModal')).hide();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to add school');
                }
            });
    });

    // View school details
    document.querySelectorAll('.view-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const schoolId = this.getAttribute('data-school-id');
            window.location.href = `/company/school_details/${schoolId}`;
        });
    });

    // Enhanced company report with date range selection
    document.getElementById('exportCompanyReportBtn')?.addEventListener('click', function () {
        const modalHtml = `
            <div class="modal fade" id="reportDateModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">Generate Company Report</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="reportStartDate" class="form-label">Start Date</label>
                                <input type="date" class="form-control" id="reportStartDate" required>
                            </div>
                            <div class="mb-3">
                                <label for="reportEndDate" class="form-label">End Date</label>
                                <input type="date" class="form-control" id="reportEndDate" required>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="generateCompanyReport">Generate Report</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('reportDateModal'));
        modal.show();

        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

        document.getElementById('reportStartDate').valueAsDate = firstDay;
        document.getElementById('reportEndDate').valueAsDate = lastDay;

        document.getElementById('generateCompanyReport').addEventListener('click', function () {
            const startDate = document.getElementById('reportStartDate').value;
            const endDate = document.getElementById('reportEndDate').value;

            if (!startDate || !endDate) {
                alert('Please select both start and end dates');
                return;
            }

            if (startDate > endDate) {
                alert('Start date cannot be after end date');
                return;
            }

            fetch(`/export_company_report?start_date=${startDate}&end_date=${endDate}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `company_report_${startDate}_to_${endDate}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    modal.hide();
                    document.getElementById('reportDateModal').remove();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to generate report');
                    modal.hide();
                    document.getElementById('reportDateModal').remove();
                });
        });

        document.getElementById('reportDateModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    });
});
