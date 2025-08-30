// Staff Management JavaScript - Enhanced Version
document.addEventListener('DOMContentLoaded', function() {
    // Initialize enhanced UI components
    initializeEnhancedUI();

    // Initialize search and filter functionality
    initializeSearchAndFilter();

    // Initialize form handlers
    initializeFormHandlers();

    // Initialize export functionality
    initializeExportFunctionality();

    // Initialize loading overlay
    initializeLoadingOverlay();

    // Update stats display
    updateStatsDisplay();
});

function initializeEnhancedUI() {
    // Initialize sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.enhanced-sidebar');
            sidebar.classList.toggle('show');
        });
    }

    // Initialize refresh button
    const refreshBtn = document.getElementById('refreshDataBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            showLoadingOverlay();
            setTimeout(() => {
                location.reload();
            }, 500);
        });
    }

    // Initialize clear filters button
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            document.getElementById('staffSearchInput').value = '';
            document.getElementById('departmentFilter').value = '';
            document.getElementById('genderFilter').value = '';
            filterTable();
        });
    }

    // Update current date in sidebar
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        const today = new Date();
        currentDateElement.textContent = today.toLocaleDateString();
    }
}

function initializeLoadingOverlay() {
    window.showLoadingOverlay = function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('d-none');
        }
    };

    window.hideLoadingOverlay = function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('d-none');
        }
    };
}

function updateStatsDisplay() {
    const totalStaffElement = document.getElementById('totalStaffDisplay');
    const totalStaffCountElement = document.getElementById('totalStaffCount');
    const tableBody = document.getElementById('staffTableBody');

    if (tableBody) {
        const totalStaff = tableBody.querySelectorAll('tr').length;
        if (totalStaffElement) {
            totalStaffElement.textContent = totalStaff;
        }
        if (totalStaffCountElement) {
            totalStaffCountElement.textContent = totalStaff;
        }
    }
}

function initializeSearchAndFilter() {
    const searchInput = document.getElementById('staffSearchInput');
    const departmentFilter = document.getElementById('departmentFilter');
    const genderFilter = document.getElementById('genderFilter');
    const tableBody = document.getElementById('staffTableBody');
    
    function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedDepartment = departmentFilter.value;
        const selectedGender = genderFilter.value;
        const rows = tableBody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 0) return;
            
            const staffId = cells[0].textContent.toLowerCase();
            const firstName = cells[1].textContent.toLowerCase();
            const lastName = cells[2].textContent.toLowerCase();
            const department = cells[5].textContent;
            const gender = cells[7].textContent;
            const phone = cells[8].textContent.toLowerCase();
            const email = cells[9].textContent.toLowerCase();
            
            const matchesSearch = searchTerm === '' || 
                staffId.includes(searchTerm) ||
                firstName.includes(searchTerm) ||
                lastName.includes(searchTerm) ||
                phone.includes(searchTerm) ||
                email.includes(searchTerm);
            
            const matchesDepartment = selectedDepartment === '' || department === selectedDepartment;
            const matchesGender = selectedGender === '' || gender === selectedGender;
            
            if (matchesSearch && matchesDepartment && matchesGender) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    searchInput.addEventListener('input', filterTable);
    departmentFilter.addEventListener('change', filterTable);
    genderFilter.addEventListener('change', filterTable);
}

function initializeFormHandlers() {
    // Add Staff Form
    const addStaffForm = document.getElementById('addStaffForm');
    if (addStaffForm) {
        addStaffForm.addEventListener('submit', handleAddStaff);

        // Add auto-generation of full name for add form
        const addFirstName = document.getElementById('addFirstName');
        const addLastName = document.getElementById('addLastName');

        if (addFirstName && addLastName) {
            function updateAddFullName() {
                const firstName = addFirstName.value.trim();
                const lastName = addLastName.value.trim();
                // We'll send the full name as a hidden field or generate it on the server
                // For now, we just ensure the form has the required data
            }

            addFirstName.addEventListener('input', updateAddFullName);
            addLastName.addEventListener('input', updateAddFullName);
        }
    }

    // Edit Staff Form
    const editStaffForm = document.getElementById('editStaffForm');
    if (editStaffForm) {
        editStaffForm.addEventListener('submit', handleEditStaff);
    }
    
    // Edit buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-staff-btn')) {
            const btn = e.target.closest('.edit-staff-btn');
            const staffId = btn.getAttribute('data-staff-id');
            loadStaffForEdit(staffId);
        }
        
        if (e.target.closest('.delete-staff-btn')) {
            const btn = e.target.closest('.delete-staff-btn');
            const staffId = btn.getAttribute('data-staff-id');
            const staffName = btn.getAttribute('data-staff-name');
            confirmDeleteStaff(staffId, staffName);
        }
    });
}

function handleAddStaff(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adding...';
    
    fetch('/add_staff_enhanced', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Staff member added successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addStaffModal')).hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Add Staff Member';
    });
}

function loadStaffForEdit(staffId) {
    const modalBody = document.getElementById('editStaffModalBody');
    
    fetch(`/get_staff_details_enhanced?id=${staffId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            populateEditForm(data.staff);
        } else {
            showAlert('Error loading staff details: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    });
}

function populateEditForm(staff) {
    const modalBody = document.getElementById('editStaffModalBody');

    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editStaffId" class="form-label">Staff ID *</label>
                    <input type="text" class="form-control" id="editStaffId" name="staff_id" value="${staff.staff_id || ''}" required>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editFirstName" class="form-label">First Name *</label>
                    <input type="text" class="form-control" id="editFirstName" name="first_name" value="${staff.first_name || ''}" required>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editLastName" class="form-label">Last Name *</label>
                    <input type="text" class="form-control" id="editLastName" name="last_name" value="${staff.last_name || ''}" required>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDateOfBirth" class="form-label">Date of Birth</label>
                    <input type="date" class="form-control" id="editDateOfBirth" name="date_of_birth" value="${staff.date_of_birth || ''}">
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDateOfJoining" class="form-label">Date of Joining</label>
                    <input type="date" class="form-control" id="editDateOfJoining" name="date_of_joining" value="${staff.date_of_joining || ''}">
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDepartment" class="form-label">Department</label>
                    <select class="form-select" id="editDepartment" name="department">
                        <option value="">Select Department</option>
                        <option value="Teaching" ${staff.department === 'Teaching' ? 'selected' : ''}>Teaching</option>
                        <option value="Administration" ${staff.department === 'Administration' ? 'selected' : ''}>Administration</option>
                        <option value="Support" ${staff.department === 'Support' ? 'selected' : ''}>Support</option>
                        <option value="Management" ${staff.department === 'Management' ? 'selected' : ''}>Management</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDestination" class="form-label">Destination *</label>
                    <input type="text" class="form-control" id="editDestination" name="destination" value="${staff.destination || ''}" required>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editGender" class="form-label">Gender</label>
                    <select class="form-select" id="editGender" name="gender">
                        <option value="">Select Gender</option>
                        <option value="Male" ${staff.gender === 'Male' ? 'selected' : ''}>Male</option>
                        <option value="Female" ${staff.gender === 'Female' ? 'selected' : ''}>Female</option>
                        <option value="Other" ${staff.gender === 'Other' ? 'selected' : ''}>Other</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editPhone" class="form-label">Phone Number</label>
                    <input type="tel" class="form-control" id="editPhone" name="phone" value="${staff.phone || ''}">
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editEmail" class="form-label">Email ID</label>
                    <input type="email" class="form-control" id="editEmail" name="email" value="${staff.email || ''}">
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editShiftType" class="form-label">Shift Assign Type</label>
                    <select class="form-select" id="editShiftType" name="shift_type">
                        <option value="general" ${staff.shift_type === 'general' ? 'selected' : ''}>General</option>
                        <option value="morning" ${staff.shift_type === 'morning' ? 'selected' : ''}>Morning</option>
                        <option value="evening" ${staff.shift_type === 'evening' ? 'selected' : ''}>Evening</option>
                        <option value="night" ${staff.shift_type === 'night' ? 'selected' : ''}>Night</option>
                    </select>
                    <small class="form-text text-muted">
                        <i class="bi bi-info-circle"></i>
                        Department default: ${getDepartmentDefaultShift(staff.department) || 'Not set'}
                    </small>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editFullName" class="form-label">Full Name (Auto-generated)</label>
                    <input type="text" class="form-control" id="editFullName" name="full_name" value="${staff.full_name || ''}" readonly>
                    <small class="form-text text-muted">This field is automatically generated from First Name + Last Name</small>
                </div>
            </div>
        </div>
    `;

    // Set the staff ID for the form
    document.getElementById('editStaffDbId').value = staff.id;

    // Add event listeners to update full name automatically
    const firstNameInput = document.getElementById('editFirstName');
    const lastNameInput = document.getElementById('editLastName');
    const fullNameInput = document.getElementById('editFullName');

    function updateFullName() {
        const firstName = firstNameInput.value.trim();
        const lastName = lastNameInput.value.trim();
        fullNameInput.value = `${firstName} ${lastName}`.trim();
    }

    firstNameInput.addEventListener('input', updateFullName);
    lastNameInput.addEventListener('input', updateFullName);
}

function handleEditStaff(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
    
    fetch('/update_staff_enhanced', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Staff member updated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editStaffModal')).hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Update Staff Member';
    });
}

function confirmDeleteStaff(staffId, staffName) {
    if (confirm(`Are you sure you want to delete ${staffName}? This action cannot be undone.`)) {
        deleteStaff(staffId);
    }
}

function deleteStaff(staffId) {
    const formData = new FormData();
    formData.append('staff_id', staffId);
    
    fetch('/delete_staff', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Staff member deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    });
}

function initializeExportFunctionality() {
    const exportBtn = document.getElementById('exportStaffExcelBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToExcel);
    }
}

function exportToExcel() {
    const exportBtn = document.getElementById('exportStaffExcelBtn');
    exportBtn.disabled = true;
    exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Exporting...';
    
    window.location.href = '/export_staff_excel';
    
    setTimeout(() => {
        exportBtn.disabled = false;
        exportBtn.innerHTML = '<i class="bi bi-file-earmark-excel"></i> Export to Excel';
    }, 2000);
}

function getDepartmentDefaultShift(department) {
    // This would ideally come from the server, but for now we'll use a simple lookup
    // In a real implementation, this data should be passed from the server
    const deptShiftMap = window.deptShiftMap || {};
    return deptShiftMap[department] || 'Not set';
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}
