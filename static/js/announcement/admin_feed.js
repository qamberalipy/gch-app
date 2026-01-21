/* static/js/announcement/admin_feed.js */

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            loading: true,
            isPosting: false,
            uploadProgress: 0,
            currentUserId: parseInt(document.querySelector('meta[name="user-id"]')?.content || 0),
            userRole: '{{ session_user_role }}', // Ensure this is available, or infer from ability to see delete btns
            posts: [],
            newPost: { content: '' },
            
            tempFiles: [], 
            linkPreview: null,
            
            showEmoji: false,
            emojis: [
                '👍','❤️','😂','😮','😢','😡','🔥','🎉','✅','🚀','👋','💯',
                '🙏','🤝','✨','💀','👀','🙌','🌟','💡','📅','📢','🔔','🎁',
                '🤔','😅','😎','🥺','🥳','🥴','👻','🤖','👽','🎃','👑','💎',
                '⚽','🏀','🎮','🎵','📸','🎥','🍔','🍕','🍺','✈️','🏠','💸'
            ],
            
            modal: { isOpen: false, type: '', url: '' },
            
            // Viewers Modal Data
            loadingViewers: false,
            viewersList: [],
            viewersModalInstance: null
        }
    },
    mounted() {
        this.fetchFeed();
        this.debouncedUrlCheck = _.debounce(this.fetchUrlMetadata, 800);
        // Init Bootstrap Modal
        const el = document.getElementById('viewersModal');
        if(el && typeof bootstrap !== 'undefined') {
            this.viewersModalInstance = new bootstrap.Modal(el);
        }
    },
    methods: {
        async fetchFeed() {
            try {
                const res = await axios.get('/api/announcement/');
                this.posts = res.data.reverse(); 
                this.$nextTick(() => this.scrollToBottom());
                if(this.posts.length > 0) this.markViewed(this.posts[this.posts.length-1].id);
            } catch (e) { 
                console.error("Feed error", e); 
            } finally { this.loading = false; }
        },

        /* --- 1. NEW FEATURES: DELETE & VIEWERS --- */
        async deletePost(id) {
            if(!confirm("Are you sure you want to delete this announcement?")) return;
            try {
                await axios.delete(`/api/announcement/${id}`);
                this.posts = this.posts.filter(p => p.id !== id);
                if (typeof toastr !== 'undefined') toastr.success("Deleted successfully");
            } catch(e) {
                if (typeof toastr !== 'undefined') toastr.error("Could not delete post");
            }
        },

        async openViewersModal(id) {
            this.viewersList = [];
            this.loadingViewers = true;
            if(this.viewersModalInstance) this.viewersModalInstance.show();

            try {
                // Assuming you have an endpoint for this. If not, you might need to add it.
                // Or if 'reactions' contains viewers, adapt accordingly. 
                // Using a hypothetical endpoint:
                const res = await axios.get(`/api/announcement/${id}/viewers`);
                this.viewersList = res.data;
            } catch(e) {
                console.error("Error fetching viewers", e);
                // Fallback for demo if API missing:
                // this.viewersList = [{full_name: "Demo User", id: 1}]; 
            } finally {
                this.loadingViewers = false;
            }
        },

        /* --- 2. GRID & FILE HELPERS --- */
        getGridClass(attachments) {
            const visualCount = attachments.filter(a => a.file_type === 'image' || a.file_type === 'video').length;
            if (visualCount >= 4) return 'grid-4';
            if (visualCount === 3) return 'grid-3';
            if (visualCount === 2) return 'grid-2';
            return 'grid-1';
        },

        handleFileSelect(e) {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                const objectUrl = URL.createObjectURL(file);
                this.tempFiles.push({
                    file: file,
                    preview: objectUrl, 
                    type: file.type
                });
            });
            e.target.value = '';
        },

        /* --- 3. UPLOAD LOGIC --- */
        async uploadAsset(file) {
            if (file.type.startsWith('video') || file.size > 10 * 1024 * 1024) {
                return await this.uploadVideoOrLargeFile(file);
            } else {
                return await this.uploadImageOrDoc(file);
            }
        },

        async uploadVideoOrLargeFile(file) {
            const ticketRes = await axios.post('/api/upload/presigned-url', {
                filename: file.name,
                content_type: file.type,
                category: 'reels'
            });
            const { upload_url, public_url } = ticketRes.data.ticket;
            await axios.put(upload_url, file, {
                headers: { 'Content-Type': file.type },
                onUploadProgress: (progressEvent) => {
                    this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                }
            });
            return public_url;
        },

        async uploadImageOrDoc(file) {
            const fd = new FormData();
            fd.append('file', file);
            let typeGroup = file.type.startsWith('image') ? 'image' : 'document';
            const res = await axios.post(`/api/upload/small-file?type_group=${typeGroup}`, fd, {
                onUploadProgress: (progressEvent) => {
                    this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                }
            });
            return res.data.url;
        },

        /* --- 4. PUBLISH --- */
        async publishPost() {
            if (!this.newPost.content && this.tempFiles.length === 0) return;
            this.isPosting = true;
            this.uploadProgress = 0;

            try {
                const attachments = await Promise.all(this.tempFiles.map(async (tf) => {
                    const url = await this.uploadAsset(tf.file);
                    return {
                        file_url: url,
                        file_type: tf.type.startsWith('image') ? 'image' : tf.type.startsWith('video') ? 'video' : 'document',
                        mime_type: tf.type,
                        file_size_mb: (tf.file.size / 1024 / 1024).toFixed(2)
                    };
                }));
                
                this.uploadProgress = 100;

                const payload = {
                    content: this.newPost.content,
                    attachments: attachments
                };

                const res = await axios.post('/api/announcement/', payload);
                this.posts.push(res.data);
                
                // Cleanup
                this.newPost.content = '';
                this.tempFiles.forEach(f => URL.revokeObjectURL(f.preview));
                this.tempFiles = [];
                this.linkPreview = null;
                this.showEmoji = false;
                
                const txt = document.querySelector('.chat-input');
                if(txt) txt.style.height = 'auto';

                this.$nextTick(() => this.scrollToBottom());
                if (typeof toastr !== 'undefined') toastr.success("Sent");

            } catch (e) {
                if (typeof toastr !== 'undefined') toastr.error("Failed to post");
                console.error(e);
            } finally {
                this.isPosting = false;
                setTimeout(() => { this.uploadProgress = 0; }, 500);
            }
        },

        /* --- 5. UI UTILS --- */
        handleInput(e) {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
            this.debouncedUrlCheck(this.newPost.content);
        },
        async fetchUrlMetadata(text) {
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            const match = text.match(urlRegex);
            if (match && match[0]) {
                if (this.linkPreview && this.linkPreview.link_url === match[0]) return;
                try {
                    const res = await axios.post('/api/announcement/preview-link', { url: match[0] });
                    if (res.data.link_title) this.linkPreview = res.data;
                } catch (e) { }
            } else {
                this.linkPreview = null;
            }
        },
        clearLinkPreview() { this.linkPreview = null; },
        removeFile(i) { URL.revokeObjectURL(this.tempFiles[i].preview); this.tempFiles.splice(i, 1); },
        toggleEmoji() {
            this.showEmoji = !this.showEmoji;
            if (this.showEmoji) document.querySelectorAll('.dropdown-menu.show').forEach(el => el.classList.remove('show'));
        },
        addEmoji(char) { this.newPost.content += char; },
        openModal(type, url) { this.modal = { isOpen: true, type, url }; },
        closeModal() { this.modal.isOpen = false; setTimeout(() => { this.modal.url = ''; }, 200); },
        async toggleReaction(post) {
            const has = this.hasLiked(post);
            if(has) post.reactions = post.reactions.filter(r => r.user_id !== this.currentUserId);
            else post.reactions.push({ user_id: this.currentUserId, emoji: '❤️' });
            try { await axios.post(`/api/announcement/${post.id}/react`, { emoji: '❤️' }); } catch(e){}
        },
        async markViewed(id) { try { await axios.post(`/api/announcement/${id}/view`); } catch(e){} },
        isMe(id) { return this.currentUserId === id; },
        hasLiked(post) { return post.reactions.some(r => r.user_id === this.currentUserId); },
        scrollToBottom() { const el = this.$refs.chatBody; if(el) el.scrollTop = el.scrollHeight; },
        formatTime(t) { return new Date(t).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}); }
    }
}).mount('#announcementApp');