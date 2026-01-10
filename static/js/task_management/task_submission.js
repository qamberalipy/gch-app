/**
 * task_creator.js
 * Logic for Digital Creators: View Tasks, Chat, Upload Deliverables, Edit Submission.
 * Updated for new Modal Layout.
 */

let allTasks = [];
let currentTask = null; // The task currently open in the modal
let newDeliverables = []; // Newly uploaded files awaiting submission
let activeChatId = null;

$(document).ready(function() {
    loadMyTasks();

    // Filters
    $(".filter-btn").click(function() {
        $(".filter-btn").removeClass("active");
        $(this).addClass("active");
        renderTasks($(this).data("filter"));
    });

    // Upload Handlers
    $("#dropZone").click(() => $("#fileInput").click());
    $("#fileInput").change(handleFileUpload);

    // Submission
    $("#btnSubmitWork").click(submitWork);

    // Chat
    $("#btnOpenChat").click(() => openChat(currentTask.id, currentTask.title));
    $("#chatForm").submit(sendChatMessage);
});

// ==========================================
// 1. DASHBOARD & LISTING
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
            grid.html('<div class="col-12 text-center text-danger mt-5">Failed to load tasks. Please refresh.</div>');
        });
}

function renderTasks(filter) {
    const grid = $("#taskGrid");
    grid.empty();

    const filtered = filter === "all" ? allTasks : allTasks.filter(t => t.status === filter);

    if (filtered.length === 0) {
        grid.html('<div class="col-12 text-center text-muted mt-5 py-5"><h4>No tasks found</h4><p>You are all caught up!</p></div>');
        return;
    }

    filtered.forEach(task => {
        let statusColor = "st-todo";
        if (task.status === "In Review") statusColor = "st-review";
        if (task.status === "Completed") statusColor = "st-completed";

        const card = `
            <div class="col-md-6 col-lg-4 col-xl-3">
                <div class="grail-card" onclick="openTaskModal(${task.id})">
                    <div class="card-top">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="task-meta text-warning">${task.req_content_type}</span>
                            <span class="status-badge ${statusColor}">${task.status}</span>
                        </div>
                        <h5 class="task-title text-truncate">${task.title}</h5>
                        <p class="task-desc small">${task.description || 'No description provided.'}</p>
                        
                        <div class="d-flex flex-wrap gap-2 mt-3">
                            <span class="badge bg-light text-dark border fw-normal"><i class="ri-calendar-event-line"></i> ${formatDateShort(task.due_date)}</span>
                            ${task.priority === 'High' ? '<span class="badge bg-danger-subtle text-danger border border-danger-subtle">Urgent</span>' : ''}
                        </div>
                    </div>
                    <div class="card-btm">
                        <div class="d-flex align-items-center text-muted small">
                            <i class="ri-attachment-2 me-1"></i> ${task.attachments.length} Files
                        </div>
                        <span class="text-primary small fw-bold">View Details <i class="ri-arrow-right-s-line"></i></span>
                    </div>
                </div>
            </div>
        `;
        grid.append(card);
    });
}

// ==========================================
// 2. DETAIL & SUBMISSION MODAL (POPULATION)
// ==========================================

function openTaskModal(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;
    currentTask = task;
    newDeliverables = []; // Reset new uploads
    $("#submissionComment").val(""); // Clear comment

    // --- Fill Left Sidebar (Details) ---
    $("#modalTitle").text(task.title);
    $("#modalDesc").text(task.description || "No description provided.");
    $("#modalContext").text(task.context || "-");
    $("#modalType").text(task.req_content_type);
    $("#modalQty").text(task.req_quantity);
    $("#modalDuration").text(task.req_duration_min ? task.req_duration_min + " mins" : "N/A");
    
    // Requirements toggles
    $("#modalFace").html(task.req_face_visible ? '<i class="ri-checkbox-circle-fill text-success"></i> Face Visible' : '<i class="ri-close-circle-fill text-muted"></i> No Face');
    $("#modalWatermark").html(task.req_watermark ? '<i class="ri-checkbox-circle-fill text-success"></i> Watermark' : '<i class="ri-close-circle-fill text-muted"></i> No Watermark');

    // Tags
    const tagContainer = $("#modalTags");
    tagContainer.empty();
    if (task.req_outfit_tags) {
        task.req_outfit_tags.split(',').forEach(tag => {
            tagContainer.append(`<span class="tag-badge">${tag}</span>`);
        });
    } else {
         tagContainer.html('<small class="text-muted">No tags.</small>');
    }

    // --- Fill Right Main Area (Work & Refs) ---
    
    // References (Uploaded by Assigner)
    const refContainer = $("#modalReferences");
    refContainer.empty();
    const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
    // Filter: Attachments where uploader != ME are references
    const references = task.attachments.filter(a => a.uploader_id !== myId);
    
    if (references.length === 0) refContainer.html('<small class="text-muted p-2 d-block">No reference files provided.</small>');
    
    references.forEach(file => {
        const icon = getIconForMime(file.mime_type);
        refContainer.append(`
            <div class="file-item p-2">
                <div class="file-icon" style="width:30px;height:30px;font-size:1rem;">${icon}</div>
                <div class="flex-grow-1 text-truncate small fw-bold">
                    <a href="${file.file_url}" target="_blank" class="text-dark text-decoration-none">${file.tags || getFileName(file.file_url)}</a>
                </div>
                <a href="${file.file_url}" target="_blank" class="btn btn-sm btn-light text-primary"><i class="ri-download-line"></i></a>
            </div>
        `);
    });

    // Render Your Work List
    renderDeliverablesList();
    
    // Configure Button & Status Banner
    const btn = $("#btnSubmitWork");
    const alert = $("#statusAlert");
    const dropZone = $("#dropZone");
    
    if (task.status === "Completed") {
        alert.attr("class", "alert alert-success border-0 p-2 mb-3 small").html('<i class="ri-check-double-line me-2"></i> Task Completed!');
        btn.prop("disabled", true).text("Completed");
        dropZone.addClass("d-none"); // Hide upload
    } else if (task.status === "In Review") {
        alert.attr("class", "alert alert-info border-0 p-2 mb-3 small").html('<i class="ri-time-line me-2"></i> Under Review. You can edit files below.');
        btn.prop("disabled", false).text("Update Submission");
        dropZone.removeClass("d-none");
        dropZone.parent().removeClass("d-none"); // Ensure col is visible
    } else {
        alert.attr("class", "alert alert-warning border-0 p-2 mb-3 small").html('<i class="ri-loader-4-line me-2"></i> Task Pending. Upload your work.');
        btn.prop("disabled", false).text("Submit Work");
        dropZone.removeClass("d-none");
        dropZone.parent().removeClass("d-none");
    }

    $("#submissionModal").modal("show");
}

function renderDeliverablesList() {
    const container = $("#deliverablesList");
    container.empty();
    
    const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
    
    // 1. Existing Deliverables (Previously uploaded by ME)
    const existing = currentTask.attachments.filter(a => a.uploader_id === myId);

    // 2. Combine with New Deliverables (in memory)
    const allFiles = [
        ...existing.map(f => ({ ...f, isNew: false })), 
        ...newDeliverables.map(f => ({ ...f, isNew: true }))
    ];

    if (allFiles.length === 0) {
        container.html('<div class="h-100 d-flex align-items-center justify-content-center"><p class="text-muted small mb-0">No files uploaded yet.</p></div>');
        return;
    }

    allFiles.forEach((file, idx) => {
        const isImg = file.mime_type && file.mime_type.startsWith("image");
        const thumb = isImg ? (file.thumbnail_url || file.file_url) : null;
        const iconOrThumb = thumb ? `<img src="${thumb}" class="file-thumb">` : `<div class="file-icon">${getIconForMime(file.mime_type)}</div>`;

        // Logic for Delete Button
        const deleteAction = file.isNew ? `removeNewFile(${newDeliverables.indexOf(file)})` : `deleteExistingFile(${file.id})`;

        container.append(`
            <div class="file-item">
                ${iconOrThumb}
                <div class="flex-grow-1 overflow-hidden">
                    <div class="small fw-bold text-truncate" title="${file.tags || file.name}">${file.tags || file.name || 'File'}</div>
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
// 3. UPLOAD & SUBMIT LOGIC
// ==========================================

async function handleFileUpload(e) {
    const files = e.target.files;
    if (!files.length) return;

    // Show simple loader in dropzone
    const origText = $("#dropZone").html();
    $("#dropZone").html('<div class="spinner-border text-warning spinner-border-sm mb-2"></div><div class="small">Uploading...</div>');

    for (let file of files) {
        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("type_group", "image"); // Default group

            const res = await axios.post('/api/upload/small-file', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (res.data.status === 'success') {
                newDeliverables.push({
                    file_url: res.data.url,
                    thumbnail_url: res.data.url, // Simple for now
                    file_size_mb: (file.size / (1024 * 1024)).toFixed(2),
                    mime_type: file.type,
                    tags: file.name
                });
            }
        } catch (err) {
            toastr.error("Upload failed for " + file.name);
        }
    }

    $("#dropZone").html(origText);
    $("#fileInput").val(""); // Reset input
    renderDeliverablesList();
}

function removeNewFile(index) {
    newDeliverables.splice(index, 1);
    renderDeliverablesList();
}

function deleteExistingFile(contentId) {
    Swal.fire({
        title: 'Remove File?',
        text: "This will delete the file from the server.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Yes, remove it'
    }).then((result) => {
        if (result.isConfirmed) {
            // Optimistic UI update
            currentTask.attachments = currentTask.attachments.filter(a => a.id !== contentId);
            renderDeliverablesList();
            
            axios.delete(`/api/tasks/content/${contentId}`)
                .then(() => toastr.success("File removed"))
                .catch(err => {
                    toastr.error("Failed to delete file on server");
                    // Revert UI if failed (reload task data would be better but complex)
                    loadMyTasks(); // Reload all to be safe
                    $("#submissionModal").modal("hide");
                });
        }
    });
}

function submitWork() {
    const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
    const existingCount = currentTask.attachments.filter(a => a.uploader_id === myId).length;

    if (newDeliverables.length === 0 && existingCount === 0) {
        toastr.warning("Please upload at least one file before submitting.");
        return;
    }

    const payload = {
        deliverables: newDeliverables,
        comment: $("#submissionComment").val()
    };

    const btn = $("#btnSubmitWork");
    const origText = btn.html();
    btn.prop("disabled", true).html('<span class="spinner-border spinner-border-sm"></span> Submitting...');

    axios.post(`/api/tasks/${currentTask.id}/submit`, payload)
        .then(res => {
            toastr.success("Work Submitted Successfully!");
            $("#submissionModal").modal("hide");
            loadMyTasks(); // Refresh grid
        })
        .catch(err => {
            console.error(err);
            toastr.error(err.response?.data?.detail || "Submission failed");
        })
        .finally(() => {
            btn.prop("disabled", false).html(origText);
        });
}

// ==========================================
// 4. CHAT (Reused simple logic)
// ==========================================
function openChat(id, title) {
    activeChatId = id;
    $("#chatContainer").html('<div class="text-center py-5"><div class="spinner-border text-secondary spinner-border-sm"></div></div>');
    $("#chatModal").modal("show");
    loadChatMessages();
}

function loadChatMessages() {
    if(!activeChatId) return;
    axios.get(`/api/tasks/${activeChatId}/chat`).then(res => {
        const box = $("#chatContainer");
        box.empty();
        const myId = parseInt($('meta[name="user-id"]').attr('content')) || 0;
        
        if(res.data.length === 0) {
             box.html('<div class="text-center small text-muted my-5">No messages yet.</div>');
             return;
        }
        
        res.data.forEach(msg => {
            if(msg.is_system_log) {
                 box.append(`<div class="text-center small text-muted my-2 fst-italic">${msg.message}</div>`);
            } else {
                const isMe = msg.author.id === myId;
                box.append(`
                    <div class="d-flex ${isMe ? 'justify-content-end' : 'justify-content-start'} p-2">
                        <div class="bg-${isMe?'primary':'white'} text-${isMe?'white':'dark'} border rounded p-2 shadow-sm" style="max-width:80%; font-size:0.9rem;">
                            ${msg.message}
                        </div>
                    </div>
                `);
            }
        });
        box.scrollTop(box[0].scrollHeight);
    });
}

function sendChatMessage(e) {
    e.preventDefault();
    const txt = $("#chatInput").val().trim();
    if(!txt) return;
    
    axios.post(`/api/tasks/${activeChatId}/chat`, { message: txt }).then(() => {
        $("#chatInput").val("");
        loadChatMessages();
    });
}

// Helpers
function formatDateShort(str) {
    if(!str) return "No Date";
    return new Date(str).toLocaleDateString();
}
function getFileName(url) {
    if(!url) return "File";
    return url.split('/').pop();
}
function getIconForMime(mime) {
    if (!mime) return '<i class="ri-file-line"></i>';
    if (mime.includes("video")) return '<i class="ri-movie-line"></i>';
    if (mime.includes("pdf")) return '<i class="ri-file-pdf-line"></i>';
    if (mime.includes("image")) return '<i class="ri-image-line"></i>';
    return '<i class="ri-file-list-2-line"></i>';
}