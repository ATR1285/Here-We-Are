/* ==========================================================================
   DAYFLOW HRMS - CENTRALIZED API CLIENT
   ========================================================================== */

const Api = {
    // Determine the base URL depending on if we are running locally or relative
    // If the frontend is served via FastAPI, paths are relative.
    BASE_URL: '/api/v1',

    /**
     * Core API request handler
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        
        const fetchOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            // Essential for HTTP-only session cookies
            credentials: 'include' 
        };

        if (fetchOptions.body && typeof fetchOptions.body !== 'string') {
            fetchOptions.body = JSON.stringify(fetchOptions.body);
        }

        try {
            const response = await fetch(url, fetchOptions);
            
            // For 204 No Content or empty responses
            let data = null;
            if (response.status !== 204) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    data = await response.text();
                }
            }

            if (!response.ok) {
                return this.handleError(response.status, data);
            }

            return { success: true, data: data, status: response.status };
        } catch (error) {
            console.error('API Request Failed:', error);
            return {
                success: false,
                status: 500,
                message: 'A network error occurred. Please try again later.',
                detail: null
            };
        }
    },

    /**
     * Standardized error handling for non-2xx responses
     */
    handleError(status, data) {
        let message = 'An unexpected error occurred.';
        let detail = null;

        if (data && typeof data === 'object') {
            if (data.detail) {
                // FastAPI standard validation error format
                if (Array.isArray(data.detail)) {
                    message = 'Validation Error';
                    detail = data.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join(', ');
                } else {
                    message = data.detail;
                }
            } else if (data.message) {
                message = data.message;
            }
        } else if (typeof data === 'string') {
            message = data; // fallback to raw string if it's not too long
        }

        // Map status codes to user-friendly messages
        switch (status) {
            case 400:
                message = message || 'Bad Request. Please check your input.';
                break;
            case 401:
                message = 'Unauthorized. Your session may have expired.';
                this.redirectToLogin();
                break;
            case 403:
                message = 'Forbidden. You do not have permission for this action.';
                break;
            case 404:
                message = 'Resource not found.';
                break;
            case 409:
                message = message || 'Conflict. The resource already exists.';
                break;
            case 422:
                message = 'Validation Error. Please verify the submitted data.';
                break;
            case 500:
                message = 'Internal Server Error. Please try again later.';
                detail = null; // NEVER expose backend traces
                break;
            default:
                message = `Error ${status}: ${message}`;
        }

        return {
            success: false,
            status: status,
            message: message,
            detail: detail
        };
    },

    redirectToLogin() {
        sessionStorage.removeItem('dayflow_session_user');
        const currentPath = window.location.pathname;
        if (currentPath.includes('/employee/') || currentPath.includes('/admin/')) {
            window.location.href = '../index.html';
        } else {
            window.location.href = 'index.html';
        }
    },

    // Shorthand methods
    get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    },

    post(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', body });
    },

    put(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', body });
    },
    
    patch(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'PATCH', body });
    },

    delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }
};

window.Api = Api;
