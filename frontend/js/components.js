/* ==========================================================================
   DAYFLOW HRMS - SHARED COMPONENTS (SIDEBAR, TOPBAR, TOASTS & MODALS)
   ========================================================================== */

const Components = {
    init() {
        this.initSidebar();
        this.initTopbar();
        this.initSharedEvents();
        this.loadNotifications();
        this.loadSwitchEmployeeView();
    },

    // Sidebar Collapsible Toggles
    initSidebar() {
        const btnToggle = document.getElementById('btn-sidebar-toggle');
        const sidebar = document.getElementById('sidebar-container');
        
        if (btnToggle && sidebar) {
            btnToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                sidebar.classList.toggle('active');
            });
            
            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 1024 && sidebar.classList.contains('active')) {
                    if (!sidebar.contains(e.target) && e.target !== btnToggle) {
                        sidebar.classList.remove('active');
                    }
                }
            });
        }

        // Render current session details in Sidebar footer
        const user = Auth.getCurrentUser();
        if (user) {
            const sidebarName = document.getElementById('sidebar-user-name');
            const sidebarAvatar = document.getElementById('sidebar-avatar-img');
            
            if (sidebarName) sidebarName.innerText = user.name;
            if (sidebarAvatar && user.avatar) sidebarAvatar.src = user.avatar;

            // Sidebar Logout
            const btnSidebarLogout = document.getElementById('btn-sidebar-logout');
            if (btnSidebarLogout) {
                btnSidebarLogout.addEventListener('click', () => Auth.logout());
            }
        }
    },

    // Topbar Details & Menus
    initTopbar() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        // Populate Topbar Username and Avatar
        const topbarName = document.getElementById('topbar-user-name');
        const topbarAvatar = document.getElementById('topbar-avatar-img');
        
        if (topbarName) topbarName.innerText = user.name;
        if (topbarAvatar && user.avatar) topbarAvatar.src = user.avatar;

        // Profile Trigger Dropdown
        const trigger = document.getElementById('btn-profile-trigger');
        const dropdown = document.getElementById('profile-dropdown');

        if (trigger && dropdown) {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('active');
                
                // Close notification dropdown if active
                const notifMenu = document.getElementById('notif-menu');
                if (notifMenu) notifMenu.classList.remove('active');
            });
        }

        // Notification Bell dropdown toggler
        const notifBtn = document.getElementById('btn-notifications');
        const notifMenu = document.getElementById('notif-menu');

        if (notifBtn && notifMenu) {
            notifBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                notifMenu.classList.toggle('active');

                // Close profile menu if active
                if (dropdown) dropdown.classList.remove('active');
            });
        }

        // Clear all menus clicking elsewhere
        document.addEventListener('click', () => {
            if (dropdown) dropdown.classList.remove('active');
            if (notifMenu) notifMenu.classList.remove('active');
        });
    },

    // Dynamic toast alerts container
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Define icons based on type
        let icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-triangle-exclamation';
        if (type === 'info') icon = 'fa-circle-info';
        if (type === 'warning') icon = 'fa-circle-exclamation';

        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Auto remove toast after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // Bind logouts
    initSharedEvents() {
        const btnTopbarLogout = document.getElementById('btn-topbar-logout');
        if (btnTopbarLogout) {
            btnTopbarLogout.addEventListener('click', () => Auth.logout());
        }
    },

    // Notification updates loader
    loadNotifications() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        const notifList = document.getElementById('notif-list');
        const notifBadge = document.getElementById('notif-badge');
        const btnClear = document.getElementById('btn-clear-notif');

        if (!notifList) return;

        const allNotifs = DayflowDB.getData(DayflowDB.NOTIFS_KEY);
        // Filter notifications belonging to active user
        const myNotifs = allNotifs.filter(n => n.empid === user.empid);

        if (myNotifs.length === 0) {
            notifList.innerHTML = '<p class="empty-notif">No new notifications</p>';
            if (notifBadge) notifBadge.style.display = 'none';
        } else {
            if (notifBadge) {
                notifBadge.innerText = myNotifs.length;
                notifBadge.style.display = 'inline-flex';
            }

            notifList.innerHTML = myNotifs.map(n => `
                <div class="notif-item">
                    <div class="notif-icon">
                        <i class="fa-solid ${n.icon || 'fa-info-circle'}"></i>
                    </div>
                    <div class="notif-item-details">
                        <p>${n.text}</p>
                        <span>${n.time || 'Just now'}</span>
                    </div>
                </div>
            `).join('');
        }

        if (btnClear) {
            btnClear.onclick = () => {
                // Clear active user's notifications
                const remaining = allNotifs.filter(n => n.empid !== user.empid);
                DayflowDB.saveData(DayflowDB.NOTIFS_KEY, remaining);
                this.loadNotifications();
                this.showToast('Notifications cleared');
            };
        }
    },

    // Seed alert notifications
    addNotification(empid, text, icon = 'fa-circle-info') {
        const allNotifs = DayflowDB.getData(DayflowDB.NOTIFS_KEY);
        allNotifs.unshift({
            empid,
            text,
            icon,
            time: 'Just now'
        });
        DayflowDB.saveData(DayflowDB.NOTIFS_KEY, allNotifs);
        this.loadNotifications();
    },

    // Admin Quick-Switch employee view loader
    loadSwitchEmployeeView() {
        const selector = document.getElementById('admin-switch-employee');
        if (!selector) return;

        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
        const employees = users.filter(u => u.role === 'employee');

        selector.innerHTML = '<option value="">-- Switch View --</option>' + 
            employees.map(emp => `<option value="${emp.empid}">${emp.name} (${emp.empid})</option>`).join('');

        // Listen for changes
        selector.addEventListener('change', (e) => {
            const empid = e.target.value;
            if (!empid) return;

            const selectedEmp = employees.find(emp => emp.empid === empid);
            if (selectedEmp) {
                // Simulate login as selected employee
                sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(selectedEmp));
                // Redirect to employee dashboard
                window.location.href = '../employee/dashboard.html';
            }
        });
    }
};

// Initialize shared components
document.addEventListener('DOMContentLoaded', () => {
    if (Auth.isAuthenticated()) {
        Components.init();
    }
});
