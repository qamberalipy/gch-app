/* static/js/base.js */

// ==================================================
// 1. UI UTILITIES & GLOBAL SETUP
// ==================================================
$(document).ready(function () {
    // Hide loader when page is fully ready
    myhideLoader();

    // Toastr Configuration
    toastr.options = {
        "closeButton": true,
        "newestOnTop": true,
        "positionClass": "toast-top-right",
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };
    
    // Sidebar Toggle Logic
    $(document).on("click", ".toggle-sidebar-btn", function () {
        $("body").toggleClass("toggle-sidebar");
    });

    // --- Initialize Notification System ---
    initNotificationSystem();
});

function myshowLoader() { $("#loader").fadeIn(200); }
function myhideLoader() { $("#loader").fadeOut(200); }

function showToastMessage(type, text) {
    switch (type) {
        case 'success': toastr.success(text); break;
        case 'info': toastr.info(text); break;
        case 'error': toastr.error(text); break;
        case 'warning': toastr.warning(text); break;
        default: toastr.info(text); break;
    }
}

// ==================================================
// 2. LOGOUT FUNCTION
// ==================================================
function handleLogout() {
    Swal.fire({
        title: 'Sign Out?',
        text: "You will need to login again to access your account.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#C89E47', // GCH Gold
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, Log out'
    }).then((result) => {
        if (result.isConfirmed) {
            axios.post('/api/auth/logout')
                .then(() => { window.location.href = "/"; })
                .catch(err => {
                    console.error("Logout failed", err);
                    window.location.href = "/";
                });
        }
    });
}

// ==================================================
// 3. AXIOS GLOBAL ERROR HANDLER
// ==================================================
if (typeof axios !== 'undefined') {
    axios.interceptors.response.use(
        response => response,
        error => {
            if (error.response && error.response.status === 401) {
                // Session expired -> Redirect to login
                window.location.href = "/"; 
            }
            return Promise.reject(error);
        }
    );
}

// ==================================================
// 4. NOTIFICATION SYSTEM (ENHANCED REAL-TIME)
// ==================================================

// --- OPTIMIZED SOUND (Base64) ---
// This is a short "ding" sound encoded in Base64 to prevent 404 errors.
const NOTIFICATION_SOUND = new Audio("data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjIwLjEwMAAAAAAAAAAAAAAA//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//tQxAAAAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq");

// State
let NOTIFICATION_SKIP = 0;
const NOTIFICATION_LIMIT = 10;
let NOTIFICATION_LOADING = false;
let wsConnection = null;
let wsRetryCount = 0;

// Visual Mapping
const notificationMap = {
    'task':     { icon: 'ri-clipboard-line', color: 'text-primary' },
    'invoice':  { icon: 'ri-file-list-3-line', color: 'text-success' },
    'system':   { icon: 'ri-settings-4-line', color: 'text-secondary' },
    'approval': { icon: 'ri-checkbox-circle-line', color: 'text-warning' },
    'critical': { icon: 'ri-alarm-warning-fill', color: 'text-danger' },
    'announcement': { icon: 'ri-megaphone-line', color: 'text-info' },
    'default':  { icon: 'ri-notification-badge-line', color: 'text-muted' }
};

// A. Initialization
function initNotificationSystem() {
    // 1. Fetch Initial Data
    fetchNotifications(true);

    // 2. Connect WebSocket with Retries
    connectWebSocket();
}

// B. WebSocket Logic (Real-time Fix)
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    // Ensure the path matches your backend router
    const wsUrl = `${protocol}://${window.location.host}/api/notification/ws`;

    if (wsConnection) {
        wsConnection.close();
    }

    wsConnection = new WebSocket(wsUrl);

    wsConnection.onopen = function() {
        console.log("🟢 WebSocket Connected: Real-time notifications active.");
        wsRetryCount = 0; // Reset retry counter on success
    };

    wsConnection.onmessage = function(event) {
        try {
            const payload = JSON.parse(event.data);
            // Check message type (Backend must send 'type': 'new_notification')
            if (payload.type === 'new_notification' && payload.data) {
                handleRealTimeNotification(payload.data);
            }
        } catch (e) {
            console.error("WS Parse Error:", e, event.data);
        }
    };

    wsConnection.onerror = function(err) {
        console.error("🔴 WebSocket Error:", err);
    };

    wsConnection.onclose = function(e) {
        console.warn("🟠 WebSocket Closed. Reconnecting in 5s...", e.reason);
        // Exponential backoff or simple 5s retry
        setTimeout(() => connectWebSocket(), 5000);
    };
}

// C. Fetch Data (Pagination)
function fetchNotifications(reset = false) {
    if (NOTIFICATION_LOADING) return;
    NOTIFICATION_LOADING = true;

    if (reset) {
        NOTIFICATION_SKIP = 0;
        $("#notification-list").empty();
    }

    // Adjust endpoint to match your backend pagination
    axios.get(`/api/notification/?limit=${NOTIFICATION_LIMIT}&skip=${NOTIFICATION_SKIP}`)
        .then(res => {
            // Support multiple API response structures
            let items = res.data.items || res.data; 
            let unreadCount = res.data.total_unread;
            
            // If items is not array, try accessing data prop
            if (!Array.isArray(items) && res.data.data) items = res.data.data;
            if (!Array.isArray(items)) items = []; // Fallback

            if (unreadCount !== undefined) {
                updateUnreadCount(unreadCount, false);
            } else {
                fetchUnreadCount(); // Fallback if count not in list response
            }

            const listContainer = $("#notification-list");
            const footer = $("#notification-footer");

            if (reset) listContainer.empty();

            if (items.length === 0 && NOTIFICATION_SKIP === 0) {
                listContainer.html(`
                    <li class="d-flex flex-column align-items-center justify-content-center py-4 text-muted">
                        <i class="ri-notification-off-line fs-3 mb-2"></i>
                        <small>No notifications</small>
                    </li>
                `);
                footer.hide();
            } else {
                items.forEach(item => {
                    listContainer.append(renderNotificationItem(item));
                });
                
                // Show footer if we have items
                footer.show(); 
                
                // Hide "Load More" if we reached the end
                if (items.length < NOTIFICATION_LIMIT) {
                    $("#notification-footer button").hide();
                } else {
                    $("#notification-footer button").show();
                }
                
                NOTIFICATION_SKIP += NOTIFICATION_LIMIT;
            }
        })
        .catch(err => {
            console.error("Fetch Error:", err);
            if (reset) $("#notification-list").html('<li class="text-center text-danger py-3 small">Failed to load</li>');
        })
        .finally(() => { NOTIFICATION_LOADING = false; });
}

function fetchUnreadCount() {
    axios.get('/api/notification/unread-count')
        .then(res => updateUnreadCount(res.data.count, false))
        .catch(err => console.log("Unread count err:", err));
}

// D. Rendering
function renderNotificationItem(notif) {
    const style = notificationMap[notif.category] || notificationMap['default'];
    
    // GCH Theme: Unread = light gold tint (bg-warning-subtle or custom css)
    // Here we use standard bootstrap utility mixed with inline style for the 'gold' feel
    const bgClass = notif.is_read ? 'bg-white' : 'bg-light';
    const borderClass = notif.is_read ? '' : 'border-start border-4 border-warning';
    
    const dateObj = new Date(notif.created_at);
    const dateStr = dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    return `
    <li class="notification-item ${bgClass} ${borderClass} border-bottom position-relative" id="notif-${notif.id}">
        <a href="javascript:void(0)" 
           class="d-flex align-items-start p-3 text-decoration-none text-dark w-100"
           onclick="handleNotificationClick(${notif.id}, '${notif.click_action_link}')">
            
            <div class="notif-icon-box rounded-circle bg-light d-flex align-items-center justify-content-center me-3" 
                 style="width: 35px; height: 35px; min-width: 35px;">
                <i class="${style.icon} ${style.color} fs-5"></i>
            </div>
            
            <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-start">
                    <h6 class="mb-1 small fw-bold" style="font-size: 0.85rem;">${notif.title}</h6>
                    <small class="text-muted ms-2" style="font-size: 0.65rem;">${dateStr}</small>
                </div>
                <p class="mb-0 text-muted small text-truncate" style="max-width: 200px; font-size: 0.75rem;">${notif.body || ''}</p>
            </div>
        </a>
    </li>`;
}

// E. Real-time Actions
function handleRealTimeNotification(data) {
    // 1. Play Sound
    playNotificationSound();

    // 2. Show Toast (Top Right)
    if (data.severity === 'critical' || data.severity === 'high') {
        toastr.error(data.body, data.title);
    } else {
        toastr.info(data.body, data.title);
    }

    // 3. Update Badge
    updateUnreadCount(1, true);

    // 4. Add to List (Prepend)
    const tempItem = {
        id: data.id || Date.now(),
        title: data.title,
        body: data.body,
        category: data.category || 'system',
        click_action_link: data.link,
        is_read: false,
        created_at: new Date().toISOString()
    };
    
    // Remove "No notifications" if present
    const list = $("#notification-list");
    if (list.find('.ri-notification-off-line').length > 0) {
        list.empty();
        $("#notification-footer").show();
    }
    
    list.prepend(renderNotificationItem(tempItem));
}

function handleNotificationClick(id, link) {
    // Mark read
    axios.put(`/api/notification/${id}/read`)
        .then(() => {
            if (link && link !== 'null' && link !== '#' && link !== 'undefined') {
                window.location.href = link;
            } else {
                // UI update only
                $(`#notif-${id}`).removeClass('bg-light border-start border-4 border-warning').addClass('bg-white');
                updateUnreadCount(-1, true);
            }
        })
        .catch(() => {
            // Fallback navigate
            if (link && link !== 'null') window.location.href = link;
        });
}

function markAllAsRead(e) {
    if(e) { e.preventDefault(); e.stopPropagation(); }
    
    axios.put('/api/notification/mark-all-read')
        .then(() => {
            $("#notification-list .notification-item").removeClass('bg-light border-start border-4 border-warning').addClass('bg-white');
            updateUnreadCount(0, false);
            showToastMessage('success', 'All marked as read');
        });
}

function updateUnreadCount(val, isRelative) {
    const badge = $("#notification-badge");
    const textBadge = $("#notification-count-text");
    let current = parseInt(badge.text()) || 0;
    let newVal = isRelative ? (current + val) : val;
    
    if (newVal < 0) newVal = 0;

    badge.text(newVal);
    textBadge.text(newVal);

    if (newVal > 0) {
        badge.show();
        badge.addClass('animate__animated animate__pulse'); // Optional animation class
    } else {
        badge.hide();
    }
}

function loadMoreNotifications(e) {
    if(e) { e.preventDefault(); e.stopPropagation(); }
    fetchNotifications(false);
}

function viewAllNotifications() {
    window.location.href = "/notifications";
}

function playNotificationSound() {
    // Reset and play
    if (NOTIFICATION_SOUND) {
        NOTIFICATION_SOUND.currentTime = 0;
        NOTIFICATION_SOUND.play().catch(e => console.log("Audio requires interaction first.", e));
    }
}