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

    // --- NEW: Initialize Notifications ---
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
        default: console.error('Invalid toast type:', type); break;
    }
}

// ==================================================
// 2. LOGOUT FUNCTION
// ==================================================
function handleLogout() {
    Swal.fire({
        title: 'Sign Out?',
        text: "You will be returned to the login screen.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#C89E47',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, Log out'
    }).then((result) => {
        if (result.isConfirmed) {
            // Call API to delete cookie on server
            axios.post('/api/auth/logout')
                .then(() => {
                    // Redirect to login page
                    window.location.href = "/";
                })
                .catch(err => {
                    console.error("Logout failed", err);
                    // Force redirect anyway
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
// 4. NOTIFICATION SYSTEM (NEW)
// ==================================================

function initNotificationSystem() {
    // 1. Initial Fetch of Badge Count
    fetchUnreadCount();
    
    // 2. Fetch Initial List
    fetchNotificationList();

    // 3. Connect to WebSocket
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    
    // [CORRECTION] Changed 'notifications' to 'notification' (Singular)
    // The backend route prefix is /api/notification
    const wsUrl = `${protocol}://${window.location.host}/api/notification/ws`;
    
    const socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        
        if (msg.type === "new_notification") {
            // A. Show Toast
            showToastMessage('info', msg.data.title);
            
            // B. Increment Badge
            let badge = $('#notif-badge');
            let current = parseInt(badge.text()) || 0;
            updateBadge(current + 1);
            
            // C. Refresh List (simplest way to keep sync)
            fetchNotificationList();
        }
    };
    
    socket.onclose = function(e) {
        console.log('Notification socket closed. Reconnecting in 5s...');
        setTimeout(initNotificationSystem, 5000);
    };
}

function fetchUnreadCount() {
    // [CORRECTION] Changed 'notifications' to 'notification'
    axios.get('/api/notification/unread-count')
        .then(res => {
            updateBadge(res.data.count);
        })
        .catch(err => console.error("Err fetching count", err));
}

function updateBadge(count) {
    const badge = $('#notif-badge');
    if (count > 0) {
        badge.text(count);
        badge.show();
    } else {
        badge.hide();
    }
}

function fetchNotificationList() {
    // [CORRECTION] Changed 'notifications' to 'notification'
    axios.get('/api/notification?limit=10')
        .then(res => {
            const list = $('#notif-list');
            list.empty();
            
            if(res.data.length === 0) {
                 list.append('<li class="text-center py-2"><small class="text-muted">No new notifications</small></li>');
                 return;
            }

            res.data.forEach(item => {
                let bgClass = item.is_read ? 'bg-white' : 'bg-light'; // Highlight unread
                let icon = item.is_read ? 'ri-mail-open-line' : 'ri-mail-unread-line';
                let time = new Date(item.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

                let html = `
                <li>
                    <a href="javascript:void(0)" class="notification-item ${bgClass}" onclick="handleNotifClick(${item.id}, '${item.click_action_link}')">
                        <div class="notif-icon-box bg-light-blue"><i class="${icon}"></i></div>
                        <div>
                            <p class="mb-0 small fw-medium text-dark">${item.title}</p>
                            <span class="text-muted" style="font-size: 0.65rem;">${item.body || ''} • ${time}</span>
                        </div>
                    </a>
                </li>`;
                list.append(html);
            });
        })
        .catch(err => console.error("Err fetching list", err));
}

function handleNotifClick(id, link) {
    // [CORRECTION] Changed 'notifications' to 'notification'
    // 1. Mark as read
    axios.put(`/api/notification/${id}/read`)
        .then(() => {
            // 2. Redirect
            if (link && link !== 'null' && link !== 'undefined') {
                window.location.href = link;
            } else {
                fetchNotificationList(); // Refresh UI if no link
                fetchUnreadCount();
            }
        });
}

function markAllRead() {
    // [CORRECTION] Assuming you create this endpoint, ensure it uses 'notification'
    /* axios.post('/api/notification/mark-all-read').then(() => {
        fetchUnreadCount();
        fetchNotificationList();
    });
    */
    // For now, reload list to simulate generic refresh
    fetchNotificationList();
}