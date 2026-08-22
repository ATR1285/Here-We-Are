/* ==========================================================================
   DAYFLOW HRMS - AUTHENTICATION UTILS (SIGN IN, SIGN UP, GUARDS)
   ========================================================================== */

const Auth = {
    SESSION_USER_KEY: 'dayflow_session_user',

    // Sign in validation
    async signIn(email, password) {
        const res = await Api.post('/auth/login', {
            username: email,
            password: password
        });

        if (res.success) {
            // Save basic user info in session storage for UI purposes
            // Real auth is handled via HttpOnly cookie
            sessionStorage.setItem(this.SESSION_USER_KEY, JSON.stringify(res.data));
            return { success: true, user: res.data };
        } else {
            return { success: false, message: res.message };
        }
    },

    // Retrieve active session user
    getCurrentUser() {
        // For UI purposes only. Critical ops use real backend APIs.
        const sessionUser = sessionStorage.getItem(this.SESSION_USER_KEY);
        if (!sessionUser) return null;
        return JSON.parse(sessionUser);
    },

    // Login checks
    isAuthenticated() {
        return sessionStorage.getItem(this.SESSION_USER_KEY) !== null;
    },

    // Logout
    async logout() {
        // Call backend to invalidate session
        await Api.post('/auth/logout');
        
        // Clear UI state
        sessionStorage.removeItem(this.SESSION_USER_KEY);
        
        // Redirect to workspace root Sign In page
        let currentPath = window.location.pathname;
        if (currentPath.includes('/employee/') || currentPath.includes('/admin/')) {
            window.location.href = '../index.html';
        } else {
            window.location.href = 'index.html';
        }
    },

    // Route guards
    async guardRoute(requiredRole) {
        if (!this.isAuthenticated()) {
            this.logout();
            return;
        }

        // Validate session with backend to ensure it hasn't expired/revoked
        const res = await Api.get('/auth/me');
        if (!res.success) {
            this.logout();
            return;
        }

        const user = res.data;
        // Update session storage with fresh data
        sessionStorage.setItem(this.SESSION_USER_KEY, JSON.stringify(user));

        const role = user.role ? user.role.name.toLowerCase() : 'employee';

        if (requiredRole === 'admin' && (role !== 'admin' && role !== 'hr' && role !== 'finance')) {
            window.location.href = '../employee/dashboard.html';
        } else if (requiredRole === 'employee' && (role === 'admin' || role === 'hr' || role === 'finance')) {
            window.location.href = '../admin/dashboard.html';
        }
    }
};

// Hook authentication listeners (Auth UI Forms)
document.addEventListener('DOMContentLoaded', () => {
    // 1. Sign In Form Logic
    const signinForm = document.getElementById('signin-form');
    if (signinForm) {
        const togglePwdIcon = document.getElementById('toggle-pwd-icon');
        const signinPassword = document.getElementById('signin-password');

        if (togglePwdIcon && signinPassword) {
            togglePwdIcon.addEventListener('click', () => {
                const type = signinPassword.getAttribute('type') === 'password' ? 'text' : 'password';
                signinPassword.setAttribute('type', type);
                togglePwdIcon.classList.toggle('fa-eye');
                togglePwdIcon.classList.toggle('fa-eye-slash');
            });
        }

        signinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // disable button
            const submitBtn = signinForm.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;

            const email = document.getElementById('signin-email').value.trim();
            const password = document.getElementById('signin-password').value;

            const res = await Auth.signIn(email, password);
            if (res.success) {
                // Redirect on role basis
                const role = res.user.role ? res.user.role.name.toLowerCase() : 'employee';
                if (role === 'admin' || role === 'hr' || role === 'finance') {
                    window.location.href = 'admin/dashboard.html';
                } else {
                    window.location.href = 'employee/dashboard.html';
                }
            } else {
                if (window.Components && window.Components.showToast) {
                    Components.showToast(res.message, 'error');
                } else {
                    alert(res.message);
                }
                if (submitBtn) submitBtn.disabled = false;
            }
        });

        // Demo Sign-in Helpers
        const btnEmployee = document.getElementById('btn-demo-employee');
        const btnAdmin = document.getElementById('btn-demo-admin');
        
        if (btnEmployee) {
            btnEmployee.addEventListener('click', () => {
                document.getElementById('signin-email').value = 'john@dayflow.com'; // Change to actual DB user
                document.getElementById('signin-password').value = 'password123';
            });
        }
        if (btnAdmin) {
            btnAdmin.addEventListener('click', () => {
                document.getElementById('signin-email').value = 'priya@dayflow.com'; // Change to actual DB user
                document.getElementById('signin-password').value = 'password123';
            });
        }
    }
});
