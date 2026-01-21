/* static/js/announcement/admin_feed.js */

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'], // Vue delimiters changed to avoid conflict with Jinja2 {{ }}
    data() {
        return {
            loading: true,
            isPosting: false,
            // Safe parsing of the user ID from the meta tag
            currentUserId: parseInt(document.querySelector('meta[name="user-id"]')?.content || 0),
            posts: [],
            newPost: {
                content: '',
                tempFiles: [], // { file: FileObj, preview: String, type: String }
            },
            currentViewers: []
        }
    },
    mounted() {
        this.fetchFeed();
    },
    methods: {
        async fetchFeed() {
            try {
                const response = await axios.get('/api/announcement/');
                this.posts = response.data;
                // Optional: Mark visible posts as viewed immediately
                if(this.posts.length > 0) {
                     this.markAsViewed(this.posts[0].id); // Example: mark newest as read
                }
            } catch (error) {
                console.error("Failed to load feed", error);
                toastr.error("Could not load announcements");
            } finally {
                this.loading = false;
            }
        },

        /* --- File Handling --- */
        handleFileSelect(event) {
            const files = Array.from(event.target.files);
            if (!files.length) return;

            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.newPost.tempFiles.push({
                        file: file,
                        preview: e.target.result,
                        type: file.type
                    });
                };
                reader.readAsDataURL(file);
            });
            
            event.target.value = ''; // Reset input
        },
        
        removeFile(index) {
            this.newPost.tempFiles.splice(index, 1);
        },

        /* --- Publishing --- */
        async publishPost() {
            if (!this.newPost.content && this.newPost.tempFiles.length === 0) return;
            
            this.isPosting = true;
            try {
                const attachments = [];

                // 1. Upload Files First
                if (this.newPost.tempFiles.length > 0) {
                    for (const temp of this.newPost.tempFiles) {
                        const formData = new FormData();
                        formData.append('file', temp.file);
                        
                        // Adjust endpoint to match your app/upload/upload.py router
                        const uploadRes = await axios.post('/api/upload/', formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });
                        
                        // Check if your API returns { public_url: ... } or { url: ... }
                        const fileUrl = uploadRes.data.public_url || uploadRes.data.url || uploadRes.data.file_url;

                        attachments.push({
                            file_url: fileUrl,
                            file_type: temp.type.startsWith('image') ? 'image' : 
                                       temp.type.startsWith('video') ? 'video' : 'document',
                            mime_type: temp.type,
                            file_size_mb: (temp.file.size / 1024 / 1024).toFixed(2)
                        });
                    }
                }

                // 2. Create Announcement
                const payload = {
                    content: this.newPost.content,
                    attachments: attachments
                };

                const response = await axios.post('/api/announcement/', payload);
                
                // 3. Update UI
                this.posts.unshift(response.data);
                this.resetForm();
                toastr.success("Announcement posted!");

            } catch (error) {
                console.error(error);
                toastr.error("Failed to post announcement");
            } finally {
                this.isPosting = false;
            }
        },

        resetForm() {
            this.newPost.content = '';
            this.newPost.tempFiles = [];
        },

        /* --- Actions --- */
        async deletePost(id) {
            Swal.fire({
                title: 'Delete this post?',
                text: "This cannot be undone.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc2626',
                confirmButtonText: 'Yes, delete it'
            }).then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        await axios.delete(`/api/announcement/${id}`);
                        this.posts = this.posts.filter(p => p.id !== id);
                        toastr.success("Post deleted");
                    } catch (error) {
                        toastr.error("Failed to delete");
                    }
                }
            });
        },

        async toggleReaction(post) {
            const myReaction = post.reactions.find(r => r.user_id === this.currentUserId);
            
            if (myReaction) {
                post.reactions = post.reactions.filter(r => r.user_id !== this.currentUserId);
            } else {
                post.reactions.push({ user_id: this.currentUserId, emoji: "❤️" });
            }

            try {
                await axios.post(`/api/announcement/${post.id}/react`, { emoji: "❤️" });
            } catch (error) {
                console.error("Reaction failed");
            }
        },

        async markAsViewed(postId) {
            try {
                await axios.post(`/api/announcement/${postId}/view`);
            } catch (e) { /* silent fail */ }
        },

        async openViewersModal(postId) {
            this.currentViewers = [];
            const modal = new bootstrap.Modal(document.getElementById('viewersModal'));
            modal.show();
            
            try {
                const res = await axios.get(`/api/announcement/${postId}/viewers`);
                this.currentViewers = res.data;
            } catch (error) {
                console.error("Could not fetch viewers");
            }
        },

        /* --- Helpers --- */
        userHasReacted(post) {
            return post.reactions.some(r => r.user_id === this.currentUserId);
        },

        canDelete(authorId) {
            return this.currentUserId === authorId; 
        },

        formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', { 
                month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' 
            });
        }
    }
}).mount('#announcementApp');