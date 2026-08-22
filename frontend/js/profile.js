/* ==========================================================================
   DAYFLOW HRMS - PROFILE SCRIPTS (TABS, EDIT ACTIONS & SKILLS DIRECTORY)
   ========================================================================== */

const Profile = {
    init() {
        const user = Auth.getCurrentUser();
        if (!user) return;

        this.initTabs();
        this.loadProfileDetails(user);
        this.initEditProfile(user);
        this.initSkillsAndCerts(user);
        this.initDocuments(user);
        
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

        if (fullnameEl) fullnameEl.innerText = user.name;
        if (designationEl) designationEl.innerText = user.designation;
        if (deptEl) deptEl.innerText = user.dept;
        if (empidEl) empidEl.innerText = user.empid;
        if (mainAvatar && user.avatar) mainAvatar.src = user.avatar;

        // Input Fields (Personal tab)
        const phoneInput = document.getElementById('prof-phone');
        const emailInput = document.getElementById('prof-email');
        const addressTextarea = document.getElementById('prof-address');
        const dobEl = document.getElementById('static-dob');
        const genderEl = document.getElementById('static-gender');

        if (phoneInput) phoneInput.value = user.phone || '';
        if (emailInput) emailInput.value = user.email || '';
        if (addressTextarea) addressTextarea.value = user.address || '';
        
        if (dobEl && user.dob) {
            dobEl.innerText = new Date(user.dob).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
        }
        if (genderEl) genderEl.innerText = user.gender || 'Not specified';

        // Static Info (Job tab)
        const managerEl = document.getElementById('job-manager');
        const joiningEl = document.getElementById('job-joining');
        if (managerEl) managerEl.innerText = user.role === 'hr' ? 'Board of Directors' : 'Priya Mehta (HR Director)';
        if (joiningEl && user.joiningDate) {
            joiningEl.innerText = new Date(user.joiningDate).toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' });
        }

        // About Wireframe Textareas (Section 2)
        const aboutMeText = document.getElementById('aboutMe-textarea');
        const loveJobText = document.getElementById('loveJob-textarea');
        const hobbiesText = document.getElementById('hobbies-textarea');

        if (aboutMeText) aboutMeText.value = user.aboutMe || 'Introduce yourself here...';
        if (loveJobText) loveJobText.value = user.loveJob || 'Write what keeps you motivated...';
        if (hobbiesText) hobbiesText.value = user.hobbies || 'Share some hobbies...';
    },

    // Edit fields management
    initEditProfile(user) {
        const toggleBtn = document.getElementById('btn-edit-toggle');
        const actionsBox = document.getElementById('profile-form-actions');
        const form = document.getElementById('profile-personal-form');

        const inputs = [
            document.getElementById('prof-phone'),
            document.getElementById('prof-email'),
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

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                const idx = users.findIndex(u => u.empid === user.empid);

                if (idx !== -1) {
                    users[idx].phone = document.getElementById('prof-phone').value.trim();
                    users[idx].email = document.getElementById('prof-email').value.trim();
                    users[idx].address = document.getElementById('prof-address').value.trim();

                    DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                    
                    // Update session
                    sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[idx]));

                    inputs.forEach(input => { if (input) input.disabled = true; });
                    actionsBox.classList.add('hidden');
                    toggleBtn.classList.remove('hidden');

                    if (window.Components && Components.showToast) {
                        Components.showToast('Profile updated successfully.');
                    }
                    this.loadProfileDetails(users[idx]);
                }
            });
        }

        // About panel field edits (Section 2 Excalidraw)
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
                        // Save Mode
                        const val = textarea.value.trim();
                        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                        const idx = users.findIndex(u => u.empid === user.empid);

                        if (idx !== -1) {
                            users[idx][fieldId] = val;
                            DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                            sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[idx]));
                        }

                        textarea.disabled = true;
                        icon.className = 'fa-solid fa-pencil box-edit-icon';
                        icon.style.color = 'var(--text-muted)';
                        if (window.Components && Components.showToast) {
                            Components.showToast('Section saved.');
                        }
                    }
                }
            };
        });

        // Photo Upload simulation
        const avatarUpload = document.getElementById('avatar-upload');
        if (avatarUpload) {
            avatarUpload.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const base64 = event.target.result;
                        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                        const idx = users.findIndex(u => u.empid === user.empid);

                        if (idx !== -1) {
                            users[idx].avatar = base64;
                            DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                            sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[idx]));
                            
                            // Re-populate avatars
                            const mainAvatar = document.getElementById('profile-main-avatar');
                            if (mainAvatar) mainAvatar.src = base64;

                            const sidebarAvatar = document.getElementById('sidebar-avatar-img');
                            const topbarAvatar = document.getElementById('topbar-avatar-img');
                            if (sidebarAvatar) sidebarAvatar.src = base64;
                            if (topbarAvatar) topbarAvatar.src = base64;

                            if (window.Components && Components.showToast) {
                                Components.showToast('Profile photo updated.');
                            }
                        }
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
    },

    // Skills and certifications tag insertion logic
    initSkillsAndCerts(user) {
        const skillsList = document.getElementById('profile-skills-list');
        const certsList = document.getElementById('profile-certs-list');

        if (!skillsList || !certsList) return;

        const renderSkills = () => {
            const freshUser = Auth.getCurrentUser();
            const skills = freshUser.skills || [];
            skillsList.innerHTML = skills.map((s, i) => `
                <span class="skill-tag">${s} <i class="fa-solid fa-xmark btn-del-skill" data-idx="${i}"></i></span>
            `).join('');

            skillsList.querySelectorAll('.btn-del-skill').forEach(btn => {
                btn.onclick = () => {
                    const idx = parseInt(btn.getAttribute('data-idx'));
                    const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                    const userIdx = users.findIndex(u => u.empid === freshUser.empid);
                    
                    if (userIdx !== -1) {
                        users[userIdx].skills.splice(idx, 1);
                        DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                        sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[userIdx]));
                        renderSkills();
                    }
                };
            });
        };

        const renderCerts = () => {
            const freshUser = Auth.getCurrentUser();
            const certs = freshUser.certs || [];
            certsList.innerHTML = certs.map((c, i) => `
                <div class="cert-item">
                    <span class="cert-name">${c}</span>
                    <button class="btn-del-cert" data-idx="${i}"><i class="fa-regular fa-trash-can"></i></button>
                </div>
            `).join('');

            certsList.querySelectorAll('.btn-del-cert').forEach(btn => {
                btn.onclick = () => {
                    const idx = parseInt(btn.getAttribute('data-idx'));
                    const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                    const userIdx = users.findIndex(u => u.empid === freshUser.empid);
                    
                    if (userIdx !== -1) {
                        users[userIdx].certs.splice(idx, 1);
                        DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                        sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[userIdx]));
                        renderCerts();
                    }
                };
            });
        };

        renderSkills();
        renderCerts();

        // Skill Toggle add form
        const btnAddSkill = document.getElementById('btn-add-skill');
        const formSkill = document.getElementById('skill-form');
        const inputSkill = document.getElementById('skill-input');
        const btnSaveSkill = document.getElementById('btn-save-skill');

        if (btnAddSkill && formSkill && inputSkill && btnSaveSkill) {
            btnAddSkill.onclick = () => formSkill.classList.toggle('hidden');
            btnSaveSkill.onclick = () => {
                const val = inputSkill.value.trim();
                if (!val) return;
                
                const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                const idx = users.findIndex(u => u.empid === user.empid);
                if (idx !== -1) {
                    if (!users[idx].skills) users[idx].skills = [];
                    users[idx].skills.push(val);
                    DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                    sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[idx]));
                    
                    inputSkill.value = '';
                    formSkill.classList.add('hidden');
                    renderSkills();
                    if (window.Components && Components.showToast) Components.showToast('Skill added.');
                }
            };
        }

        // Cert Toggle Add form
        const btnAddCert = document.getElementById('btn-add-cert');
        const formCert = document.getElementById('cert-form');
        const inputCert = document.getElementById('cert-input');
        const btnSaveCert = document.getElementById('btn-save-cert');

        if (btnAddCert && formCert && inputCert && btnSaveCert) {
            btnAddCert.onclick = () => formCert.classList.toggle('hidden');
            btnSaveCert.onclick = () => {
                const val = inputCert.value.trim();
                if (!val) return;

                const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                const idx = users.findIndex(u => u.empid === user.empid);
                if (idx !== -1) {
                    if (!users[idx].certs) users[idx].certs = [];
                    users[idx].certs.push(val);
                    DayflowDB.saveData(DayflowDB.USERS_KEY, users);
                    sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(users[idx]));

                    inputCert.value = '';
                    formCert.classList.add('hidden');
                    renderCerts();
                    if (window.Components && Components.showToast) Components.showToast('Certification added.');
                }
            };
        }
    },

    // Official documents placeholder manager
    initDocuments(user) {
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
    loadEmployeeDirectory() {
        const tbody = document.getElementById('directory-tbody');
        if (!tbody) return;

        const users = DayflowDB.getData(DayflowDB.USERS_KEY);
        const employees = users.filter(u => u.role === 'employee');

        const searchVal = document.getElementById('employee-search') ? document.getElementById('employee-search').value.toLowerCase() : '';
        const deptVal = document.getElementById('dept-filter') ? document.getElementById('dept-filter').value : '';

        // Filter search results
        const filtered = employees.filter(emp => {
            const matchesSearch = emp.name.toLowerCase().includes(searchVal) || 
                                  emp.empid.toLowerCase().includes(searchVal) || 
                                  emp.email.toLowerCase().includes(searchVal);
            const matchesDept = !deptVal || emp.dept === deptVal;

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
                            <img src="${emp.avatar || '../assets/avatar-placeholder.svg'}" alt="${emp.name}">
                        </div>
                        <div>
                            <strong>${emp.name}</strong><br>
                            <span class="text-muted" style="font-size:0.75rem">${emp.email}</span>
                        </div>
                    </div>
                </td>
                <td>${emp.empid}</td>
                <td>${emp.dept}</td>
                <td>${emp.designation}</td>
                <td>${emp.joiningDate || 'N/A'}</td>
                <td><span class="status-pill active-status">Active</span></td>
                <td>
                    <div class="directory-actions-cell">
                        <button class="btn btn-secondary btn-xs btn-switch-dir" data-empid="${emp.empid}">Switch View</button>
                        <button class="btn btn-danger btn-xs btn-deactivate" data-empid="${emp.empid}">Deactivate</button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Bind quick actions
        tbody.querySelectorAll('.btn-switch-dir').forEach(btn => {
            btn.onclick = () => {
                const empid = btn.getAttribute('data-empid');
                const selectedEmp = employees.find(emp => emp.empid === empid);
                if (selectedEmp) {
                    sessionStorage.setItem(Auth.SESSION_USER_KEY, JSON.stringify(selectedEmp));
                    window.location.href = '../employee/dashboard.html';
                }
            };
        });

        tbody.querySelectorAll('.btn-deactivate').forEach(btn => {
            btn.onclick = () => {
                const empid = btn.getAttribute('data-empid');
                if (confirm(`Are you sure you want to deactivate employee ${empid}?`)) {
                    const freshUsers = users.filter(u => u.empid !== empid);
                    DayflowDB.saveData(DayflowDB.USERS_KEY, freshUsers);
                    if (window.Components && Components.showToast) Components.showToast('Employee deactivated successfully.');
                    this.loadEmployeeDirectory();
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

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const empid = document.getElementById('new-empid').value.trim();
                const name = document.getElementById('new-name').value.trim();
                const email = document.getElementById('new-email').value.trim();
                const role = document.getElementById('new-role').value;
                const dept = document.getElementById('new-dept').value;
                const designation = document.getElementById('new-designation').value.trim();
                const joining = document.getElementById('new-joining').value;
                const salary = parseFloat(document.getElementById('new-salary').value);

                const users = DayflowDB.getData(DayflowDB.USERS_KEY);
                if (users.some(u => u.empid.toLowerCase() === empid.toLowerCase())) {
                    alert('Employee ID already exists.');
                    return;
                }

                const newUser = {
                    empid,
                    name,
                    email,
                    password: 'password123', // Default hackathon pass
                    role,
                    dept,
                    designation,
                    joiningDate: joining,
                    phone: '',
                    dob: '',
                    gender: '',
                    address: '',
                    aboutMe: '',
                    loveJob: '',
                    hobbies: '',
                    skills: [],
                    certs: []
                };

                users.push(newUser);
                DayflowDB.saveData(DayflowDB.USERS_KEY, users);

                // Configure starting salary structure components (seeding total)
                const payrolls = DayflowDB.getData(DayflowDB.PAYROLL_KEY);
                payrolls.push({
                    empid,
                    basic: salary * 0.5,
                    hra: salary * 0.2,
                    standard: salary * 0.1,
                    bonus: salary * 0.1,
                    lta: salary * 0.05,
                    fixed: salary * 0.05
                });
                DayflowDB.saveData(DayflowDB.PAYROLL_KEY, payrolls);

                form.reset();
                modal.classList.remove('active');
                if (window.Components && Components.showToast) Components.showToast('Employee account created.');
                this.loadEmployeeDirectory();
            });
        }
    }
};

// Initializer
document.addEventListener('DOMContentLoaded', () => {
    Profile.init();
});
