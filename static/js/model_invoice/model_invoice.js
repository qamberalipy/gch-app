// static/js/model_invoice/model_invoice.js

console.log("Model Invoice JS Initializing...");

let currentPage = 1;
let totalItems = 0;
const pageSize = 10;
let invoiceModal;

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Loaded - Model Invoice");
    
    // Initialize Modal
    const modalEl = document.getElementById('invoiceModal');
    if (modalEl) {
        invoiceModal = new bootstrap.Modal(modalEl);
    }

    // Attach Event Listeners (Safe method)
    document.getElementById('btnNewInvoice')?.addEventListener('click', openInvoiceModal);
    document.getElementById('btnApplyFilters')?.addEventListener('click', () => loadInvoices(1));
    document.getElementById('btnResetFilters')?.addEventListener('click', resetFilters);
    document.getElementById('btnSave')?.addEventListener('click', submitInvoice);
    
    document.getElementById('btnPrevPage')?.addEventListener('click', () => {
        if (currentPage > 1) loadInvoices(currentPage - 1);
    });
    
    document.getElementById('btnNextPage')?.addEventListener('click', () => {
        const totalPages = Math.ceil(totalItems / pageSize);
        if (currentPage < totalPages) loadInvoices(currentPage + 1);
    });

    // Initial Load
    loadCreators();
    loadInvoices(1);
    setupLiveCalculation();
});

// --- Formatting ---
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
};

// --- Toast Helper ---
function showToast(message, isError = false) {
    const toastEl = document.getElementById('liveToast');
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastMessage');
    
    if(!toastEl) return;

    toastBody.textContent = message;
    if (isError) {
        toastTitle.className = 'me-auto text-danger fw-bold';
        toastTitle.textContent = 'Error';
    } else {
        toastTitle.className = 'me-auto text-success fw-bold';
        toastTitle.textContent = 'Success';
    }

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// --- Live Calculation ---
function setupLiveCalculation() {
    const inputs = document.querySelectorAll('.money-input');
    const totalDisplay = document.getElementById('displayTotal');

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            let total = 0;
            inputs.forEach(inp => total += parseFloat(inp.value) || 0);
            if(totalDisplay) totalDisplay.textContent = formatCurrency(total);
        });
    });
}

// --- Load Data ---
async function loadInvoices(page) {
    const tableBody = document.getElementById('invoiceTableBody');
    const emptyState = document.getElementById('emptyState');
    const btnPrev = document.getElementById('btnPrevPage');
    const btnNext = document.getElementById('btnNextPage');
    const pageInfo = document.getElementById('paginationInfo');
    
    // Show loading state
    if(tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-5">
                    <div class="spinner-border text-warning" role="status"></div>
                    <p class="text-xs text-muted mt-2">Loading...</p>
                </td>
            </tr>`;
    }
    if(emptyState) emptyState.classList.add('d-none');

    // Prepare Query
    const userId = document.getElementById('filterUser')?.value;
    const dateFrom = document.getElementById('filterDateFrom')?.value;
    const dateTo = document.getElementById('filterDateTo')?.value;

    let query = new URLSearchParams({
        page: page,
        size: pageSize
    });
    
    if (userId) query.append('user_id', userId);
    if (dateFrom) query.append('from_date', dateFrom);
    if (dateTo) query.append('to_date', dateTo);

    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/model_invoice/?${query.toString()}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }
        
        const data = await response.json();
        
        currentPage = data.page;
        totalItems = data.total;
        
        renderTable(data.items);
        updatePaginationUI(btnPrev, btnNext, pageInfo);

    } catch (error) {
        console.error("Load Error:", error);
        if(tableBody) tableBody.innerHTML = '';
        if(emptyState) {
            emptyState.innerHTML = `<p class="text-danger small">Error loading data: ${error.message}</p>`;
            emptyState.classList.remove('d-none');
        }
    }
}

function renderTable(invoices) {
    const tableBody = document.getElementById('invoiceTableBody');
    const emptyState = document.getElementById('emptyState');
    
    if (!tableBody) return;
    tableBody.innerHTML = '';

    if (!invoices || invoices.length === 0) {
        if(emptyState) emptyState.classList.remove('d-none');
        return;
    }
    
    if(emptyState) emptyState.classList.add('d-none');

    invoices.forEach(inv => {
        const userName = inv.user ? (inv.user.full_name || inv.user.username) : 'Unknown User';
        const userImg = inv.user && inv.user.profile_picture_url ? inv.user.profile_picture_url : '/static/img/default-avatar.png';
        
        // Date Fix
        let dateStr = inv.invoice_date;
        try {
             // Split YYYY-MM-DD manually to prevent timezone offset issues
            const parts = inv.invoice_date.split('-');
            if(parts.length === 3) {
                 const d = new Date(parts[0], parts[1] - 1, parts[2]);
                 dateStr = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
            }
        } catch(e) { console.error("Date parse error", e); }
        
        // We use window.editInvoice to ensure global scope access for onclick
        const row = `
            <tr>
                <td class="fw-bold text-secondary">#${inv.id}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <img src="${userImg}" class="user-avatar-small" alt="dp">
                        <div>
                            <div class="fw-bold text-dark text-sm">${userName}</div>
                            <div class="text-muted text-xs">ID: ${inv.user_id}</div>
                        </div>
                    </div>
                </td>
                <td class="text-secondary text-sm font-weight-500">${dateStr}</td>
                <td class="text-end fw-bold text-success">${formatCurrency(inv.total_earnings)}</td>
                <td class="text-end">
                    <i class="ri-pencil-fill action-icon me-2" onclick='window.editInvoice(${JSON.stringify(inv)})' title="Edit"></i>
                    <i class="ri-delete-bin-line action-icon delete" onclick="window.deleteInvoice(${inv.id})" title="Delete"></i>
                </td>
            </tr>
        `;
        tableBody.insertAdjacentHTML('beforeend', row);
    });
}

function updatePaginationUI(btnPrev, btnNext, pageInfo) {
    if(!btnPrev || !btnNext || !pageInfo) return;

    const totalPages = Math.ceil(totalItems / pageSize);
    const start = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalItems);

    pageInfo.innerText = `Showing ${start}-${end} of ${totalItems}`;
    
    btnPrev.disabled = currentPage === 1;
    btnNext.disabled = currentPage >= totalPages || totalItems === 0;
}

function resetFilters() {
    if(document.getElementById('filterUser')) document.getElementById('filterUser').value = '';
    if(document.getElementById('filterDateFrom')) document.getElementById('filterDateFrom').value = '';
    if(document.getElementById('filterDateTo')) document.getElementById('filterDateTo').value = '';
    loadInvoices(1);
}

// --- Creators Dropdown ---
async function loadCreators() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/users/?role=digital_creator', {
             headers: { 'Authorization': `Bearer ${token}` }
        });
        if(!response.ok) return;
        const users = await response.json();
        
        const filterSelect = document.getElementById('filterUser');
        const formSelect = document.getElementById('inputUser');

        // Clear existing (except first option) if re-running
        if(filterSelect && filterSelect.options.length > 1) filterSelect.length = 1;
        if(formSelect && formSelect.options.length > 1) formSelect.length = 1;

        users.forEach(u => {
            const option = `<option value="${u.id}">${u.full_name || u.username}</option>`;
            if(filterSelect) filterSelect.insertAdjacentHTML('beforeend', option);
            if(formSelect) formSelect.insertAdjacentHTML('beforeend', option);
        });
    } catch (error) {
        console.error("Could not load creators", error);
    }
}

// --- Functions attached to WINDOW for Global Scope Access ---

// 1. Open Modal
function openInvoiceModal() {
    document.getElementById('invoiceForm').reset();
    document.getElementById('invoiceId').value = '';
    document.getElementById('modalTitle').innerText = "Add Revenue Record";
    document.getElementById('displayTotal').innerText = "$0.00";
    document.getElementById('inputDate').valueAsDate = new Date();
    
    if(invoiceModal) invoiceModal.show();
}

// 2. Edit Invoice
window.editInvoice = function(data) {
    document.getElementById('modalTitle').innerText = "Edit Revenue Record";
    document.getElementById('invoiceId').value = data.id;
    document.getElementById('inputUser').value = data.user_id;
    document.getElementById('inputDate').value = data.invoice_date;
    
    document.getElementById('inputSubs').value = data.subscription || '';
    document.getElementById('inputTips').value = data.tips || '';
    document.getElementById('inputMsgs').value = data.messages || '';
    document.getElementById('inputPosts').value = data.posts || '';
    document.getElementById('inputReferrals').value = data.referrals || '';
    document.getElementById('inputOthers').value = data.others || '';

    const total = (data.subscription || 0) + (data.tips || 0) + (data.messages || 0) + 
                  (data.posts || 0) + (data.referrals || 0) + (data.others || 0);
    document.getElementById('displayTotal').innerText = formatCurrency(total);

    if(invoiceModal) invoiceModal.show();
};

// 3. Submit
async function submitInvoice() {
    const btn = document.getElementById('btnSave');
    const spinner = document.getElementById('btnSaveSpinner');
    const form = document.getElementById('invoiceForm');
    
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
        others: parseFloat(document.getElementById('inputOthers').value) || 0,
    };

    btn.disabled = true;
    if(spinner) spinner.classList.remove('d-none');

    const url = isEdit ? `/api/model_invoice/${id}` : '/api/model_invoice/';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const token = localStorage.getItem('token');
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            if(invoiceModal) invoiceModal.hide();
            loadInvoices(currentPage); 
            showToast(isEdit ? 'Record updated successfully!' : 'Record added successfully!');
        } else {
            showToast('Failed to save record.', true);
        }
    } catch (e) {
        console.error(e);
        showToast('Network error occurred.', true);
    } finally {
        btn.disabled = false;
        if(spinner) spinner.classList.add('d-none');
    }
}

// 4. Delete
window.deleteInvoice = async function(id) {
    if (!confirm("Are you sure? This action cannot be undone.")) return;

    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/model_invoice/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            loadInvoices(currentPage);
            showToast('Record deleted.');
        } else {
            showToast('Failed to delete record.', true);
        }
    } catch (e) {
        console.error(e);
        showToast('Error deleting record.', true);
    }
};