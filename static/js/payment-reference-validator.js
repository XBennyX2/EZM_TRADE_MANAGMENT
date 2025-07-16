/**
 * Payment Reference Validator
 * Real-time validation and error prevention for payment references
 */

class PaymentReferenceValidator {
    constructor() {
        this.initializeValidator();
        this.setupErrorHandling();
        this.setupRetryMechanism();
    }

    initializeValidator() {
        console.log('🔧 Payment Reference Validator initialized');
        
        // Override fetch for payment requests
        this.originalFetch = window.fetch;
        window.fetch = this.interceptFetch.bind(this);
        
        // Override XMLHttpRequest for older AJAX requests
        this.interceptXHR();
    }

    interceptFetch(url, options = {}) {
        // Check if this is a payment-related request
        if (this.isPaymentRequest(url)) {
            console.log('🔍 Intercepting payment request:', url);
            return this.validateAndRetryPayment(url, options);
        }
        
        return this.originalFetch(url, options);
    }

    interceptXHR() {
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;
        const validator = this;

        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            this._url = url;
            this._method = method;
            return originalOpen.apply(this, [method, url, ...args]);
        };

        XMLHttpRequest.prototype.send = function(data) {
            if (validator.isPaymentRequest(this._url)) {
                console.log('🔍 Intercepting XHR payment request:', this._url);
                
                const originalOnLoad = this.onload;
                this.onload = function() {
                    validator.handlePaymentResponse(this.responseText, this._url);
                    if (originalOnLoad) originalOnLoad.apply(this, arguments);
                };
            }
            
            return originalSend.apply(this, arguments);
        };
    }

    isPaymentRequest(url) {
        if (!url) return false;
        
        const paymentEndpoints = [
            '/payments/initiate/',
            '/payments/create/',
            '/cart/checkout/',
            '/payments/process/'
        ];
        
        return paymentEndpoints.some(endpoint => url.includes(endpoint));
    }

    async validateAndRetryPayment(url, options) {
        const maxRetries = 3;
        let attempt = 0;
        
        while (attempt < maxRetries) {
            try {
                console.log(`🔄 Payment attempt ${attempt + 1}/${maxRetries}`);
                
                const response = await this.originalFetch(url, options);
                const responseText = await response.text();
                
                // Check for payment reference errors
                if (this.hasReferenceError(responseText)) {
                    console.warn('⚠️ Payment reference error detected, retrying...');
                    attempt++;
                    
                    if (attempt < maxRetries) {
                        // Wait before retry with exponential backoff
                        await this.delay(1000 * Math.pow(2, attempt));
                        
                        // Generate new reference if possible
                        options = this.refreshPaymentData(options);
                        continue;
                    } else {
                        console.error('❌ Max retries reached for payment reference error');
                        this.showUserFriendlyError();
                    }
                }
                
                // Return successful response
                return new Response(responseText, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: response.headers
                });
                
            } catch (error) {
                console.error(`❌ Payment attempt ${attempt + 1} failed:`, error);
                attempt++;
                
                if (attempt >= maxRetries) {
                    throw error;
                }
                
                await this.delay(1000 * attempt);
            }
        }
    }

    hasReferenceError(responseText) {
        if (!responseText) return false;
        
        const errorPatterns = [
            'invalid payment reference',
            'transaction reference has been used',
            'reference has been used before',
            'duplicate transaction reference',
            'invalid reference format'
        ];
        
        const lowerResponse = responseText.toLowerCase();
        return errorPatterns.some(pattern => lowerResponse.includes(pattern));
    }

    handlePaymentResponse(responseText, url) {
        if (this.hasReferenceError(responseText)) {
            console.warn('⚠️ Payment reference error detected in XHR response');
            this.showUserFriendlyError();
        }
    }

    refreshPaymentData(options) {
        // Add timestamp to force new reference generation
        if (options.body) {
            try {
                const data = JSON.parse(options.body);
                data._timestamp = Date.now();
                data._retry = true;
                options.body = JSON.stringify(data);
            } catch (e) {
                // If not JSON, add as form data
                if (typeof options.body === 'string') {
                    options.body += `&_timestamp=${Date.now()}&_retry=true`;
                }
            }
        }
        
        return options;
    }

    showUserFriendlyError() {
        // Remove any existing error messages
        const existingError = document.getElementById('payment-reference-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Create user-friendly error message
        const errorDiv = document.createElement('div');
        errorDiv.id = 'payment-reference-error';
        errorDiv.className = 'alert alert-warning';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            padding: 15px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        
        errorDiv.innerHTML = `
            <div style="display: flex; align-items: center;">
                <span style="font-size: 20px; margin-right: 10px;">⚠️</span>
                <div>
                    <strong>Payment Processing Issue</strong><br>
                    <small>Please try again or refresh the page</small>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="margin-left: auto; background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 10000);
    }

    setupErrorHandling() {
        // Global error handler for unhandled payment errors
        window.addEventListener('error', (event) => {
            if (event.error && event.error.message) {
                const message = event.error.message.toLowerCase();
                if (message.includes('payment') && message.includes('reference')) {
                    console.warn('🚨 Global payment reference error caught:', event.error);
                    this.showUserFriendlyError();
                }
            }
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            if (event.reason && typeof event.reason === 'string') {
                const reason = event.reason.toLowerCase();
                if (reason.includes('payment') && reason.includes('reference')) {
                    console.warn('🚨 Unhandled payment reference rejection:', event.reason);
                    this.showUserFriendlyError();
                }
            }
        });
    }

    setupRetryMechanism() {
        // Add retry button to payment forms
        document.addEventListener('DOMContentLoaded', () => {
            const paymentForms = document.querySelectorAll('form[action*="payment"], form[action*="checkout"]');
            
            paymentForms.forEach(form => {
                this.addRetryMechanism(form);
            });
        });
    }

    addRetryMechanism(form) {
        // Add hidden retry counter
        const retryInput = document.createElement('input');
        retryInput.type = 'hidden';
        retryInput.name = '_retry_count';
        retryInput.value = '0';
        form.appendChild(retryInput);
        
        // Override form submission
        const originalSubmit = form.onsubmit;
        form.onsubmit = (event) => {
            // Add timestamp to prevent caching
            const timestampInput = document.createElement('input');
            timestampInput.type = 'hidden';
            timestampInput.name = '_timestamp';
            timestampInput.value = Date.now().toString();
            form.appendChild(timestampInput);
            
            if (originalSubmit) {
                return originalSubmit.call(form, event);
            }
        };
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Public method to manually validate a reference
    validateReference(reference) {
        if (!reference) return false;
        
        // Check format
        const formatValid = /^EZM-\d+-[A-Z0-9]+$/.test(reference);
        
        // Check length
        const lengthValid = reference.length >= 15 && reference.length <= 50;
        
        // Check for valid characters
        const charValid = /^[A-Z0-9\-]+$/.test(reference);
        
        return formatValid && lengthValid && charValid;
    }

    // Public method to get system status
    getSystemStatus() {
        return {
            validator: 'active',
            interceptors: 'enabled',
            errorHandling: 'active',
            retryMechanism: 'enabled'
        };
    }
}

// Initialize the validator when the script loads
const paymentValidator = new PaymentReferenceValidator();

// Expose to global scope for debugging
window.PaymentReferenceValidator = PaymentReferenceValidator;
window.paymentValidator = paymentValidator;

console.log('✅ Payment Reference Validator loaded successfully');
console.log('🔧 System status:', paymentValidator.getSystemStatus());
