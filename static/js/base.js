// Base URL for API calls
let baseUrl = window.location.origin;

$(document).ready(function () {
    // Ensure loader is hidden on page load
    myhideLoader();

    // Configure Toastr Global Options
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
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

/* --- Loader Functions --- */
function myshowLoader() {
    $("#loader").fadeIn(200);
}

function myhideLoader() {
    $("#loader").fadeOut(200);
}

/* --- Toastr Wrapper Function --- */
function showToastMessage(type, text) {
    switch (type) {
        case 'success':
            toastr.success(text);
            break;
        case 'info':
            toastr.info(text);
            break;
        case 'error':
            toastr.error(text);
            break;
        case 'warning':
            toastr.warning(text);
            break;
        default:
            console.error('Invalid toast type:', type);
            break;
    }
}

/* --- Date Formatting Utility --- */
function formatDateOnly(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

/* --- Axios Interceptors (Optional: Auto-Loader) --- */
if (typeof axios !== 'undefined') {
    // Add a request interceptor
    axios.interceptors.request.use(function (config) {
        // myshowLoader(); // Uncomment if you want loader on every request
        return config;
    }, function (error) {
        // myhideLoader();
        return Promise.reject(error);
    });

    // Add a response interceptor
    axios.interceptors.response.use(function (response) {
        // myhideLoader();
        return response;
    }, function (error) {
        // myhideLoader();
        return Promise.reject(error);
    });
}