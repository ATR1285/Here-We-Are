/* ==========================================================================
   DAYFLOW HRMS - LOCAL STORAGE DATABASE & SEEDING
   ========================================================================== */

const DayflowDB = {
    // Database Keys
    USERS_KEY: 'dayflow_users',
    ATTENDANCE_KEY: 'dayflow_attendance',
    LEAVES_KEY: 'dayflow_leaves',
    PAYROLL_KEY: 'dayflow_payroll',
    NOTIFS_KEY: 'dayflow_notifications',

    // Seeding Initial Data
    init() {
        if (!localStorage.getItem(this.USERS_KEY)) {
            // Seed Users
            const users = [
                {
                    empid: 'EMP001',
                    name: 'John Doe',
                    email: 'john@dayflow.com',
                    password: 'password123',
                    role: 'employee',
                    dept: 'Engineering',
                    designation: 'Software Engineer',
                    joiningDate: '2024-01-15',
                    phone: '+1 (555) 123-4567',
                    dob: '1993-10-12',
                    gender: 'Male',
                    address: '123 Indigo Way, Tech Valley, CA 94025',
                    aboutMe: 'Passionate frontend developer who loves building slick glassmorphic user interfaces.',
                    loveJob: 'Aligning complex workflows and working with premium dark design systems.',
                    hobbies: 'Hiking, photography, playing strategy video games.',
                    skills: ['JavaScript', 'HTML5', 'CSS3', 'UI Design', 'Vite'],
                    certs: ['AWS Cloud Practitioner', 'Google UX Design Specialization']
                },
                {
                    empid: 'EMP002',
                    name: 'Sarah Connor',
                    email: 'sarah@dayflow.com',
                    password: 'password123',
                    role: 'employee',
                    dept: 'Design',
                    designation: 'UI/UX Designer',
                    joiningDate: '2024-03-01',
                    phone: '+1 (555) 987-6543',
                    dob: '1995-05-24',
                    gender: 'Female',
                    address: '456 Cyberdyne Blvd, Los Angeles, CA 90001',
                    aboutMe: 'Passionate designer trying to align every pixel beautifully.',
                    loveJob: 'Collaborating in Excalidraw and making user experiences outstanding.',
                    hobbies: 'Drawing, reading sci-fi books, yoga.',
                    skills: ['Figma', 'Excalidraw', 'Wireframing', 'Prototyping'],
                    certs: ['NN/g UX Certification']
                },
                {
                    empid: 'ADM001',
                    name: 'Priya Mehta',
                    email: 'priya@dayflow.com',
                    password: 'admin123',
                    role: 'hr',
                    dept: 'HR',
                    designation: 'HR Director',
                    joiningDate: '2023-05-10',
                    phone: '+1 (555) 555-0199',
                    dob: '1988-08-15',
                    gender: 'Female',
                    address: '789 Alignment St, San Francisco, CA 94103',
                    aboutMe: 'HR Lead dedicated to bringing employee performance and health in alignment.',
                    loveJob: 'Helping people achieve their goals and managing company structures.',
                    hobbies: 'Travel, cooking, gardening.',
                    skills: ['Talent Acquisition', 'HR Strategy', 'Conflict Resolution'],
                    certs: ['SHRM Senior Certified Professional']
                }
            ];
            localStorage.setItem(this.USERS_KEY, JSON.stringify(users));
        }

        if (!localStorage.getItem(this.ATTENDANCE_KEY)) {
            // Seed 30 days of attendance for John and Sarah (July 2026 to August 22, 2026)
            const attendance = [];
            const users = JSON.parse(localStorage.getItem(this.USERS_KEY));
            const employees = users.filter(u => u.role === 'employee');

            employees.forEach(emp => {
                // Seed July (31 days)
                for (let d = 1; d <= 31; d++) {
                    const dayString = d < 10 ? `0${d}` : d;
                    const date = `2026-07-${dayString}`;
                    const dayOfWeek = new Date(date).getDay();

                    if (dayOfWeek === 0 || dayOfWeek === 6) continue; // Skip weekends

                    // Random status
                    const rand = Math.random();
                    let status = 'present';
                    let checkIn = '09:05 AM';
                    let checkOut = '06:02 PM';
                    let hours = 8.95;

                    if (rand < 0.05) {
                        status = 'absent';
                        checkIn = '';
                        checkOut = '';
                        hours = 0;
                    } else if (rand < 0.1) {
                        status = 'half-day';
                        checkIn = '09:12 AM';
                        checkOut = '01:15 PM';
                        hours = 4.05;
                    } else if (rand < 0.15) {
                        status = 'leave';
                        checkIn = '';
                        checkOut = '';
                        hours = 0;
                    }

                    attendance.push({
                        empid: emp.empid,
                        date,
                        checkIn,
                        checkOut,
                        hours,
                        status
                    });
                }

                // Seed August (1 to 21)
                for (let d = 1; d <= 21; d++) {
                    const dayString = d < 10 ? `0${d}` : d;
                    const date = `2026-08-${dayString}`;
                    const dayOfWeek = new Date(date).getDay();

                    if (dayOfWeek === 0 || dayOfWeek === 6) continue;

                    attendance.push({
                        empid: emp.empid,
                        date,
                        checkIn: '09:02 AM',
                        checkOut: '06:05 PM',
                        hours: 9.05,
                        status: 'present'
                    });
                }
            });

            localStorage.setItem(this.ATTENDANCE_KEY, JSON.stringify(attendance));
        }

        if (!localStorage.getItem(this.LEAVES_KEY)) {
            // Seed Leave Requests
            const leaves = [
                {
                    id: 'L001',
                    empid: 'EMP001',
                    name: 'John Doe',
                    type: 'Paid',
                    start: '2026-07-10',
                    end: '2026-07-12',
                    days: 3,
                    remarks: 'Family trip alignment.',
                    status: 'Approved',
                    comments: 'Enjoy your holidays!',
                    appliedOn: '2026-07-02'
                },
                {
                    id: 'L002',
                    empid: 'EMP002',
                    name: 'Sarah Connor',
                    type: 'Sick',
                    start: '2026-07-28',
                    end: '2026-07-28',
                    days: 1,
                    remarks: 'Dental checkup override.',
                    status: 'Approved',
                    comments: 'Approved.',
                    appliedOn: '2026-07-27'
                },
                {
                    id: 'L003',
                    empid: 'EMP001',
                    name: 'John Doe',
                    type: 'Paid',
                    start: '2026-08-28',
                    end: '2026-08-30',
                    days: 3,
                    remarks: 'Attending hackathon.',
                    status: 'Pending',
                    comments: '',
                    appliedOn: '2026-08-20'
                }
            ];
            localStorage.setItem(this.LEAVES_KEY, JSON.stringify(leaves));
        }

        if (!localStorage.getItem(this.PAYROLL_KEY)) {
            // Seed Salary Component details (Annual)
            const payroll = [
                {
                    empid: 'EMP001',
                    basic: 60000,
                    hra: 24000,
                    standard: 12000,
                    bonus: 12000,
                    lta: 6000,
                    fixed: 6000
                },
                {
                    empid: 'EMP002',
                    basic: 54000,
                    hra: 21600,
                    standard: 10800,
                    bonus: 10800,
                    lta: 5400,
                    fixed: 5400
                }
            ];
            localStorage.setItem(this.PAYROLL_KEY, JSON.stringify(payroll));
        }

        if (!localStorage.getItem(this.NOTIFS_KEY)) {
            // Seed empty notification list
            localStorage.setItem(this.NOTIFS_KEY, JSON.stringify([]));
        }
    },

    // Read helper methods
    getData(key) {
        return JSON.parse(localStorage.getItem(key)) || [];
    },

    saveData(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    }
};

// Auto initialize on script load
DayflowDB.init();
