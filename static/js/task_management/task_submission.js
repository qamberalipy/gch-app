/**
 * task_submission.js
 * Logic for Digital Creators: View, Upload, Chat, Submit.
 * Features: Recursion fix, Grail Theme, Heavy Chat, No Comments, Expandable Desc.
 */

let allTasks = [];
let currentTask = null;
let newDeliverables = []; // Only for new files
let activeChatTaskId = null;
let isChatSending = false; // Chat semaphore

$(document).ready(function() {
    loadMyTasks();

    // Filters
    $(".filter-btn").click(function() {
        $(".filter-btn").removeClass("active");
        $(this).addClass("active");
        renderTasks($(this).data("filter"));
    });

    // Upload Handlers (Fixed Recursion)
    $("#dropZone").on("click", function(e) {
        // Prevent triggering if clicked directly on input
        if (e.target.id !== 'fileInput') {
            $("#fileInput").click();
        }
    });
    
    $("#fileInput").on("click", function(e) {
        e.stopPropagation(); // STOP BUBBLING to dropZone
    });
    
    $("#fileInput").on("change", handleFileUpload);

    // Actions
    $("#btnSubmitWork").click(submitWork);
    $("#btnOpenChat").click(() => openChatModal(currentTask.id, currentTask.title));
    $("#chatForm").submit(sendMessage);
});

// ==========================================
// 1. DASHBOARD GRID
// ==========================================

function loadMyTasks() {
    const grid = $("#taskGrid");
    grid.html('<div class="col-12 text-center py-5"><div class="spinner-border text-warning"></div></div>');
    
    axios.get('/api/tasks/')
        .then(res => {
            allTasks = res.data;
            renderTasks("all");
        })
        .catch(err => {
            console.error(err);
            grid.html('<div class="col-12 text-center text-danger mt-5">Failed to load tasks.</div>');
        });
}

function renderTasks(filter) {
    const grid = $("#taskGrid");
    grid.empty();

    // Filter Logic based on Backend Enums
    const filtered = filter === "all" ? allTasks : allTasks.filter(t => t.status === filter);

    if (filtered.length === 0) {
        grid.html('<div class="col-12 text-center text-muted mt-5 py-5"><h4>No tasks found</h4><p>You are all caught up!</p></div>');
        return;
    }

    filtered.forEach(task => {
        let statusClass = "st-todo";
        if (task.status === "Completed") statusClass = "st-completed";
        if (task.status === "Blocked") statusClass = "st-blocked";
        if (task.status === "Missed") statusClass = "st-missed";

        const card = `
            <div class="col-md-6 col-lg-4 col-xl-3">
                <div class="grail-card" onclick="openTaskModal(${task.id})">
                    <div class="card-top">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="task-meta">${task.req_content_type}</span>
                            <span class="status-badge ${statusClass}">${task.status}</span>
                        </div>
                        <h5 class="task-title text-truncate">${task.title}</h5>
                        <p class="task-desc">${task.description || 'No description provided.'}</p>
                        
                        <div class="d-flex gap-2 mt-3">
                            <span class="badge bg-light text-dark border fw-normal"><i class="ri-calendar-event-line"></i> ${formatDateShort(task.due_date)}</span>
                            ${task.priority === 'High' ? '<span class="badge bg-danger-subtle text-danger border border-danger-subtle">Urgent</span>' : ''}
                        </div>
                    </div>
                    <div class="card-btm">
                        <div class="d-flex align-items-center text-muted small">
                            <i class="ri-attachment-2 me-1"></i> ${task.attachments.length} Files
                        </div>
                        <span class="text-warning small fw-bold">Open Task <i class="ri-arrow-right-s-line"></i></span>
                    </div>
                </div>
            </div>
        `;
        grid.append(card);
    });
}

// ==========================================
// 2. MODAL & DETAILS
// ==========================================

function openTaskModal(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;
    currentTask = task;
    newDeliverables = [];

    // --- Populate Details (Left) ---
    $("#modalTitle").text(task.title);
    
    // Description Logic (Truncate)
    const desc = task.description || "No description provided.";
    $("#modalDesc").text(desc);
    if (desc.length > 150) {
        $("#modalDesc").addClass("desc-clamp");
        $("#toggleDescBtn").removeClass("d-none").text("Read More");
    } else {
        $("#modalDesc").removeClass("desc-clamp");
        $("#toggleDescBtn").addClass("d-none");
    }

    $("#modalQty").text(task.req_quantity);
    $("#modalDuration").text(task.req_duration_min ? task.req_duration_min + " mins" : "N/A");
    
    // Icons
    $("#modalFace").html(task.req_face_visible ? '<i class="ri-checkbox-circle-fill text-success"></i> Face' : '<i class="ri-close-circle-fill text-muted"></i> No Face');
    $("#modalWatermark").html(task.req_watermark ? '<i class="ri-checkbox-circle-fill text-success"></i> Watermark' : '<i class="ri-close-circle-fill text-muted"></i> No Watermark');

    // Tags
    const tagContainer = $("#modalTags");
    tagContainer.empty();
    if (task.req_outfit_tags) {
        task.req_outfit_tags.split(',').forEach(tag => {
            tagContainer.append(`<span class="tag-badge me-1">${tag}</span>`);
        });
    } else {
         tagContainer.html('<small class="text-muted">No tags.</small>');
    }

    // References (Uploaded by Assigner)
    const refContainer = $("#modalReferences");
    refContainer.empty();
    const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
    
    // Filter: uploader != ME
    const references = task.attachments.filter(a => a.uploader_id !== myId);
    
    if (references.length === 0) refContainer.html('<small class="text-muted">No reference files.</small>');
    
    references.forEach(file => {
        refContainer.append(`
            <div class="ref-file">
                <div class="ref-icon"><i class="ri-file-list-line"></i></div>
                <div class="flex-grow-1 text-truncate small fw-bold">
                    <a href="${file.file_url}" target="_blank" class="text-dark text-decoration-none">${file.tags || getFileName(file.file_url)}</a>
                </div>
                <a href="${file.file_url}" target="_blank" class="text-primary small"><i class="ri-download-line"></i></a>
            </div>
        `);
    });

    // --- Submission State (Right) ---
    renderDeliverablesList();
    
    const btn = $("#btnSubmitWork");
    const alert = $("#statusAlert");
    const dropZone = $("#dropZone");
    
    if (task.status === "Completed") {
        alert.attr("class", "alert alert-success border-0 small").html('<i class="ri-check-double-line me-2"></i> <strong>Completed.</strong> Good job!');
        btn.prop("disabled", true).text("Task Completed");
        dropZone.addClass("d-none"); 
    } else if (task.status === "Blocked" || task.status === "Missed") {
        alert.attr("class", "alert alert-danger border-0 small").html(`<i class="ri-error-warning-line me-2"></i> <strong>${task.status}.</strong> Contact manager.`);
        btn.prop("disabled", true).text(task.status);
        dropZone.addClass("d-none");
    } else {
        // To Do
        alert.attr("class", "alert alert-warning border-0 small").html('<i class="ri-loader-4-line me-2"></i> <strong>Pending.</strong> Upload your work below.');
        btn.prop("disabled", false).text("Submit Work");
        dropZone.removeClass("d-none");
    }

    $("#submissionModal").modal("show");
}

function toggleDescription() {
    const el = $("#modalDesc");
    const btn = $("#toggleDescBtn");
    if (el.hasClass("desc-clamp")) {
        el.removeClass("desc-clamp");
        btn.text("Read Less");
    } else {
        el.addClass("desc-clamp");
        btn.text("Read More");
    }
}

function renderDeliverablesList() {
    const container = $("#deliverablesList");
    container.empty();
    
    const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
    
    // Existing files (Uploader = Me)
    const existing = currentTask.attachments.filter(a => a.uploader_id === myId);
    
    // Combine lists
    const allFiles = [
        ...existing.map(f => ({ ...f, isNew: false })), 
        ...newDeliverables.map(f => ({ ...f, isNew: true }))
    ];

    $("#fileCount").text(`${allFiles.length} Files`);

    if (allFiles.length === 0) {
        container.html('<div class="h-100 d-flex align-items-center justify-content-center text-muted small">No files uploaded yet.</div>');
        return;
    }

    allFiles.forEach((file, idx) => {
        const isImg = file.mime_type && file.mime_type.startsWith("image");
        const thumb = isImg ? (file.thumbnail_url || file.file_url) : null;
        const iconOrThumb = thumb ? `<img src="${thumb}" class="deliverable-thumb">` : `<div class="deliverable-thumb bg-light d-flex align-items-center justify-content-center"><i class="ri-file-line"></i></div>`;

        // Action logic
        const deleteAction = file.isNew ? `removeNewFile(${newDeliverables.indexOf(file)})` : `deleteExistingFile(${file.id})`;

        container.append(`
            <div class="deliverable-item">
                ${iconOrThumb}
                <div class="flex-grow-1 overflow-hidden">
                    <div class="small fw-bold text-truncate">${file.tags || file.name || 'File'}</div>
                    <div class="text-xs text-muted">
                        ${file.file_size_mb ? file.file_size_mb + ' MB' : ''} 
                        ${file.isNew ? '<span class="text-success fw-bold ms-1">New</span>' : '<span class="text-secondary ms-1">Saved</span>'}
                    </div>
                </div>
                <button class="btn btn-sm btn-light text-danger" onclick="${deleteAction}"><i class="ri-delete-bin-line"></i></button>
            </div>
        `);
    });
}

// ==========================================
// 3. UPLOAD & SUBMIT
// ==========================================

async function handleFileUpload(e) {
    const files = e.target.files;
    if (!files.length) return;

    const origText = $("#dropZone").html();
    $("#dropZone").html('<div class="spinner-border text-warning spinner-border-sm mb-2"></div><div class="small">Uploading...</div>');

    for (let file of files) {
        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("type_group", "image");

            const res = await axios.post('/api/upload/small-file', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (res.data.status === 'success') {
                newDeliverables.push({
                    file_url: res.data.url,
                    thumbnail_url: res.data.url,
                    file_size_mb: (file.size / (1024*1024)).toFixed(2),
                    mime_type: file.type,
                    tags: file.name
                });
            }
        } catch (err) {
            toastr.error("Upload failed for " + file.name);
        }
    }

    $("#dropZone").html(origText);
    $("#fileInput").val(""); 
    renderDeliverablesList();
}

function removeNewFile(index) {
    newDeliverables.splice(index, 1);
    renderDeliverablesList();
}

function deleteExistingFile(contentId) {
    Swal.fire({
        title: 'Remove File?', text: "Delete from server?", icon: 'warning',
        showCancelButton: true, confirmButtonColor: '#d33', confirmButtonText: 'Yes'
    }).then((result) => {
        if (result.isConfirmed) {
            axios.delete(`/api/tasks/content/${contentId}`)
                .then(() => {
                    toastr.success("Removed");
                    currentTask.attachments = currentTask.attachments.filter(a => a.id !== contentId);
                    renderDeliverablesList();
                })
                .catch(() => toastr.error("Failed to delete"));
        }
    });
}

function submitWork() {
    const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
    const existingCount = currentTask.attachments.filter(a => a.uploader_id === myId).length;

    if (newDeliverables.length === 0 && existingCount === 0) {
        toastr.warning("Please upload at least one file.");
        return;
    }

    const payload = { deliverables: newDeliverables }; // No comment field

    const btn = $("#btnSubmitWork");
    const origText = btn.html();
    btn.prop("disabled", true).html('<span class="spinner-border spinner-border-sm"></span> Submitting...');

    axios.post(`/api/tasks/${currentTask.id}/submit`, payload)
        .then(res => {
            toastr.success("Work Submitted! Task Completed.");
            $("#submissionModal").modal("hide");
            loadMyTasks(); // Refresh grid
        })
        .catch(err => {
            console.error(err);
            toastr.error("Submission failed");
        })
        .finally(() => {
            btn.prop("disabled", false).html(origText);
        });
}

// ==========================================
// 4. CHAT (ROBUST & ROLED)
// ==========================================

function openChatModal(id, title) {
    activeChatTaskId = id;
    $("#chatContainer").html('<div class="text-center py-5"><div class="spinner-border text-secondary spinner-border-sm"></div></div>');
    $("#chatModal").modal("show");
    enableChatInput();
    loadChat();
}

function loadChat() {
    if (!activeChatTaskId) return;
    axios.get(`/api/tasks/${activeChatTaskId}/chat`).then(res => {
        const container = $("#chatContainer");
        container.empty();
        const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;

        if (res.data.length === 0) {
            container.html('<div class="text-center text-muted small mt-5 opacity-50">No messages yet.<br>Start the conversation!</div>');
            return;
        }

        res.data.forEach(msg => {
            if (msg.is_system_log) {
                container.append(`
                    <div class="text-center my-3">
                        <span class="badge bg-white border text-muted fw-normal rounded-pill px-3 py-1" style="font-size:0.7rem;">${msg.message}</span>
                    </div>
                `);
            } else {
                const isMe = msg.author.id === myId;
                const roleBadge = `<span class="role-badge bg-light border">${msg.author.role || 'User'}</span>`;
                
                const bubbleHtml = `
                    <div class="chat-bubble ${isMe ? 'sent' : 'received'}">
                        ${!isMe ? `<span class="chat-meta text-primary">${msg.author.full_name} ${roleBadge}</span>` : ''}
                        <div class="message-text">${msg.message}</div>
                        <div class="text-end mt-1" style="font-size:0.6rem; opacity:0.6;">${formatDateShort(msg.created_at)}</div>
                    </div>
                `;
                container.append(bubbleHtml);
            }
        });
        container.scrollTop(container[0].scrollHeight);
    });
}

function sendMessage(e) {
    e.preventDefault();
    const input = $("#chatInput");
    const txt = input.val().trim();
    if (!txt || isChatSending) return;

    isChatSending = true;
    disableChatInput();

    axios.post(`/api/tasks/${activeChatTaskId}/chat`, { message: txt })
        .then(() => { input.val(""); loadChat(); })
        .catch(() => toastr.error("Failed to send"))
        .finally(() => { 
            isChatSending = false; 
            enableChatInput(); 
            setTimeout(() => input.focus(), 100); 
        });
}

function disableChatInput() { $("#chatInput").prop("disabled", true); $("#btnSendChat").prop("disabled", true); $("#iconSend").addClass("d-none"); $("#spinnerSend").removeClass("d-none"); }
function enableChatInput() { $("#chatInput").prop("disabled", false); $("#btnSendChat").prop("disabled", false); $("#iconSend").removeClass("d-none"); $("#spinnerSend").addClass("d-none"); }

// Helpers
function formatDateShort(str) { return str ? new Date(str).toLocaleDateString() : "-"; }
function getFileName(url) { return url ? url.split('/').pop() : "File"; }
function getIconForMime(mime) {
    if (!mime) return '<i class="ri-file-line"></i>';
    if (mime.includes("video")) return '<i class="ri-movie-line text-danger"></i>';
    if (mime.includes("image")) return '<i class="ri-image-2-line text-primary"></i>';
    return '<i class="ri-file-text-line"></i>';
}