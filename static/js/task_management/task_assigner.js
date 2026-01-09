/* static/js/task_assigner.js */

// --- Global State ---
let uploadedAttachments = []; // Stores {file_url, mime_type...} ready for API
let currentChatTaskId = null;
let chatPollInterval = null;
let currentUser = null; // Loaded from token

$(document).ready(function() {
    initPage();

    // --- Drag & Drop Event Listeners ---
    const dropZone = document.getElementById('dropZone');
    
    $('#dropZone').on('click', () => $('#fileInput').click());
    
    $('#fileInput').on('change', function(e) {
        handleFiles(e.target.files);
    });

    // Drag effects
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });
    
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        handleFiles(dt.files);
    }, false);

    // Save Task Button
    $('#btnSaveTask').on('click', createAtomicTask);

    // Chat Enter Key
    $('#chatInput').on('keypress', function(e) {
        if(e.which === 13) sendMessage();
    });

    // Stop Chat polling when modal closes
    $('#chatModal').on('hidden.bs.modal', function () {
        if(chatPollInterval) clearInterval(chatPollInterval);
    });
});

// --- 1. Initialization ---
async function initPage() {
    // 1. Get User from Token (Shared logic)
    const token = localStorage.getItem('access_token');
    if(token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Assuming sub is {user_id: 1, role: '...'} or just ID depending on your login logic
        currentUser = typeof payload.sub === 'string' ? JSON.parse(payload.sub) : payload.sub;
    }

    await loadAssignees();
    loadTasks();
}

// --- 2. Load Assignees (Creators) ---
async function loadAssignees() {
    try {
        // Use the utility endpoint provided in user.py
        const res = await axios.get('/api/users/available/models');
        const creators = res.data;
        
        const $select = $('#assigneeSelect');
        $select.empty().append('<option value="">Select Creator...</option>');
        
        creators.forEach(c => {
            $select.append(`<option value="${c.id}">${c.full_name || c.username}</option>`);
        });
    } catch (err) {
        console.error("Failed to load creators", err);
    }
}

// --- 3. Load Tasks List ---
async function loadTasks() {
    const $tbody = $('#taskTableBody');
    $tbody.html('<tr><td colspan="6" class="text-center py-5">Loading...</td></tr>');

    try {
        const res = await axios.get('/api/tasks/');
        const tasks = res.data;

        if(tasks.length === 0) {
            $tbody.html('<tr><td colspan="6" class="text-center py-5 text-muted">No tasks found. Create one!</td></tr>');
            return;
        }

        $tbody.empty();
        tasks.forEach(task => {
            const assigneeName = task.assignee?.full_name || "Unknown";
            const assigneePic = task.assignee?.profile_picture_url || `https://ui-avatars.com/api/?name=${assigneeName}`;
            const dateStr = task.due_date ? new Date(task.due_date).toLocaleDateString() : '-';
            
            const row = `
                <tr>
                    <td>
                        <div class="fw-bold text-dark">${task.title}</div>
                        <div class="small text-muted text-truncate" style="max-width: 200px;">${task.description || ''}</div>
                    </td>
                    <td>
                        <div class="d-flex align-items-center">
                            <img src="${assigneePic}" class="rounded-circle me-2" width="30" height="30" style="object-fit:cover;">
                            <span class="small fw-medium">${assigneeName}</span>
                        </div>
                    </td>
                    <td><span class="badge bg-light text-dark border">${task.context}</span></td>
                    <td><span class="badge-status badge-${task.status.toLowerCase().replace(' ', '_')}">${task.status}</span></td>
                    <td class="small">${dateStr}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-light text-muted" onclick="openChat(${task.id}, '${task.title}')">
                            <i class="ri-message-3-line"></i> 
                            ${task.chat_count > 0 ? `<span class="badge bg-danger rounded-pill" style="font-size:0.6rem;">${task.chat_count}</span>` : ''}
                        </button>
                        <button class="btn btn-sm btn-light text-muted ms-1"><i class="ri-pencil-line"></i></button>
                    </td>
                </tr>
            `;
            $tbody.append(row);
        });

    } catch (err) {
        $tbody.html('<tr><td colspan="6" class="text-center text-danger">Error loading tasks.</td></tr>');
    }
}

// --- 4. File Upload Handlers (Presigned URL) ---
async function handleFiles(files) {
    const $list = $('#filePreviewList');
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // UI: Add loading state
        const tempId = `file-${Date.now()}`;
        const itemHtml = `
            <div class="file-preview-item" id="${tempId}">
                <div class="file-preview-icon"><div class="spinner-border spinner-border-sm"></div></div>
                <div class="flex-grow-1 small text-truncate">${file.name}</div>
            </div>`;
        $list.append(itemHtml);

        try {
            // 1. Get Presigned URL
            const ticketRes = await axios.post('/api/upload/presigned-url', {
                filename: file.name,
                content_type: file.type,
                category: "vault" 
            });
            
            const { upload_url, public_url } = ticketRes.data.ticket;

            // 2. Upload to R2 (Direct)
            await axios.put(upload_url, file, {
                headers: { 'Content-Type': file.type }
            });

            // 3. Success! Add to global array for the final POST
            // Note: For videos, you ideally generate a thumbnail on client side here.
            // For now, we leave thumbnail_url null or a placeholder.
            uploadedAttachments.push({
                file_url: public_url,
                file_size_mb: parseFloat((file.size / (1024*1024)).toFixed(2)),
                mime_type: file.type,
                thumbnail_url: null, // If you implement JS canvas thumb gen, put it here
                tags: "Reference"
            });

            // Update UI
            $(`#${tempId} .file-preview-icon`).html('<i class="ri-check-line text-success"></i>');

        } catch (err) {
            console.error(err);
            $(`#${tempId} .file-preview-icon`).html('<i class="ri-error-warning-line text-danger"></i>');
            showToastMessage('error', `Failed to upload ${file.name}`);
        }
    }
}

// --- 5. Create Task (Atomic) ---
async function createAtomicTask() {
    const payload = {
        title: $('#taskTitle').val(),
        description: $('#taskDescription').val(),
        assignee_id: $('#assigneeSelect').val(),
        priority: $('#taskPriority').val(),
        due_date: $('#dueDate').val() || null, // Ensure null if empty
        context: $('#taskContext').val(),
        req_content_type: $('#contentType').val(),
        req_length: $('#contentLength').val(),
        req_face_visible: $('#reqFace').is(':checked'),
        req_watermark: $('#reqWatermark').is(':checked'),
        
        // The Atomic Magic: Send files WITH the task
        attachments: uploadedAttachments 
    };

    if(!payload.title || !payload.assignee_id) {
        showToastMessage('warning', 'Title and Assignee are required.');
        return;
    }

    myshowLoader();
    try {
        await axios.post('/api/tasks/', payload);
        
        $('#taskModal').modal('hide');
        showToastMessage('success', 'Task assigned successfully!');
        
        // Reset Form
        $('#taskForm')[0].reset();
        $('#filePreviewList').empty();
        uploadedAttachments = [];
        
        loadTasks(); // Refresh table
    } catch (err) {
        showToastMessage('error', err.response?.data?.detail || "Failed to create task");
    } finally {
        myhideLoader();
    }
}

// --- 6. Chat System ---
function openChat(taskId, taskTitle) {
    currentChatTaskId = taskId;
    $('#chatTaskTitle').text(taskTitle);
    $('#chatContainer').html('<div class="text-center small text-muted mt-5">Loading chat...</div>');
    $('#chatModal').modal('show');
    
    loadChatHistory();
    // Poll every 3 seconds
    if(chatPollInterval) clearInterval(chatPollInterval);
    chatPollInterval = setInterval(loadChatHistory, 3000);
}

async function loadChatHistory() {
    if(!currentChatTaskId) return;
    try {
        const res = await axios.get(`/api/tasks/${currentChatTaskId}/chat`);
        renderChat(res.data);
    } catch (err) {
        console.error("Chat load failed");
    }
}

function renderChat(messages) {
    const $container = $('#chatContainer');
    // Simple diffing: If count changed, re-render (Enhancement: append only new)
    // For simplicity in this demo, we re-render (it's fast for text)
    $container.empty();

    if(messages.length === 0) {
        $container.html('<div class="text-center small text-muted mt-5">No messages yet. Start the conversation!</div>');
        return;
    }

    messages.forEach(msg => {
        // Assume currentUser ID is available via token logic or API
        // For this demo, let's look at the 'author' object
        // NOTE: You need to know YOUR user ID. 
        // We set 'currentUser' in initPage().
        
        const isMe = (msg.author.id === currentUser?.user_id) || (msg.author.id === currentUser?.id);
        
        const bubbleClass = isMe ? 'sent' : 'received';
        const time = new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let html = '';
        if(msg.is_system_log) {
            html = `<div class="text-center small text-muted fst-italic my-2">${msg.message}</div>`;
        } else {
            html = `
                <div class="chat-bubble ${bubbleClass}">
                    ${msg.message}
                    <div class="chat-meta">${time}</div>
                </div>
            `;
        }
        $container.append(html);
    });
    
    // Scroll to bottom
    // $container.scrollTop($container[0].scrollHeight);
}

async function sendMessage() {
    const text = $('#chatInput').val().trim();
    if(!text || !currentChatTaskId) return;

    try {
        await axios.post(`/api/tasks/${currentChatTaskId}/chat`, { message: text });
        $('#chatInput').val('');
        loadChatHistory(); // Refresh immediately
    } catch (err) {
        showToastMessage('error', "Failed to send message");
    }
}

// --- Helpers ---
function openCreateTaskModal() {
    $('#taskModal').modal('show');
}

function setPriority(el) {
    $('.priority-option').removeClass('active');
    $(el).addClass('active');
    $('#taskPriority').val($(el).data('value'));
}