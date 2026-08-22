/* ==========================================================================
   DAYFLOW HRMS - LEAVE SYSTEM SCRIPTS (SUBMIT FORMS & APPROVAL MODALS)
   ========================================================================== */

const Leave = {
    init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        this.initEmployeeLeave(user);
        this.initAdminLeave();
    },

    // Employee specific requests submissions & tables
    initEmployeeLeave(user) {
        const form = document.getElementById('apply-leave-form');
        if (!form) return;

        const startDateInput = document.getElementById('leave-start-date');
        const endDateInput = document.getElementById('leave-end-date');
        const daysBadge = document.getElementById('leave-days-badge');
        const daysLabel = document.getElementById('lbl-total-days');

        const calculateDays = () => {
            const startVal = startDateInput.value;
            const endVal = endDateInput.value;

            if (startVal && endVal) {
                const start = new Date(startVal);
                const end = new Date(endVal);
                const diffTime = end - start;
                
                if (diffTime >= 0) {
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                    daysLabel.innerText = diffDays;
                    daysBadge.classList.remove('hidden');
                    return diffDays;
                }
            }
            daysBadge.classList.add('hidden');
            return 0;
        };

        if (startDateInput && endDateInput) {
            startDateInput.addEventListener('change', calculateDays);
            endDateInput.addEventListener('change', calculateDays);
        }

        // Apply leave submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const type = document.getElementById('leave-type').value;
            const start = startDateInput.value;
            const end = endDateInput.value;
            const remarks = document.getElementById('leave-remarks').value.trim();
            const days = calculateDays();

            if (days <= 0) {
                alert('End Date must be after or equal to Start Date.');
                return;
            }

            // Perform balance checks before saving
            const balances = this.getLeaveBalances(user.empid);
            if (type === 'Paid' && days > balances.paid) {
                alert(`Insufficient Paid Leave balance. You only have ${balances.paid} days remaining.`);
                return;
            }
            if (type === 'Sick' && days > balances.sick) {
                alert(`Insufficient Sick Leave balance. You only have ${balances.sick} days remaining.`);
                return;
            }

            const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);
            const newReq = {
                id: `L0${leaves.length + 1}`,
                empid: user.empid,
                name: user.name,
                type,
                start,
                end,
                days,
                remarks,
                status: 'Pending',
                comments: '',
                appliedOn: new Date().toISOString().split('T')[0]
            };

            leaves.push(newReq);
            DayflowDB.saveData(DayflowDB.LEAVES_KEY, leaves);
            
            form.reset();
            daysBadge.classList.add('hidden');

            if (window.Components && Components.showToast) {
                Components.showToast('Leave request submitted successfully.');
            }
            
            this.renderEmployeeHistory(user.empid);
            this.renderEmployeeBalances(user.empid);
        });

        // Initialize displays
        this.renderEmployeeHistory(user.empid);
        this.renderEmployeeBalances(user.empid);
    },

    // Calculate balances remaining
    getLeaveBalances(empid) {
        const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);
        const myApproved = leaves.filter(l => l.empid === empid && l.status === 'Approved');

        let paidUsed = 0;
        let sickUsed = 0;
        let unpaidUsed = 0;

        myApproved.forEach(l => {
            if (l.type === 'Paid') paidUsed += l.days;
            if (l.type === 'Sick') sickUsed += l.days;
            if (l.type === 'Unpaid') unpaidUsed += l.days;
        });

        return {
            paid: Math.max(0, 15 - paidUsed),
            sick: Math.max(0, 8 - sickUsed),
            unpaid: unpaidUsed
        };
    },

    // Populate balances boxes
    renderEmployeeBalances(empid) {
        const balPaid = document.getElementById('bal-paid-avail');
        const balSick = document.getElementById('bal-sick-avail');
        const balUnpaid = document.getElementById('bal-unpaid-used');

        if (!balPaid) return;

        const balances = this.getLeaveBalances(empid);
        balPaid.innerText = `${balances.paid} / 15`;
        balSick.innerText = `${balances.sick} / 8`;
        balUnpaid.innerText = `${balances.unpaid} days`;
    },

    // Render employee personal requests list table
    renderEmployeeHistory(empid) {
        const tbody = document.getElementById('leave-history-tbody');
        if (!tbody) return;

        const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);
        const myRequests = leaves.filter(l => l.empid === empid).sort((a, b) => b.appliedOn.localeCompare(a.appliedOn));

        if (myRequests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state-text">No leave requests found.</td></tr>';
            return;
        }

        tbody.innerHTML = myRequests.map(r => `
            <tr>
                <td><strong>${r.type}</strong></td>
                <td>${r.start} &rarr; ${r.end}</td>
                <td>${r.days} days</td>
                <td><span class="status-badge ${r.status.toLowerCase()}">${r.status}</span></td>
            </tr>
        `).join('');
    },

    // Admin leaves approvals dashboard controller (Section 4 Excalidraw)
    initAdminLeave() {
        const tbody = document.getElementById('approvals-tbody');
        if (!tbody) return;

        const tabs = document.querySelectorAll('#leave-tabs-row .tab-btn');
        let currentFilter = 'all';

        const loadApprovals = () => {
            const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);
            let filtered = [...leaves].sort((a, b) => b.appliedOn.localeCompare(a.appliedOn));

            if (currentFilter !== 'all') {
                filtered = filtered.filter(l => l.status === currentFilter);
            }

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state-text">No leave requests found.</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map(r => {
                const actionButtons = r.status === 'Pending' ? `
                    <div class="approvals-action-btns">
                        <button class="btn btn-danger btn-xs btn-reject" data-id="${r.id}"><i class="fa-solid fa-xmark"></i> Reject</button>
                        <button class="btn btn-success btn-xs btn-approve" data-id="${r.id}"><i class="fa-solid fa-check"></i> Approve</button>
                    </div>
                ` : `<span class="text-muted" style="font-size: 0.8rem;">Processed</span>`;

                return `
                    <tr class="row-status-${r.status.toLowerCase()}">
                        <td><strong>${r.name}</strong><br><span class="text-muted" style="font-size:0.75rem">${r.empid}</span></td>
                        <td>${r.type}</td>
                        <td>${r.start}</td>
                        <td>${r.end}</td>
                        <td>${r.days} days</td>
                        <td><span class="remarks-preview" title="${r.remarks}">${r.remarks || '--'}</span></td>
                        <td><span class="status-badge ${r.status.toLowerCase()}">${r.status}</span></td>
                        <td>${actionButtons}</td>
                    </tr>
                `;
            }).join('');

            // Bind triggers
            const modal = document.getElementById('decision-modal');
            const hiddenId = document.getElementById('decision-request-id');
            const hiddenAction = document.getElementById('decision-type-action');
            const modalTitle = document.getElementById('decision-modal-title');
            const btnSubmit = document.getElementById('btn-decision-submit');

            tbody.querySelectorAll('.btn-approve').forEach(btn => {
                btn.onclick = () => {
                    const id = btn.getAttribute('data-id');
                    if (modal) {
                        hiddenId.value = id;
                        hiddenAction.value = 'Approved';
                        modalTitle.innerText = 'Approve Leave Request';
                        btnSubmit.className = 'btn btn-block btn-success';
                        btnSubmit.innerText = 'Approve Request';
                        modal.classList.add('active');
                    }
                };
            });

            tbody.querySelectorAll('.btn-reject').forEach(btn => {
                btn.onclick = () => {
                    const id = btn.getAttribute('data-id');
                    if (modal) {
                        hiddenId.value = id;
                        hiddenAction.value = 'Rejected';
                        modalTitle.innerText = 'Reject Leave Request';
                        btnSubmit.className = 'btn btn-block btn-danger';
                        btnSubmit.innerText = 'Reject Request';
                        modal.classList.add('active');
                    }
                };
            });
        };

        // Bind filter tabs click
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentFilter = tab.getAttribute('data-filter');
                loadApprovals();
            });
        });

        // Modal Action decision form submit handler
        const form = document.getElementById('decision-form');
        const modal = document.getElementById('decision-modal');
        const closeBtn = document.getElementById('close-decision-modal');

        if (form && modal) {
            closeBtn.onclick = () => modal.classList.remove('active');

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const id = document.getElementById('decision-request-id').value;
                const status = document.getElementById('decision-type-action').value;
                const comments = document.getElementById('decision-comments').value.trim();

                const leaves = DayflowDB.getData(DayflowDB.LEAVES_KEY);
                const reqIndex = leaves.findIndex(l => l.id === id);

                if (reqIndex !== -1) {
                    leaves[reqIndex].status = status;
                    leaves[reqIndex].comments = comments;

                    // Deduct balance from employee records if approved
                    if (status === 'Approved') {
                        const leaveStart = new Date(leaves[reqIndex].start);
                        const leaveEnd = new Date(leaves[reqIndex].end);
                        const allAtt = DayflowDB.getData(DayflowDB.ATTENDANCE_KEY);
                        
                        // Seed employee attendance days as 'leave'
                        for (let d = new Date(leaveStart); d <= leaveEnd; d.setDate(d.getDate() + 1)) {
                            const dateStr = d.toISOString().split('T')[0];
                            const dayOfWeek = d.getDay();
                            
                            if (dayOfWeek === 0 || dayOfWeek === 6) continue; // skip weekends

                            const attIdx = allAtt.findIndex(a => a.empid === leaves[reqIndex].empid && a.date === dateStr);
                            if (attIdx !== -1) {
                                allAtt[attIdx].status = 'leave';
                                allAtt[attIdx].checkIn = '';
                                allAtt[attIdx].checkOut = '';
                                allAtt[attIdx].hours = 0;
                            } else {
                                allAtt.push({
                                    empid: leaves[reqIndex].empid,
                                    date: dateStr,
                                    checkIn: '',
                                    checkOut: '',
                                    hours: 0,
                                    status: 'leave'
                                });
                            }
                        }
                        DayflowDB.saveData(DayflowDB.ATTENDANCE_KEY, allAtt);
                    }

                    DayflowDB.saveData(DayflowDB.LEAVES_KEY, leaves);
                    
                    // Dispatch alert notifications
                    if (window.Components && Components.addNotification) {
                        Components.addNotification(
                            leaves[reqIndex].empid,
                            `Your leave request from ${leaves[reqIndex].start} has been ${status}.`,
                            status === 'Approved' ? 'fa-circle-check' : 'fa-circle-xmark'
                        );
                    }

                    form.reset();
                    modal.classList.remove('active');
                    if (window.Components && Components.showToast) Components.showToast(`Request ${status}`);
                    loadApprovals();
                }
            });
        }

        // Run pre-loads
        loadApprovals();
    }
};

// Auto initialize
document.addEventListener('DOMContentLoaded', () => {
    Leave.init();
});
