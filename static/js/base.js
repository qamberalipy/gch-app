/* static/js/base.js */

// ==================================================
// 1. GLOBAL AUDIO ENGINE (Industrial "Priming" Fix)
// ==================================================

// Robust Sound Source (Short "Pop" Sound)
// For production, replacing this with a local file like "/static/audio/pop.mp3" is recommended.
const AUDIO_SRC = "https://pub-0bc0d3c98bb94e3a86698f0aa603f181.r2.dev/audio/mixkit-correct-answer-tone-2870.wav";
const notificationAudio = new Audio(AUDIO_SRC);
notificationAudio.volume = 0.5;

// Flag to track if the browser has allowed audio
let isAudioUnlocked = false;

/**
 * "Unlocks" the audio context on the first user interaction.
 * Browsers block auto-play until the user interacts with the DOM.
 */
function unlockAudioEngine() {
    if (isAudioUnlocked) return;

    // Attempt to play and immediately pause
    const playPromise = notificationAudio.play();

    if (playPromise !== undefined) {
        playPromise.then(() => {
            // Success! The browser now trusts this audio object.
            notificationAudio.pause();
            notificationAudio.currentTime = 0;
            isAudioUnlocked = true;
            
            // Clean up listeners since we are done
            document.removeEventListener('click', unlockAudioEngine);
            document.removeEventListener('keydown', unlockAudioEngine);
            // console.log("[Audio] System unlocked successfully.");
        }).catch(error => {
            console.log("[Audio] Unlock waiting for interaction:", error);
        });
    }
}

// ==================================================
// 2. UI UTILITIES & GLOBAL SETUP
// ==================================================
$(document).ready(function () {
    // 1. Loader
    if (typeof myhideLoader === 'function') myhideLoader();

    // 2. Audio Priming Listeners (The Fix)
    // We listen for a click or keypress anywhere on the page
    document.addEventListener('click', unlockAudioEngine, { once: true });
    document.addEventListener('keydown', unlockAudioEngine, { once: true });

    // 3. Toastr Configuration
    toastr.options = {
        "closeButton": true,
        "newestOnTop": true,
        "positionClass": "toast-top-right",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };
    
    // 4. Sidebar Toggle
    $(document).on("click", ".toggle-sidebar-btn", function () {
        $("body").toggleClass("toggle-sidebar");
    });

    // 5. Start Notification System
    initNotificationSystem();
});

function myshowLoader() { $("#loader").fadeIn(200); }
function myhideLoader() { $("#loader").fadeOut(200); }

// ==================================================
// 3. HELPER FUNCTIONS
// ==================================================
function showToastMessage(type, text) {
    switch (type) {
        case 'success': toastr.success(text); break;
        case 'info': toastr.info(text); break;
        case 'error': toastr.error(text); break;
        case 'warning': toastr.warning(text); break;
        default: toastr.info(text); break;
    }
}

function handleLogout() {
    Swal.fire({
        title: 'Sign Out?',
        text: "You will need to login again to access your account.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#C89E47', 
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

// Global Axios Interceptor for 401 Unauthorized
if (typeof axios !== 'undefined') {
    axios.interceptors.response.use(
        response => response,
        error => {
            if (error.response && error.response.status === 401) {
                window.location.href = "/"; 
            }
            return Promise.reject(error);
        }
    );
}

// ==================================================
// 4. NOTIFICATION SYSTEM LOGIC
// ==================================================

let NOTIFICATION_SKIP = 0;
const NOTIFICATION_LIMIT = 10;
let NOTIFICATION_LOADING = false;
let wsConnection = null;

const notificationMap = {
    'task':     { icon: 'ri-clipboard-line', color: 'text-primary' },
    'invoice':  { icon: 'ri-file-list-3-line', color: 'text-success' },
    'system':   { icon: 'ri-settings-4-line', color: 'text-secondary' },
    'approval': { icon: 'ri-checkbox-circle-line', color: 'text-warning' },
    'critical': { icon: 'ri-alarm-warning-fill', color: 'text-danger' },
    'announcement': { icon: 'ri-megaphone-line', color: 'text-info' },
    'default':  { icon: 'ri-notification-badge-line', color: 'text-muted' }
};

function initNotificationSystem() {
    fetchNotifications(true);
    connectWebSocket();
}

function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/api/notification/ws`;

    if (wsConnection) wsConnection.close();

    wsConnection = new WebSocket(wsUrl);

    wsConnection.onopen = function() {
        // Connected silently
    };

    wsConnection.onmessage = function(event) {
        try {
            const payload = JSON.parse(event.data);
            if (payload.type === 'new_notification' && payload.data) {
                handleRealTimeNotification(payload.data);
            }
        } catch (e) { console.error("WS Parse Error", e); }
    };

    wsConnection.onclose = function(e) {
        // Reconnect logic
        setTimeout(() => connectWebSocket(), 5000);
    };

    wsConnection.onerror = function(err) {
        console.error("WS Error:", err);
    };
}

function fetchNotifications(reset = false) {
    if (NOTIFICATION_LOADING) return;
    NOTIFICATION_LOADING = true;

    if (reset) {
        NOTIFICATION_SKIP = 0;
        $("#notification-list").empty();
    }

    axios.get(`/api/notification/?limit=${NOTIFICATION_LIMIT}&skip=${NOTIFICATION_SKIP}`)
        .then(res => {
            let items = res.data.items || res.data; 
            if (!Array.isArray(items) && res.data.data) items = res.data.data;
            if (!Array.isArray(items)) items = []; 

            if (res.data.total_unread !== undefined) updateUnreadCount(res.data.total_unread, false);
            else fetchUnreadCount(); 

            const listContainer = $("#notification-list");
            if (reset) listContainer.empty();

            if (items.length === 0 && NOTIFICATION_SKIP === 0) {
                listContainer.html(`<li class="d-flex flex-column align-items-center justify-content-center py-4 text-muted"><i class="ri-notification-off-line fs-3 mb-2"></i><small>No notifications</small></li>`);
                $("#notification-footer").hide();
            } else {
                items.forEach(item => listContainer.append(renderNotificationItem(item)));
                $("#notification-footer").show();
                
                if (items.length < NOTIFICATION_LIMIT) $("#notification-footer button").hide();
                else $("#notification-footer button").show();
                
                NOTIFICATION_SKIP += NOTIFICATION_LIMIT;
            }
        })
        .finally(() => { NOTIFICATION_LOADING = false; });
}

function fetchUnreadCount() {
    axios.get('/api/notification/unread-count')
        .then(res => updateUnreadCount(res.data.count, false));
}

function renderNotificationItem(notif) {
    const style = notificationMap[notif.category] || notificationMap['default'];
    const bgClass = notif.is_read ? 'bg-white' : 'bg-light';
    const borderClass = notif.is_read ? '' : 'border-start border-4 border-warning';
    
    let dateStr = "Just now";
    if (notif.created_at) {
        dateStr = new Date(notif.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    const linkUrl = notif.click_action_link || '#';

    return `
    <li class="notification-item ${bgClass} ${borderClass} border-bottom position-relative" id="notif-${notif.id}">
        <a href="javascript:void(0)" 
           class="d-flex align-items-start p-3 text-decoration-none text-dark w-100"
           onclick="handleNotificationClick(${notif.id}, '${linkUrl}')">
            <div class="notif-icon-box rounded-circle bg-light d-flex align-items-center justify-content-center me-3" style="width: 35px; height: 35px; min-width: 35px;">
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

function handleRealTimeNotification(data) {
    // 1. Play Sound (Only if Unlocked)
    if (isAudioUnlocked) {
        notificationAudio.currentTime = 0;
        notificationAudio.play().catch(e => console.warn("Audio play prevented:", e));
    }

    // 2. Toast Color Logic
    const severity = (data.severity || 'normal').toLowerCase();

    if (severity === 'critical') {
        toastr.error(data.body, data.title);
    } else if (severity === 'high') {
        toastr.warning(data.body, data.title);
    } else {
        toastr.success(data.body, data.title);
    }

    // 3. Update Badge UI
    updateUnreadCount(1, true);

    // 4. Construct & Prepend Item
    const tempItem = {
        id: data.id,
        title: data.title,
        body: data.body,
        category: data.category || 'system',
        click_action_link: data.click_action_link, 
        is_read: false,
        created_at: data.created_at || new Date().toISOString()
    };
    
    const list = $("#notification-list");
    if (list.find('.ri-notification-off-line').length > 0) {
        list.empty();
        $("#notification-footer").show();
    }
    list.prepend(renderNotificationItem(tempItem));
}

function handleNotificationClick(id, link) {
    axios.put(`/api/notification/${id}/read`)
        .then(() => {
            if (link && link !== 'null' && link !== '#' && link !== 'undefined') window.location.href = link;
            else {
                $(`#notif-${id}`).removeClass('bg-light border-start border-4 border-warning').addClass('bg-white');
                updateUnreadCount(-1, true);
            }
        })
        .catch(() => {
            if (link && link !== 'null' && link !== '#') window.location.href = link;
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
        badge.addClass('animate__animated animate__pulse'); 
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