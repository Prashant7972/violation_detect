// AI Video File Analysis & Compliance Client Application

// DOM Elements: Video File Upload
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileNameText = document.getElementById('fileNameText');
const fileSizeText = document.getElementById('fileSizeText');
const videoPreviewBox = document.getElementById('videoPreviewBox');
const videoPreview = document.getElementById('videoPreview');

const sampleFpsSelect = document.getElementById('sampleFpsSelect');
const maxPhoneInput = document.getElementById('maxPhoneInput');
const maxMissingInput = document.getElementById('maxMissingInput');
const analyzeBtn = document.getElementById('analyzeBtn');

const statusBadge = document.getElementById('statusBadge');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultsContainer = document.getElementById('resultsContainer');
const overallResultBadge = document.getElementById('overallResultBadge');

const metricsGrid = document.getElementById('metricsGrid');
const metaDuration = document.getElementById('metaDuration');
const metaSampledFrames = document.getElementById('metaSampledFrames');
const metaIntervalsCount = document.getElementById('metaIntervalsCount');

const limitSection = document.getElementById('limitSection');
const limitList = document.getElementById('limitList');
const intervalsSection = document.getElementById('intervalsSection');
const intervalsList = document.getElementById('intervalsList');

let selectedFile = null;

// Drag and Drop Event Listeners
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
        handleFileSelected(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
    }
});

function handleFileSelected(file) {
    if (!file.type.startsWith('video/') && !file.name.match(/\.(mp4|webm|avi|mov)$/i)) {
        alert('Please select a valid video file (.mp4, .webm, .avi, .mov)');
        return;
    }

    selectedFile = file;
    fileNameText.textContent = file.name;
    fileSizeText.textContent = formatBytes(file.size);
    fileInfo.style.display = 'flex';

    // Set video preview stream
    const videoUrl = URL.createObjectURL(file);
    videoPreview.src = videoUrl;
    videoPreviewBox.style.display = 'block';

    analyzeBtn.disabled = false;
    statusBadge.textContent = 'File Loaded';
    statusBadge.className = 'status-badge stopped';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Execute Video Analysis API Call
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    loadingOverlay.style.display = 'flex';
    analyzeBtn.disabled = true;
    statusBadge.textContent = 'Analyzing Video...';
    statusBadge.className = 'status-badge stopped';

    const formData = new FormData();
    formData.append('file', selectedFile);

    const sampleFps = parseFloat(sampleFpsSelect.value) || 1.0;
    const maxPhone = parseFloat(maxPhoneInput.value) || 5.0;
    const maxMissing = parseFloat(maxMissingInput.value) || 10.0;

    const url = `/api/v1/videos/process?sample_fps=${sampleFps}&max_phone_limit=${maxPhone}&max_missing_limit=${maxMissing}`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Video analysis failed');
        }

        const report = await response.json();
        renderAnalysisReport(report);

    } catch (err) {
        alert(`Error analyzing video file: ${err.message}`);
        console.error(err);
        statusBadge.textContent = 'Analysis Error';
        statusBadge.className = 'status-badge failed';
    } finally {
        loadingOverlay.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

function renderAnalysisReport(report) {
    const isExceeded = report.overall_limit_exceeded;
    
    // Overall Status
    if (isExceeded) {
        statusBadge.textContent = 'LIMIT EXCEEDED (FAILED)';
        statusBadge.className = 'status-badge failed';
        overallResultBadge.textContent = 'FAILED ❌';
        overallResultBadge.className = 'badge bg-danger';
    } else {
        statusBadge.textContent = 'COMPLIANCE PASSED';
        statusBadge.className = 'status-badge passed';
        overallResultBadge.textContent = 'PASSED ✅';
        overallResultBadge.className = 'badge bg-success';
    }

    // Video Metadata Metrics
    metaDuration.textContent = report.video_metadata.duration_formatted;
    metaSampledFrames.textContent = report.analysis_settings.sampled_frames_processed;
    metaIntervalsCount.textContent = report.total_violation_intervals_count;

    metricsGrid.style.display = 'grid';

    // Limit Breakdown
    limitList.innerHTML = '';
    for (const [evType, info] of Object.entries(report.limit_enforcement)) {
        const item = document.createElement('div');
        item.className = `limit-item ${info.limit_exceeded ? 'exceeded' : ''}`;
        
        const statusText = info.limit_exceeded ? 'EXCEEDED ❌' : 'OK ✅';
        item.innerHTML = `
            <div class="limit-info">
                <span class="limit-title">${evType}</span>
                <span class="limit-dur">Duration: ${info.cumulative_duration_seconds}s / Limit: ${info.limit_threshold_seconds}s</span>
            </div>
            <span class="badge">${statusText}</span>
        `;
        limitList.appendChild(item);
    }
    limitSection.style.display = 'flex';

    // Violation Intervals List
    intervalsList.innerHTML = '';
    if (report.violation_intervals.length === 0) {
        intervalsList.innerHTML = '<div class="empty-state"><p>No compliance violations detected in this video clip.</p></div>';
    } else {
        report.violation_intervals.forEach(interval => {
            const item = document.createElement('div');
            item.className = `interval-card ${interval.event_type.includes('PHONE') ? 'phone' : ''}`;
            
            let imgUrl = interval.evidence_file;
            if (imgUrl && imgUrl.includes('/evidence/')) {
                imgUrl = '/evidence/' + imgUrl.split('/evidence/')[1];
            }

            const imgHtml = imgUrl 
                ? `<a href="${imgUrl}" target="_blank"><img src="${imgUrl}" class="evidence-preview-img" alt="Keyframe Evidence" title="Click to view annotated evidence image"/></a>`
                : '';

            item.innerHTML = `
                <div class="interval-details">
                    <span class="interval-type">⚠️ ${interval.event_type} (${(interval.peak_confidence * 100).toFixed(0)}%)</span>
                    <span class="interval-times">⏱️ ${interval.start_timestamp} ➔ ${interval.end_timestamp}</span>
                    <span class="interval-dur">Interval Duration: <strong>${interval.duration_seconds}s</strong></span>
                </div>
                ${imgHtml}
            `;
            intervalsList.appendChild(item);
        });
    }
    intervalsSection.style.display = 'flex';

    // Scroll results smoothly
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}
