/* static/js/announcement/admin_feed.js */

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            loading: true,
            isPosting: false,
            // Safe parsing of user ID
            currentUserId: parseInt(document.querySelector('meta[name="user-id"]')?.content || 0),
            posts: [],
            newPost: {
                content: '',
                tempFiles: [], 
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
                // Fetch posts (API returns Newest -> Oldest)
                const response = await axios.get('/api/announcement/');
                
                // REVERSE for Chat Interface (Oldest Top -> Newest Bottom)
                this.posts = response.data.reverse(); 

                // Mark latest visible as viewed
                if(this.posts.length > 0) {
                     this.markAsViewed(this.posts[this.posts.length - 1].id);
                }

                this.$nextTick(() => {
                    this.scrollToBottom();
                });

            } catch (error) {
                console.error("Failed to load feed", error);
                if (typeof toastr !== 'undefined') toastr.error("Could not load announcements");
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
            event.target.value = ''; 
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

                if (this.newPost.tempFiles.length > 0) {
                    for (const temp of this.newPost.tempFiles) {
                        const formData = new FormData();
                        formData.append('file', temp.file);
                        
                        let typeGroup = 'document';
                        if (temp.type.startsWith('image') || temp.type.startsWith('video')) {
                            typeGroup = 'image';
                        }

                        const uploadRes = await axios.post(`/api/upload/small-file?type_group=${typeGroup}`, formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });
                        
                        attachments.push({
                            file_url: uploadRes.data.url,
                            file_type: temp.type.startsWith('image') ? 'image' : 
                                       temp.type.startsWith('video') ? 'video' : 'document',
                            mime_type: temp.type,
                            file_size_mb: (temp.file.size / 1024 / 1024).toFixed(2)
                        });
                    }
                }

                const payload = {
                    content: this.newPost.content,
                    attachments: attachments
                };

                const response = await axios.post('/api/announcement/', payload);
                
                // Add to Bottom of List (Push)
                this.posts.push(response.data);
                
                this.resetForm();
                this.$nextTick(() => this.scrollToBottom());
                if (typeof toastr !== 'undefined') toastr.success("Sent!");

            } catch (error) {
                console.error(error);
                const msg = error.response?.data?.detail || "Failed to post";
                if (typeof toastr !== 'undefined') toastr.error(msg);
            } finally {
                this.isPosting = false;
            }
        },

        resetForm() {
            this.newPost.content = '';
            this.newPost.tempFiles = [];
            // Reset textarea height
            const textarea = document.querySelector('.chat-input');
            if(textarea) textarea.style.height = 'auto';
        },

        /* --- Actions --- */
        async deletePost(id) {
            try {
                await axios.delete(`/api/announcement/${id}`);
                this.posts = this.posts.filter(p => p.id !== id);
                if (typeof toastr !== 'undefined') toastr.success("Deleted");
            } catch (error) {
                if (typeof toastr !== 'undefined') toastr.error("Failed to delete");
            }
        },

        async toggleReaction(post) {
            const myReaction = post.reactions.find(r => r.user_id === this.currentUserId);
            if (myReaction) {
                post.reactions = post.reactions.filter(r => r.user_id !== this.currentUserId);
            } else {
                post.reactions.push({ user_id: this.currentUserId, emoji: "❤️" });
            }

            try { await axios.post(`/api/announcement/${post.id}/react`, { emoji: "❤️" }); } catch (e) {}
        },

        async markAsViewed(postId) {
            try { await axios.post(`/api/announcement/${postId}/view`); } catch (e) {}
        },

        async openViewersModal(postId) {
            this.currentViewers = [];
            const modal = new bootstrap.Modal(document.getElementById('viewersModal'));
            modal.show();
            try {
                const res = await axios.get(`/api/announcement/${postId}/viewers`);
                this.currentViewers = res.data;
            } catch (error) {}
        },

        openImage(url) {
            window.open(url, '_blank');
        },

        /* --- UI Helpers --- */
        isMe(authorId) {
            return this.currentUserId === authorId;
        },

        canDelete(authorId) {
            return this.currentUserId === authorId; 
        },

        scrollToBottom() {
            const container = this.$refs.chatBody;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },

        autoResize(event) {
            const el = event.target;
            el.style.height = 'auto';
            el.style.height = el.scrollHeight + 'px';
        },

        formatTime(dateString) {
            const date = new Date(dateString);
            return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        }
    }
}).mount('#announcementApp');