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
// If the cookie expires while the user is on the page, 
// any API call they make will return 401. We catch that here.
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