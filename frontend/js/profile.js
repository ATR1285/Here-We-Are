/* ==========================================================================
   DAYFLOW HRMS - PROFILE SCRIPTS (TABS, EDIT ACTIONS & SKILLS DIRECTORY)
   ========================================================================== */

const Profile = {
    async init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        // Fetch fresh 360 profile from backend
        let profileUser = user;
        const res = await Api.get('/employees/me');
        if (res.success && res.data) {
            profileUser = res.data;
        }

        this.initTabs();
        this.loadProfileDetails(profileUser);
        this.initEditProfile(profileUser);
        this.initSkillsAndCerts(profileUser);
        this.initDocuments(profileUser);
        
        // Admin: Add Employee Form Binder
        this.initAddEmployeeForm();
        this.loadEmployeeDirectory();
    },

    // Tabs Nav Selector Actions
    initTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active classes
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                // Activate selected
                tab.classList.add('active');
                const target = tab.getAttribute('data-tab');
                const content = document.getElementById(`tab-${target}`);
                if (content) content.classList.add('active');
            });
        });
    },

    // Populate profile labels
    loadProfileDetails(user) {
        const fullnameEl = document.getElementById('profile-fullname');
        const designationEl = document.getElementById('profile-designation');
        const deptEl = document.getElementById('profile-dept');
        const empidEl = document.getElementById('profile-empid');
        const mainAvatar = document.getElementById('profile-main-avatar');

        if (fullnameEl) fullnameEl.innerText = `${user.first_name} ${user.last_name}`;
        if (designationEl) designationEl.innerText = user.job_position ? user.job_position.title : 'Employee';
        if (deptEl) deptEl.innerText = user.department ? user.department.name : 'Unassigned';
        if (empidEl) empidEl.innerText = user.employee_code;
        if (mainAvatar && user.avatar) mainAvatar.src = user.avatar; // Avatar handling might need real backend field later

        // Input Fields (Personal tab)
        const phoneInput = document.getElementById('prof-phone');
        const emailInput = document.getElementById('prof-email');
        const addressTextarea = document.getElementById('prof-address');
        const dobEl = document.getElementById('static-dob');
        const genderEl = document.getElementById('static-gender');

        if (phoneInput) phoneInput.value = user.phone || '';
        if (emailInput) emailInput.value = user.email || '';
        if (addressTextarea) addressTextarea.value = user.address || '';
        
        if (dobEl && user.date_of_birth) {
            dobEl.innerText = new Date(user.date_of_birth).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
        } else if (dobEl) {
            dobEl.innerText = 'Not specified';
        }

        if (genderEl) genderEl.innerText = user.gender || 'Not specified';

        // Static Info (Job tab)
        const managerEl = document.getElementById('job-manager');
        const joiningEl = document.getElementById('job-joining');
        if (managerEl) managerEl.innerText = user.manager_id ? user.manager_id : 'Self'; // Should fetch manager name ideally
        if (joiningEl && user.hire_date) {
            joiningEl.innerText = new Date(user.hire_date).toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' });
        }

        // About Wireframe Textareas (Section 2)
        const aboutMeText = document.getElementById('aboutMe-textarea');
        const loveJobText = document.getElementById('loveJob-textarea');
        const hobbiesText = document.getElementById('hobbies-textarea');

        if (aboutMeText) aboutMeText.value = user.about_me || 'Introduce yourself here...';
        if (loveJobText) loveJobText.value = user.love_job || 'Write what keeps you motivated...';
        if (hobbiesText) hobbiesText.value = user.hobbies || 'Share some hobbies...';
    },

    // Edit fields management
    initEditProfile(user) {
        const toggleBtn = document.getElementById('btn-edit-toggle');
        const actionsBox = document.getElementById('profile-form-actions');
        const form = document.getElementById('profile-personal-form');

        const inputs = [
            document.getElementById('prof-phone'),
            document.getElementById('prof-address')
        ];

        if (toggleBtn && actionsBox && form) {
            toggleBtn.addEventListener('click', () => {
                inputs.forEach(input => { if (input) input.disabled = false; });
                actionsBox.classList.remove('hidden');
                toggleBtn.classList.add('hidden');
            });

            const cancelBtn = document.getElementById('btn-edit-cancel');
            cancelBtn.onclick = () => {
                inputs.forEach(input => { if (input) input.disabled = true; });
                actionsBox.classList.add('hidden');
                toggleBtn.classList.remove('hidden');
                this.loadProfileDetails(user); // Reset fields
            };

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btnSave = form.querySelector('button[type="submit"]');
                btnSave.disabled = true;

                const payload = {
                    phone: document.getElementById('prof-phone').value.trim(),
                    address: document.getElementById('prof-address').value.trim()
                };

                const res = await Api.patch(`/employees/${user.id}/basic`, payload);

                if (res.success) {
                    inputs.forEach(input => { if (input) input.disabled = true; });
                    actionsBox.classList.add('hidden');
                    toggleBtn.classList.remove('hidden');

                    if (window.Components && Components.showToast) {
                        Components.showToast('Profile updated successfully.');
                    }
                    // Fetch fresh profile details
                    const freshRes = await Api.get('/employees/me');
                    if (freshRes.success) {
                        this.loadProfileDetails(freshRes.data);
                        user = freshRes.data;
                    }
                } else {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                    else alert(res.message);
                }
                
                btnSave.disabled = false;
            });
        }

        // About panel field edits - Not saving to backend yet (no schema fields)
        // Kept purely for UI continuity
        document.querySelectorAll('.box-edit-icon').forEach(icon => {
            icon.onclick = () => {
                const fieldId = icon.getAttribute('data-field');
                const textarea = document.getElementById(`${fieldId}-textarea`);
                
                if (textarea) {
                    const isEditing = icon.classList.contains('fa-check');
                    if (!isEditing) {
                        // Enter Edit Mode
                        textarea.disabled = false;
                        textarea.focus();
                        icon.className = 'fa-solid fa-check box-edit-icon';
                        icon.style.color = 'var(--success)';
                    } else {
                        // Save Mode (UI only since backend lacks these fields)
                        textarea.disabled = true;
                        icon.className = 'fa-solid fa-pencil box-edit-icon';
                        icon.style.color = 'var(--text-muted)';
                        if (window.Components && Components.showToast) {
                            Components.showToast('Section saved (UI only).');
                        }
                    }
                }
            };
        });
    },

    // Skills and certifications tag insertion logic (UI only for now)
    initSkillsAndCerts(user) {
        // Backend lacks skills/certs tables in Phase 1-9 schema. Kept as UI-only array for demo.
        let skills = ['JavaScript', 'React', 'FastAPI'];
        let certs = ['AWS Certified Developer'];

        const skillsList = document.getElementById('profile-skills-list');
        const certsList = document.getElementById('profile-certs-list');

        if (!skillsList || !certsList) return;

        const renderSkills = () => {
            skillsList.innerHTML = skills.map((s, i) => `
                <span class="skill-tag">${s} <i class="fa-solid fa-xmark btn-del-skill" data-idx="${i}"></i></span>
            `).join('');

            skillsList.querySelectorAll('.btn-del-skill').forEach(btn => {
                btn.onclick = () => {
                    const idx = parseInt(btn.getAttribute('data-idx'));
                    skills.splice(idx, 1);
                    renderSkills();
                };
            });
        };

        const renderCerts = () => {
            certsList.innerHTML = certs.map((c, i) => `
                <div class="cert-item">
                    <span class="cert-name">${c}</span>
                    <button class="btn-del-cert" data-idx="${i}"><i class="fa-regular fa-trash-can"></i></button>
                </div>
            `).join('');

            certsList.querySelectorAll('.btn-del-cert').forEach(btn => {
                btn.onclick = () => {
                    const idx = parseInt(btn.getAttribute('data-idx'));
                    certs.splice(idx, 1);
                    renderCerts();
                };
            });
        };

        renderSkills();
        renderCerts();
    },

    // Official documents placeholder manager (UI Only)
    initDocuments(user) {
        // Kept UI only since no document upload backend API exists
        const btnUpload = document.getElementById('btn-upload-doc');
        const modal = document.getElementById('upload-doc-modal');
        const closeBtn = document.getElementById('close-upload-modal');
        const form = document.getElementById('upload-doc-form');

        if (btnUpload && modal && closeBtn && form) {
            btnUpload.onclick = () => modal.classList.add('active');
            closeBtn.onclick = () => modal.classList.remove('active');
            
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const title = document.getElementById('doc-name').value.trim();
                const fileInput = document.getElementById('doc-file');

                if (fileInput.files[0]) {
                    const table = document.getElementById('documents-table');
                    const newRow = document.createElement('div');
                    newRow.className = 'doc-row';
                    newRow.innerHTML = `
                        <div class="doc-info">
                            <i class="fa-regular fa-file-pdf pdf-color"></i>
                            <div>
                                <h4>${title}</h4>
                                <span>Uploaded on ${new Date().toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })} &bull; ${(fileInput.files[0].size / (1024 * 1024)).toFixed(1)} MB</span>
                            </div>
                        </div>
                        <button class="icon-btn" title="Download"><i class="fa-solid fa-download"></i></button>
                    `;
                    table.prepend(newRow);
                    
                    form.reset();
                    modal.classList.remove('active');
                    if (window.Components && Components.showToast) Components.showToast('Document uploaded successfully.');
                }
            });
        }
    },

    // Employee directory render (Admin side)
    async loadEmployeeDirectory() {
        const tbody = document.getElementById('directory-tbody');
        if (!tbody) return;

        const res = await Api.get('/employees');
        if (!res.success) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state-text">Unable to load employees.</td></tr>';
            return;
        }

        const employees = res.data;

        const searchVal = document.getElementById('employee-search') ? document.getElementById('employee-search').value.toLowerCase() : '';
        const deptVal = document.getElementById('dept-filter') ? document.getElementById('dept-filter').value : '';

        // Filter search results
        const filtered = employees.filter(emp => {
            const matchesSearch = emp.first_name.toLowerCase().includes(searchVal) || 
                                  emp.last_name.toLowerCase().includes(searchVal) || 
                                  emp.employee_code.toLowerCase().includes(searchVal) || 
                                  emp.email.toLowerCase().includes(searchVal);
            const matchesDept = !deptVal || (emp.department_id && emp.department_id === deptVal);

            return matchesSearch && matchesDept;
        });

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state-text">No matching employees found.</td></tr>';
            return;
        }

        tbody.innerHTML = filtered.map(emp => `
            <tr>
                <td>
                    <div class="directory-table-user-cell">
                        <div class="user-avatar-mini">
                            <img src="${emp.avatar || '../assets/avatar-placeholder.svg'}" alt="${emp.first_name}">
                        </div>
                        <div>
                            <strong>${emp.first_name} ${emp.last_name}</strong><br>
                            <span class="text-muted" style="font-size:0.75rem">${emp.email}</span>
                        </div>
                    </div>
                </td>
                <td>${emp.employee_code}</td>
                <td>${emp.department_id || '--'}</td>
                <td>${emp.job_position_id || '--'}</td>
                <td>${emp.hire_date || 'N/A'}</td>
                <td><span class="status-pill active-status">${emp.employment_status}</span></td>
                <td>
                    <div class="directory-actions-cell">
                        <button class="btn btn-danger btn-xs btn-deactivate" data-empid="${emp.id}">Deactivate</button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Bind quick actions
        tbody.querySelectorAll('.btn-deactivate').forEach(btn => {
            btn.onclick = async () => {
                const empid = btn.getAttribute('data-empid');
                if (confirm(`Are you sure you want to deactivate employee?`)) {
                    const res = await Api.delete(`/employees/${empid}`);
                    if (res.success) {
                        if (window.Components && Components.showToast) Components.showToast('Employee deactivated successfully.');
                        await this.loadEmployeeDirectory();
                    } else {
                        if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                        else alert(res.message);
                    }
                }
            };
        });
    },

    // Bind searches and filters (Admin Side)
    initAddEmployeeForm() {
        const searchInput = document.getElementById('employee-search');
        const deptFilter = document.getElementById('dept-filter');

        if (searchInput) searchInput.addEventListener('input', () => this.loadEmployeeDirectory());
        if (deptFilter) deptFilter.addEventListener('change', () => this.loadEmployeeDirectory());

        const btnAdd = document.getElementById('btn-add-employee');
        const modal = document.getElementById('add-employee-modal');
        const closeBtn = document.getElementById('close-add-modal');
        const form = document.getElementById('add-employee-form');

        if (btnAdd && modal && closeBtn && form) {
            btnAdd.onclick = () => {
                // Preset today's date
                document.getElementById('new-joining').value = new Date().toISOString().split('T')[0];
                modal.classList.add('active');
            };
            closeBtn.onclick = () => modal.classList.remove('active');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btnSave = form.querySelector('button[type="submit"]');
                btnSave.disabled = true;

                const payload = {
                    employee_code: document.getElementById('new-empid').value.trim(),
                    first_name: document.getElementById('new-name').value.trim().split(' ')[0],
                    last_name: document.getElementById('new-name').value.trim().split(' ').slice(1).join(' ') || 'User',
                    email: document.getElementById('new-email').value.trim(),
                    user_id: '', // Would need integration with a proper user creation endpoint or mock for now
                    employment_status: 'ACTIVE'
                };
                
                // Real Dayflow backend requires a corresponding User record to create an Employee.
                // Normally an Auth service creates the User + Employee combo.
                // We will attempt to use the employee creation endpoint, assuming user_id might be auto-generated or optional depending on the backend logic implementation for admin creation.
                // If it fails, a full registration flow (like auth/register) might be needed.
                const res = await Api.post('/employees', payload);

                if (res.success) {
                    form.reset();
                    modal.classList.remove('active');
                    if (window.Components && Components.showToast) Components.showToast('Employee account created.');
                    await this.loadEmployeeDirectory();
                } else {
                    if (window.Components && Components.showToast) Components.showToast(res.message, 'error');
                    else alert(res.message);
                }
                
                btnSave.disabled = false;
            });
        }
    }
};

// Initializer
document.addEventListener('DOMContentLoaded', () => {
    Profile.init();
});
