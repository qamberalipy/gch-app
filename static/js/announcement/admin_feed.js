/* static/js/announcement/admin_feed.js */

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            loading: true,
            isPosting: false,
            // Safe parsing of User ID from Meta tag
            currentUserId: parseInt(document.querySelector('meta[name="user-id"]')?.content || 0),
            posts: [],
            newPost: { content: '' },
            
            // Files & Preview
            tempFiles: [], 
            linkPreview: null,
            
            // UI States
            showEmoji: false,
            emojis: ['👍','❤️','😂','😮','😢','😡','🔥','🎉','✅','🚀','👋','💯'],
            modal: { isOpen: false, type: '', url: '' }
        }
    },
    mounted() {
        this.fetchFeed();
        // Create a debounced function for URL checking (waits 800ms after typing)
        this.debouncedUrlCheck = _.debounce(this.fetchUrlMetadata, 800);
    },
    methods: {
        async fetchFeed() {
            try {
                // Fetch posts (Backend returns Newest -> Oldest)
                const res = await axios.get('/api/announcement/');
                
                // Reverse them for Chat Interface (Oldest Top -> Newest Bottom)
                this.posts = res.data.reverse(); 
                
                this.$nextTick(() => this.scrollToBottom());
                
                // Mark latest as seen (if any)
                if(this.posts.length > 0) {
                     this.markViewed(this.posts[this.posts.length-1].id);
                }
            } catch (e) { 
                console.error("Feed error", e); 
                if (typeof toastr !== 'undefined') toastr.error("Could not load feed");
            } 
            finally { this.loading = false; }
        },

        /* --- 1. SMART UPLOAD SYSTEM --- */
        async uploadAsset(file) {
            // Logic: If Video OR File > 10MB -> Use Presigned URL (Direct to Cloud)
            if (file.type.startsWith('video') || file.size > 10 * 1024 * 1024) {
                return await this.uploadVideoOrLargeFile(file);
            } else {
                return await this.uploadImageOrDoc(file);
            }
        },

        async uploadVideoOrLargeFile(file) {
            console.log("Using Presigned Route for Large File/Video...");
            // Step 1: Get Presigned Ticket
            const ticketRes = await axios.post('/api/upload/presigned-url', {
                filename: file.name,
                content_type: file.type,
                category: 'reels' // Storing in video folder
            });
            const { upload_url, public_url } = ticketRes.data.ticket;

            // Step 2: Direct PUT to Cloud (Bypassing Server Limits)
            await axios.put(upload_url, file, {
                headers: { 'Content-Type': file.type }
            });

            return public_url;
        },

        async uploadImageOrDoc(file) {
            console.log("Using Fast Server Route for Image/Doc...");
            const fd = new FormData();
            fd.append('file', file);
            
            // Determine folder group
            let typeGroup = file.type.startsWith('image') ? 'image' : 'document';
            
            // Using your existing 'small-file' route
            const res = await axios.post(`/api/upload/small-file?type_group=${typeGroup}`, fd);
            return res.data.url;
        },

        /* --- 2. PUBLISHING --- */
        async publishPost() {
            if (!this.newPost.content && this.tempFiles.length === 0) return;
            this.isPosting = true;

            try {
                // Upload all files concurrently
                const attachments = await Promise.all(this.tempFiles.map(async (tf) => {
                    const url = await this.uploadAsset(tf.file);
                    return {
                        file_url: url,
                        file_type: tf.type.startsWith('image') ? 'image' : tf.type.startsWith('video') ? 'video' : 'document',
                        mime_type: tf.type,
                        file_size_mb: (tf.file.size / 1024 / 1024).toFixed(2)
                    };
                }));

                const payload = {
                    content: this.newPost.content,
                    attachments: attachments
                };

                // The backend automatically scrapes URLs if content has one.
                // We rely on that for the database save, but we showed the user a live preview.

                const res = await axios.post('/api/announcement/', payload);
                
                // Add new post to bottom
                this.posts.push(res.data);
                
                // Reset UI
                this.newPost.content = '';
                this.tempFiles = [];
                this.linkPreview = null;
                this.showEmoji = false;
                
                // Reset Textarea Height
                const txt = document.querySelector('.chat-input');
                if(txt) txt.style.height = 'auto';

                this.$nextTick(() => this.scrollToBottom());
                if (typeof toastr !== 'undefined') toastr.success("Sent");

            } catch (e) {
                if (typeof toastr !== 'undefined') toastr.error("Failed to post");
                console.error(e);
            } finally {
                this.isPosting = false;
            }
        },

        /* --- 3. URL LIVE PREVIEW --- */
        handleInput(e) {
            // Auto-resize textarea
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
            
            // Trigger Debounced Check
            this.debouncedUrlCheck(this.newPost.content);
        },

        async fetchUrlMetadata(text) {
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            const match = text.match(urlRegex);
            
            if (match && match[0]) {
                // Avoid re-fetching same URL
                if (this.linkPreview && this.linkPreview.link_url === match[0]) return;

                try {
                    const res = await axios.post('/api/announcement/preview-link', { url: match[0] });
                    if (res.data.link_title) {
                        this.linkPreview = res.data;
                    }
                } catch (e) { /* ignore preview errors */ }
            } else {
                this.linkPreview = null;
            }
        },

        clearLinkPreview() {
            this.linkPreview = null;
        },

        /* --- 4. UI HELPERS --- */
        handleFileSelect(e) {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = (ev) => {
                    this.tempFiles.push({
                        file: file,
                        preview: ev.target.result,
                        type: file.type
                    });
                };
                reader.readAsDataURL(file);
            });
            e.target.value = '';
        },
        removeFile(i) { this.tempFiles.splice(i, 1); },
        
        addEmoji(char) {
            this.newPost.content += char;
            this.showEmoji = false;
        },

        openModal(type, url) {
            this.modal = { isOpen: true, type, url };
        },
        closeModal() {
            this.modal.isOpen = false;
            setTimeout(() => { this.modal.url = ''; }, 200); // Clear after fade out
        },

        async toggleReaction(post) {
            const has = this.hasLiked(post);
            // Optimistic UI
            if(has) post.reactions = post.reactions.filter(r => r.user_id !== this.currentUserId);
            else post.reactions.push({ user_id: this.currentUserId, emoji: '❤️' });

            try { await axios.post(`/api/announcement/${post.id}/react`, { emoji: '❤️' }); } catch(e){}
        },

        async markViewed(id) {
            try { await axios.post(`/api/announcement/${id}/view`); } catch(e){}
        },

        isMe(id) { return this.currentUserId === id; },
        hasLiked(post) { return post.reactions.some(r => r.user_id === this.currentUserId); },
        scrollToBottom() { 
            const el = this.$refs.chatBody;
            if(el) el.scrollTop = el.scrollHeight; 
        },
        formatTime(t) { 
            return new Date(t).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}); 
        }
    }
}).mount('#announcementApp');