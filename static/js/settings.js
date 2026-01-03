/* static/js/settings.js */

$(document).ready(function() {
    
    // --- State Variables ---
    let currentUserId = null;
    let uploadedProfilePicUrl = null;
    let iti = null; // Phone input instance
    let cropper = null; // Cropper instance

    // --- 1. Initialization ---
    initSettings();

    function initSettings() {
        const token = localStorage.getItem("access_token");
        if (!token) { 
            window.location.href = "/login"; 
            return; 
        }

        // Init Phone Input
        const inputPhone = document.querySelector("#inputPhone");
        if(inputPhone) {
            iti = window.intlTelInput(inputPhone, {
                utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
                separateDialCode: true,
                preferredCountries: ["us", "gb", "pk"], // Add preferences
            });
        }

        const decoded = parseJwt(token);
        currentUserId = (typeof decoded.sub === 'object') ? decoded.sub.user_id : decoded.sub;

        if (currentUserId) {
            loadUserProfile(currentUserId);
        } else {
            showToastMessage('error', 'Could not identify user session.');
        }
    }

    // --- 2. Tab Switching Logic ---
    $('.settings-nav-item').on('click', function() {
        $('.settings-nav-item').removeClass('active');
        $(this).addClass('active');
        
        $('.settings-nav-item span').css('color', '#9ca3af'); 
        $(this).find('span').css('color', '#d97706'); 

        const target = $(this).data('tab');
        $('.tab-pane').removeClass('active').hide(); 
        $('#tab-' + target).fadeIn(200).addClass('active');
    });

    // --- 3. Load User Data (GET) ---
    async function loadUserProfile(id) {
        myshowLoader(); 
        try {
            const res = await axios.get(`/api/users/${id}`);
            const data = res.data;

            $('#inputFullName').val(data.full_name);
            $('#inputEmail').val(data.email);
            $('#inputRole').val(data.role || 'digital_creator');
            
            // Set Phone
            if (data.phone && iti) {
                iti.setNumber(data.phone);
            } else {
                $('#inputPhone').val(data.phone);
            }

            $('#inputBio').val(data.bio);
            $('#inputDob').val(data.dob);
            $('#inputGender').val(data.gender);

            $('#inputInsta').val(data.insta_link);
            $('#inputX').val(data.x_link);
            $('#inputOF').val(data.of_link);

            if (data.profile_picture_url) {
                $('#settingsAvatar').attr('src', data.profile_picture_url);
                uploadedProfilePicUrl = data.profile_picture_url;
            }

        } catch (err) {
            console.error(err);
            showToastMessage('error', 'Failed to load profile details.');
        } finally {
            myhideLoader();
        }
    }

    // --- 4. Image Cropping & Upload Logic ---
    
    // A. Trigger File Input
    $('#uploadDropZone').on('click', function() {
        $('#fileInput').val(''); // clear input to allow re-selection
        $('#fileInput').click();
    });

    // B. Handle File Selection -> Open Modal
    $('#fileInput').on('change', function(e) {
        const files = e.target.files;
        if (files && files.length > 0) {
            const file = files[0];
            const reader = new FileReader();
            
            reader.onload = function(evt) {
                // Set image src for cropper
                $('#imageToCrop').attr('src', evt.target.result);
                // Open Modal
                $('#cropModal').modal('show');
            };
            reader.readAsDataURL(file);
        }
    });

    // C. Initialize Cropper when Modal opens
    $('#cropModal').on('shown.bs.modal', function () {
        const image = document.getElementById('imageToCrop');
        cropper = new Cropper(image, {
            aspectRatio: 1, // 1:1 for Profile Pictures
            viewMode: 1,
            autoCropArea: 0.8,
        });
    }).on('hidden.bs.modal', function () {
        // Destroy cropper when modal closes to reset
        if(cropper) {
            cropper.destroy();
            cropper = null;
        }
    });

    // D. Handle Crop Confirmation
    $('#btnCropConfirm').on('click', function() {
        if (!cropper) return;

        // Get cropped canvas
        const canvas = cropper.getCroppedCanvas({
            width: 400, // Resize for consistency
            height: 400,
        });

        if (!canvas) {
            showToastMessage('error', 'Could not crop image.');
            return;
        }

        // Convert to Blob and Upload
        canvas.toBlob(async function(blob) {
            // Close Modal
            $('#cropModal').modal('hide');

            // --- Upload Logic (Reused from previous code) ---
            const formData = new FormData();
            // Append the blob, give it a filename
            formData.append('file', blob, 'profile-cropped.png'); 

            const $dropZone = $('#uploadDropZone');
            const originalContent = $dropZone.html();
            $dropZone.html('<div class="spinner-border text-warning spinner-border-sm"></div> Uploading...');

            try {
                const res = await axios.post('/api/upload/general-upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                if (res.data.status === 'success') {
                    uploadedProfilePicUrl = res.data.url;
                    $('#settingsAvatar').attr('src', uploadedProfilePicUrl);
                    $('#user-avatar-display').attr('src', uploadedProfilePicUrl); 
                    showToastMessage('success', 'Photo uploaded! Click Save to confirm.');
                }
            } catch (err) {
                let msg = err.response?.data?.detail || "Upload failed.";
                if(err.response?.status === 413) msg = "File too large.";
                showToastMessage('error', msg);
            } finally {
                $dropZone.html(originalContent);
            }

        }, 'image/png'); // Output type
    });

    // --- 5. Save Profile (PUT) ---
    $('#btnSaveProfile').on('click', async function() {
        if (!currentUserId) return;

        // Get Number from ITI plugin (E.164 format for database, e.g., +12015550123)
        const fullPhoneNumber = iti ? iti.getNumber() : $('#inputPhone').val();

        const payload = {
            full_name: $('#inputFullName').val(),
            bio: $('#inputBio').val(),
            phone: fullPhoneNumber, // Use formatted number
            dob: $('#inputDob').val() || null,
            gender: $('#inputGender').val() || null,
            insta_link: $('#inputInsta').val(),
            x_link: $('#inputX').val(),
            of_link: $('#inputOF').val(),
            profile_picture_url: uploadedProfilePicUrl
        };

        myshowLoader();
        try {
            await axios.put(`/api/users/${currentUserId}`, payload);
            showToastMessage('success', 'Profile updated successfully!');

            let userInfo = JSON.parse(localStorage.getItem("user_info") || '{}');
            userInfo.full_name = payload.full_name;

            // --- FIX START: Use correct key name ---
            if(payload.profile_picture_url) {
                userInfo.profile_picture_url = payload.profile_picture_url; // Was userInfo.avatar_url
            }
            // --- FIX END ---

            localStorage.setItem("user_info", JSON.stringify(userInfo));

        } catch (err) {
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

        if (!oldPass || !newPass || !confirmPass) {
            showToastMessage('warning', 'Please fill in all password fields.');
            return;
        }
        if (newPass !== confirmPass) {
            showToastMessage('error', 'New passwords do not match.');
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
            $('#oldPassword').val('');
            $('#newPassword').val('');
            $('#confirmPassword').val('');
            
            Swal.fire({
                icon: 'success',
                title: 'Password Changed',
                text: 'Please log in again.',
                confirmButtonColor: '#d97706'
            }).then(() => { handleLogout(); });

        } catch (err) {
            const msg = err.response?.data?.detail || "Password change failed.";
            showToastMessage('error', msg);
        } finally {
            myhideLoader();
        }
    });
});