/* ==========================================================================
   DAYFLOW HRMS - ATTENDANCE PROCESSORS (CHECK-IN, OVERRIDES & CALENDARS)
   ========================================================================== */

const Attendance = {
    init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        this.initEmployeeAttendance(user.empid);
        this.initAdminAttendance();
    },

    // Employee specific check-in / calendar layout
    initEmployeeAttendance(empid) {
        const btnCheckIn = document.getElementById('btn-checkin');
        const btnCheckOut = document.getElementById('btn-checkout');
        const statusText = document.getElementById('clock-status-text');
        const logTimeText = document.getElementById('clock-time-log');

        if (!statusText) return; // Not employee attendance page

        const today = new Date().toISOString().split('T')[0];

        // Check if checked in today
        const getTodayRecord = () => {
            const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
            return attendance.find(a => a.empid === empid && a.date === today);
        };

        const updateClockInCardState = () => {
            const record = getTodayRecord();
            if (record) {
                if (record.checkOut) {
                    statusText.innerText = 'Shift Completed';
                    logTimeText.innerText = `Logged: ${record.checkIn} - ${record.checkOut} (${record.hours.toFixed(2)} hrs)`;
                    if (btnCheckIn) btnCheckIn.classList.add('hidden');
                    if (btnCheckOut) btnCheckOut.classList.add('hidden');
                } else {
                    statusText.innerText = 'Checked In';
                    logTimeText.innerText = `Active since: ${record.checkIn}`;
                    if (btnCheckIn) btnCheckIn.classList.add('hidden');
                    if (btnCheckOut) btnCheckOut.classList.remove('hidden');
                }
            } else {
                statusText.innerText = 'Not Checked In';
                logTimeText.innerText = 'Shift: 09:00 AM - 06:00 PM';
                if (btnCheckIn) btnCheckIn.classList.remove('hidden');
                if (btnCheckOut) btnCheckOut.classList.add('hidden');
            }
        };

        updateClockInCardState();

        // Check In Click Event
        if (btnCheckIn) {
            btnCheckIn.onclick = () => {
                const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
                const now = new Date();
                const checkIn = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                attendance.push({
                    empid,
                    date: today,
                    checkIn,
                    checkOut: '',
                    hours: 0,
                    status: 'present'
                });

                DayflowDB.saveData(DayflowDB.ATTENDANCE_KEY, attendance);
                if (window.Components && Components.showToast) Components.showToast('Checked in successfully!');
                
                updateClockInCardState();
                this.renderWeeklyLogs(empid);
                this.renderMonthlyCalendar(empid);
                this.renderSummaryCounters(empid);
            };
        }

        // Check Out Click Event
        if (btnCheckOut) {
            btnCheckOut.onclick = () => {
                const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
                const idx = attendance.findIndex(a => a.empid === empid && a.date === today);

                if (idx !== -1) {
                    const now = new Date();
                    const checkOut = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    
                    // Parse check-in to get hours worked
                    const checkInTime = new Date(`${today} ${attendance[idx].checkIn}`);
                    const checkOutTime = new Date(`${today} ${checkOut}`);
                    const diffMs = checkOutTime - checkInTime;
                    const hours = diffMs > 0 ? diffMs / (1000 * 60 * 60) : 8.5; // fallback hours

                    attendance[idx].checkOut = checkOut;
                    attendance[idx].hours = parseFloat(hours.toFixed(2));
                    
                    // Determine half-day or present
                    if (hours < 4) {
                        attendance[idx].status = 'half-day';
                    }

                    DayflowDB.saveData(DayflowDB.ATTENDANCE_KEY, attendance);
                    if (window.Components && Components.showToast) Components.showToast('Checked out successfully!');
                    
                    updateClockInCardState();
                    this.renderWeeklyLogs(empid);
                    this.renderMonthlyCalendar(empid);
                    this.renderSummaryCounters(empid);
                }
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

        // Initialize display
        this.renderWeeklyLogs(empid);
        this.renderMonthlyCalendar(empid);
        this.renderSummaryCounters(empid);
    },

    // Render employee weekly lists logs (Section 3 Excalidraw)
    renderWeeklyLogs(empid) {
        const tbody = document.getElementById('weekly-logs-tbody');
        if (!tbody) return;

        const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
        // Load latest 10 logs
        const myLogs = attendance.filter(a => a.empid === empid).sort((a, b) => b.date.localeCompare(a.date)).slice(0, 10);

        if (myLogs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state-text">No attendance records found.</td></tr>';
            return;
        }

        tbody.innerHTML = myLogs.map(log => {
            const dayOfWeek = new Date(log.date).toLocaleDateString([], { weekday: 'long' });
            return `
                <tr>
                    <td><strong>${log.date}</strong></td>
                    <td>${dayOfWeek}</td>
                    <td>${log.checkIn || '--'}</td>
                    <td>${log.checkOut || '--'}</td>
                    <td>${log.hours ? log.hours.toFixed(2) + ' hrs' : '--'}</td>
                    <td><span class="status-badge ${log.status}">${log.status}</span></td>
                </tr>
            `;
        }).join('');
    },

    // Render monthly calendar heatmap grid (Section 3 Excalidraw details)
    renderMonthlyCalendar(empid) {
        const container = document.getElementById('calendar-days-container');
        if (!container) return;

        // Current Month (August 2026)
        const year = 2026;
        const monthIndex = 7; // August (0-indexed)
        const daysInMonth = 31;
        
        // Find starting day of week
        const startDay = new Date(year, monthIndex, 1).getDay();

        const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
        const myMonthAtt = attendance.filter(a => a.empid === empid && a.date.startsWith('2026-08'));

        let cellsHtml = '';

        // Empty cells for starting offset
        for (let i = 0; i < startDay; i++) {
            cellsHtml += `<div class="calendar-day-cell empty"></div>`;
        }

        // Render days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayString = day < 10 ? `0${day}` : day;
            const dateStr = `2026-08-${dayString}`;
            const record = myMonthAtt.find(a => a.date === dateStr);
            
            let statusClass = '';
            if (record) {
                statusClass = record.status; // present, absent, half-day, leave
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
    renderSummaryCounters(empid) {
        const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
        const myMonthAtt = attendance.filter(a => a.empid === empid && a.date.startsWith('2026-08'));

        const pCount = myMonthAtt.filter(a => a.status === 'present').length;
        const aCount = myMonthAtt.filter(a => a.status === 'absent').length;
        const hCount = myMonthAtt.filter(a => a.status === 'half-day').length;
        const lCount = myMonthAtt.filter(a => a.status === 'leave').length;

        const sumPresent = document.getElementById('sum-present');
        const sumAbsent = document.getElementById('sum-absent');
        const sumHalfday = document.getElementById('sum-halfday');
        const sumLeave = document.getElementById('sum-leave');

        if (sumPresent) sumPresent.innerText = pCount;
        if (sumAbsent) sumAbsent.innerText = aCount;
        if (sumHalfday) sumHalfday.innerText = hCount;
        if (sumLeave) sumLeave.innerText = lCount;
    },

    // Admin side company attendance overrides (Section 3 Excalidraw - HR View)
    initAdminAttendance() {
        const tbody = document.getElementById('admin-att-tbody');
        if (!tbody) return;

        const datePicker = document.getElementById('admin-att-date');
        const deptSelect = document.getElementById('admin-att-dept');

        const loadRecords = () => {
            const selectedDate = datePicker.value;
            const selectedDept = deptSelect.value;

            const users = DayflowDB.getData(DayflowDB.USERS_KEY);
            const attendance = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);

            const employees = users.filter(u => u.role === 'employee' && (!selectedDept || u.dept === selectedDept));
            const dateRecords = attendance.filter(a => a.date === selectedDate);

            tbody.innerHTML = employees.map(emp => {
                const record = dateRecords.find(r => r.empid === emp.empid);
                const checkIn = record ? record.checkIn : '';
                const checkOut = record ? record.checkOut : '';
                const hours = record ? record.hours : 0;
                const status = record ? record.status : 'absent';

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
                        <td>${checkIn || '--'}</td>
                        <td>${checkOut || '--'}</td>
                        <td>${hours ? hours.toFixed(2) + ' hrs' : '--'}</td>
                        <td>
                            <select class="admin-override-select" data-empid="${emp.empid}" data-date="${selectedDate}">
                                <option value="present" ${status === 'present' ? 'selected' : ''}>Present</option>
                                <option value="absent" ${status === 'absent' ? 'selected' : ''}>Absent</option>
                                <option value="half-day" ${status === 'half-day' ? 'selected' : ''}>Half-Day</option>
                                <option value="leave" ${status === 'leave' ? 'selected' : ''}>Leave</option>
                            </select>
                        </td>
                    </tr>
                `;
            }).join('');

            // Bind override changes
            tbody.querySelectorAll('.admin-override-select').forEach(select => {
                select.onchange = (e) => {
                    const empid = select.getAttribute('data-empid');
                    const date = select.getAttribute('data-date');
                    const status = e.target.value;

                    const allAtt = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
                    const idx = allAtt.findIndex(a => a.empid === empid && a.date === date);

                    if (idx !== -1) {
                        allAtt[idx].status = status;
                        if (status === 'absent' || status === 'leave') {
                            allAtt[idx].checkIn = '';
                            allAtt[idx].checkOut = '';
                            allAtt[idx].hours = 0;
                        } else if (status === 'present' && !allAtt[idx].checkIn) {
                            allAtt[idx].checkIn = '09:00 AM';
                            allAtt[idx].checkOut = '06:00 PM';
                            allAtt[idx].hours = 9.0;
                        }
                    } else {
                        // Create new record override
                        allAtt.push({
                            empid,
                            date,
                            checkIn: status === 'present' ? '09:00 AM' : '',
                            checkOut: status === 'present' ? '06:00 PM' : '',
                            hours: status === 'present' ? 9.0 : 0,
                            status
                        });
                    }

                    DayflowDB.saveData(DayflowDB.ATTENDANCE_KEY, allAtt);
                    if (window.Components && Components.showToast) {
                        Components.showToast(`Override saved for ${empid}`);
                    }
                    loadRecords();
                };
            });
        };

        // Listen for filter overrides
        datePicker.addEventListener('change', loadRecords);
        deptSelect.addEventListener('change', loadRecords);

        // Pre-run
        loadRecords();

        // Sim Export CSV
        const btnExport = document.getElementById('btn-export-att');
        if (btnExport) {
            btnExport.onclick = () => {
                alert('Exporting attendance records report to CSV... Download completed.');
            };
        }
    }
};

// Auto initialize
document.addEventListener('DOMContentLoaded', () => {
    Attendance.init();
});
