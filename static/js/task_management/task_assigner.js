/* static/js/task_management/task_assigner.js */

let uploadedAttachments = [];
let currentChatTaskId = null;
let chatPollInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    initPage();
    setupUploadHandlers();
    
    // Chat Enter Key
    const chatInput = document.getElementById('chatInput');
    if(chatInput){
        chatInput.addEventListener('keypress', function(e) {
            if(e.key === 'Enter') sendMessage();
        });
    }

    // Clean up interval
    const chatModal = document.getElementById('chatModal');
    if(chatModal){
        chatModal.addEventListener('hidden.bs.modal', function () {
            if(chatPollInterval) clearInterval(chatPollInterval);
        });
    }
});

async function initPage() {
    await loadAssignees();
    loadTasks();
}

// --- 1. Load Assignees ---
async function loadAssignees() {
    const select = document.getElementById('assigneeSelect');
    if(!select) return;

    try {
        const res = await axios.get('/api/tasks/assignees');
        const creators = res.data;
        
        select.innerHTML = '<option value="">Select Creator...</option>';
        if(creators.length === 0) {
            select.innerHTML += '<option disabled>No models found for your team</option>';
        }

        creators.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.text = c.full_name || c.username;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load creators", err);
        select.innerHTML = '<option disabled>Error loading list</option>';
    }
}

// --- 2. Load Tasks (Updated for UI Consistency) ---
async function loadTasks() {
    const tbody = document.getElementById('taskTableBody');
    if(!tbody) return;

    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-5"><div class="spinner-border text-warning"></div></td></tr>';

    try {
        const res = await axios.get('/api/tasks/');
        const tasks = res.data;

        if(tasks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-5 text-muted">No tasks found.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        tasks.forEach(task => {
            const assigneeName = task.assignee?.full_name || "Unknown";
            const assigneePic = task.assignee?.profile_picture_url || `https://ui-avatars.com/api/?name=${assigneeName}&background=random`;
            const dateStr = task.due_date ? new Date(task.due_date).toLocaleDateString() : '-';
            
            let statusClass = 'badge-todo';
            if(task.status === 'In Progress') statusClass = 'badge-in_progress';
            if(task.status === 'In Review') statusClass = 'badge-review';
            if(task.status === 'Completed') statusClass = 'badge-completed';
            if(task.status === 'Blocked') statusClass = 'badge-blocked';

            const row = `
                <tr>
                    <td>
                        <div class="fw-bold text-dark" style="font-size:0.95rem;">${task.title}</div>
                        <div class="small text-muted text-truncate" style="max-width: 200px;">${task.description || ''}</div>
                    </td>
                    <td>
                        <div class="d-flex align-items-center">
                            <img src="${assigneePic}" class="user-avatar-small">
                            <span class="small fw-medium">${assigneeName}</span>
                        </div>
                    </td>
                    <td><span class="badge bg-light text-dark border fw-normal">${task.context}</span></td>
                    <td><span class="badge-status ${statusClass}">${task.status}</span></td>
                    <td class="small text-muted">${dateStr}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-light text-muted border-0" onclick="openChat(${task.id}, '${task.title}')">
                            <i class="ri-message-3-line fs-5"></i> 
                            ${task.chat_count > 0 ? `<span class="badge bg-danger rounded-pill position-absolute" style="font-size:0.6rem; transform:translate(-10px, -5px)">${task.chat_count}</span>` : ''}
                        </button>
                    </td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });

    } catch (err) {
        console.error(err);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading tasks.</td></tr>';
    }
}

// --- 3. Upload Logic (Fix for "Nothing Happening") ---
function setupUploadHandlers() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    if(!dropZone || !fileInput) return;

    // Trigger file input on click
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Handle File Selection
    fileInput.addEventListener('change', (e) => {
        if(e.target.files.length > 0){
            handleFiles(e.target.files);
        }
    });

    // Drag & Drop Visuals
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
}

async function handleFiles(files) {
    const list = document.getElementById('filePreviewList');
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const tempId = `file-${Date.now()}-${i}`;
        
        const html = `
            <div class="file-preview-item" id="${tempId}">
                <div class="file-preview-icon"><div class="spinner-border spinner-border-sm text-primary"></div></div>
                <div class="flex-grow-1 small text-truncate ps-2">${file.name}</div>
            </div>`;
        list.insertAdjacentHTML('beforeend', html);

        try {
            // 1. Get Presigned URL
            const ticketRes = await axios.post('/api/upload/presigned-url', {
                filename: file.name,
                content_type: file.type || 'application/octet-stream',
                category: "vault" 
            });
            
            const { upload_url, public_url } = ticketRes.data.ticket;

            // 2. Upload to R2 (This triggers CORS if bucket settings are wrong)
            await axios.put(upload_url, file, {
                headers: { 'Content-Type': file.type || 'application/octet-stream' }
            });

            // 3. Success
            uploadedAttachments.push({
                file_url: public_url,
                file_size_mb: parseFloat((file.size / (1024*1024)).toFixed(2)),
                mime_type: file.type || 'application/octet-stream',
                tags: "Reference"
            });

            const iconEl = document.querySelector(`#${tempId} .file-preview-icon`);
            if(iconEl) iconEl.innerHTML = '<i class="ri-check-line text-success fs-5"></i>';

        } catch (err) {
            console.error("Upload failed", err);
            toastr.error(`Failed to upload ${file.name}. Check Console.`);
            
            const iconEl = document.querySelector(`#${tempId} .file-preview-icon`);
            if(iconEl) iconEl.innerHTML = '<i class="ri-error-warning-line text-danger fs-5"></i>';
        }
    }
}

// --- 4. Create Task ---
async function createAtomicTask() {
    const title = document.getElementById('taskTitle').value;
    const assignee = document.getElementById('assigneeSelect').value;

    if(!title || !assignee) {
        toastr.warning('Title and Assignee are required.');
        return;
    }

    // Gather Switches
    const reqFace = document.getElementById('reqFace').checked;
    const reqWatermark = document.getElementById('reqWatermark').checked;

    const payload = {
        title: title,
        description: document.getElementById('taskDescription').value,
        assignee_id: parseInt(assignee),
        priority: document.getElementById('taskPriority').value,
        due_date: document.getElementById('dueDate').value || null,
        context: document.getElementById('taskContext').value,
        req_content_type: document.getElementById('contentType').value,
        req_length: document.getElementById('contentLength').value,
        req_face_visible: reqFace,
        req_watermark: reqWatermark,
        attachments: uploadedAttachments 
    };

    if(typeof myshowLoader === 'function') myshowLoader();

    try {
        await axios.post('/api/tasks/', payload);
        
        // Success
        const modalEl = document.getElementById('taskModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        toastr.success('Task assigned successfully!');
        
        // Reset Form
        document.getElementById('taskForm').reset();
        document.getElementById('filePreviewList').innerHTML = '';
        uploadedAttachments = [];
        
        // Refresh Table
        loadTasks();

    } catch (err) {
        const msg = err.response?.data?.detail || "Failed to create task";
        toastr.error(msg);
    } finally {
        if(typeof myhideLoader === 'function') myhideLoader();
    }
}

// --- 5. Helpers ---
function openCreateTaskModal() {
    new bootstrap.Modal(document.getElementById('taskModal')).show();
}

function setPriority(el) {
    document.querySelectorAll('.priority-option').forEach(d => d.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('taskPriority').value = el.getAttribute('data-value');
}

function openChat(taskId, title) {
    currentChatTaskId = taskId;
    const titleEl = document.getElementById('chatTaskTitle');
    if(titleEl) titleEl.innerText = title;
    
    new bootstrap.Modal(document.getElementById('chatModal')).show();
    loadChatHistory();
    
    if(chatPollInterval) clearInterval(chatPollInterval);
    chatPollInterval = setInterval(loadChatHistory, 3000);
}

async function loadChatHistory() {
    if(!currentChatTaskId) return;
    try {
        const res = await axios.get(`/api/tasks/${currentChatTaskId}/chat`);
        const container = document.getElementById('chatContainer');
        if(!container) return;
        
        container.innerHTML = '';
        
        if(res.data.length === 0) {
            container.innerHTML = '<div class="text-center small text-muted mt-5">No messages yet.</div>';
            return;
        }

        res.data.forEach(msg => {
            if(msg.is_system_log) {
                container.insertAdjacentHTML('beforeend', `<div class="text-center small text-muted fst-italic my-2" style="font-size:0.75rem;">${msg.message}</div>`);
            } else {
                // Determine alignment (Need a way to know "my" ID, usually stored in meta tag)
                const myId = document.querySelector('meta[name="user-id"]')?.content;
                const isMe = myId && parseInt(myId) === msg.author.id;
                
                const bubbleClass = isMe ? 'sent' : 'received';
                
                const bubble = `
                    <div class="d-flex flex-column ${isMe ? 'align-items-end' : 'align-items-start'}">
                        <div class="chat-bubble ${bubbleClass}">
                            ${msg.message}
                        </div>
                        <span class="text-muted" style="font-size:0.65rem; margin-top:2px;">${msg.author.full_name || 'User'}</span>
                    </div>`;
                container.insertAdjacentHTML('beforeend', bubble);
            }
        });
        
        // Auto scroll to bottom
        container.scrollTop = container.scrollHeight;

    } catch(err) { console.error(err); }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const val = input.value.trim();
    if(!val || !currentChatTaskId) return;

    try {
        await axios.post(`/api/tasks/${currentChatTaskId}/chat`, { message: val });
        input.value = '';
        loadChatHistory();
    } catch(err) { toastr.error("Failed to send"); }
}