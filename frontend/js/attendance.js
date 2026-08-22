/* ==========================================================================
   DAYFLOW HRMS - ATTENDANCE PROCESSORS (CHECK-IN, OVERRIDES & CALENDARS)
   ========================================================================== */

const Attendance = {
    async init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        // Ensure we block rendering until API calls finish where needed
        await this.initEmployeeAttendance(user.id); // pass user id or nothing as the API uses cookies
        this.initAdminAttendance();
    },

    // Format Date safely
    formatTime(dateString) {
        if (!dateString) return '--';
        const d = new Date(dateString);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },

    // Employee specific check-in / calendar layout
    async initEmployeeAttendance(userId) {
        const btnCheckIn = document.getElementById('btn-checkin');
        const btnCheckOut = document.getElementById('btn-checkout');
        const statusText = document.getElementById('clock-status-text');
        const logTimeText = document.getElementById('clock-time-log');

        if (!statusText) return; // Not employee attendance page

        let myLogs = [];

        // Fetch logs
        const fetchAttendance = async () => {
            const res = await Api.get('/attendance/me');
            if (res.success) {
                myLogs = res.data;
            }
        };

        const getTodayRecord = () => {
            const today = new Date().toISOString().split('T')[0];
            return myLogs.find(a => a.attendance_date === today);
        };

        const updateClockInCardState = async () => {
            await fetchAttendance();
            const record = getTodayRecord();
            if (record) {
                if (record.check_out_at) {
                    statusText.innerText = 'Shift Completed';
                    const hours = record.worked_minutes ? (record.worked_minutes / 60).toFixed(2) : '0';
                    logTimeText.innerText = `Logged: ${this.formatTime(record.check_in_at)} - ${this.formatTime(record.check_out_at)} (${hours} hrs)`;
                    if (btnCheckIn) btnCheckIn.classList.add('hidden');
                    if (btnCheckOut) btnCheckOut.classList.add('hidden');
                } else {
                    statusText.innerText = 'Checked In';
                    logTimeText.innerText = `Active since: ${this.formatTime(record.check_in_at)}`;
                    if (btnCheckIn) btnCheckIn.classList.add('hidden');
                    if (btnCheckOut) btnCheckOut.classList.remove('hidden');
                }
            } else {
                statusText.innerText = 'Not Checked In';
                logTimeText.innerText = 'Shift: 09:00 AM - 06:00 PM';
                if (btnCheckIn) btnCheckIn.classList.remove('hidden');
                if (btnCheckOut) btnCheckOut.classList.add('hidden');
            }

            this.renderWeeklyLogs(myLogs);
            this.renderMonthlyCalendar(myLogs);
            this.renderSummaryCounters(myLogs);
        };

        await updateClockInCardState();

        // Check In Click Event
        if (btnCheckIn) {
            btnCheckIn.onclick = async () => {
                btnCheckIn.disabled = true;
                const res = await Api.post('/attendance/check-in');
                
                if (res.success) {
                    if (window.Components && Components.showToast) Components.showToast('Checked in successfully!');
                    await updateClockInCardState();
                } else {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                    else alert(res.message);
                }
                btnCheckIn.disabled = false;
            };
        }

        // Check Out Click Event
        if (btnCheckOut) {
            btnCheckOut.onclick = async () => {
                btnCheckOut.disabled = true;
                const res = await Api.post('/attendance/check-out');
                
                if (res.success) {
                    if (window.Components && Components.showToast) Components.showToast('Checked out successfully!');
                    await updateClockInCardState();
                } else {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                    else alert(res.message);
                }
                btnCheckOut.disabled = false;
            };
        }

        // Toggle calendar view vs list view
        const toggles = document.querySelectorAll('.toggle-btn');
        toggles.forEach(btn => {
            btn.onclick = () => {
                toggles.forEach(t => t.classList.remove('active'));
                btn.classList.add('active');

                const view = btn.getAttribute('data-view');
                document.querySelectorAll('.attendance-view-panel').forEach(p => p.classList.remove('active'));
                
                const panel = document.getElementById(`view-${view}`);
                if (panel) panel.classList.add('active');
            };
        });
    },

    // Render employee weekly lists logs
    renderWeeklyLogs(myLogs) {
        const tbody = document.getElementById('weekly-logs-tbody');
        if (!tbody) return;

        if (myLogs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state-text">No attendance records found.</td></tr>';
            return;
        }

        // latest 10
        const logsToShow = myLogs.slice(0, 10);

        tbody.innerHTML = logsToShow.map(log => {
            const dayOfWeek = new Date(log.attendance_date).toLocaleDateString([], { weekday: 'long' });
            const checkIn = this.formatTime(log.check_in_at);
            const checkOut = log.check_out_at ? this.formatTime(log.check_out_at) : '--';
            const hours = log.worked_minutes ? (log.worked_minutes / 60).toFixed(2) + ' hrs' : '--';
            
            return `
                <tr>
                    <td><strong>${log.attendance_date}</strong></td>
                    <td>${dayOfWeek}</td>
                    <td>${checkIn}</td>
                    <td>${checkOut}</td>
                    <td>${hours}</td>
                    <td><span class="status-badge ${log.status.toLowerCase()}">${log.status}</span></td>
                </tr>
            `;
        }).join('');
    },

    // Render monthly calendar heatmap grid
    renderMonthlyCalendar(myLogs) {
        const container = document.getElementById('calendar-days-container');
        if (!container) return;

        const now = new Date();
        const year = now.getFullYear();
        const monthIndex = now.getMonth();
        const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
        
        // Find starting day of week
        const startDay = new Date(year, monthIndex, 1).getDay();

        let cellsHtml = '';

        // Empty cells for starting offset
        for (let i = 0; i < startDay; i++) {
            cellsHtml += `<div class="calendar-day-cell empty"></div>`;
        }

        // Render days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayString = day < 10 ? `0${day}` : day;
            const monthString = monthIndex + 1 < 10 ? `0${monthIndex + 1}` : monthIndex + 1;
            const dateStr = `${year}-${monthString}-${dayString}`;
            const record = myLogs.find(a => a.attendance_date === dateStr);
            
            let statusClass = '';
            if (record) {
                statusClass = record.status.toLowerCase();
            }

            cellsHtml += `
                <div class="calendar-day-cell ${statusClass}">
                    <span class="day-num">${day}</span>
                    <span class="day-status-indicator"></span>
                </div>
            `;
        }

        container.innerHTML = cellsHtml;
    },

    // Summary counters loader
    renderSummaryCounters(myLogs) {
        const now = new Date();
        const monthPrefix = `${now.getFullYear()}-${now.getMonth() + 1 < 10 ? '0' : ''}${now.getMonth() + 1}`;
        const myMonthAtt = myLogs.filter(a => a.attendance_date.startsWith(monthPrefix));

        const pCount = myMonthAtt.filter(a => a.status === 'PRESENT').length;
        const aCount = myMonthAtt.filter(a => a.status === 'ABSENT').length;
        const hCount = myMonthAtt.filter(a => a.status === 'HALF_DAY').length;
        const lCount = myMonthAtt.filter(a => a.status === 'ON_LEAVE').length;

        const sumPresent = document.getElementById('sum-present');
        const sumAbsent = document.getElementById('sum-absent');
        const sumHalfday = document.getElementById('sum-halfday');
        const sumLeave = document.getElementById('sum-leave');

        if (sumPresent) sumPresent.innerText = pCount;
        if (sumAbsent) sumAbsent.innerText = aCount;
        if (sumHalfday) sumHalfday.innerText = hCount;
        if (sumLeave) sumLeave.innerText = lCount;
    },

    // Admin side company attendance overrides
    async initAdminAttendance() {
        const tbody = document.getElementById('admin-att-tbody');
        if (!tbody) return;

        const datePicker = document.getElementById('admin-att-date');
        const deptSelect = document.getElementById('admin-att-dept');

        // Set default date to today
        if (datePicker && !datePicker.value) {
            datePicker.value = new Date().toISOString().split('T')[0];
        }

        const loadRecords = async () => {
            const selectedDate = datePicker.value;
            if (!selectedDate) return;

            tbody.innerHTML = '<tr><td colspan="6">Loading attendance...</td></tr>';

            // Get all employees and attendance
            const empRes = await Api.get('/employees');
            const attRes = await Api.get('/attendance');
            
            if (!empRes.success || !attRes.success) {
                tbody.innerHTML = '<tr><td colspan="6" class="empty-state-text">Unable to load attendance records.</td></tr>';
                return;
            }

            const employees = empRes.data;
            const allAtt = attRes.data;

            const selectedDept = deptSelect ? deptSelect.value : '';

            const filteredEmps = employees.filter(u => u.employment_status === 'ACTIVE' && (!selectedDept || u.department_id === selectedDept));
            const dateRecords = allAtt.filter(a => a.attendance_date === selectedDate);

            if (filteredEmps.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="empty-state-text">No employees found.</td></tr>';
                return;
            }

            tbody.innerHTML = filteredEmps.map(emp => {
                const record = dateRecords.find(r => r.employee_id === emp.id);
                const checkIn = record && record.check_in_at ? this.formatTime(record.check_in_at) : '';
                const checkOut = record && record.check_out_at ? this.formatTime(record.check_out_at) : '';
                const hours = record && record.worked_minutes ? (record.worked_minutes / 60).toFixed(2) : 0;
                const status = record ? record.status : 'ABSENT';

                return `
                    <tr>
                        <td>
                            <div class="directory-table-user-cell">
                                <div class="user-avatar-mini">
                                    <img src="../assets/avatar-placeholder.svg" alt="${emp.first_name}">
                                </div>
                                <strong>${emp.first_name} ${emp.last_name}</strong>
                            </div>
                        </td>
                        <td>${emp.employee_code}</td>
                        <td>${checkIn || '--'}</td>
                        <td>${checkOut || '--'}</td>
                        <td>${hours ? hours + ' hrs' : '--'}</td>
                        <td>
                            <span class="status-badge ${status.toLowerCase()}">${status}</span>
                        </td>
                    </tr>
                `;
            }).join('');
        };

        if (datePicker) datePicker.addEventListener('change', loadRecords);
        if (deptSelect) deptSelect.addEventListener('change', loadRecords);

        // Pre-run
        loadRecords();

        // Overrides logic is disabled in UI since backend enforces actual DB integrity, 
        // Admin overrides would need a specific endpoint to edit attendance which we can add later.
    }
};

// Auto initialize
document.addEventListener('DOMContentLoaded', () => {
    Attendance.init();
});
