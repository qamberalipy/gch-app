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
            userRole: '{{ session_user_role }}', 
            
            posts: [],
            
            // Pagination
            isLoadingMore: false,
            allLoaded: false,
            
            // Composer
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
            loadingViewers: false,
            viewersList: [],
            viewersModalInstance: null,
            
            // Realtime
            socket: null
        }
    },
    mounted() {
        // 1. Initial Load
        this.fetchFeed(true);
        
        // 2. Connect Realtime
        this.connectWebSocket();

        // 3. Scroll Listener for Pagination
        const chatBody = this.$refs.chatBody;
        if(chatBody) {
            chatBody.addEventListener('scroll', this.handleScroll);
        }

        this.debouncedUrlCheck = _.debounce(this.fetchUrlMetadata, 800);
        
        const el = document.getElementById('viewersModal');
        if(el && typeof bootstrap !== 'undefined') {
            this.viewersModalInstance = new bootstrap.Modal(el);
        }
    },
    beforeUnmount() {
        if(this.socket) this.socket.close();
        const chatBody = this.$refs.chatBody;
        if(chatBody) chatBody.removeEventListener('scroll', this.handleScroll);
    },
    methods: {
        // --- WebSocket ---
        connectWebSocket() {
            // Auto-detect secure connection
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/announcement/ws`;
            
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => console.log("WS Connected");
            
            this.socket.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                
                if (msg.type === 'new_post') {
                    // Prevent duplicate if we just posted it ourselves via REST
                    if (!this.posts.find(p => p.id === msg.data.id)) {
                        this.posts.push(msg.data);
                        this.$nextTick(() => this.scrollToBottom());
                    }
                } 
                else if (msg.type === 'delete_post') {
                    this.posts = this.posts.filter(p => p.id !== msg.id);
                }
            };

            this.socket.onclose = () => {
                console.log("WS Disconnected. Reconnecting...");
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        },

        // --- Feed & Pagination ---
        async fetchFeed(isInitial = false) {
            if (this.isLoadingMore || this.allLoaded) return;
            
            this.isLoadingMore = true;
            
            try {
                const params = { limit: 20 };
                
                // Cursor: Get posts OLDER than the top one in our list
                if (!isInitial && this.posts.length > 0) {
                    params.last_id = this.posts[0].id;
                }

                const res = await axios.get('/api/announcement/', { params });
                
                // API returns Newest -> Oldest. We reverse for Chat (Oldest -> Newest)
                const newPosts = res.data.reverse(); 

                if (newPosts.length < 20) {
                    this.allLoaded = true;
                }

                if (isInitial) {
                    this.posts = newPosts;
                    this.loading = false;
                    this.$nextTick(() => {
                        this.scrollToBottom();
                        // Mark latest viewed
                        if(this.posts.length > 0) this.markViewed(this.posts[this.posts.length-1].id);
                    });
                } else {
                    // Prepend logic with Scroll Position Restoration
                    const chatBody = this.$refs.chatBody;
                    const oldHeight = chatBody.scrollHeight;
                    const oldTop = chatBody.scrollTop;

                    this.posts = [...newPosts, ...this.posts];
                    
                    this.$nextTick(() => {
                        const newHeight = chatBody.scrollHeight;
                        chatBody.scrollTop = oldTop + (newHeight - oldHeight);
                    });
                }
            } catch (e) { 
                console.error("Feed error", e); 
            } finally { 
                this.isLoadingMore = false; 
                this.loading = false;
            }
        },

        handleScroll() {
            const el = this.$refs.chatBody;
            // If user scrolls near the top (50px buffer), load more
            if (el.scrollTop < 50) {
                this.fetchFeed(false);
            }
        },

        // --- CRUD & Upload ---
        async deletePost(id) {
            if(!confirm("Are you sure?")) return;
            try {
                await axios.delete(`/api/announcement/${id}`);
                // Optimistic delete
                this.posts = this.posts.filter(p => p.id !== id);
            } catch(e) {
                if (typeof toastr !== 'undefined') toastr.error("Delete failed");
            }
        },

        async openViewersModal(id) {
            this.viewersList = [];
            this.loadingViewers = true;
            if(this.viewersModalInstance) this.viewersModalInstance.show();

            try {
                const res = await axios.get(`/api/announcement/${id}/viewers`);
                this.viewersList = res.data;
            } catch(e) {
                console.error(e);
            } finally {
                this.loadingViewers = false;
            }
        },

        // Grid & Helpers
        getGridClass(attachments) {
            const count = attachments.filter(a => ['image','video'].includes(a.file_type)).length;
            if (count >= 4) return 'grid-4';
            if (count === 3) return 'grid-3';
            if (count === 2) return 'grid-2';
            return 'grid-1';
        },

        handleFileSelect(e) {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                const objectUrl = URL.createObjectURL(file);
                this.tempFiles.push({ file: file, preview: objectUrl, type: file.type });
            });
            e.target.value = '';
        },

        // --- RESTORED UPLOAD LOGIC ---
        async uploadAsset(file) {
            // Check for large file/video -> Use Presigned URL
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
        // ------------------------------

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
                const payload = { content: this.newPost.content, attachments: attachments };

                await axios.post('/api/announcement/', payload);
                
                // Clear form
                this.newPost.content = '';
                this.tempFiles.forEach(f => URL.revokeObjectURL(f.preview));
                this.tempFiles = [];
                this.linkPreview = null;
                this.showEmoji = false;
                
                const txt = document.querySelector('.chat-input');
                if(txt) txt.style.height = 'auto';

            } catch (e) {
                if (typeof toastr !== 'undefined') toastr.error("Failed to post");
                console.error(e);
            } finally {
                this.isPosting = false;
                setTimeout(() => { this.uploadProgress = 0; }, 500);
            }
        },

        handleInput(e) {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
            this.debouncedUrlCheck(this.newPost.content);
        },
        async fetchUrlMetadata(text) {
            if (!text) return;
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