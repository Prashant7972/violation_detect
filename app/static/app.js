// Candidate Multi-Entry Video Compliance Application

// Elements: Form Inputs
const studentIdInput = document.getElementById('studentIdInput');
const studentNameInput = document.getElementById('studentNameInput');
const examIdInput = document.getElementById('examIdInput');

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileNameText = document.getElementById('fileNameText');
const fileSizeText = document.getElementById('fileSizeText');
const videoPreviewBox = document.getElementById('videoPreviewBox');
const videoPreview = document.getElementById('videoPreview');

const sampleFpsSelect = document.getElementById('sampleFpsSelect');
const maxPhoneInput = document.getElementById('maxPhoneInput');
const maxPersonsInput = document.getElementById('maxPersonsInput');
const maxMissingInput = document.getElementById('maxMissingInput');
const analyzeBtn = document.getElementById('analyzeBtn');

const statusBadge = document.getElementById('statusBadge');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const resetSystemBtn = document.getElementById('resetSystemBtn');

// Elements: Candidate Directory Table
const searchStudentId = document.getElementById('searchStudentId');
const filterStatus = document.getElementById('filterStatus');
const candidateTableBody = document.getElementById('candidateTableBody');
const refreshCandidatesBtn = document.getElementById('refreshCandidatesBtn');

// Elements: Inspection Drawer
const inspectionDrawer = document.getElementById('inspectionDrawer');
const inspectTitle = document.getElementById('inspectTitle');
const drawerBody = document.getElementById('drawerBody');
const closeDrawerBtn = document.getElementById('closeDrawerBtn');

let selectedFiles = [];

// Drag & Drop Handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFilesSelected(Array.from(e.dataTransfer.files));
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFilesSelected(Array.from(e.target.files));
    }
});

function handleFilesSelected(files) {
    const validFiles = files.filter(f => f.type.startsWith('video/') || f.name.match(/\.(mp4|webm|avi|mov)$/i));
    if (validFiles.length === 0) {
        alert('Please select valid video file(s) (.mp4, .webm, .avi, .mov)');
        return;
    }

    selectedFiles = validFiles;
    if (validFiles.length === 1) {
        const file = validFiles[0];
        fileNameText.textContent = file.name;
        fileSizeText.textContent = formatBytes(file.size);
        fileInfo.style.display = 'flex';

        const videoUrl = URL.createObjectURL(file);
        videoPreview.src = videoUrl;
        videoPreviewBox.style.display = 'block';
    } else {
        fileNameText.textContent = `${validFiles.length} Video Clips Selected`;
        fileSizeText.textContent = formatBytes(validFiles.reduce((acc, f) => acc + f.size, 0));
        fileInfo.style.display = 'flex';
        videoPreviewBox.style.display = 'none';
    }

    analyzeBtn.disabled = false;
    statusBadge.textContent = `${validFiles.length} File(s) Loaded`;
    statusBadge.className = 'status-badge stopped';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Fetch Next Serial Student ID (STU-001, STU-002, ...)
async function fetchNextSerialStudentId() {
    try {
        const res = await fetch('/api/v1/system/next-student-id');
        if (res.ok) {
            const data = await res.json();
            studentIdInput.placeholder = `Auto-assigned (${data.next_student_id})`;
        }
    } catch (e) {
        console.error('Error fetching next serial student ID:', e);
    }
}

// Execute Candidate Video Submission
analyzeBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) return;

    const studentId = studentIdInput.value.trim();
    const studentName = studentNameInput.value.trim();
    const examId = examIdInput.value.trim();
    const sampleFps = parseFloat(sampleFpsSelect.value) || 1.0;
    const maxPhone = parseFloat(maxPhoneInput.value) ?? 0.0;
    const maxPersons = parseFloat(maxPersonsInput.value) ?? 0.0;
    const maxMissing = parseFloat(maxMissingInput.value) ?? 5.0;

    loadingOverlay.style.display = 'flex';
    analyzeBtn.disabled = true;

    try {
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            loadingText.textContent = `Analyzing Clip [${i+1}/${selectedFiles.length}]: ${file.name}...`;

            const formData = new FormData();
            formData.append('file', file);
            if (studentId) formData.append('student_id', studentId);
            if (studentName) formData.append('student_name', studentName);
            if (examId) formData.append('exam_id', examId);

            const url = `/api/v1/videos/process?sample_fps=${sampleFps}&max_phone_limit=${maxPhone}&max_multiple_persons_limit=${maxPersons}&max_missing_limit=${maxMissing}`;

            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Analysis failed for file ${file.name}`);
            }
        }

        statusBadge.textContent = 'Submissions Processed';
        statusBadge.className = 'status-badge passed';
        
        // Clear inputs & update directory
        studentIdInput.value = '';
        await fetchNextSerialStudentId();
        await loadCandidateDirectory();

    } catch (err) {
        alert(`Error processing candidate submission: ${err.message}`);
        console.error(err);
        statusBadge.textContent = 'Processing Error';
        statusBadge.className = 'status-badge failed';
    } finally {
        loadingOverlay.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

// System Reset Handler
resetSystemBtn.addEventListener('click', async () => {
    const confirmReset = confirm(
        '⚠️ ARE YOU SURE YOU WANT TO RESET ALL SYSTEM DATA?\n\n' +
        'This will purge all database records, delete extracted evidence files from disk, and reset the serial Student ID counter back to STU-001.'
    );

    if (!confirmReset) return;

    loadingOverlay.style.display = 'flex';
    loadingText.textContent = 'Resetting Database Records & Storage Files...';

    try {
        const response = await fetch('/api/v1/system/reset', { method: 'POST' });
        if (!response.ok) throw new Error('Reset request failed');

        const data = await response.json();
        alert(`✅ System Reset Complete: ${data.message}`);

        studentIdInput.value = '';
        inspectionDrawer.style.display = 'none';

        await fetchNextSerialStudentId();
        await loadCandidateDirectory();

    } catch (err) {
        alert(`Error resetting system data: ${err.message}`);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

// Candidate Directory Table Loading & Search Filter
refreshCandidatesBtn.addEventListener('click', loadCandidateDirectory);
searchStudentId.addEventListener('input', loadCandidateDirectory);
filterStatus.addEventListener('change', loadCandidateDirectory);

async function loadCandidateDirectory() {
    const sId = searchStudentId.value.trim();
    const statusFilter = filterStatus.value;

    let url = '/api/v1/candidates?';
    if (sId) url += `student_id=${encodeURIComponent(sId)}&`;
    if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch candidate directory');
        
        const data = await response.json();
        renderCandidateTable(data.submissions);
    } catch (err) {
        console.error(err);
    }
}

function renderCandidateTable(submissions) {
    candidateTableBody.innerHTML = '';

    if (!submissions || submissions.length === 0) {
        candidateTableBody.innerHTML = '<tr><td colspan="6" class="empty-table-cell">No candidate submissions recorded. Upload a video on the left to start.</td></tr>';
        return;
    }

    submissions.forEach(sub => {
        const tr = document.createElement('tr');
        
        const statusBadgeClass = sub.overall_status === 'PASSED' ? 'badge-passed' : 'badge-failed';
        const statusIcon = sub.overall_status === 'PASSED' ? 'PASSED ✅' : 'FAILED ❌';
        
        const dateStr = new Date(sub.created_at).toLocaleString();

        tr.innerHTML = `
            <td>
                <strong>${sub.student_id}</strong><br>
                <small style="color: #94a3b8;">${sub.student_name || 'N/A'}</small>
            </td>
            <td>${sub.exam_id || 'GENERAL'}</td>
            <td>
                <span>${sub.video_filename}</span><br>
                <small style="color: #64748b;">${sub.video_duration_seconds}s (${dateStr})</small>
            </td>
            <td><strong style="color: ${sub.phone_duration_seconds > 0 ? '#ef4444' : '#10b981'};">${sub.phone_duration_seconds}s</strong></td>
            <td><span class="badge ${statusBadgeClass}">${statusIcon}</span></td>
            <td>
                <button class="btn btn-secondary" onclick="inspectCandidateReport('${sub.submission_id}')">Inspect Report</button>
            </td>
        `;
        candidateTableBody.appendChild(tr);
    });
}

// Candidate Inspection Drawer
async function inspectCandidateReport(submissionId) {
    loadingOverlay.style.display = 'flex';
    loadingText.textContent = 'Loading Candidate Report Details...';

    try {
        const response = await fetch(`/api/v1/submissions/${submissionId}`);
        if (!response.ok) throw new Error('Could not load submission report');

        const report = await response.json();
        
        inspectTitle.textContent = `Candidate Report: ${report.candidate_info?.student_id || 'STU'} (${report.overall_status})`;

        let intervalsHtml = '';
        if (!report.violation_intervals || report.violation_intervals.length === 0) {
            intervalsHtml = '<div class="empty-state"><p>No compliance violations recorded for this video clip.</p></div>';
        } else {
            report.violation_intervals.forEach(inv => {
                let imgUrl = inv.evidence_file;
                if (imgUrl && imgUrl.includes('/evidence/')) {
                    imgUrl = '/evidence/' + imgUrl.split('/evidence/')[1];
                }

                const imgHtml = imgUrl 
                    ? `<a href="${imgUrl}" target="_blank"><img src="${imgUrl}" class="evidence-preview-img" alt="Keyframe Evidence" title="Click to open annotated evidence image"/></a>`
                    : '';

                intervalsHtml += `
                    <div class="interval-card ${inv.event_type.includes('PHONE') ? 'phone' : ''}">
                        <div class="interval-details">
                            <span class="interval-type">⚠️ ${inv.event_type} (${(inv.peak_confidence * 100).toFixed(0)}%)</span>
                            <span class="interval-times">⏱️ ${inv.start_timestamp} ➔ ${inv.end_timestamp}</span>
                            <span class="interval-dur">Duration: <strong>${inv.duration_seconds}s</strong></span>
                        </div>
                        ${imgHtml}
                    </div>
                `;
            });
        }

        drawerBody.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-box">
                    <span class="m-label">Student ID</span>
                    <span class="m-val">${report.candidate_info?.student_id}</span>
                </div>
                <div class="metric-box">
                    <span class="m-label">Candidate Name</span>
                    <span class="m-val">${report.candidate_info?.student_name || 'N/A'}</span>
                </div>
                <div class="metric-box">
                    <span class="m-label">Overall Status</span>
                    <span class="m-val ${report.overall_limit_exceeded ? 'alert-text' : ''}">${report.overall_status}</span>
                </div>
            </div>

            <div class="limit-section">
                <h3>Cumulative Violation Durations</h3>
                <div class="limit-list">
                    <div class="limit-item ${report.limit_enforcement?.PHONE_DETECTED?.limit_exceeded ? 'exceeded' : ''}">
                        <div class="limit-info">
                            <span class="limit-title">PHONE_DETECTED</span>
                            <span class="limit-dur">Duration: ${report.cumulative_durations?.PHONE_DETECTED || 0}s (Limit: ${report.limit_enforcement?.PHONE_DETECTED?.limit_threshold_seconds || 0}s)</span>
                        </div>
                    </div>
                    <div class="limit-item ${report.limit_enforcement?.MULTIPLE_PERSONS?.limit_exceeded ? 'exceeded' : ''}">
                        <div class="limit-info">
                            <span class="limit-title">MULTIPLE_PERSONS</span>
                            <span class="limit-dur">Duration: ${report.cumulative_durations?.MULTIPLE_PERSONS || 0}s (Limit: ${report.limit_enforcement?.MULTIPLE_PERSONS?.limit_threshold_seconds || 0}s)</span>
                        </div>
                    </div>
                    <div class="limit-item ${report.limit_enforcement?.NO_PERSON_DETECTED?.limit_exceeded ? 'exceeded' : ''}">
                        <div class="limit-info">
                            <span class="limit-title">NO_PERSON_DETECTED</span>
                            <span class="limit-dur">Duration: ${report.cumulative_durations?.NO_PERSON_DETECTED || 0}s (Limit: ${report.limit_enforcement?.NO_PERSON_DETECTED?.limit_threshold_seconds || 5.0}s)</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="intervals-section">
                <h3>Violation Timeline & Keyframe Evidence</h3>
                <div class="intervals-list">${intervalsHtml}</div>
            </div>
        `;

        inspectionDrawer.style.display = 'flex';

    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

closeDrawerBtn.addEventListener('click', () => {
    inspectionDrawer.style.display = 'none';
});

// Initial Load
window.addEventListener('DOMContentLoaded', () => {
    fetchNextSerialStudentId();
    loadCandidateDirectory();
});
