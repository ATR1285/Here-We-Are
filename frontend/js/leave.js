/* ==========================================================================
   DAYFLOW HRMS - LEAVE SYSTEM SCRIPTS (SUBMIT FORMS & APPROVAL MODALS)
   ========================================================================== */

const Leave = {
    async init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        await this.initEmployeeLeave();
        this.initAdminLeave();
    },

    // Format Date safely
    formatDate(dateString) {
        if (!dateString) return '--';
        return dateString;
    },

    // Employee specific requests submissions & tables
    async initEmployeeLeave() {
        const form = document.getElementById('apply-leave-form');
        if (!form) return;

        const startDateInput = document.getElementById('leave-start-date');
        const endDateInput = document.getElementById('leave-end-date');
        const daysBadge = document.getElementById('leave-days-badge');
        const daysLabel = document.getElementById('lbl-total-days');
        const leaveTypeSelect = document.getElementById('leave-type');
        
        let leaveTypes = [];

        // Fetch leave types for dropdown
        const loadLeaveTypes = async () => {
            const res = await Api.get('/leave/types');
            if (res.success) {
                leaveTypes = res.data;
                leaveTypeSelect.innerHTML = leaveTypes.map(lt => 
                    `<option value="${lt.id}">${lt.name}</option>`
                ).join('');
            }
        };

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
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btnSubmit = form.querySelector('button[type="submit"]');
            
            const leave_type_id = leaveTypeSelect.value;
            const start_date = startDateInput.value;
            const end_date = endDateInput.value;
            const reason = document.getElementById('leave-remarks').value.trim();
            const days = calculateDays();

            if (days <= 0) {
                alert('End Date must be after or equal to Start Date.');
                return;
            }
            
            btnSubmit.disabled = true;

            const res = await Api.post('/leave/apply', {
                leave_type_id,
                start_date,
                end_date,
                reason
            });

            if (res.success) {
                form.reset();
                daysBadge.classList.add('hidden');

                if (window.Components && Components.showToast) {
                    Components.showToast('Leave request submitted successfully.');
                }
                
                await this.renderEmployeeHistory();
                await this.renderEmployeeBalances();
            } else {
                if (window.Components && Components.showToast) {
                    Components.showToast(res.message, 'error');
                } else {
                    alert(res.message);
                }
            }
            
            btnSubmit.disabled = false;
        });

        // Initialize displays
        await loadLeaveTypes();
        await this.renderEmployeeHistory();
        await this.renderEmployeeBalances();
    },

    // Populate balances boxes
    async renderEmployeeBalances() {
        const balPaid = document.getElementById('bal-paid-avail');
        const balSick = document.getElementById('bal-sick-avail');
        const balUnpaid = document.getElementById('bal-unpaid-used');

        if (!balPaid) return;

        const res = await Api.get('/leave/me/balances');
        if (res.success) {
            const balances = res.data;
            
            const findBal = (code) => balances.find(b => b.leave_type && b.leave_type.code === code) || { available_days: 0, allocated_days: 0, used_days: 0 };
            
            const paid = findBal('PAID');
            const sick = findBal('SICK');
            const unpaid = findBal('UNPAID');

            balPaid.innerText = `${paid.available_days} / ${paid.allocated_days}`;
            balSick.innerText = `${sick.available_days} / ${sick.allocated_days}`;
            balUnpaid.innerText = `${unpaid.used_days} days`;
        }
    },

    // Render employee personal requests list table
    async renderEmployeeHistory() {
        const tbody = document.getElementById('leave-history-tbody');
        if (!tbody) return;

        const res = await Api.get('/leave/me/requests');
        if (res.success) {
            const myRequests = res.data;
            
            if (myRequests.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="empty-state-text">No leave requests found.</td></tr>';
                return;
            }

            tbody.innerHTML = myRequests.map(r => `
                <tr>
                    <td><strong>${r.leave_type ? r.leave_type.name : 'Leave'}</strong></td>
                    <td>${this.formatDate(r.start_date)} &rarr; ${this.formatDate(r.end_date)}</td>
                    <td>${r.requested_days} days</td>
                    <td><span class="status-badge ${r.status.toLowerCase()}">${r.status}</span></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state-text">Unable to load requests.</td></tr>';
        }
    },

    // Admin leaves approvals dashboard controller
    async initAdminLeave() {
        const tbody = document.getElementById('approvals-tbody');
        if (!tbody) return;

        const tabs = document.querySelectorAll('#leave-tabs-row .tab-btn');
        let currentFilter = 'all';

        const loadApprovals = async () => {
            const res = await Api.get('/leave/requests');
            if (!res.success) {
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state-text">Unable to load requests.</td></tr>';
                return;
            }

            let allRequests = res.data;
            let filtered = allRequests;

            if (currentFilter !== 'all') {
                filtered = filtered.filter(l => l.status.toLowerCase() === currentFilter.toLowerCase());
            }

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state-text">No leave requests found.</td></tr>';
                return;
            }

            // Fetch employees for details if not included in the response (assumes backend includes employee object)
            tbody.innerHTML = filtered.map(r => {
                const actionButtons = r.status === 'PENDING' ? `
                    <div class="approvals-action-btns">
                        <button class="btn btn-danger btn-xs btn-reject" data-id="${r.id}"><i class="fa-solid fa-xmark"></i> Reject</button>
                        <button class="btn btn-success btn-xs btn-approve" data-id="${r.id}"><i class="fa-solid fa-check"></i> Approve</button>
                    </div>
                ` : `<span class="text-muted" style="font-size: 0.8rem;">Processed</span>`;

                const empName = r.employee ? `${r.employee.first_name} ${r.employee.last_name}` : 'Unknown';
                const empCode = r.employee ? r.employee.employee_code : '';
                const typeName = r.leave_type ? r.leave_type.name : 'Leave';

                return `
                    <tr class="row-status-${r.status.toLowerCase()}">
                        <td><strong>${empName}</strong><br><span class="text-muted" style="font-size:0.75rem">${empCode}</span></td>
                        <td>${typeName}</td>
                        <td>${this.formatDate(r.start_date)}</td>
                        <td>${this.formatDate(r.end_date)}</td>
                        <td>${r.requested_days} days</td>
                        <td><span class="remarks-preview" title="${r.reason}">${r.reason || '--'}</span></td>
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
                        hiddenAction.value = 'approve';
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
                        hiddenAction.value = 'reject';
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

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const id = document.getElementById('decision-request-id').value;
                const action = document.getElementById('decision-type-action').value;
                const comments = document.getElementById('decision-comments').value.trim();

                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;

                const res = await Api.post(`/leave/${id}/${action}`, { comments });
                
                if (res.success) {
                    form.reset();
                    modal.classList.remove('active');
                    if (window.Components && Components.showToast) Components.showToast(`Request ${action}d successfully`);
                    loadApprovals();
                } else {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                    else alert(res.message);
                }
                
                submitBtn.disabled = false;
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
