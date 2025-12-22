/* static/js/auth.js */

$(document).ready(function() {

    // --- 1. Global Password Toggler ---
    // Works for any input with .eye-icon inside .password-wrapper
    $(".eye-icon").click(function() {
        const wrapper = $(this).closest('.password-wrapper');
        const input = wrapper.find('input');
        const icon = $(this).find('i');
        
        if (input.attr("type") === "password") {
            input.attr("type", "text");
            icon.removeClass("bi-eye").addClass("bi-eye-slash");
        } else {
            input.attr("type", "password");
            icon.removeClass("bi-eye-slash").addClass("bi-eye");
        }
    });

    // --- 2. Helper: Loading State ---
    function showLoading(title) {
        Swal.fire({
            heightAuto: false,
            title: title || 'Processing...',
            text: 'Please wait a moment',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });
    }

    // --- 3. Helper: Error State ---
    function showError(xhr, defaultMsg) {
        Swal.close();
        let errorMsg = defaultMsg || "An error occurred.";
        if (xhr.responseJSON && xhr.responseJSON.detail) {
            errorMsg = xhr.responseJSON.detail;
        }
        Swal.fire({
            heightAuto: false,
            icon: 'error',
            title: 'Oops...',
            text: errorMsg,
            confirmButtonColor: '#C49A6C'
        });
    }

    // ==========================================
    //  LOGIC: LOGIN PAGE
    // ==========================================
    if ($("#loginForm").length) {
        $("#loginForm").submit(function(e) {
            e.preventDefault();
            showLoading('Signing in...');

            const formData = {
                email: $("#email").val(),
                password: $("#password").val()
            };

            $.ajax({
                type: "POST",
                url: "/api/auth/login",
                contentType: "application/json",
                data: JSON.stringify(formData),
                success: function(response) {
                    Swal.close();
                    localStorage.setItem("access_token", response.access_token);
                    if (response.user && response.user.role) {
                        localStorage.setItem("user_role", response.user.role);
                    }
                    Swal.fire({
                        heightAuto: false,
                        icon: 'success',
                        title: 'Login Successful',
                        timer: 1500,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.href = "/demo"; // Change as needed
                    });
                },
                error: function(xhr) { showError(xhr, "Login failed."); }
            });
        });
    }

    // ==========================================
    //  LOGIC: FORGOT PASSWORD PAGE
    // ==========================================
    if ($("#forgotForm").length) {
        $("#forgotForm").submit(function(e) {
            e.preventDefault();
            const email = $("#email").val();
            showLoading('Sending OTP...');

            $.ajax({
                type: "POST",
                url: "/api/auth/forgot-password",
                contentType: "application/json",
                data: JSON.stringify({ email: email }),
                success: function(response) {
                    Swal.close();
                    Swal.fire({
                        heightAuto: false,
                        icon: 'success',
                        title: 'OTP Sent!',
                        text: 'Please check your email for the reset code.',
                        confirmButtonColor: '#C49A6C'
                    }).then(() => {
                        // Redirect to Reset Page with email pre-filled in URL
                        window.location.href = `/reset-password?email=${encodeURIComponent(email)}`;
                    });
                },
                error: function(xhr) { showError(xhr, "Could not send reset email."); }
            });
        });
    }

    // ==========================================
    //  LOGIC: RESET PASSWORD PAGE
    // ==========================================
    if ($("#resetForm").length) {
        // Auto-fill email from URL if present
        const urlParams = new URLSearchParams(window.location.search);
        const emailParam = urlParams.get('email');
        if (emailParam) {
            $("#email").val(emailParam);
        }

        $("#resetForm").submit(function(e) {
            e.preventDefault();
            
            const password = $("#new_password").val();
            const confirmPassword = $("#confirm_password").val();

            if(password !== confirmPassword) {
                Swal.fire({ heightAuto: false, icon: 'warning', title: 'Mismatch', text: 'Passwords do not match!', confirmButtonColor: '#C49A6C' });
                return;
            }

            showLoading('Resetting Password...');

            const formData = {
                email: $("#email").val(),
                otp: $("#otp").val(),
                new_password: password
            };

            $.ajax({
                type: "POST",
                url: "/api/auth/reset-password",
                contentType: "application/json",
                data: JSON.stringify(formData),
                success: function(response) {
                    Swal.close();
                    Swal.fire({
                        heightAuto: false,
                        icon: 'success',
                        title: 'Password Reset!',
                        text: 'You can now login with your new password.',
                        confirmButtonColor: '#C49A6C'
                    }).then(() => {
                        window.location.href = "/login";
                    });
                },
                error: function(xhr) { showError(xhr, "Password reset failed."); }
            });
        });
    }
});