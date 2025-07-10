/**
 * Real-time Notification System for EZM Trade Management
 * Handles AJAX updates, user interactions, and notification management
 */

class NotificationManager {
    constructor() {
        this.pollInterval = 30000; // 30 seconds
        this.pollTimer = null;
        this.isDropdownOpen = false;
        this.lastUpdateTime = null;
        this.lastUnreadCount = 0;
        this.isInitialized = false;

        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadNotifications();
        this.startPolling();
    }
    
    bindEvents() {
        // Notification bell click
        const bellBtn = document.getElementById('notificationBell');
        if (bellBtn) {
            bellBtn.addEventListener('shown.bs.dropdown', () => {
                this.isDropdownOpen = true;
                this.loadNotifications();
            });
            
            bellBtn.addEventListener('hidden.bs.dropdown', () => {
                this.isDropdownOpen = false;
            });
        }
        
        // Mark all as read
        const markAllBtn = document.getElementById('markAllReadBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => this.markAllAsRead());
        }
        
        // Refresh notifications
        const refreshBtn = document.getElementById('refreshNotificationsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadNotifications());
        }
        
        // Handle notification item clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.mark-read-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const notificationId = e.target.closest('.notification-item').dataset.notificationId;
                this.markAsRead(notificationId);
            }
            
            if (e.target.closest('.notification-item')) {
                const item = e.target.closest('.notification-item');
                const actionBtn = item.querySelector('.notification-action-btn');
                if (actionBtn && actionBtn.href && actionBtn.href !== '#') {
                    window.location.href = actionBtn.href;
                }
            }
        });
    }
    
    async loadNotifications() {
        try {
            this.showLoading();
            
            const response = await fetch('/api/notifications/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.updateNotifications(data);
            this.lastUpdateTime = new Date();
            
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError();
        }
    }
    
    updateNotifications(data) {
        const { notifications, unread_count } = data;

        // Check for changes in unread count
        const countChanged = this.lastUnreadCount !== unread_count;

        // Update badge with animation if count changed
        this.updateBadge(unread_count, countChanged);

        // Update dropdown content
        if (notifications.length === 0) {
            this.showEmpty();
        } else {
            this.renderNotifications(notifications);
        }

        // Store last count for comparison
        this.lastUnreadCount = unread_count;

        this.hideLoading();

        // Mark as initialized after first successful load
        if (!this.isInitialized) {
            this.isInitialized = true;
        }
    }
    
    updateBadge(count, animate = false) {
        const badge = document.getElementById('notificationBadge');
        const bell = document.querySelector('.notification-icon');

        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'block';

                // Add visual emphasis for new notifications
                if (bell) {
                    bell.classList.remove('bi-bell');
                    bell.classList.add('bi-bell-fill');
                }

                // Animate badge if count increased
                if (animate && count > this.lastUnreadCount) {
                    badge.classList.add('badge-pulse');
                    setTimeout(() => {
                        badge.classList.remove('badge-pulse');
                    }, 1000);
                }
            } else {
                badge.style.display = 'none';
                if (bell) {
                    bell.classList.remove('bi-bell-fill');
                    bell.classList.add('bi-bell');
                }
            }
        }
    }
    
    renderNotifications(notifications) {
        const container = document.getElementById('notificationList');
        const template = document.getElementById('notificationItemTemplate');
        
        if (!container || !template) return;
        
        container.innerHTML = '';
        
        notifications.forEach(item => {
            const clone = template.content.cloneNode(true);
            const notificationDiv = clone.querySelector('.notification-item');
            
            // Set data attributes
            notificationDiv.dataset.notificationId = item.notification.id;
            
            // Set read/unread state
            if (!item.is_read) {
                notificationDiv.classList.add('unread');
            } else {
                notificationDiv.classList.add('read');
            }
            
            // Set icon
            const iconElement = clone.querySelector('.notification-item-icon');
            iconElement.className = `notification-item-icon ${this.getNotificationIcon(item.notification.notification_type)}`;
            
            // Set content
            clone.querySelector('.notification-item-title').textContent = item.notification.title;
            clone.querySelector('.notification-item-message').textContent = item.notification.message;
            clone.querySelector('.notification-item-time').textContent = this.formatTime(item.notification.created_at);
            
            // Set action button
            if (item.notification.action_url && item.notification.action_text) {
                const actionDiv = clone.querySelector('.notification-item-action');
                const actionBtn = clone.querySelector('.notification-action-btn');
                actionBtn.href = item.notification.action_url;
                clone.querySelector('.notification-action-text').textContent = item.notification.action_text;
                actionDiv.style.display = 'block';
            }
            
            container.appendChild(clone);
        });
    }
    
    getNotificationIcon(type) {
        const iconMap = {
            'unassigned_store_manager': 'bi-person-exclamation',
            'pending_restock_request': 'bi-box-seam',
            'pending_transfer_request': 'bi-arrow-left-right',
            'new_supplier_registration': 'bi-shop',
            'request_approved': 'bi-check-circle',
            'request_rejected': 'bi-x-circle',
            'low_stock_alert': 'bi-exclamation-triangle',
            'system_announcement': 'bi-megaphone'
        };
        
        return iconMap[type] || 'bi-bell';
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/mark-read/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // Update UI immediately
                const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (item) {
                    item.classList.remove('unread');
                    item.classList.add('read');
                }
                
                // Refresh to update badge count
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }
    
    showLoading() {
        const loading = document.getElementById('notificationLoading');
        const content = document.getElementById('notificationList');
        const empty = document.getElementById('notificationEmpty');
        
        if (loading) loading.style.display = 'block';
        if (content) content.style.display = 'none';
        if (empty) empty.style.display = 'none';
    }
    
    hideLoading() {
        const loading = document.getElementById('notificationLoading');
        if (loading) loading.style.display = 'none';
    }
    
    showEmpty() {
        const loading = document.getElementById('notificationLoading');
        const content = document.getElementById('notificationList');
        const empty = document.getElementById('notificationEmpty');
        
        if (loading) loading.style.display = 'none';
        if (content) content.style.display = 'none';
        if (empty) empty.style.display = 'block';
    }
    
    showError() {
        const container = document.getElementById('notificationList');
        if (container) {
            container.innerHTML = `
                <div class="notification-error text-center py-4">
                    <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
                    <div class="mt-2 text-muted">Failed to load notifications</div>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="notificationManager.loadNotifications()">
                        Try Again
                    </button>
                </div>
            `;
        }
        this.hideLoading();
    }
    
    startPolling() {
        this.pollTimer = setInterval(() => {
            // Only poll if dropdown is not open to avoid disrupting user interaction
            if (!this.isDropdownOpen) {
                this.loadNotifications();
            }
        }, this.pollInterval);
    }
    
    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialize notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.notificationManager = new NotificationManager();
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (window.notificationManager) {
        window.notificationManager.stopPolling();
    }
});
