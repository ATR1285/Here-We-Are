/* ==========================================================================
   DAYFLOW HRMS - PAYROLL MANAGER (CALCULATORS, PAYSLIPS & CONFIGURATIONS)
   ========================================================================== */

const Payroll = {
    async init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        this.initEmployeePayroll();
        this.initAdminPayroll();
    },

    // Employee specific pay summaries & slip selectors
    initEmployeePayroll() {
        const selectPeriod = document.getElementById('payroll-month-select');
        if (!selectPeriod) return; // Not employee payroll page

        const renderPeriodPay = async () => {
            const period = selectPeriod.value;
            const [year, month] = period.split('-');
            const labelPeriod = document.getElementById('pay-period-lbl');
            if (labelPeriod) labelPeriod.innerText = selectPeriod.options[selectPeriod.selectedIndex].text;

            const res = await Api.get(`/payroll/me/${year}/${month}`);
            
            if (!res.success) {
                this.updateComponentsDisplay(0, 0, 0, 0);
                if (res.status !== 404) {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                }
                return;
            }

            const record = res.data;

            // Simple derived mock breakdown for UI purposes since backend only stores totals
            const gross = record.gross_earnings || 0;
            const deductions = record.total_deductions || 0;
            const net = record.net_pay || 0;
            
            this.updateComponentsDisplay(gross, deductions, net, record.lop_deduction || 0);
        };

        selectPeriod.addEventListener('change', renderPeriodPay);
        renderPeriodPay();

        // Simulate PDF download slip
        const btnDownload = document.getElementById('btn-download-payslip');
        if (btnDownload) {
            btnDownload.onclick = () => {
                alert(`Exporting payslip statement for ${selectPeriod.options[selectPeriod.selectedIndex].text} in PDF format... Completed.`);
            };
        }
    },

    // Update frontend text components (Employee View)
    updateComponentsDisplay(gross, totalDeductions, net, lop) {
        // Backend returns totals. We fake the breakdown for the UI if gross > 0
        const basic = gross > 0 ? gross * 0.5 : 0;
        const hra = gross > 0 ? gross * 0.2 : 0;
        const standard = gross > 0 ? gross * 0.1 : 0;
        const bonus = gross > 0 ? gross * 0.1 : 0;
        const lta = gross > 0 ? gross * 0.05 : 0;
        const fixed = gross > 0 ? gross * 0.05 : 0;

        const tds = gross > 0 ? gross * 0.1 : 0;
        const pf = gross > 0 ? basic * 0.06 : 0;
        // Adjust TDS/PF slightly to match total_deductions - lop if they don't perfectly match,
        // but for demo, we'll just show them as is.

        const basicEl = document.getElementById('pay-basic');
        const hraEl = document.getElementById('pay-hra');
        const standardEl = document.getElementById('pay-standard');
        const bonusEl = document.getElementById('pay-bonus');
        const ltaEl = document.getElementById('pay-lta');
        const fixedEl = document.getElementById('pay-fixed');

        if (basicEl) basicEl.innerText = this.formatCurrency(basic);
        if (hraEl) hraEl.innerText = this.formatCurrency(hra);
        if (standardEl) standardEl.innerText = this.formatCurrency(standard);
        if (bonusEl) bonusEl.innerText = this.formatCurrency(bonus);
        if (ltaEl) ltaEl.innerText = this.formatCurrency(lta);
        if (fixedEl) fixedEl.innerText = this.formatCurrency(fixed);

        const grossEl = document.getElementById('lbl-gross-total');
        const deductionsEl = document.getElementById('lbl-deductions-total');
        const netEl = document.getElementById('pay-net-amount');
        const tdsEl = document.getElementById('pay-tds');
        const pfEl = document.getElementById('pay-pf');

        if (grossEl) grossEl.innerText = this.formatCurrency(gross);
        if (deductionsEl) deductionsEl.innerText = '-' + this.formatCurrency(totalDeductions);
        if (tdsEl) tdsEl.innerText = '-' + this.formatCurrency(tds);
        if (pfEl) pfEl.innerText = '-' + this.formatCurrency(pf + lop);
        if (netEl) netEl.innerText = this.formatCurrency(net);
    },

    // Format utility
    formatCurrency(val) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
    },

    // Admin salary configs controls panel
    async initAdminPayroll() {
        const empSelect = document.getElementById('payroll-employee-select');
        if (!empSelect) return; // Not admin payroll page

        const empRes = await Api.get('/employees');
        if (!empRes.success) return;
        
        const employees = empRes.data.filter(e => e.employment_status === 'ACTIVE');

        // Populate dropdown
        empSelect.innerHTML = employees.map(emp => `<option value="${emp.id}">${emp.first_name} ${emp.last_name} (${emp.employee_code})</option>`).join('');

        const form = document.getElementById('salary-structure-form');
        const configInputs = {
            basic: document.getElementById('cfg-basic'),
            hra: document.getElementById('cfg-hra'),
            standard: document.getElementById('cfg-standard'),
            bonus: document.getElementById('cfg-bonus'),
            lta: document.getElementById('cfg-lta'),
            fixed: document.getElementById('cfg-fixed')
        };

        const loadEmployeeSalaryStructure = async () => {
            const empid = empSelect.value;
            if (!empid) return;
            
            const res = await Api.get(`/payroll/structure/${empid}`);
            let structure = { basic: 50000, hra: 20000, standard: 10000, bonus: 10000, lta: 5000, fixed: 5000 };
            
            if (res.success && res.data && res.data.base_salary) {
                const s = res.data;
                // Deconstruct backend totals into frontend UI inputs
                structure.basic = s.base_salary;
                const allowances = s.allowances || 0;
                structure.hra = allowances * 0.4;
                structure.standard = allowances * 0.2;
                structure.bonus = allowances * 0.2;
                structure.lta = allowances * 0.1;
                structure.fixed = allowances * 0.1;
            }

            // Fill inputs
            configInputs.basic.value = structure.basic;
            configInputs.hra.value = structure.hra;
            configInputs.standard.value = structure.standard;
            configInputs.bonus.value = structure.bonus;
            configInputs.lta.value = structure.lta;
            configInputs.fixed.value = structure.fixed;

            this.updateAdminPreview();
        };

        // Live Preview calculation logic
        this.updateAdminPreview = () => {
            const basic = parseFloat(configInputs.basic.value) || 0;
            const hra = parseFloat(configInputs.hra.value) || 0;
            const standard = parseFloat(configInputs.standard.value) || 0;
            const bonus = parseFloat(configInputs.bonus.value) || 0;
            const lta = parseFloat(configInputs.lta.value) || 0;
            const fixed = parseFloat(configInputs.fixed.value) || 0;

            const annualGross = basic + hra + standard + bonus + lta + fixed;
            const monthlyGross = annualGross / 12;
            const monthlyBasic = basic / 12;
            
            // Deductions
            const monthlyTds = monthlyGross * 0.1;
            const monthlyPf = monthlyBasic * 0.06;
            const monthlyDeductions = monthlyTds + monthlyPf;
            const monthlyNet = monthlyGross - monthlyDeductions;

            // Update preview values
            document.getElementById('cfg-ctc-total').innerText = this.formatCurrency(annualGross);
            document.getElementById('cfg-monthly-gross').innerText = this.formatCurrency(monthlyGross);
            
            document.getElementById('preview-basic').innerText = this.formatCurrency(basic);
            document.getElementById('preview-allowances').innerText = this.formatCurrency(hra + standard + bonus + lta + fixed);
            document.getElementById('preview-deductions').innerText = '-' + this.formatCurrency(monthlyDeductions * 12);
            document.getElementById('preview-net').innerText = this.formatCurrency(monthlyNet);
        };

        // Bind update triggers
        Object.values(configInputs).forEach(input => {
            input.addEventListener('input', () => this.updateAdminPreview());
        });

        empSelect.addEventListener('change', loadEmployeeSalaryStructure);
        
        // Save Structure Submit event
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const empid = empSelect.value;
            const btnSubmit = form.querySelector('button[type="submit"]');
            
            btnSubmit.disabled = true;
            
            const payload = {
                basic: parseFloat(configInputs.basic.value) || 0,
                hra: parseFloat(configInputs.hra.value) || 0,
                standard: parseFloat(configInputs.standard.value) || 0,
                bonus: parseFloat(configInputs.bonus.value) || 0,
                lta: parseFloat(configInputs.lta.value) || 0,
                fixed: parseFloat(configInputs.fixed.value) || 0
            };

            const res = await Api.post(`/payroll/structure/${empid}`, payload);

            if (res.success) {
                if (window.Components && Components.showToast) {
                    Components.showToast('Salary structure updated successfully.');
                } else {
                    alert('Salary structure updated.');
                }
                await loadEmployeeSalaryStructure();
            } else {
                if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                else alert(res.message);
            }
            
            btnSubmit.disabled = false;
        });
        
        // Process Payroll button logic
        const btnProcess = document.getElementById('btn-process-payroll');
        if (btnProcess) {
            btnProcess.onclick = async () => {
                const empid = empSelect.value;
                const now = new Date();
                const year = now.getFullYear();
                const month = now.getMonth() + 1; // current month
                
                btnProcess.disabled = true;
                const originalText = btnProcess.innerHTML;
                btnProcess.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
                
                const res = await Api.post(`/payroll/process/${empid}/${year}/${month}`);
                
                if (res.success) {
                    if (window.Components && Components.showToast) Components.showToast(`Payroll processed successfully for ${year}-${month}`);
                } else {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                    else alert(res.message);
                }
                
                btnProcess.disabled = false;
                btnProcess.innerHTML = originalText;
            };
        }

        // Pre-run
        loadEmployeeSalaryStructure();
    }
};

// Auto initialize
document.addEventListener('DOMContentLoaded', () => {
    Payroll.init();
});
