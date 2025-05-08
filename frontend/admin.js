/**
 * Admin functionality for the "What Beats Rock?" game
 * Handles admin dashboard and report management
 */

// Admin state
const adminState = {
    currentReportId: null,
    currentPage: 1,
    pageSize: 10,
    totalPages: 1,
    statusFilters: [],
    sortBy: 'created_at',
    sortDirection: 'desc',
    reports: [],
    isAuthenticated: false
};

// Edit comparison state
const editComparisonState = {
    item1: '',
    item2: '',
    reportId: null
};

// DOM Elements
const elements = {
    // Admin elements
    statusCheckboxes: document.querySelectorAll('.status-checkbox'),
    statusAllCheckbox: document.getElementById('status-all'),
    reportsBody: document.getElementById('reports-body'),
    prevReportsPageBtn: document.getElementById('prev-reports-page-btn'),
    nextReportsPageBtn: document.getElementById('next-reports-page-btn'),
    reportsPageInfo: document.getElementById('reports-page-info'),
    backToGameBtn: document.getElementById('back-to-game-btn'),
    logoutBtn: document.getElementById('logout-btn'),
    
    // Edit comparison elements
    editComparisonModal: document.getElementById('edit-comparison-modal'),
    closeEditComparisonModalBtn: document.getElementById('close-edit-comparison-modal'),
    editComparisonForm: document.getElementById('edit-comparison-form'),
    editItem1: document.getElementById('edit-item1'),
    editItem2: document.getElementById('edit-item2'),
    item1WinsRadio: document.getElementById('item1-wins'),
    item2WinsRadio: document.getElementById('item2-wins'),
    editDescription: document.getElementById('edit-description'),
    editEmoji: document.getElementById('edit-emoji'),
    saveComparisonBtn: document.getElementById('save-comparison-btn'),
    cancelEditBtn: document.getElementById('cancel-edit-btn'),
    editSuccess: document.getElementById('edit-success'),
    editError: document.getElementById('edit-error'),
    closeEditSuccessBtn: document.getElementById('close-edit-success-btn'),
    retryEditBtn: document.getElementById('retry-edit-btn'),
    
    // Tab elements
    tabButtons: document.querySelectorAll('.tab-btn')
};

/**
 * Initialize the admin application
 */
function initApp() {
    // Check if user is authenticated
    checkAuthentication();
    
    // Add event listeners for status checkboxes
    elements.statusCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleStatusFilterChange);
    });
    
    elements.prevReportsPageBtn.addEventListener('click', () => navigateReportsPage(-1));
    elements.nextReportsPageBtn.addEventListener('click', () => navigateReportsPage(1));
    elements.backToGameBtn.addEventListener('click', () => window.location.href = '/');
    elements.logoutBtn.addEventListener('click', logout);
    
    // Edit comparison functionality
    elements.closeEditComparisonModalBtn.addEventListener('click', closeEditComparisonModal);
    elements.editComparisonForm.addEventListener('submit', saveComparisonChanges);
    elements.cancelEditBtn.addEventListener('click', closeEditComparisonModal);
    elements.closeEditSuccessBtn.addEventListener('click', closeEditComparisonModal);
    elements.retryEditBtn.addEventListener('click', resetEditForm);
    
    // Tab switching
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // Automatically load the reports tab on page load
    switchTab('reports');
}

/**
 * Check if the user is authenticated
 * If not, redirect to login page
 */
async function checkAuthentication() {
    // First check if we have a token in localStorage
    const token = localStorage.getItem('jwt_token');
    if (!token) {
        console.log('No token found in localStorage, redirecting to login');
        redirectToLogin();
        return;
    }
    
    try {
        // Try to load reports as a way to check authentication
        await loadAdminReports();
        adminState.isAuthenticated = true;
    } catch (error) {
        // If we get a 401 Unauthorized error, clear token and redirect to login page
        if (error.response && error.response.status === 401) {
            console.log('Token invalid or expired, redirecting to login');
            localStorage.removeItem('jwt_token'); // Clear invalid token
            redirectToLogin();
        } else {
            console.error('Error checking authentication:', error);
        }
    }
}

/**
 * Redirect to login page
 */
function redirectToLogin() {
    window.location.href = '/login.html';
}

/**
 * Logout the user
 * Clears the JWT token and redirects to login page
 */
function logout() {
    // Clear the token from localStorage
    localStorage.removeItem('jwt_token');
    console.log('User logged out, token removed');
    
    // Redirect to login page
    redirectToLogin();
}

/**
 * Switch between tabs
 * @param {string} tabName - The name of the tab to switch to
 */
function switchTab(tabName) {
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show the selected tab content
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Add active class to the clicked button
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
}

/**
 * Load reports for admin view
 */
async function loadAdminReports() {
    try {
        // Show loading state
        elements.reportsBody.innerHTML = '<tr><td colspan="7" class="loading-message">Loading reports...</td></tr>';
        
        // Prepare options for API call
        const options = {
            page: adminState.currentPage,
            pageSize: adminState.pageSize,
            statusFilters: adminState.statusFilters,
            sortBy: adminState.sortBy,
            sortDirection: adminState.sortDirection
        };
        
        // Call API to get reports
        const result = await apiService.getAdminReports(options);
        
        // Update admin state
        adminState.reports = result.reports;
        adminState.totalPages = result.total_pages;
        adminState.isAuthenticated = true;
        
        // Display reports
        displayAdminReports(result.reports);
        
        // Update pagination
        updateReportsPagination();
        
    } catch (error) {
        console.error('Error loading admin reports:', error);
        
        // Check if the error is due to authentication
        if (error.response && error.response.status === 401) {
            redirectToLogin();
            return;
        }
        
        elements.reportsBody.innerHTML = `<tr><td colspan="7" class="error-message-cell">Error loading reports: ${error.message}</td></tr>`;
    }
}

/**
 * Display reports in the admin table
 * @param {Array} reports - Array of report objects
 */
function displayAdminReports(reports) {
    elements.reportsBody.innerHTML = '';
    
    if (reports.length === 0) {
        elements.reportsBody.innerHTML = '<tr><td colspan="7" class="empty-message-cell">No reports found.</td></tr>';
        return;
    }
    
    reports.forEach(report => {
        const row = document.createElement('tr');
        
        // ID cell
        const idCell = document.createElement('td');
        idCell.textContent = report.report_id.substring(0, 8) + '...'; // Show truncated ID
        
        // Item 1 cell
        const item1Cell = document.createElement('td');
        item1Cell.textContent = report.item1;
        
        // Item 2 cell
        const item2Cell = document.createElement('td');
        item2Cell.textContent = report.item2;
        
        // Reason cell
        const reasonCell = document.createElement('td');
        reasonCell.textContent = report.reason || 'No reason provided';
        
        // Status cell
        const statusCell = document.createElement('td');
        const statusBadge = document.createElement('span');
        statusBadge.className = `status-badge status-${report.status}`;
        statusBadge.textContent = report.status;
        statusCell.appendChild(statusBadge);
        
        // Date cell
        const dateCell = document.createElement('td');
        const date = new Date(report.created_at);
        dateCell.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        // Actions cell
        const actionsCell = document.createElement('td');
        
        // Edit button
        const editBtn = document.createElement('button');
        editBtn.className = 'action-btn edit-btn';
        editBtn.textContent = 'Edit';
        editBtn.addEventListener('click', () => openEditComparisonModal(report));
        
        // Approve button
        const approveBtn = document.createElement('button');
        approveBtn.className = 'action-btn approve-btn';
        approveBtn.textContent = 'Approve';
        approveBtn.addEventListener('click', () => updateReportStatus(report.report_id, 'approved'));
        
        // Reject button
        const rejectBtn = document.createElement('button');
        rejectBtn.className = 'action-btn reject-btn';
        rejectBtn.textContent = 'Reject';
        rejectBtn.addEventListener('click', () => updateReportStatus(report.report_id, 'rejected'));
        
        actionsCell.appendChild(editBtn);
        actionsCell.appendChild(approveBtn);
        actionsCell.appendChild(rejectBtn);
        
        // Add cells to row
        row.appendChild(idCell);
        row.appendChild(item1Cell);
        row.appendChild(item2Cell);
        row.appendChild(reasonCell);
        row.appendChild(statusCell);
        row.appendChild(dateCell);
        row.appendChild(actionsCell);
        
        // Add row to table
        elements.reportsBody.appendChild(row);
    });
}

/**
 * Update pagination for reports
 */
function updateReportsPagination() {
    elements.reportsPageInfo.textContent = `Page ${adminState.currentPage} of ${adminState.totalPages}`;
    
    // Enable/disable pagination buttons
    elements.prevReportsPageBtn.disabled = adminState.currentPage <= 1;
    elements.nextReportsPageBtn.disabled = adminState.currentPage >= adminState.totalPages;
}

/**
 * Navigate to a different page of reports
 * @param {number} direction - Direction to navigate (-1 for previous, 1 for next)
 */
async function navigateReportsPage(direction) {
    const newPage = adminState.currentPage + direction;
    
    if (newPage < 1 || newPage > adminState.totalPages) {
        return;
    }
    
    adminState.currentPage = newPage;
    await loadAdminReports();
}

/**
 * Handle status filter checkbox changes
 */
async function handleStatusFilterChange(event) {
    const checkbox = event.target;
    
    // Handle "All" checkbox special case
    if (checkbox.id === 'status-all') {
        if (checkbox.checked) {
            // Uncheck all other status checkboxes
            elements.statusCheckboxes.forEach(cb => {
                if (cb.id !== 'status-all') {
                    cb.checked = false;
                }
            });
            adminState.statusFilters = [];
        } else {
            // If unchecking "All", check the first status option
            const firstStatusCheckbox = document.getElementById('status-pending');
            if (firstStatusCheckbox) {
                firstStatusCheckbox.checked = true;
                adminState.statusFilters = ['pending'];
            }
        }
    } else {
        // If checking any specific status, uncheck "All"
        if (checkbox.checked) {
            elements.statusAllCheckbox.checked = false;
        }
        
        // Update the statusFilters array based on checked checkboxes
        adminState.statusFilters = Array.from(elements.statusCheckboxes)
            .filter(cb => cb.checked && cb.id !== 'status-all')
            .map(cb => cb.value);
            
        // If no specific status is selected, check "All"
        if (adminState.statusFilters.length === 0) {
            elements.statusAllCheckbox.checked = true;
        }
    }
    
    // Reset to first page and reload reports
    adminState.currentPage = 1;
    await loadAdminReports();
}

/**
 * Update the status of a report
 * @param {string} reportId - The report ID
 * @param {string} status - The new status
 */
async function updateReportStatus(reportId, status) {
    try {
        await apiService.updateReportStatus(reportId, status);
        
        // Reload reports to reflect the change
        await loadAdminReports();
    } catch (error) {
        console.error('Error updating report status:', error);
        
        // Check if the error is due to authentication
        if (error.response && error.response.status === 401) {
            redirectToLogin();
            return;
        }
        
        alert(`Error updating report status: ${error.message}`);
    }
}

/**
 * Open the edit comparison modal
 * @param {Object} report - The report object
 */
function openEditComparisonModal(report) {
    // Store the current report data
    editComparisonState.item1 = report.item1;
    editComparisonState.item2 = report.item2;
    editComparisonState.reportId = report.report_id;
    
    // Set form values
    elements.editItem1.value = report.item1;
    elements.editItem2.value = report.item2;
    
    // Set radio buttons based on current comparison result
    if (report.result === 'item1') {
        elements.item1WinsRadio.checked = true;
    } else if (report.result === 'item2') {
        elements.item2WinsRadio.checked = true;
    } else {
        // Default to item1 if no result is set
        elements.item1WinsRadio.checked = true;
    }
    
    // Set description and emoji
    elements.editDescription.value = report.description || '';
    elements.editEmoji.value = report.emoji || '';
    
    // Show the modal
    elements.editComparisonModal.classList.remove('hidden');
    
    // Hide success/error messages
    elements.editSuccess.classList.add('hidden');
    elements.editError.classList.add('hidden');
}

/**
 * Close the edit comparison modal
 */
function closeEditComparisonModal() {
    elements.editComparisonModal.classList.add('hidden');
}

/**
 * Reset the edit form
 */
function resetEditForm() {
    elements.editSuccess.classList.add('hidden');
    elements.editError.classList.add('hidden');
}

/**
 * Save changes to a comparison
 * @param {Event} event - The form submit event
 */
async function saveComparisonChanges(event) {
    event.preventDefault();
    
    try {
        // Get form values
        const item1 = elements.editItem1.value;
        const item2 = elements.editItem2.value;
        const result = document.querySelector('input[name="result"]:checked').value;
        const description = elements.editDescription.value;
        const emoji = elements.editEmoji.value;
        
        // Validate form
        if (!description) {
            alert('Please enter a description');
            return;
        }
        
        if (!emoji) {
            alert('Please enter an emoji');
            return;
        }
        
        // Determine which item wins
        const item1Wins = result === 'item1';
        const item2Wins = result === 'item2';
        
        // Call API to update comparison
        await apiService.updateComparison(item1, item2, item1Wins, item2Wins, description, emoji);
        
        // If there's a report ID, update its status to reviewed
        if (editComparisonState.reportId) {
            await apiService.updateReportStatus(editComparisonState.reportId, 'reviewed');
        }
        
        // Show success message
        elements.editSuccess.classList.remove('hidden');
        
        // Reload reports to reflect the change
        await loadAdminReports();
        
    } catch (error) {
        console.error('Error saving comparison changes:', error);
        
        // Check if the error is due to authentication
        if (error.response && error.response.status === 401) {
            redirectToLogin();
            return;
        }
        
        elements.editError.classList.remove('hidden');
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);