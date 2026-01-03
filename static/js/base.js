/* static/js/main.js */

// ==================================================
// 1. JWT UTILITIES (Parse Token Locally)
// ==================================================
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

function isTokenExpired(token) {
    const decoded = parseJwt(token);
    if (!decoded || !decoded.exp) return true;
    // JWT exp is in seconds, Date.now() is in milliseconds
    return (decoded.exp * 1000) < Date.now();
}

// ==================================================
// 2. AUTH GUARD & UI HYDRATION
// ==================================================
(function initDashboard() {
    const publicPages = ['/login', '/register', '/forgot-password', '/reset-password', '/'];
    const currentPath = window.location.pathname;

    if (publicPages.includes(currentPath)) return;

    // --- Security Check ---
    const accessToken = localStorage.getItem("access_token");
    const userInfoRaw = localStorage.getItem("user_info");

    // 1. Check if token exists
    if (!accessToken || !userInfoRaw) {
        console.warn("No token found.");
        window.location.href = "/login";
        return;
    }

    // 2. Check if token is expired locally (Optional but faster)
    if (isTokenExpired(accessToken)) {
        console.warn("Token expired. Attempting refresh via Interceptor...");
        // We allow the page to load; the first API call will trigger the refresh flow automatically.
    }

    // --- UI Hydration ---
    document.addEventListener("DOMContentLoaded", function () {
        try {
            const user = JSON.parse(userInfoRaw);
            const nameEl = document.getElementById("user-name-display");
            const roleEl = document.getElementById("user-role-display");
            const avatarEl = document.getElementById("user-avatar-display");

            if (nameEl) nameEl.innerText = user.full_name || user.username || "User";
            if (roleEl) roleEl.innerText = user.role || "Member";

            if (avatarEl) {
                // --- FIX START: Change user.avatar_url to user.profile_picture_url ---
                const imgSrc = user.profile_picture_url || `https://ui-avatars.com/api/?name=${user.username}&background=C89E47&color=fff`;
                // --- FIX END ---

                avatarEl.src = imgSrc;
            }
        } catch (e) {
            handleLogout(); // Data corrupted
        }
    });
})();

// ==================================================
// 3. LOGOUT FUNCTION (With API Call)
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
            const refreshToken = localStorage.getItem("refresh_token");

            // Call API to invalidate token on server
            if (refreshToken) {
                axios.post('/api/auth/logout', { refresh_token: refreshToken })
                    .catch(err => console.error("Logout API failed", err))
                    .finally(() => {
                        performLocalLogout();
                    });
            } else {
                performLocalLogout();
            }
        }
    });
}

function performLocalLogout() {
    localStorage.clear();
    window.location.href = "/login";
}

// ==================================================
// 4. AXIOS INTERCEPTORS (The Refresh Logic)
// ==================================================
let baseUrl = window.location.origin;

// Flag to prevent infinite refresh loops
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

if (typeof axios !== 'undefined') {

    // REQUEST INTERCEPTOR: Attach Token
    axios.interceptors.request.use(function (config) {
        const token = localStorage.getItem("access_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    }, function (error) {
        return Promise.reject(error);
    });

    // RESPONSE INTERCEPTOR: Handle 401 & Refresh
    axios.interceptors.response.use(function (response) {
        return response;
    }, function (error) {

        const originalRequest = error.config;

        // If error is 401 (Unauthorized) and we haven't tried refreshing yet
        if (error.response && error.response.status === 401 && !originalRequest._retry) {

            if (isRefreshing) {
                return new Promise(function (resolve, reject) {
                    failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers['Authorization'] = 'Bearer ' + token;
                    return axios(originalRequest);
                }).catch(err => {
                    return Promise.reject(err);
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem("refresh_token");

            if (!refreshToken) {
                performLocalLogout();
                return Promise.reject(error);
            }

            // Call Refresh API
            return axios.post('/api/auth/refresh', { refresh_token: refreshToken })
                .then(res => {
                    if (res.status === 200 || res.status === 201) {
                        // 1. Save new tokens
                        const newAccessToken = res.data.access_token;
                        localStorage.setItem("access_token", newAccessToken);
                        if (res.data.refresh_token) {
                            localStorage.setItem("refresh_token", res.data.refresh_token);
                        }

                        // 2. Update header
                        axios.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
                        originalRequest.headers['Authorization'] = 'Bearer ' + newAccessToken;

                        // 3. Process queued requests
                        processQueue(null, newAccessToken);

                        // 4. Retry original request
                        return axios(originalRequest);
                    }
                })
                .catch(err => {
                    processQueue(err, null);
                    performLocalLogout();
                    return Promise.reject(err);
                })
                .finally(() => {
                    isRefreshing = false;
                });
        }

        return Promise.reject(error);
    });
}

// ==================================================
// 5. UI UTILITIES
// ==================================================
$(document).ready(function () {
    myhideLoader();
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