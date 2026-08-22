/* ==========================================================================
   DAYFLOW HRMS - DASHBOARD SCRIPTS (EMPLOYEE & ADMIN VIEWS)
   ========================================================================== */

const Dashboard = {
    async init() {
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
        
        const user = Auth.getCurrentUser();
        if (!user) return;

        // Ensure user obj has the right properties (mapping from backend schema to UI)
        const name = user.first_name ? `${user.first_name} ${user.last_name}` : user.name;
        const role = user.role && user.role.name ? user.role.name.toLowerCase() : (user.role || 'employee');
        
        this.setGreeting(name);

        if (role === 'employee' || role === 'manager') {
            await this.loadEmployeeDashboard(user.id);
        } else {
            await this.loadAdminDashboard();
        }
    },

    // Clock and Date Widget updater
    updateClock() {
        const timeEl = document.getElementById('live-time');
        const dateEl = document.getElementById('live-date');
        if (!timeEl || !dateEl) return;

        const now = new Date();
        timeEl.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        dateEl.innerText = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    },

    // Greeting banner text based on hours
    setGreeting(name) {
        const titleEl = document.getElementById('greeting-title');
        if (!titleEl) return;

        const hr = new Date().getHours();
        let greeting = 'Good morning';
        if (hr >= 12 && hr < 17) greeting = 'Good afternoon';
        if (hr >= 17) greeting = 'Good evening';

        titleEl.innerHTML = `${greeting}, <span class="highlight">${name}</span>!`;
    },

    // Loading Employee specific dashboard counters
    async loadEmployeeDashboard(userId) {
        let myAtt = [];
        let myLeaves = [];

        // Fetch Attendance
        const attRes = await Api.get('/attendance/me');
        if (attRes.success) {
            myAtt = attRes.data;
        }

        // Fetch Leaves
        const leaveRes = await Api.get('/leave/me/requests');
        if (leaveRes.success) {
            myLeaves = leaveRes.data;
        }

        const now = new Date();
        const monthPrefix = `${now.getFullYear()}-${now.getMonth() + 1 < 10 ? '0' : ''}${now.getMonth() + 1}`;

        // Filter active employee attendance for current month
        const myMonthAtt = myAtt.filter(a => a.attendance_date.startsWith(monthPrefix));
        const presentCount = myMonthAtt.filter(a => a.status === 'PRESENT').length;
        const halfdayCount = myMonthAtt.filter(a => a.status === 'HALF_DAY').length;
        
        const statPresent = document.getElementById('stat-present-days');
        if (statPresent) {
            statPresent.innerText = `${presentCount + (halfdayCount * 0.5)} days`;
        }

        // Pending Leave Count
        const myPendingLeaves = myLeaves.filter(l => l.status === 'PENDING').length;
        const statLeaves = document.getElementById('stat-pending-leaves');
        if (statLeaves) {
            statLeaves.innerText = myPendingLeaves;
        }

        // Total hours worked counter
        let totalMins = 0;
        myMonthAtt.forEach(a => totalMins += a.worked_minutes || 0);
        const statHours = document.getElementById('stat-work-hours');
        if (statHours) {
            statHours.innerText = `${(totalMins / 60).toFixed(1)}h`;
        }

        // Load recent check-in/out history timeline logs
        const timeline = document.getElementById('activity-timeline');
        if (timeline) {
            // Sort attendance newest first (already sorted by API but just in case)
            const sortedAtt = [...myAtt].slice(0, 4);

            if (sortedAtt.length === 0) {
                timeline.innerHTML = '<p class="empty-state-text">No recent check-in/out logs.</p>';
            } else {
                timeline.innerHTML = sortedAtt.map(a => {
                    let logs = [];
                    const checkInFormat = a.check_in_at ? new Date(a.check_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
                    const checkOutFormat = a.check_out_at ? new Date(a.check_out_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

                    if (a.check_in_at) {
                        logs.push(`
                            <div class="timeline-item checkin">
                                <span class="timeline-time">${a.attendance_date} &bull; ${checkInFormat}</span>
                                <p class="timeline-desc">Checked In successfully (Status: <strong class="${a.status === 'PRESENT' ? 'present-color' : 'half-day-color'}">${a.status}</strong>)</p>
                            </div>
                        `);
                    }
                    if (a.check_out_at) {
                        logs.push(`
                            <div class="timeline-item checkout">
                                <span class="timeline-time">${a.attendance_date} &bull; ${checkOutFormat}</span>
                                <p class="timeline-desc">Checked Out successfully (${((a.worked_minutes || 0) / 60).toFixed(2)} hours logged)</p>
                            </div>
                        `);
                    }
                    return logs.join('');
                }).join('');
            }
        }
    },

    // Loading Admin/HR dashboard widgets and logs checklist
    async loadAdminDashboard() {
        let employees = [];
        let allAtt = [];
        let allLeaves = [];

        const [empRes, attRes, leaveRes] = await Promise.all([
            Api.get('/employees'),
            Api.get('/attendance'),
            Api.get('/leave/requests')
        ]);

        if (empRes.success) employees = empRes.data.filter(e => e.employment_status === 'ACTIVE');
        if (attRes.success) allAtt = attRes.data;
        if (leaveRes.success) allLeaves = leaveRes.data;

        // Stat 1: Total Employees
        const totalEmpEl = document.getElementById('stat-total-emp');
        if (totalEmpEl) totalEmpEl.innerText = employees.length;

        // Today's Date
        const todayDate = new Date().toISOString().split('T')[0];

        // Stat 2: Present Today
        const todayAtt = allAtt.filter(a => a.attendance_date === todayDate);
        const presentToday = todayAtt.filter(a => a.status === 'PRESENT' || a.status === 'HALF_DAY').length;
        const presentTodayEl = document.getElementById('stat-present-today');
        if (presentTodayEl) presentTodayEl.innerText = presentToday;

        // Stat 3: Pending Leaves
        const pendingLeaves = allLeaves.filter(l => l.status === 'PENDING');
        const pendingLeavesEl = document.getElementById('stat-leaves-pending');
        if (pendingLeavesEl) pendingLeavesEl.innerText = pendingLeaves.length;

        // Render company employees logs grid table
        const tbody = document.getElementById('admin-emp-overview-tbody');
        if (tbody) {
            tbody.innerHTML = employees.map(emp => {
                const todayRecord = todayAtt.find(a => a.employee_id === emp.id);
                let statusBadge = `<span class="status-badge off">No Record</span>`;
                
                if (todayRecord) {
                    statusBadge = `<span class="status-badge ${todayRecord.status.toLowerCase()}">${todayRecord.status}</span>`;
                }

                return `
                    <tr>
                        <td>
                            <div class="directory-table-user-cell">
                                <div class="user-avatar-mini">
                                    <img src="${emp.avatar || '../assets/avatar-placeholder.svg'}" alt="${emp.first_name}">
                                </div>
                                <strong>${emp.first_name} ${emp.last_name}</strong>
                            </div>
                        </td>
                        <td>${emp.employee_code}</td>
                        <td>${statusBadge}</td>
                        <td>
                            <button class="btn btn-secondary btn-xs btn-switch-quick" data-empid="${emp.employee_code}">
                                <i class="fa-solid fa-right-to-bracket"></i> Switch View
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            // Bind click switches view - This is tricky since it's a mock UI feature, but we can fake it by storing in sessionStorage as a hint.
            tbody.querySelectorAll('.btn-switch-quick').forEach(btn => {
                btn.onclick = () => {
                    alert('Switch view requires proper impersonation token from backend. Currently disabled for security.');
                };
            });
        }

        // Render Quick Leaves Approvals widgets
        const quickLeavesList = document.getElementById('quick-leaves-list');
        if (quickLeavesList) {
            if (pendingLeaves.length === 0) {
                quickLeavesList.innerHTML = '<p class="empty-state-text">No pending leave requests.</p>';
            } else {
                // Show latest 3 pending requests
                quickLeavesList.innerHTML = pendingLeaves.slice(0, 3).map(l => {
                    const empName = l.employee ? `${l.employee.first_name} ${l.employee.last_name}` : 'Unknown';
                    const empCode = l.employee ? l.employee.employee_code : '';
                    const typeName = l.leave_type ? l.leave_type.name : 'Leave';
                    
                    return `
                        <div class="quick-leave-card">
                            <div class="q-leave-header">
                                <strong class="q-leave-user">${empName} (${empCode})</strong>
                                <span class="q-leave-date">Applied: ${new Date(l.created_at).toISOString().split('T')[0]}</span>
                            </div>
                            <div class="q-leave-details">
                                <p><strong>Type:</strong> ${typeName} &bull; <strong>Duration:</strong> ${l.start_date} to ${l.end_date} (${l.requested_days} days)</p>
                                <p class="text-muted" style="margin-top: 4px;">"${l.reason}"</p>
                            </div>
                            <div class="q-leave-actions">
                                <button class="btn btn-danger btn-xs btn-quick-reject" data-id="${l.id}">Reject</button>
                                <button class="btn btn-success btn-xs btn-quick-approve" data-id="${l.id}">Approve</button>
                            </div>
                        </div>
                    `;
                }).join('');

                // Bind approval quick triggers
                quickLeavesList.querySelectorAll('.btn-quick-approve').forEach(btn => {
                    btn.onclick = () => {
                        const leaveId = btn.getAttribute('data-id');
                        this.processQuickLeave(leaveId, 'approve');
                    };
                });

                quickLeavesList.querySelectorAll('.btn-quick-reject').forEach(btn => {
                    btn.onclick = () => {
                        const leaveId = btn.getAttribute('data-id');
                        this.processQuickLeave(leaveId, 'reject');
                    };
                });
            }
        }
    },

    // Process Quick Leave status action from Dashboard
    async processQuickLeave(id, action) {
        const comments = `${action}d via quick admin action on dashboard.`;
        const res = await Api.post(`/leave/${id}/${action}`, { comments });
        
        if (res.success) {
            if (window.Components && Components.showToast) {
                Components.showToast(`Leave request ${action}d successfully.`);
            }
            await this.loadAdminDashboard();
        } else {
            if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
            else alert(res.message);
        }
    }
};

// Auto run on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});
