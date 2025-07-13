/**
 * EZM Trade Management - Real-time Notification System
 * Handles real-time payment notifications for suppliers
 */

class EZMNotificationSystem {
    constructor() {
        this.isSupplier = document.body.classList.contains('supplier-dashboard');
        this.updateInterval = 30000; // 30 seconds
        this.intervalId = null;
        this.lastUpdateTime = null;
        this.isOnline = true;
        
        this.init();
    }
    
    init() {
        if (this.isSupplier) {
            this.startRealTimeUpdates();
            this.setupVisibilityHandler();
            this.setupConnectionMonitoring();
        }
    }
    
    startRealTimeUpdates() {
        // Initial update
        this.updateNotifications();
        
        // Set up periodic updates
        this.intervalId = setInterval(() => {
            this.updateNotifications();
        }, this.updateInterval);
        
        console.log('EZM Notification System: Real-time updates started');
    }
    
    stopRealTimeUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        console.log('EZM Notification System: Real-time updates stopped');
    }
    
    async updateNotifications() {
        try {
            const response = await fetch('/supplier/payments/notifications/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.processNotificationUpdate(data);
            this.updateConnectionStatus(true);
            this.lastUpdateTime = new Date();
            
        } catch (error) {
            console.error('EZM Notification System: Update failed', error);
            this.updateConnectionStatus(false);
            this.handleUpdateError(error);
        }
    }
    
    processNotificationUpdate(data) {
        // Update sidebar notification badge
        this.updateSidebarBadge(data.pending_payments);
        
        // Update dashboard statistics if on payments page
        this.updateDashboardStats(data);
        
        // Check for new notifications
        this.checkForNewNotifications(data);
        
        // Update last update indicator
        this.updateLastUpdateIndicator();
    }
    
    updateSidebarBadge(pendingCount) {
        const badge = document.getElementById('payment-notification-badge');
        if (badge) {
            const badgeElement = badge.querySelector('.badge');
            if (pendingCount > 0) {
                badge.style.display = 'block';
                badgeElement.textContent = pendingCount;
                badgeElement.className = 'badge bg-warning rounded-pill';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    updateDashboardStats(data) {
        // Update statistics cards if they exist
        const statsElements = {
            successful: document.querySelector('[data-stat="successful"]'),
            pending: document.querySelector('[data-stat="pending"]'),
            failed: document.querySelector('[data-stat="failed"]'),
            total: document.querySelector('[data-stat="total"]')
        };
        
        if (statsElements.successful) {
            statsElements.successful.textContent = data.successful_payments;
        }
        if (statsElements.pending) {
            statsElements.pending.textContent = data.pending_payments;
        }
        if (statsElements.failed) {
            statsElements.failed.textContent = data.failed_payments;
        }
        if (statsElements.total) {
            statsElements.total.textContent = data.total_transactions;
        }
        
        // Update pending badge in stats card
        const pendingBadge = document.querySelector('.notification-badge .badge');
        if (pendingBadge && data.pending_payments > 0) {
            pendingBadge.textContent = data.pending_payments;
            pendingBadge.style.display = 'flex';
        } else if (pendingBadge) {
            pendingBadge.style.display = 'none';
        }
    }
    
    checkForNewNotifications(data) {
        // Store previous counts to detect new notifications
        if (!this.previousCounts) {
            this.previousCounts = {
                successful: data.successful_payments,
                pending: data.pending_payments,
                failed: data.failed_payments,
                total: data.total_transactions
            };
            return;
        }
        
        // Check for new successful payments
        if (data.successful_payments > this.previousCounts.successful) {
            const newPayments = data.successful_payments - this.previousCounts.successful;
            this.showNotificationToast('success', `${newPayments} new payment${newPayments > 1 ? 's' : ''} confirmed!`);
            this.playNotificationSound();
        }
        
        // Check for new pending payments
        if (data.pending_payments > this.previousCounts.pending) {
            const newPending = data.pending_payments - this.previousCounts.pending;
            this.showNotificationToast('info', `${newPending} new payment${newPending > 1 ? 's' : ''} pending confirmation`);
        }
        
        // Check for failed payments
        if (data.failed_payments > this.previousCounts.failed) {
            const newFailed = data.failed_payments - this.previousCounts.failed;
            this.showNotificationToast('warning', `${newFailed} payment${newFailed > 1 ? 's' : ''} failed`);
        }
        
        // Update previous counts
        this.previousCounts = {
            successful: data.successful_payments,
            pending: data.pending_payments,
            failed: data.failed_payments,
            total: data.total_transactions
        };
    }
    
    showNotificationToast(type, message) {
        // Create toast notification
        const toastContainer = this.getOrCreateToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-bell-fill me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
        
        // Remove toast from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toast);
        });
    }
    
    getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    }
    
    playNotificationSound() {
        // Play a subtle notification sound
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
            audio.volume = 0.3;
            audio.play().catch(() => {
                // Ignore audio play errors (browser restrictions)
            });
        } catch (error) {
            // Ignore audio errors
        }
    }
    
    updateConnectionStatus(isOnline) {
        this.isOnline = isOnline;
        
        const statusIndicator = document.querySelector('.real-time-status');
        if (statusIndicator) {
            if (isOnline) {
                statusIndicator.textContent = 'Live';
                statusIndicator.classList.remove('offline');
            } else {
                statusIndicator.textContent = 'Offline';
                statusIndicator.classList.add('offline');
            }
        }
    }
    
    updateLastUpdateIndicator() {
        const indicator = document.querySelector('.last-update-time');
        if (indicator && this.lastUpdateTime) {
            indicator.textContent = `Last updated: ${this.lastUpdateTime.toLocaleTimeString()}`;
        }
    }
    
    setupVisibilityHandler() {
        // Pause updates when page is not visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopRealTimeUpdates();
            } else {
                this.startRealTimeUpdates();
            }
        });
    }
    
    setupConnectionMonitoring() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            this.updateConnectionStatus(true);
            this.startRealTimeUpdates();
        });
        
        window.addEventListener('offline', () => {
            this.updateConnectionStatus(false);
            this.stopRealTimeUpdates();
        });
    }
    
    handleUpdateError(error) {
        // Implement exponential backoff for failed requests
        if (error.message.includes('HTTP 5')) {
            // Server error - increase update interval temporarily
            this.stopRealTimeUpdates();
            setTimeout(() => {
                this.startRealTimeUpdates();
            }, 60000); // Wait 1 minute before retrying
        }
    }
    
    // Public methods for manual control
    forceUpdate() {
        this.updateNotifications();
    }
    
    setUpdateInterval(milliseconds) {
        this.updateInterval = milliseconds;
        if (this.intervalId) {
            this.stopRealTimeUpdates();
            this.startRealTimeUpdates();
        }
    }
    
    destroy() {
        this.stopRealTimeUpdates();
        
        // Remove event listeners
        document.removeEventListener('visibilitychange', this.visibilityHandler);
        window.removeEventListener('online', this.onlineHandler);
        window.removeEventListener('offline', this.offlineHandler);
    }
}

// Initialize notification system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize for supplier users
    if (document.body.classList.contains('supplier-dashboard') || 
        document.querySelector('[data-user-role="supplier"]')) {
        
        window.ezmNotificationSystem = new EZMNotificationSystem();
        
        // Expose to global scope for debugging
        window.EZMNotifications = window.ezmNotificationSystem;
        
        console.log('EZM Notification System: Initialized for supplier dashboard');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.ezmNotificationSystem) {
        window.ezmNotificationSystem.destroy();
    }
});
