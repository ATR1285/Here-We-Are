/* ==========================================================================
   DAYFLOW HRMS - PAYROLL MANAGER (CALCULATORS, PAYSLIPS & CONFIGURATIONS)
   ========================================================================== */

const Payroll = {
    init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        this.initEmployeePayroll(user.empid);
        this.initAdminPayroll();
    },

    // Employee specific pay summaries & slip selectors
    initEmployeePayroll(empid) {
        const selectPeriod = document.getElementById('payroll-month-select');
        if (!selectPeriod) return; // Not employee payroll page

        const renderPeriodPay = () => {
            const period = selectPeriod.value;
            const labelPeriod = document.getElementById('pay-period-lbl');
            if (labelPeriod) labelPeriod.innerText = selectPeriod.options[selectPeriod.selectedIndex].text;

            const payrolls = DayflowDB.getData(DayflowDB.PAYROLL_KEY);
            const structure = payrolls.find(p => p.empid === empid);

            if (!structure) {
                this.updateComponentsDisplay(0, 0, 0, 0, 0, 0);
                return;
            }

            // Calculations based on seeded components (Annual -> Monthly)
            const basic = structure.basic / 12;
            const hra = structure.hra / 12;
            const standard = structure.standard / 12;
            const bonus = structure.bonus / 12;
            const lta = structure.lta / 12;
            const fixed = structure.fixed / 12;

            this.updateComponentsDisplay(basic, hra, standard, bonus, lta, fixed);
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
    updateComponentsDisplay(basic, hra, standard, bonus, lta, fixed) {
        const gross = basic + hra + standard + bonus + lta + fixed;
        // Calculations for Deductions: Est Tax (10% of gross) + PF (6% of basic)
        const tds = gross * 0.1;
        const pf = basic * 0.06;
        const net = gross - (tds + pf);

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
        if (deductionsEl) deductionsEl.innerText = '-' + this.formatCurrency(tds + pf);
        if (tdsEl) tdsEl.innerText = '-' + this.formatCurrency(tds);
        if (pfEl) pfEl.innerText = '-' + this.formatCurrency(pf);
        if (netEl) netEl.innerText = this.formatCurrency(net);
    },

    // Format utility
    formatCurrency(val) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
    },

    // Admin salary configs controls panel
    initAdminPayroll() {
        const empSelect = document.getElementById('payroll-employee-select');
        if (!empSelect) return; // Not admin payroll page

        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
        const employees = users.filter(u => u.role === 'employee');

        // Populate dropdown
        empSelect.innerHTML = employees.map(emp => `<option value="${emp.empid}">${emp.name} (${emp.empid})</option>`).join('');

        const form = document.getElementById('salary-structure-form');
        const configInputs = {
            basic: document.getElementById('cfg-basic'),
            hra: document.getElementById('cfg-hra'),
            standard: document.getElementById('cfg-standard'),
            bonus: document.getElementById('cfg-bonus'),
            lta: document.getElementById('cfg-lta'),
            fixed: document.getElementById('cfg-fixed')
        };

        const loadEmployeeSalaryStructure = () => {
            const empid = empSelect.value;
            const payrolls = DayflowDB.getData(DayflowDB.PAYROLL_KEY);
            let structure = payrolls.find(p => p.empid === empid);

            if (!structure) {
                // Seed a default one if not existing
                structure = {
                    empid,
                    basic: 50000,
                    hra: 20000,
                    standard: 10000,
                    bonus: 10000,
                    lta: 5000,
                    fixed: 5000
                };
                payrolls.push(structure);
                DayflowDB.saveData(DayflowDB.PAYROLL_KEY, payrolls);
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
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const empid = empSelect.value;
            const payrolls = DayflowDB.getData(DayflowDB.PAYROLL_KEY);
            const idx = payrolls.findIndex(p => p.empid === empid);

            if (idx !== -1) {
                payrolls[idx].basic = parseFloat(configInputs.basic.value) || 0;
                payrolls[idx].hra = parseFloat(configInputs.hra.value) || 0;
                payrolls[idx].standard = parseFloat(configInputs.standard.value) || 0;
                payrolls[idx].bonus = parseFloat(configInputs.bonus.value) || 0;
                payrolls[idx].lta = parseFloat(configInputs.lta.value) || 0;
                payrolls[idx].fixed = parseFloat(configInputs.fixed.value) || 0;

                DayflowDB.saveData(DayflowDB.PAYROLL_KEY, payrolls);

                // Add alert notification
                if (window.Components && Components.addNotification) {
                    Components.addNotification(
                        empid,
                        `Your salary structure components have been updated by Admin.`,
                        'fa-file-invoice-dollar'
                    );
                }

                if (window.Components && Components.showToast) {
                    Components.showToast('Salary structure updated successfully.');
                } else {
                    alert('Salary structure updated.');
                }
                loadEmployeeSalaryStructure();
            }
        });

        // Pre-run
        loadEmployeeSalaryStructure();
    }
};

// Auto initialize
document.addEventListener('DOMContentLoaded', () => {
    Payroll.init();
});
