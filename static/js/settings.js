/* static/js/settings.js */

$(document).ready(function() {
    
    // --- State Variables ---
    let currentUserId = null;
    let uploadedProfilePicUrl = null;

    // --- 1. Initialization ---
    initSettings();

    function initSettings() {
        const token = localStorage.getItem("access_token");
        if (!token) { 
            // base.js usually handles redirect, but just in case
            window.location.href = "/login"; 
            return; 
        }

        // Use base.js utility to get ID
        const decoded = parseJwt(token);
        // Supports both schema styles: {sub: 1} or {sub: {user_id: 1}}
        currentUserId = (typeof decoded.sub === 'object') ? decoded.sub.user_id : decoded.sub;

        if (currentUserId) {
            loadUserProfile(currentUserId);
        } else {
            showToastMessage('error', 'Could not identify user session.');
        }
    }

    // --- 2. Tab Switching Logic ---
    $('.settings-nav-item').on('click', function() {
        // Active State UI
        $('.settings-nav-item').removeClass('active');
        $(this).addClass('active');

        // Show Content
        const target = $(this).data('tab');
        $('.tab-pane').removeClass('active').hide(); // Hide all
        $('#tab-' + target).fadeIn(200).addClass('active'); // Show target
    });

    // --- 3. Load User Data (GET) ---
    async function loadUserProfile(id) {
        myshowLoader(); // from base.js
        try {
            // Axios base URL and headers are handled by base.js interceptors
            const res = await axios.get(`/api/users/${id}`);
            const data = res.data;

            // Populate Form
            $('#inputFullName').val(data.full_name);
            $('#inputEmail').val(data.email);
            $('#inputRole').val(data.role || 'digital_creator');
            $('#inputPhone').val(data.phone);
            $('#inputBio').val(data.bio);
            $('#inputDob').val(data.dob);
            $('#inputGender').val(data.gender);

            // Populate Socials
            $('#inputInsta').val(data.insta_link);
            $('#inputX').val(data.x_link);
            $('#inputOF').val(data.of_link);

            // Handle Avatar
            if (data.profile_picture_url) {
                $('#settingsAvatar').attr('src', data.profile_picture_url);
                uploadedProfilePicUrl = data.profile_picture_url;
            }

        } catch (err) {
            console.error(err);
            showToastMessage('error', 'Failed to load profile details.');
        } finally {
            myhideLoader(); // from base.js
        }
    }

    // --- 4. File Upload Logic ---
    // Trigger hidden input when clicking area
    $('#uploadDropZone').on('click', function() {
        $('#fileInput').click();
    });

    // Handle File Selection
    $('#fileInput').on('change', async function() {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const formData = new FormData();
            formData.append('file', file);

            // UI Feedback
            const $dropZone = $('#uploadDropZone');
            const originalContent = $dropZone.html();
            $dropZone.html('<div class="spinner-border text-warning spinner-border-sm"></div> Uploading...');

            try {
                // Important: Let browser set Content-Type for FormData
                const res = await axios.post('/api/upload/general-upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                if (res.data.status === 'success') {
                    uploadedProfilePicUrl = res.data.url;
                    
                    // Update Previews
                    $('#settingsAvatar').attr('src', uploadedProfilePicUrl);
                    $('#user-avatar-display').attr('src', uploadedProfilePicUrl); // Navbar
                    
                    showToastMessage('success', 'Photo uploaded! Click Save to confirm.');
                }
            } catch (err) {
                console.error(err);
                let msg = err.response?.data?.detail || "Upload failed.";
                if(err.response?.status === 413) msg = "File too large (Max 15MB).";
                showToastMessage('error', msg);
            } finally {
                $dropZone.html(originalContent);
            }
        }
    });

    // --- 5. Save Profile (PUT) ---
    $('#btnSaveProfile').on('click', async function() {
        if (!currentUserId) return;

        const payload = {
            full_name: $('#inputFullName').val(),
            bio: $('#inputBio').val(),
            phone: $('#inputPhone').val(),
            dob: $('#inputDob').val() || null,
            gender: $('#inputGender').val() || null,
            
            // Socials
            insta_link: $('#inputInsta').val(),
            x_link: $('#inputX').val(),
            of_link: $('#inputOF').val(),

            // Image URL (from R2)
            profile_picture_url: uploadedProfilePicUrl
        };

        // Filter out empty strings if needed, though Backend handles Optionals
        
        myshowLoader();
        try {
            await axios.put(`/api/users/${currentUserId}`, payload);
            
            showToastMessage('success', 'Profile updated successfully!');

            // Update LocalStorage User Info for Sidebar/Navbar consistency
            let userInfo = JSON.parse(localStorage.getItem("user_info") || '{}');
            userInfo.full_name = payload.full_name;
            if(payload.profile_picture_url) userInfo.avatar_url = payload.profile_picture_url;
            localStorage.setItem("user_info", JSON.stringify(userInfo));

        } catch (err) {
            console.error(err);
            showToastMessage('error', 'Failed to save changes.');
        } finally {
            myhideLoader();
        }
    });

    // --- 6. Save Password (POST) ---
    $('#btnSavePassword').on('click', async function() {
        const oldPass = $('#oldPassword').val();
        const newPass = $('#newPassword').val();
        const confirmPass = $('#confirmPassword').val();

        // Basic Validation
        if (!oldPass || !newPass || !confirmPass) {
            showToastMessage('warning', 'Please fill in all password fields.');
            return;
        }
        if (newPass !== confirmPass) {
            showToastMessage('error', 'New passwords do not match.');
            return;
        }
        if (newPass.length < 6) {
            showToastMessage('warning', 'Password must be at least 6 characters.');
            return;
        }

        const payload = {
            old_password: oldPass,
            new_password: newPass,
            confirm_password: confirmPass
        };

        myshowLoader();
        try {
            await axios.post('/api/users/change-password', payload);
            
            // Clear fields
            $('#oldPassword').val('');
            $('#newPassword').val('');
            $('#confirmPassword').val('');

            Swal.fire({
                icon: 'success',
                title: 'Password Changed',
                text: 'Please log in again with your new password.',
                confirmButtonColor: '#d97706'
            }).then(() => {
                handleLogout(); // from base.js
            });

        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || "Password change failed.";
            showToastMessage('error', msg);
        } finally {
            myhideLoader();
        }
    });

});