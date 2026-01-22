// static/js/model_invoice/model_invoice.js

document.addEventListener('DOMContentLoaded', () => {
    loadCreators();
    loadInvoices();
    setupLiveCalculation();
});

let invoiceModal;
// Helper: Format Money
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
};

// --- 1. Notification Toast Helper ---
function showToast(message, isError = false) {
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastMessage');
    const toastIcon = toastEl.querySelector('.ni');
    
    toastBody.textContent = message;
    
    if (isError) {
        toastIcon.className = 'ni ni-fat-remove me-2 text-danger';
        toastBody.classList.remove('text-success');
        toastBody.classList.add('text-danger');
    } else {
        toastIcon.className = 'ni ni-check-bold me-2 text-success';
        toastBody.classList.remove('text-danger');
        toastBody.classList.add('text-success');
    }

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// --- 2. Live Calculation Logic ---
function setupLiveCalculation() {
    const inputs = document.querySelectorAll('.money-input');
    const totalDisplay = document.getElementById('displayTotal');

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            let total = 0;
            inputs.forEach(inp => {
                total += parseFloat(inp.value) || 0;
            });
            totalDisplay.textContent = formatCurrency(total);
        });
    });
}

// --- 3. Load Data ---
async function loadInvoices() {
    const tableBody = document.getElementById('invoiceTableBody');
    const spinner = document.getElementById('loadingSpinner');
    
    // Filters
    const userId = document.getElementById('filterUser').value;
    const dateFrom = document.getElementById('filterDateFrom').value;
    const dateTo = document.getElementById('filterDateTo').value;

    let query = new URLSearchParams();
    if (userId) query.append('user_id', userId);
    if (dateFrom) query.append('from_date', dateFrom);
    if (dateTo) query.append('to_date', dateTo);

    tableBody.innerHTML = '';
    spinner.classList.remove('d-none');

    try {
        const response = await fetch(`/api/model_invoice/?${query.toString()}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (!response.ok) throw new Error('Failed to fetch data');
        
        const invoices = await response.json();
        spinner.classList.add('d-none');
        renderTable(invoices);

    } catch (error) {
        console.error(error);
        spinner.classList.add('d-none');
        showToast('Error loading records. Please refresh.', true);
    }
}

function renderTable(invoices) {
    const tableBody = document.getElementById('invoiceTableBody');
    
    if (invoices.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5">
                    <div class="d-flex flex-column align-items-center">
                        <i class="ni ni-folder-17 text-secondary text-lg mb-2"></i>
                        <h6 class="text-secondary font-weight-normal">No invoice records found.</h6>
                    </div>
                </td>
            </tr>`;
        return;
    }

    invoices.forEach(inv => {
        const userName = inv.user ? (inv.user.full_name || inv.user.username) : 'Unknown User';
        const userImg = inv.user && inv.user.profile_picture_url ? inv.user.profile_picture_url : '/static/img/default-avatar.png';
        
        // Summing up miscellaneous for display if needed, or just showing total
        const row = `
            <tr>
                <td class="ps-4">
                    <span class="text-secondary text-xs font-weight-bold">${new Date(inv.invoice_date).toLocaleDateString()}</span>
                </td>
                <td>
                    <div class="d-flex px-2 py-1">
                        <div>
                            <img src="${userImg}" class="avatar avatar-sm me-3" alt="user1">
                        </div>
                        <div class="d-flex flex-column justify-content-center">
                            <h6 class="mb-0 text-sm font-weight-bold">${userName}</h6>
                            <p class="text-xs text-secondary mb-0">ID: ${inv.user_id}</p>
                        </div>
                    </div>
                </td>
                <td class="text-end">
                    <span class="text-xs font-weight-bold text-secondary">${inv.subscription > 0 ? formatCurrency(inv.subscription) : '-'}</span>
                </td>
                <td class="text-end">
                    <span class="text-xs font-weight-bold text-secondary">${inv.tips > 0 ? formatCurrency(inv.tips) : '-'}</span>
                </td>
                <td class="text-end">
                    <span class="text-xs font-weight-bold text-secondary">${(inv.posts + inv.messages) > 0 ? formatCurrency(inv.posts + inv.messages) : '-'}</span>
                </td>
                <td class="text-end align-middle">
                    <span class="badge badge-sm bg-gradient-success">${formatCurrency(inv.total_earnings)}</span>
                </td>
                <td class="text-end align-middle">
                    <a href="javascript:;" class="text-secondary font-weight-bold text-xs me-3" 
                       onclick='editInvoice(${JSON.stringify(inv)})' data-bs-toggle="tooltip" title="Edit">
                        <i class="fas fa-pencil-alt"></i>
                    </a>
                    <a href="javascript:;" class="text-danger font-weight-bold text-xs pe-3" 
                       onclick="deleteInvoice(${inv.id})" data-bs-toggle="tooltip" title="Delete">
                        <i class="fas fa-trash"></i>
                    </a>
                </td>
            </tr>
        `;
        tableBody.insertAdjacentHTML('beforeend', row);
    });
}

async function loadCreators() {
    try {
        const response = await fetch('/api/users/?role=digital_creator', {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const users = await response.json();
        
        const filterSelect = document.getElementById('filterUser');
        const formSelect = document.getElementById('inputUser');

        users.forEach(u => {
            const option = `<option value="${u.id}">${u.full_name || u.username}</option>`;
            filterSelect.insertAdjacentHTML('beforeend', option);
            formSelect.insertAdjacentHTML('beforeend', option);
        });
    } catch (error) {
        console.error("Could not load creators", error);
    }
}

// --- 4. Modal Functions ---
function openInvoiceModal() {
    document.getElementById('invoiceForm').reset();
    document.getElementById('invoiceId').value = '';
    document.getElementById('modalTitle').innerText = "New Revenue Record";
    document.getElementById('displayTotal').innerText = "$0.00";
    document.getElementById('inputDate').valueAsDate = new Date();
    
    invoiceModal = new bootstrap.Modal(document.getElementById('invoiceModal'));
    invoiceModal.show();
}

function editInvoice(data) {
    document.getElementById('modalTitle').innerText = "Edit Revenue Record";
    document.getElementById('invoiceId').value = data.id;
    document.getElementById('inputUser').value = data.user_id;
    document.getElementById('inputDate').value = data.invoice_date;
    
    document.getElementById('inputSubs').value = data.subscription || '';
    document.getElementById('inputTips').value = data.tips || '';
    document.getElementById('inputMsgs').value = data.messages || '';
    document.getElementById('inputPosts').value = data.posts || '';
    document.getElementById('inputReferrals').value = data.referrals || '';
    document.getElementById('inputStreams').value = data.streams || '';
    document.getElementById('inputOthers').value = data.others || '';

    // Trigger calc to show total immediately
    const total = (data.subscription || 0) + (data.tips || 0) + (data.messages || 0) + 
                  (data.posts || 0) + (data.referrals || 0) + (data.streams || 0) + (data.others || 0);
    document.getElementById('displayTotal').innerText = formatCurrency(total);

    invoiceModal = new bootstrap.Modal(document.getElementById('invoiceModal'));
    invoiceModal.show();
}

async function submitInvoice() {
    const btn = document.getElementById('btnSave');
    const spinner = document.getElementById('btnSaveSpinner');
    const form = document.getElementById('invoiceForm');
    
    // Simple validation
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const id = document.getElementById('invoiceId').value;
    const isEdit = !!id;
    
    const payload = {
        user_id: document.getElementById('inputUser').value,
        invoice_date: document.getElementById('inputDate').value,
        subscription: parseFloat(document.getElementById('inputSubs').value) || 0,
        tips: parseFloat(document.getElementById('inputTips').value) || 0,
        messages: parseFloat(document.getElementById('inputMsgs').value) || 0,
        posts: parseFloat(document.getElementById('inputPosts').value) || 0,
        referrals: parseFloat(document.getElementById('inputReferrals').value) || 0,
        streams: parseFloat(document.getElementById('inputStreams').value) || 0,
        others: parseFloat(document.getElementById('inputOthers').value) || 0,
    };

    // UI Loading State
    btn.disabled = true;
    spinner.classList.remove('d-none');

    const url = isEdit ? `/api/model_invoice/${id}` : '/api/model_invoice/';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            invoiceModal.hide();
            loadInvoices();
            showToast(isEdit ? 'Record updated successfully!' : 'Record added successfully!');
        } else {
            showToast('Failed to save record. Check inputs.', true);
        }
    } catch (e) {
        console.error(e);
        showToast('Network error occurred.', true);
    } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
    }
}

async function deleteInvoice(id) {
    if (!confirm("Are you sure? This will permanently remove this financial record.")) return;

    try {
        const response = await fetch(`/api/model_invoice/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });

        if (response.ok) {
            loadInvoices();
            showToast('Record deleted.');
        } else {
            showToast('Failed to delete record.', true);
        }
    } catch (e) {
        console.error(e);
        showToast('Error deleting record.', true);
    }
}