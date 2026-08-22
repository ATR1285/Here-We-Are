/* ==========================================================================
   DAYFLOW HRMS - AUTHENTICATION UTILS (SIGN IN, SIGN UP, GUARDS)
   ========================================================================== */

const Auth = {
    SESSION_USER_KEY: 'dayflow_session_user',

    // Sign in validation
    signIn(email, password) {
        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
        const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());

        if (!user) {
            return { success: false, message: 'Invalid credentials. User not found.' };
        }

        if (user.password !== password) {
            return { success: false, message: 'Invalid credentials. Incorrect password.' };
        }

        // Save session user details
        sessionStorage.setItem(this.SESSION_USER_KEY, JSON.stringify(user));
        return { success: true, user };
    },

    // Sign up processing
    signUp(userData) {
        const users = DayflowDB.getData(DayflowDB.USERS_KEY);

        // Check ID duplication
        if (users.some(u => u.empid.toLowerCase() === userData.empid.toLowerCase())) {
            return { success: false, message: 'Employee ID is already registered.' };
        }

        // Check Email duplication
        if (users.some(u => u.email.toLowerCase() === userData.email.toLowerCase())) {
            return { success: false, message: 'Email address is already registered.' };
        }

        // Insert new user profiles
        const newUser = {
            empid: userData.empid,
            name: userData.name,
            email: userData.email,
            password: userData.password,
            role: userData.role,
            dept: userData.role === 'hr' ? 'HR' : 'Engineering', // Default dept
            designation: userData.role === 'hr' ? 'HR Specialist' : 'Software Engineer',
            joiningDate: new Date().toISOString().split('T')[0],
            phone: '',
            dob: '',
            gender: '',
            address: '',
            aboutMe: '',
            loveJob: '',
            hobbies: '',
            skills: [],
            certs: []
        };

        users.push(newUser);
        DayflowDB.saveData(DayflowDB.USERS_KEY, users);

        // Seed default payroll for new employee
        if (newUser.role === 'employee') {
            const payrolls = DayflowDB.getData(DayflowDB.PAYROLL_KEY);
            payrolls.push({
                empid: newUser.empid,
                basic: 48000,
                hra: 19200,
                standard: 9600,
                bonus: 9600,
                lta: 4800,
                fixed: 4800
            });
            DayflowDB.saveData(DayflowDB.PAYROLL_KEY, payrolls);
        }

        return { success: true, user: newUser };
    },

    // Retrieve active session user
    getCurrentUser() {
        const sessionUser = sessionStorage.getItem(this.SESSION_USER_KEY);
        if (!sessionUser) return null;
        
        // Always read fresh fields from LocalStorage in case of profile changes
        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
        const parsedSession = JSON.parse(sessionUser);
        const freshUser = users.find(u => u.empid === parsedSession.empid);
        return freshUser || parsedSession;
    },

    // Login checks
    isAuthenticated() {
        return sessionStorage.getItem(this.SESSION_USER_KEY) !== null;
    },

    // Logout
    logout() {
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
    guardRoute(requiredRole) {
        if (!this.isAuthenticated()) {
            this.logout();
            return;
        }

        const user = this.getCurrentUser();
        if (requiredRole === 'admin' && (user.role !== 'admin' && user.role !== 'hr')) {
            window.location.href = '../employee/dashboard.html';
        } else if (requiredRole === 'employee' && (user.role === 'admin' || user.role === 'hr')) {
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

        signinForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('signin-email').value.trim();
            const password = document.getElementById('signin-password').value;

            const res = Auth.signIn(email, password);
            if (res.success) {
                // Redirect on role basis
                if (res.user.role === 'admin' || res.user.role === 'hr') {
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
            }
        });

        // Demo Sign-in Helpers
        const btnEmployee = document.getElementById('btn-demo-employee');
        const btnAdmin = document.getElementById('btn-demo-admin');
        
        if (btnEmployee) {
            btnEmployee.addEventListener('click', () => {
                document.getElementById('signin-email').value = 'john@dayflow.com';
                document.getElementById('signin-password').value = 'password123';
            });
        }
        if (btnAdmin) {
            btnAdmin.addEventListener('click', () => {
                document.getElementById('signin-email').value = 'priya@dayflow.com';
                document.getElementById('signin-password').value = 'admin123';
            });
        }
    }

    // 2. Sign Up Form Logic
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        const toggleSignupPwd = document.getElementById('toggle-signup-pwd');
        const signupPassword = document.getElementById('signup-password');
        const pwdStrength = document.getElementById('pwd-strength');

        if (toggleSignupPwd && signupPassword) {
            toggleSignupPwd.addEventListener('click', () => {
                const type = signupPassword.getAttribute('type') === 'password' ? 'text' : 'password';
                signupPassword.setAttribute('type', type);
                toggleSignupPwd.classList.toggle('fa-eye');
                toggleSignupPwd.classList.toggle('fa-eye-slash');
            });

            // Password strength meter
            signupPassword.addEventListener('input', () => {
                const val = signupPassword.value;
                pwdStrength.className = 'password-strength-bar';
                if (val.length === 0) return;
                
                if (val.length < 6) {
                    pwdStrength.classList.add('weak');
                } else if (val.length < 10) {
                    pwdStrength.classList.add('medium');
                } else {
                    pwdStrength.classList.add('strong');
                }
            });
        }

        // Submit Sign Up
        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const empid = document.getElementById('signup-empid').value.trim();
            const name = document.getElementById('signup-name').value.trim();
            const email = document.getElementById('signup-email').value.trim();
            const password = signupPassword.value;
            const confirmPassword = document.getElementById('signup-confirm-password').value;
            const role = document.getElementById('signup-role').value;

            if (password !== confirmPassword) {
                if (window.Components && window.Components.showToast) {
                    Components.showToast('Passwords do not match.', 'error');
                } else {
                    alert('Passwords do not match.');
                }
                return;
            }

            // Perform simulated signup & show email verification modal
            const verifyModal = document.getElementById('verify-modal');
            const verifyEmailText = document.getElementById('verify-email-text');
            const btnSimulateVerify = document.getElementById('btn-simulate-verify');

            if (verifyModal && verifyEmailText && btnSimulateVerify) {
                verifyEmailText.innerText = email;
                verifyModal.classList.add('active');

                // Simulate validation success
                btnSimulateVerify.onclick = () => {
                    verifyModal.classList.remove('active');
                    const res = Auth.signUp({ empid, name, email, password, role });
                    
                    if (res.success) {
                        alert('Registration successful! Click OK to Sign In.');
                        window.location.href = 'index.html';
                    } else {
                        alert(res.message);
                    }
                };
            } else {
                // Fallback direct register (if modal doesn't exist)
                const res = Auth.signUp({ empid, name, email, password, role });
                if (res.success) {
                    window.location.href = 'index.html';
                } else {
                    alert(res.message);
                }
            }
        });
    }
});
