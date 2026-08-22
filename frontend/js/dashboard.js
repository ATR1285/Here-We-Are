/* ==========================================================================
   DAYFLOW HRMS - DASHBOARD SCRIPTS (EMPLOYEE & ADMIN VIEWS)
   ========================================================================== */

const Dashboard = {
    init() {
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
        
        const user = Auth.getCurrentUser();
        if (!user) return;

        this.setGreeting(user.name);

        if (user.role === 'employee') {
            this.loadEmployeeDashboard(user.empid);
        } else {
            this.loadAdminDashboard();
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
    loadEmployeeDashboard(empid) {
        const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
        const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);

        // Filter active employee attendance (August 2026)
        const myAtt = attendance.filter(a => a.empid === empid && a.date.startsWith('2026-08'));
        const presentCount = myAtt.filter(a => a.status === 'present').length;
        const halfdayCount = myAtt.filter(a => a.status === 'half-day').length;
        
        const statPresent = document.getElementById('stat-present-days');
        if (statPresent) {
            statPresent.innerText = `${presentCount + halfdayCount} days`;
        }

        // Pending Leave Count
        const myPendingLeaves = leaves.filter(l => l.empid === empid && l.status === 'Pending').length;
        const statLeaves = document.getElementById('stat-pending-leaves');
        if (statLeaves) {
            statLeaves.innerText = myPendingLeaves;
        }

        // Total hours worked counter
        let totalHrs = 0;
        myAtt.forEach(a => totalHrs += a.hours || 0);
        const statHours = document.getElementById('stat-work-hours');
        if (statHours) {
            statHours.innerText = `${totalHrs.toFixed(1)}h`;
        }

        // Load recent check-in/out history timeline logs
        const timeline = document.getElementById('activity-timeline');
        if (timeline) {
            // Sort attendance newest first
            const sortedAtt = [...myAtt].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 4);

            if (sortedAtt.length === 0) {
                timeline.innerHTML = '<p class="empty-state-text">No recent check-in/out logs.</p>';
            } else {
                timeline.innerHTML = sortedAtt.map(a => {
                    let logs = [];
                    if (a.checkIn) {
                        logs.push(`
                            <div class="timeline-item checkin">
                                <span class="timeline-time">${a.date} &bull; ${a.checkIn}</span>
                                <p class="timeline-desc">Checked In successfully (Status: <strong class="${a.status === 'present' ? 'present-color' : 'half-day-color'}">${a.status}</strong>)</p>
                            </div>
                        `);
                    }
                    if (a.checkOut) {
                        logs.push(`
                            <div class="timeline-item checkout">
                                <span class="timeline-time">${a.date} &bull; ${a.checkOut}</span>
                                <p class="timeline-desc">Checked Out successfully (${a.hours.toFixed(2)} hours logged)</p>
                            </div>
                        `);
                    }
                    return logs.join('');
                }).join('');
            }
        }
    },

    // Loading Admin/HR dashboard widgets and logs checklist
    loadAdminDashboard() {
        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
        const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
        const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);

        const employees = users.filter(u => u.role === 'employee');

        // Stat 1: Total Employees
        const totalEmpEl = document.getElementById('stat-total-emp');
        if (totalEmpEl) totalEmpEl.innerText = employees.length;

        // Today's Date
        const todayDate = new Date().toISOString().split('T')[0];

        // Stat 2: Present Today
        const todayAtt = attendance.filter(a => a.date === todayDate);
        const presentToday = todayAtt.filter(a => a.status === 'present' || a.status === 'half-day').length;
        const presentTodayEl = document.getElementById('stat-present-today');
        if (presentTodayEl) presentTodayEl.innerText = presentToday;

        // Stat 3: Pending Leaves
        const pendingLeaves = leaves.filter(l => l.status === 'Pending');
        const pendingLeavesEl = document.getElementById('stat-leaves-pending');
        if (pendingLeavesEl) pendingLeavesEl.innerText = pendingLeaves.length;

        // Render company employees logs grid table
        const tbody = document.getElementById('admin-emp-overview-tbody');
        if (tbody) {
            tbody.innerHTML = employees.map(emp => {
                const todayRecord = todayAtt.find(a => a.empid === emp.empid);
                let statusBadge = `<span class="status-badge off">No Record</span>`;
                
                if (todayRecord) {
                    statusBadge = `<span class="status-badge ${todayRecord.status}">${todayRecord.status}</span>`;
                }

                return `
                    <tr>
                        <td>
                            <div class="directory-table-user-cell">
                                <div class="user-avatar-mini">
                                    <img src="${emp.avatar || '../assets/avatar-placeholder.svg'}" alt="${emp.name}">
                                </div>
                                <strong>${emp.name}</strong>
                            </div>
                        </td>
                        <td>${emp.designation}</td>
                        <td>${statusBadge}</td>
                        <td>
                            <button class="btn btn-secondary btn-xs btn-switch-quick" data-empid="${emp.empid}">
                                <i class="fa-solid fa-right-to-bracket"></i> Switch View
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            // Bind click switches view
            tbody.querySelectorAll('.btn-switch-quick').forEach(btn => {
                btn.onclick = () => {
                    const empid = btn.getAttribute('data-empid');
                    const selectedEmp = employees.find(emp => emp.empid === empid);
                    if (selectedEmp) {
                        sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(selectedEmp));
                        window.location.href = '../employee/dashboard.html';
                    }
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
                quickLeavesList.innerHTML = pendingLeaves.slice(0, 3).map(l => `
                    <div class="quick-leave-card">
                        <div class="q-leave-header">
                            <strong class="q-leave-user">${l.name} (${l.empid})</strong>
                            <span class="q-leave-date">Applied: ${l.appliedOn}</span>
                        </div>
                        <div class="q-leave-details">
                            <p><strong>Type:</strong> ${l.type} Leave &bull; <strong>Duration:</strong> ${l.start} to ${l.end} (${l.days} days)</p>
                            <p class="text-muted" style="margin-top: 4px;">"${l.remarks}"</p>
                        </div>
                        <div class="q-leave-actions">
                            <button class="btn btn-danger btn-xs btn-quick-reject" data-id="${l.id}">Reject</button>
                            <button class="btn btn-success btn-xs btn-quick-approve" data-id="${l.id}">Approve</button>
                        </div>
                    </div>
                `).join('');

                // Bind approval quick triggers
                quickLeavesList.querySelectorAll('.btn-quick-approve').forEach(btn => {
                    btn.onclick = () => {
                        const leaveId = btn.getAttribute('data-id');
                        this.processQuickLeave(leaveId, 'Approved');
                    };
                });

                quickLeavesList.querySelectorAll('.btn-quick-reject').forEach(btn => {
                    btn.onclick = () => {
                        const leaveId = btn.getAttribute('data-id');
                        this.processQuickLeave(leaveId, 'Rejected');
                    };
                });
            }
        }
    },

    // Process Quick Leave status action from Dashboard
    processQuickLeave(id, status) {
        const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);
        const reqIndex = leaves.findIndex(l => l.id === id);

        if (reqIndex !== -1) {
            leaves[reqIndex].status = status;
            leaves[reqIndex].comments = `${status} via quick admin action.`;
            DayflowDB.saveData(DayflowDB.LEAVES_KEY, leaves);
            
            // Send in-app alert notification
            if (window.Components && Components.addNotification) {
                Components.addNotification(
                    leaves[reqIndex].empid, 
                    `Your leave request for ${leaves[reqIndex].start} has been ${status}.`,
                    status === 'Approved' ? 'fa-circle-check' : 'fa-circle-xmark'
                );
            }

            if (window.Components && Components.showToast) {
                Components.showToast(`Leave request ${status} successfully.`);
            } else {
                alert(`Leave request ${status}.`);
            }

            this.loadAdminDashboard();
        }
    }
};

// Auto run on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});
