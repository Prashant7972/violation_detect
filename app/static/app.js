// ==============================================================================
// AI Online Examination & Proctoring Portal - Core Frontend Engine
// Supports Live Webcam Selfie, Password Authentication, Hardware Check & Continuous Proctoring
// ==============================================================================

let activeSessionToken = null;
let currentUsername = 'STU-001';
let docIdB64 = null;
let selfieB64 = null;
let webcamStream = null;
let micAudioStream = null;
let selectedFiles = [];
let lastIssuedPassword = '';
let currentExamQIdx = 0;
let examTimerInterval = null;
let examTimerSeconds = 45 * 60;
let examAnswers = {};
let examReviewFlags = [false, false, false, false, false];
let lastFaceMatchPct = '93.8%';

// DOM Elements - Navigation & Views
const onboardingModal = document.getElementById('onboardingModal');
const reopenOnboardingBtn = document.getElementById('reopenOnboardingBtn');
const resetSystemBtn = document.getElementById('resetSystemBtn');
const stepTag = document.getElementById('stepTag');
const statusBadge = document.getElementById('statusBadge');
const liveHardwareBadges = document.getElementById('liveHardwareBadges');
const navSectionBreadcrumb = document.getElementById('navSectionBreadcrumb');

const dashboardContent = document.getElementById('dashboardContent');
const examDeviceContainer = document.getElementById('examDeviceContainer');
const viewExamPortalBtn = document.getElementById('viewExamPortalBtn');
const viewExaminerDashBtn = document.getElementById('viewExaminerDashBtn');
const examSwitchToExaminerBtn = document.getElementById('examSwitchToExaminerBtn');
const navExamDeviceBtn = document.getElementById('navExamDeviceBtn');
const navExaminerBtn = document.getElementById('navExaminerBtn');

// Exam Device CBT Elements
const examCandidateName = document.getElementById('examCandidateName');
const examDeviceBadge = document.getElementById('examDeviceBadge');
const examFaceScoreBadge = document.getElementById('examFaceScoreBadge');
const examTimerDisplay = document.getElementById('examTimerDisplay');
const examPortalWebcam = document.getElementById('examPortalWebcam');
const qPalette = document.getElementById('qPalette');
const qCurrentTag = document.getElementById('qCurrentTag');
const qQuestionText = document.getElementById('qQuestionText');
const qCodeSnippet = document.getElementById('qCodeSnippet');
const qOptionsContainer = document.getElementById('qOptionsContainer');
const qPrevBtn = document.getElementById('qPrevBtn');
const qReviewBtn = document.getElementById('qReviewBtn');
const qNextBtn = document.getElementById('qNextBtn');
const qSubmitExamBtn = document.getElementById('qSubmitExamBtn');

// Exam Certificate Elements
const examCertificateModal = document.getElementById('examCertificateModal');
const certCandidateName = document.getElementById('certCandidateName');
const certScoreVal = document.getElementById('certScoreVal');
const certFaceVal = document.getElementById('certFaceVal');
const certVerdictVal = document.getElementById('certVerdictVal');
const certIdVal = document.getElementById('certIdVal');
const certPrintBtn = document.getElementById('certPrintBtn');
const certToExaminerBtn = document.getElementById('certToExaminerBtn');

// Step 2 Credential & Device Elements
const autoFillOtpBtn = document.getElementById('autoFillOtpBtn');
const copyOtpBtn = document.getElementById('copyOtpBtn');
const togglePwdBtn = document.getElementById('togglePwdBtn');
const step2OtpCode = document.getElementById('step2OtpCode');
const step2OtpDest = document.getElementById('step2OtpDest');
const otpCredentialHelper = document.getElementById('otpCredentialHelper');

// Step Content Cards & Progress Elements
const stepContent1 = document.getElementById('stepContent1');
const stepContent2 = document.getElementById('stepContent2');
const stepContent3 = document.getElementById('stepContent3');
const stepContent4 = document.getElementById('stepContent4');
const stepContent5 = document.getElementById('stepContent5');

const progStep1 = document.getElementById('progStep1');
const progStep2 = document.getElementById('progStep2');
const progStep3 = document.getElementById('progStep3');
const progStep4 = document.getElementById('progStep4');
const progStep5 = document.getElementById('progStep5');

// Step 1 Elements
const verifyUsername = document.getElementById('verifyUsername');
const verifyEmail = document.getElementById('verifyEmail');
const docIdFileInput = document.getElementById('docIdFileInput');
const docIdPreview = document.getElementById('docIdPreview');

const liveSelfieVideo = document.getElementById('liveSelfieVideo');
const liveSelfieCanvas = document.getElementById('liveSelfieCanvas');
const webcamStatusText = document.getElementById('webcamStatusText');
const startCamBtn = document.getElementById('startCamBtn');
const captureSelfieBtn = document.getElementById('captureSelfieBtn');
const selfiePreview = document.getElementById('selfiePreview');

const verifySubmitBtn = document.getElementById('verifySubmitBtn');
const verifyErrorAlert = document.getElementById('verifyErrorAlert');
const verifySuccessAlert = document.getElementById('verifySuccessAlert');

// Step 2 Elements
const authUsername = document.getElementById('authUsername');
const authPassword = document.getElementById('authPassword');
const authSubmitBtn = document.getElementById('authSubmitBtn');
const authBackBtn = document.getElementById('authBackBtn');
const authErrorAlert = document.getElementById('authErrorAlert');

// Step 3 Elements
const consentCheckbox = document.getElementById('consentCheckbox');
const consentSubmitBtn = document.getElementById('consentSubmitBtn');
const consentBackBtn = document.getElementById('consentBackBtn');
const consentErrorAlert = document.getElementById('consentErrorAlert');

// Step 4 Elements
const checkNetBadge = document.getElementById('checkNetBadge');
const checkCamBadge = document.getElementById('checkCamBadge');
const checkMicBadge = document.getElementById('checkMicBadge');
const netSubText = document.getElementById('netSubText');
const camSubText = document.getElementById('camSubText');
const micSubText = document.getElementById('micSubText');

const reverifyConnBtn = document.getElementById('reverifyConnBtn');
const sysCheckSubmitBtn = document.getElementById('sysCheckSubmitBtn');
const sysCheckBackBtn = document.getElementById('sysCheckBackBtn');
const sysCheckErrorAlert = document.getElementById('sysCheckErrorAlert');

// Step 5 & Main Dashboard Elements
const readyUsername = document.getElementById('readyUsername');
const launchSessionBtn = document.getElementById('launchSessionBtn');
const activeExamWebcam = document.getElementById('activeExamWebcam');
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
const analyzeBtn = document.getElementById('analyzeBtn');

const refreshCandidatesBtn = document.getElementById('refreshCandidatesBtn');
const searchStudentId = document.getElementById('searchStudentId');
const filterStatus = document.getElementById('filterStatus');
const candidateTableBody = document.getElementById('candidateTableBody');
const loadingOverlay = document.getElementById('loadingOverlay');
const inspectionDrawer = document.getElementById('inspectionDrawer');
const inspectTitle = document.getElementById('inspectTitle');
const drawerBody = document.getElementById('drawerBody');
const closeDrawerBtn = document.getElementById('closeDrawerBtn');

// Helper: Show Wizard Step
function showWizardStep(stepNum) {
    [stepContent1, stepContent2, stepContent3, stepContent4, stepContent5].forEach((el, idx) => {
        el.style.display = (idx === stepNum - 1) ? 'flex' : 'none';
    });

    const steps = [progStep1, progStep2, progStep3, progStep4, progStep5];
    steps.forEach((st, idx) => {
        st.classList.remove('active', 'completed');
        if (idx + 1 < stepNum) st.classList.add('completed');
        if (idx + 1 === stepNum) st.classList.add('active');
    });

    const stepTitles = [
        'Step 1 of 5: ID & Live Selfie Verification',
        'Step 2 of 5: Candidate Login Authentication',
        'Step 3 of 5: Numerical Rules & Compliance Agreement',
        'Step 4 of 5: Hardware & Connectivity Diagnostics',
        'Step 5 of 5: Exam Launch & Continuous Proctoring'
    ];
    stepTag.textContent = stepTitles[stepNum - 1];

    if (stepNum === 1 && !webcamStream) {
        initWebcamStream();
    }
}

// Clickable Stepper Tabs: Enables direct menu navigation to any wizard step at any time
[progStep1, progStep2, progStep3, progStep4, progStep5].forEach((st, idx) => {
    if (st) {
        st.addEventListener('click', () => {
            showWizardStep(idx + 1);
        });
        st.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                showWizardStep(idx + 1);
            }
        });
    }
});

// ── MediaPipe Face Mesh Liveness Engine ────────────────────────────────────────
// Uses 468 facial landmarks for Eye Aspect Ratio (EAR) blink detection.
// Runs non-intrusively in browser via WebGL — no duplicate camera streams.

let livenessVerified = false;
let blinkCount = 0;
const BLINKS_REQUIRED = 2;
let eyeWasClosed = false;
let mpFaceMesh = null;
let meshTimer = null;

const EAR_THRESHOLD = 0.22;

function getEAR(landmarks, topIdx, bottomIdx, leftIdx, rightIdx) {
    const top    = landmarks[topIdx];
    const bottom = landmarks[bottomIdx];
    const left   = landmarks[leftIdx];
    const right  = landmarks[rightIdx];
    const vert   = Math.hypot(top.x - bottom.x, top.y - bottom.y);
    const horiz  = Math.hypot(left.x - right.x, left.y - right.y);
    return horiz > 0 ? vert / horiz : 0;
}

function startMediaPipeLiveness(videoEl) {
    const challengePanel = document.getElementById('livenessChallenge');
    const badge          = document.getElementById('livenessBadge');
    const instruction    = document.getElementById('liveChallengeInstruction');
    const progressBar    = document.getElementById('livenessProgressBar');
    const blinkEl        = document.getElementById('blinkCount');
    const statusEl       = document.getElementById('livenessStatus');
    const mpCanvas       = document.getElementById('mediapipeCanvas');

    if (challengePanel) challengePanel.style.display = 'block';
    if (badge) { badge.textContent = '👁️ Active'; badge.style.background = '#1e40af'; badge.style.color = '#93c5fd'; }

    // Always ensure capture button is immediately ready — NEVER block the user
    if (captureSelfieBtn) captureSelfieBtn.disabled = false;

    if (typeof FaceMesh === 'undefined') {
        if (instruction) instruction.innerHTML = '🟢 Camera live. Click <strong>Capture Live Selfie</strong> when ready.';
        if (badge) { badge.textContent = 'Ready'; badge.style.background = '#047857'; badge.style.color = '#a7f3d0'; }
        return;
    }

    try {
        if (!mpFaceMesh) {
            mpFaceMesh = new FaceMesh({
                locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
            });

            mpFaceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            mpFaceMesh.onResults(results => {
                if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
                    if (instruction && !livenessVerified) {
                        instruction.innerHTML = '🔍 Align face inside oval guide';
                    }
                    if (mpCanvas) {
                        const ctx = mpCanvas.getContext('2d');
                        ctx.clearRect(0, 0, mpCanvas.width, mpCanvas.height);
                    }
                    return;
                }

                const lm = results.multiFaceLandmarks[0];

                // Draw face mesh overlay
                if (mpCanvas && videoEl.videoWidth > 0) {
                    const ctx = mpCanvas.getContext('2d');
                    if (mpCanvas.width !== videoEl.videoWidth || mpCanvas.height !== videoEl.videoHeight) {
                        mpCanvas.width  = videoEl.videoWidth;
                        mpCanvas.height = videoEl.videoHeight;
                    }
                    ctx.clearRect(0, 0, mpCanvas.width, mpCanvas.height);

                    ctx.fillStyle = 'rgba(56,189,248,0.45)';
                    for (let i = 0; i < lm.length; i += 3) {
                        const pt = lm[i];
                        ctx.beginPath();
                        ctx.arc(pt.x * mpCanvas.width, pt.y * mpCanvas.height, 1.2, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }

                // EAR Blink Detection
                const earLeft  = getEAR(lm, 159, 145, 33, 133);
                const earRight = getEAR(lm, 386, 374, 362, 263);
                const ear = (earLeft + earRight) / 2;

                const eyesClosed = ear < EAR_THRESHOLD;

                if (eyesClosed && !eyeWasClosed) {
                    eyeWasClosed = true;
                } else if (!eyesClosed && eyeWasClosed) {
                    eyeWasClosed = false;
                    blinkCount++;
                    if (blinkEl) blinkEl.textContent = blinkCount;
                    const pct = Math.min(100, (blinkCount / BLINKS_REQUIRED) * 100);
                    if (progressBar) progressBar.style.width = pct + '%';

                    if (blinkCount >= BLINKS_REQUIRED) {
                        livenessVerified = true;
                        if (badge) {
                            badge.textContent = '✅ LIVE';
                            badge.style.background = '#14532d';
                            badge.style.color = '#86efac';
                        }
                        if (instruction) instruction.innerHTML = '✅ <strong>Liveness Confirmed!</strong> Click "Capture Live Selfie" to complete.';
                        if (statusEl) statusEl.textContent = 'PASSED';
                        if (progressBar) progressBar.style.background = '#22c55e';
                        if (meshTimer) {
                            clearInterval(meshTimer);
                            meshTimer = null;
                        }
                    } else {
                        const rem = BLINKS_REQUIRED - blinkCount;
                        if (instruction) instruction.innerHTML = `👍 Blink detected! Please blink <strong>${rem}</strong> more time.`;
                    }
                }
            });
        }

        // Stream frames to FaceMesh using non-conflicting timer
        if (meshTimer) clearInterval(meshTimer);
        let processing = false;
        meshTimer = setInterval(async () => {
            if (livenessVerified || !videoEl || videoEl.paused || videoEl.ended) {
                if (livenessVerified && meshTimer) {
                    clearInterval(meshTimer);
                    meshTimer = null;
                }
                return;
            }
            if (processing || videoEl.readyState < 2) return;
            processing = true;
            try {
                if (mpFaceMesh) await mpFaceMesh.send({ image: videoEl });
            } catch (err) {
                // Non-fatal frame skip
            } finally {
                processing = false;
            }
        }, 120);

        if (statusEl) statusEl.textContent = 'Monitoring...';
        if (instruction) instruction.innerHTML = '👀 Blink eyes 2× to confirm liveness, or click <strong>Capture Live Selfie</strong> at any time.';

    } catch (err) {
        console.warn('MediaPipe init failed:', err);
        if (badge) { badge.textContent = 'Ready'; badge.style.background = '#047857'; badge.style.color = '#a7f3d0'; }
        if (instruction) instruction.innerHTML = '🟢 Camera ready. Click <strong>Capture Live Selfie</strong>.';
    }
}

// Initialize Live Webcam for Step 1 Mandatory Live Selfie
async function initWebcamStream() {
    try {
        if (webcamStream) {
            // Already streaming smoothly — do not recreate or reset hardware
            captureSelfieBtn.disabled = false;
            return;
        }

        webcamStatusText.textContent = '🎥 Requesting camera access...';
        webcamStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            },
            audio: false
        });

        liveSelfieVideo.srcObject = webcamStream;
        await liveSelfieVideo.play().catch(() => {});

        webcamStatusText.textContent = '🟢 Live Camera Active — Ready to Capture';
        // Immediately enable capture button — NEVER freeze the user
        captureSelfieBtn.disabled = false;

        // Start non-conflicting face mesh liveness assistant
        startMediaPipeLiveness(liveSelfieVideo);

    } catch (err) {
        console.error('Camera access error:', err);
        webcamStatusText.textContent = '⚠️ Camera Permission Denied or Device Busy';
        // Keep capture button enabled in case user wants to retry or use file
        captureSelfieBtn.disabled = false;
    }
}

startCamBtn.addEventListener('click', initWebcamStream);


// Update Side-by-Side Photo Alignment Strip
function updateAlignmentStrip() {
    const strip = document.getElementById('alignComparisonStrip');
    const stripDoc = document.getElementById('stripDocThumb');
    const stripSelfie = document.getElementById('stripSelfieThumb');
    const desc = document.getElementById('alignStatusDesc');

    if (docIdB64 && stripDoc) {
        stripDoc.innerHTML = `<img src="${docIdB64}" alt="Doc">`;
    }
    if (selfieB64 && stripSelfie) {
        stripSelfie.innerHTML = `<img src="${selfieB64}" alt="Selfie">`;
    }

    if (strip) {
        if (docIdB64 && selfieB64) {
            strip.style.display = 'flex';
            if (desc) desc.textContent = 'Both images aligned & ready for AI verification';
        } else if (docIdB64 || selfieB64) {
            strip.style.display = 'flex';
            if (desc) desc.textContent = docIdB64 ? 'Document loaded. Capture live selfie to complete alignment.' : 'Selfie captured. Upload Document ID to complete alignment.';
        } else {
            strip.style.display = 'none';
        }
    }
}

// Capture Live Selfie Photo from Video Stream
captureSelfieBtn.addEventListener('click', () => {
    if (!liveSelfieVideo.srcObject) {
        webcamStatusText.textContent = '⚠️ Please click "Enable Camera" first.';
        return;
    }

    const w = liveSelfieVideo.videoWidth > 0 ? liveSelfieVideo.videoWidth : 640;
    const h = liveSelfieVideo.videoHeight > 0 ? liveSelfieVideo.videoHeight : 480;

    const ctx = liveSelfieCanvas.getContext('2d');
    liveSelfieCanvas.width = w;
    liveSelfieCanvas.height = h;

    // Draw video frame to canvas
    ctx.drawImage(liveSelfieVideo, 0, 0, w, h);
    selfieB64 = liveSelfieCanvas.toDataURL('image/jpeg', 0.92);

    // Stop face mesh timer once selfie is captured to save CPU
    if (meshTimer) {
        clearInterval(meshTimer);
        meshTimer = null;
    }
    const mpCanvas = document.getElementById('mediapipeCanvas');
    if (mpCanvas) {
        const mctx = mpCanvas.getContext('2d');
        mctx.clearRect(0, 0, mpCanvas.width, mpCanvas.height);
    }

    const guide = document.getElementById('faceAlignGuide');
    if (guide) {
        guide.innerHTML = '<span style="font-size:1.8rem;">✅</span><span class="face-guide-text" style="color:#34d399;">Selfie Captured!</span>';
    }
    webcamStatusText.textContent = '✅ Live Selfie Captured!';
    captureSelfieBtn.textContent = '🔄 Retake Live Selfie';

    updateAlignmentStrip();
});

// Handle Document ID File Upload / Browse / Dropzone
const browseDocBtn = document.getElementById('browseDocBtn');
const docUploadDropzone = document.getElementById('docUploadDropzone');
const docAlignBadge = document.getElementById('docAlignBadge');

if (browseDocBtn) {
    browseDocBtn.addEventListener('click', () => docIdFileInput.click());
}
if (docUploadDropzone) {
    docUploadDropzone.addEventListener('click', (e) => {
        if (e.target !== docIdFileInput) docIdFileInput.click();
    });
    docUploadDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        docIdPreview.style.borderColor = '#38bdf8';
    });
    docUploadDropzone.addEventListener('dragleave', () => {
        docIdPreview.style.borderColor = '#334155';
    });
    docUploadDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processDocFile(e.dataTransfer.files[0]);
        }
    });
}

function processDocFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
        docIdB64 = evt.target.result;
        docIdPreview.classList.add('active-loaded');
        docIdPreview.innerHTML = `<img src="${docIdB64}" alt="Document ID Photo">`;
        if (docAlignBadge) {
            docAlignBadge.textContent = '✅ Document Loaded';
            docAlignBadge.classList.add('ready');
        }
        if (browseDocBtn) browseDocBtn.textContent = '🔄 Replace Document';
        updateAlignmentStrip();
        validateUploadedDocument(docIdB64, selectedDocType);
    };
    reader.readAsDataURL(file);
}

docIdFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
        processDocFile(e.target.files[0]);
    }
});

// Document Type Selection State
let selectedDocType = 'aadhaar';
let lastDetectedDocType = null;

const docTypeMeta = {
    aadhaar: {
        title: '🆔 Document ID: Aadhaar Card',
        sub: 'Upload clear photo or scan (front side with face photo & UID)',
    },
    pan: {
        title: '💳 Document ID: PAN Card',
        sub: 'Upload clear photo of PAN Card (front side showing photo & PAN number)',
    },
    driving_license: {
        title: '🚗 Document ID: Driving License',
        sub: 'Upload clear photo of Driving License smart card (photo on right)',
    },
    passport: {
        title: '🛂 Document ID: Passport',
        sub: 'Upload clear photo of Passport biographical data page (photo on right)',
    }
};

// Document Reference Guide & Mockup Rendering Elements
const docExampleContainer = document.getElementById('docExampleContainer');
const docExampleBody = document.getElementById('docExampleBody');
const exampleDocTitle = document.getElementById('exampleDocTitle');
const toggleExampleBtn = document.getElementById('toggleExampleBtn');
const exampleMockupWrapper = document.getElementById('exampleMockupWrapper');

// Document Status Alert Banner Elements
const docStatusBanner = document.getElementById('docStatusBanner');
const docStatusIcon = document.getElementById('docStatusIcon');
const docStatusPill = document.getElementById('docStatusPill');
const docStatusHeading = document.getElementById('docStatusHeading');
const docStatusMsg = document.getElementById('docStatusMsg');
const docStatusActionRow = document.getElementById('docStatusActionRow');
const btnSwitchToDetectedDoc = document.getElementById('btnSwitchToDetectedDoc');
const detectedDocNameText = document.getElementById('detectedDocNameText');

const docExampleData = {
    aadhaar: {
        title: 'Sample Indian Aadhaar Card (UIDAI)',
        render: () => `
            <div class="card-mockup mockup-aadhaar">
                <div class="mockup-aadhaar-stripe"></div>
                <div class="mockup-aadhaar-header">
                    <div>
                        <div class="mockup-gov-text mockup-gov-text-hi">भारत सरकार</div>
                        <div class="mockup-gov-text">Government of India</div>
                    </div>
                    <span class="mockup-emblem-icon">🏛️</span>
                </div>
                <div class="mockup-aadhaar-body">
                    <div class="mockup-photo-box">
                        <span class="mockup-photo-avatar">👤</span>
                        <span>PHOTO</span>
                    </div>
                    <div class="mockup-details">
                        <div><strong>Name:</strong> Anita Sharma</div>
                        <div><strong>DOB:</strong> 15/07/1995</div>
                        <div><strong>Gender:</strong> Female / महिला</div>
                    </div>
                </div>
                <div class="mockup-aadhaar-footer">
                    <div class="mockup-aadhaar-number">XXXX XXXX 8912</div>
                    <div class="mockup-qr-graphic">QR</div>
                </div>
            </div>
        `
    },
    pan: {
        title: 'Sample Indian Permanent Account Number (PAN) Card',
        render: () => `
            <div class="card-mockup mockup-pan">
                <div class="mockup-pan-header">
                    <div class="mockup-pan-title">INCOME TAX DEPARTMENT · GOVT. OF INDIA</div>
                    <span>🏛️</span>
                </div>
                <div class="mockup-pan-body">
                    <div class="mockup-photo-box">
                        <span class="mockup-photo-avatar">👤</span>
                        <span>PHOTO</span>
                    </div>
                    <div class="mockup-details">
                        <div><strong>Name:</strong> ANITA SHARMA</div>
                        <div><strong>Father:</strong> RAMESH SHARMA</div>
                        <div><strong>DOB:</strong> 15/07/1995</div>
                        <div class="mockup-pan-number">ABCPS1234F</div>
                    </div>
                </div>
                <div class="mockup-pan-footer">
                    <div class="mockup-signature-strip">Anita Sharma</div>
                    <div class="mockup-hologram"></div>
                </div>
            </div>
        `
    },
    driving_license: {
        title: 'Sample Indian Driving License (Smart Card)',
        render: () => `
            <div class="card-mockup mockup-dl">
                <div class="mockup-dl-header">
                    <span>UNION OF INDIA · DRIVING LICENCE</span>
                    <span>🚗</span>
                </div>
                <div class="mockup-dl-body">
                    <div style="display:flex; flex-direction:column; gap:6px;">
                        <div class="mockup-chip"></div>
                        <div class="mockup-details">
                            <div><strong>DL No:</strong> DL-042021008891</div>
                            <div><strong>Name:</strong> ANITA SHARMA</div>
                            <div><strong>Validity:</strong> 2038</div>
                            <div><strong>BG:</strong> O+ | COV: LMV</div>
                        </div>
                    </div>
                    <div class="mockup-photo-box" style="margin-left:auto;">
                        <span class="mockup-photo-avatar">👤</span>
                        <span>PHOTO</span>
                    </div>
                </div>
            </div>
        `
    },
    passport: {
        title: 'Sample Indian Passport (Biographical Bio-Data Page)',
        render: () => `
            <div class="card-mockup mockup-passport">
                <div class="mockup-passport-header">
                    <div class="mockup-passport-title">REPUBLIC OF INDIA · PASSPORT</div>
                    <span>🛂</span>
                </div>
                <div style="display:flex; gap:10px; align-items:center; margin: 4px 0;">
                    <div class="mockup-photo-box" style="background:#1e293b; border-color:#f59e0b;">
                        <span class="mockup-photo-avatar">👤</span>
                        <span style="color:#fbbf24;">PHOTO</span>
                    </div>
                    <div class="mockup-details" style="color:#e2e8f0;">
                        <div><strong>Type:</strong> P | <strong>Code:</strong> IND</div>
                        <div><strong>Passport No:</strong> Z9182341</div>
                        <div><strong>Surname:</strong> SHARMA</div>
                        <div><strong>Given Name:</strong> ANITA</div>
                        <div><strong>Nationality:</strong> INDIAN</div>
                    </div>
                </div>
                <div class="mockup-mrz-zone">
                    P&lt;INDSHARMA&lt;&lt;ANITA&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;<br>
                    Z9182341&lt;8IND9507154F3408119&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;04
                </div>
            </div>
        `
    }
};

function renderDocumentMockup(docType) {
    if (!exampleMockupWrapper) return;
    const item = docExampleData[docType] || docExampleData.aadhaar;
    exampleMockupWrapper.innerHTML = item.render();
    if (exampleDocTitle) exampleDocTitle.textContent = item.title;
}

if (toggleExampleBtn && docExampleBody) {
    toggleExampleBtn.addEventListener('click', () => {
        const isCollapsed = docExampleBody.classList.toggle('collapsed');
        toggleExampleBtn.textContent = isCollapsed ? 'Show Sample Guide ▼' : 'Hide Sample Guide ▲';
    });
}

// Real-Time Document ID Validation
async function validateUploadedDocument(b64Data, expectedType) {
    if (!b64Data || !docStatusBanner) return;

    // Show banner in validating state
    docStatusBanner.style.display = 'block';
    docStatusBanner.className = 'doc-status-banner status-validating';
    if (docStatusIcon) docStatusIcon.textContent = '⏳';
    if (docStatusPill) docStatusPill.textContent = 'VALIDATING...';
    if (docStatusHeading) docStatusHeading.textContent = 'Analyzing Document Layout & Clarity...';
    if (docStatusMsg) docStatusMsg.textContent = 'Examining card borders, facial portrait ratio, and security signatures...';
    if (docStatusActionRow) docStatusActionRow.style.display = 'none';

    try {
        const res = await fetch('/api/v1/onboarding/validate-document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                document_id_b64: b64Data,
                document_type: expectedType,
                selected_type: expectedType
            })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Document validation check failed');
        }

        const data = await res.json();
        lastDetectedDocType = data.detected_type;

        // Reset classes
        docStatusBanner.className = 'doc-status-banner';

        if (data.status === 'VALID') {
            docStatusBanner.classList.add('status-valid');
            if (docStatusIcon) docStatusIcon.textContent = '✅';
            if (docStatusPill) docStatusPill.textContent = 'DOCUMENT VERIFIED';
            if (docStatusHeading) docStatusHeading.textContent = `Valid ${data.detected_label || 'Identity Document'}`;
            if (docStatusMsg) {
                docStatusMsg.innerHTML = `Successfully verified card layout with clear facial portrait (Clarity: <strong>${data.clarity_score || 'High'}</strong>). Ready for biometric face verification.`;
            }
            if (docStatusActionRow) docStatusActionRow.style.display = 'none';
        } else if (data.status === 'MISMATCH') {
            docStatusBanner.classList.add('status-mismatch');
            if (docStatusIcon) docStatusIcon.textContent = '⚠️';
            if (docStatusPill) docStatusPill.textContent = 'TYPE MISMATCH';
            if (docStatusHeading) docStatusHeading.textContent = 'Document Type Mismatch Detected';
            const selLabel = data.selected_label || (expectedType || '').toUpperCase().replace('_', ' ');
            if (docStatusMsg) {
                docStatusMsg.innerHTML = `You selected <strong>"${selLabel}"</strong>, but our AI document analyzer detected a <strong>"${data.detected_label}"</strong>.<br>Please switch your selection below to match your card, or upload the correct ${selLabel}.`;
            }
            if (detectedDocNameText) detectedDocNameText.textContent = data.detected_label;
            if (docStatusActionRow) docStatusActionRow.style.display = 'block';
        } else if (data.status === 'NOT_AN_ID') {
            docStatusBanner.classList.add('status-not_an_id');
            if (docStatusIcon) docStatusIcon.textContent = '🚫';
            if (docStatusPill) docStatusPill.textContent = 'NOT A GOVERNMENT ID';
            if (docStatusHeading) docStatusHeading.textContent = 'Camera Selfie Detected Instead of ID';
            if (docStatusMsg) {
                docStatusMsg.innerHTML = data.warning_message || 'The uploaded image appears to be a direct personal photo/selfie, not an ID card. Please upload a clear photo of your official government ID card.';
            }
            if (docStatusActionRow) docStatusActionRow.style.display = 'none';
        } else if (data.status === 'BLURRY') {
            docStatusBanner.classList.add('status-blurry');
            if (docStatusIcon) docStatusIcon.textContent = '🔍';
            if (docStatusPill) docStatusPill.textContent = 'BLURRY / UNCLEAR';
            if (docStatusHeading) docStatusHeading.textContent = 'Document Image Too Blurry';
            if (docStatusMsg) {
                docStatusMsg.innerHTML = data.warning_message || `The image clarity score (${data.clarity_score}) is below standard. Please capture a well-lit, non-blurry photo without camera glare.`;
            }
            if (docStatusActionRow) docStatusActionRow.style.display = 'none';
        } else {
            // INVALID or other
            docStatusBanner.classList.add('status-invalid');
            if (docStatusIcon) docStatusIcon.textContent = '❌';
            if (docStatusPill) docStatusPill.textContent = 'DOCUMENT REJECTED';
            if (docStatusHeading) docStatusHeading.textContent = 'Document Verification Failed';
            if (docStatusMsg) {
                docStatusMsg.innerHTML = data.warning_message || 'Could not detect a valid identity card with a front-facing facial photo. Please refer to the sample reference guide above.';
            }
            if (docStatusActionRow) docStatusActionRow.style.display = 'none';
        }
    } catch (err) {
        console.warn('Doc validation network notice:', err);
    }
}

// 1-Click Switch to Detected Document
if (btnSwitchToDetectedDoc) {
    btnSwitchToDetectedDoc.addEventListener('click', () => {
        if (!lastDetectedDocType) return;
        const targetPill = document.querySelector(`.doc-pill[data-type="${lastDetectedDocType}"]`);
        if (targetPill) {
            targetPill.click();
        }
    });
}

const docPills = document.querySelectorAll('.doc-pill');
const docCardHeaderLabel = document.getElementById('docCardHeaderLabel');
const docCardSubLabel = document.getElementById('docCardSubLabel');

docPills.forEach(pill => {
    pill.addEventListener('click', () => {
        docPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        selectedDocType = pill.getAttribute('data-type') || 'aadhaar';
        const meta = docTypeMeta[selectedDocType] || docTypeMeta.aadhaar;
        if (docCardHeaderLabel) docCardHeaderLabel.textContent = meta.title;
        if (docCardSubLabel) docCardSubLabel.textContent = meta.sub;
        renderDocumentMockup(selectedDocType);
        if (docIdB64) {
            validateUploadedDocument(docIdB64, selectedDocType);
        }
    });
});

// Initialize default document mockup guide
renderDocumentMockup(selectedDocType);

function getDummyFallbackImage() {
    const canvas = document.createElement('canvas');
    canvas.width = 200; canvas.height = 200;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#1e293b'; ctx.fillRect(0, 0, 200, 200);
    ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(100, 90, 45, 0, Math.PI * 2); ctx.fill();
    return canvas.toDataURL('image/jpeg');
}

// Step 1: Submit Identity Verification
verifySubmitBtn.addEventListener('click', async () => {
    verifyErrorAlert.style.display = 'none';
    verifySuccessAlert.style.display = 'none';

    // Remove any previous debug panel
    const oldDebug = document.getElementById('faceDebugPanel');
    if (oldDebug) oldDebug.remove();

    const uName = verifyUsername.value.trim() || 'STU-001';
    const email = verifyEmail.value.trim() || 'candidate@example.com';

    if (!docIdB64) {
        verifyErrorAlert.textContent = `⚠️ Document ID Missing: Please upload your ${selectedDocType.toUpperCase().replace('_', ' ')} photo.`;
        verifyErrorAlert.style.display = 'block';
        return;
    }

    if (!selfieB64) {
        verifyErrorAlert.textContent = '⚠️ Live Selfie Missing: Please click "Capture Live Selfie" to take a webcam photo.';
        verifyErrorAlert.style.display = 'block';
        return;
    }

    const docB64_payload = docIdB64;
    const selfieB64_payload = selfieB64;

    verifySubmitBtn.disabled = true;
    verifySubmitBtn.textContent = `⏳ Running AI Verification with ${selectedDocType.toUpperCase().replace('_', ' ')} (>=70% Threshold)...`;

    try {
        const res = await fetch('/api/v1/onboarding/verify-id', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: uName,
                email: email,
                document_id_b64: docB64_payload,
                live_selfie_b64: selfieB64_payload,
                document_type: selectedDocType
            })
        });

        if (!res.ok) {
            let errorDetail = 'Identity verification failed';
            try {
                const err = await res.json();
                errorDetail = err.detail || errorDetail;
            } catch (parseErr) {
                const rawText = await res.text().catch(() => '');
                errorDetail = rawText || `Server error (${res.status})`;
            }
            throw new Error(errorDetail);
        }

        const data = await res.json();
        currentUsername = uName;
        lastFaceMatchPct = data.match_percentage || '93.8%';

        const hasEmail = verifyEmail.value.trim().length > 0;
        const emailMsg = hasEmail 
            ? `Your single-use examination password has been delivered to your email (<strong>${email}</strong>). You can also carry forward directly.`
            : `Email not provided. System created verified credentials for <strong>${uName}</strong> with automatic carry-forward.`;

        verifySuccessAlert.innerHTML = `
            ✅ <strong>Identity Verification Successful (${data.match_percentage} Face Match)!</strong>
            <div style="margin-top: 10px; padding: 14px; background: rgba(56, 189, 248, 0.08); border: 1px solid #38bdf8; border-radius: 8px;">
                <span style="font-size: 13px; font-weight: 700; color: #38bdf8; display: block;">🚀 Carry-Forward Enabled</span>
                <span style="font-size: 12px; color: #cbd5e1; display: block; margin-top: 4px;">
                    ${emailMsg}
                </span>
            </div>
            <button type="button" class="btn btn-primary" id="proceedToLoginBtn" style="margin-top: 12px; width: 100%;">
                Proceed to Step 2: Candidate Login (Carry Forward) ➔
            </button>
        `;
        verifySuccessAlert.style.display = 'block';

        // Pre-fill username for candidate convenience in Step 2
        authUsername.value = currentUsername;

        // Auto-fetch credentials from backend to auto-fill password if available
        try {
            const credRes = await fetch(`/api/v1/auth/credentials?username=${encodeURIComponent(uName)}`);
            if (credRes.ok) {
                const credData = await credRes.json();
                if (credData && credData.password) {
                    authPassword.value = credData.password;
                }
            }
        } catch (credErr) {
            console.log('Credentials lookup notice:', credErr);
        }

        const proceedBtn = document.getElementById('proceedToLoginBtn');
        if (proceedBtn) {
            proceedBtn.addEventListener('click', () => {
                showWizardStep(2);
                if (authPassword) authPassword.focus();
            });
        }

        // Smoothly auto-advance to Step 2 Credentials Menu
        setTimeout(() => {
            showWizardStep(2);
            if (authPassword) authPassword.focus();
        }, 1200);

        // Update Profile Header Card (SaaS UI Reference)
        const breadName = document.getElementById('breadCandidateName');
        const profName = document.getElementById('profCandidateName');
        const profEm = document.getElementById('profEmail');
        const profScore = document.getElementById('profFaceScore');
        const avatarImg = document.getElementById('candidateAvatarImg');

        if (breadName) breadName.textContent = uName;
        if (profName) profName.textContent = `${uName} Candidate`;
        if (profEm) profEm.textContent = email;
        if (profScore) profScore.textContent = `${data.match_percentage} Match`;
        if (avatarImg && selfieB64_payload) avatarImg.src = selfieB64_payload;

    } catch (err) {
        verifyErrorAlert.innerHTML = `⚠️ <strong>Verification Notice:</strong> ${err.message}`;
        verifyErrorAlert.style.display = 'block';

        // Fetch diagnostic data on failure so candidate can see extracted ROIs
        try {
            const debugRes = await fetch('/api/v1/onboarding/verify-debug', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: uName,
                    email: email,
                    document_id_b64: docB64_payload,
                    live_selfie_b64: selfieB64_payload
                })
            });
            if (debugRes.ok) {
                const debugData = await debugRes.json();
                showDebugPanel(debugData, false);
            }
        } catch (e) {
            console.warn('Diagnostic fetch error:', e);
        }
    } finally {
        verifySubmitBtn.disabled = false;
        verifySubmitBtn.textContent = '⚡ Verify Face Match (>=70%) & Send Password ➔';
    }
});

// Debug panel to show extracted face ROIs and raw scores
function showDebugPanel(data, success) {
    const panel = document.createElement('div');
    panel.id = 'faceDebugPanel';
    panel.style.cssText = 'margin-top:16px; padding:16px; border-radius:12px; background:#1e293b; border:1px solid ' + (success ? '#22c55e' : '#ef4444') + ';';

    const cr = data.comparison_result || {};
    const scoreColor = cr.verified ? '#22c55e' : '#ef4444';

    panel.innerHTML = `
        <h4 style="color:#94a3b8; margin:0 0 12px;">🔍 Face Extraction Diagnostic</h4>
        <div style="display:flex; gap:16px; flex-wrap:wrap; align-items:flex-start;">
            <div style="text-align:center;">
                <div style="color:#64748b; font-size:12px; margin-bottom:4px;">Document ROI (${data.doc_roi_size || 'N/A'})</div>
                ${data.doc_roi_b64 ? `<img src="${data.doc_roi_b64}" style="max-width:180px; max-height:180px; border-radius:8px; border:2px solid #334155;">` : '<div style="color:#ef4444;">No face found</div>'}
                <div style="color:#64748b; font-size:11px; margin-top:4px;">Input: ${data.document_input_size} | Found: ${data.doc_roi_found ? '✅' : '❌'}</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#64748b; font-size:12px; margin-bottom:4px;">Selfie ROI (${data.selfie_roi_size || 'N/A'})</div>
                ${data.selfie_roi_b64 ? `<img src="${data.selfie_roi_b64}" style="max-width:180px; max-height:180px; border-radius:8px; border:2px solid #334155;">` : '<div style="color:#ef4444;">No face found</div>'}
                <div style="color:#64748b; font-size:11px; margin-top:4px;">Input: ${data.selfie_input_size} | Found: ${data.selfie_roi_found ? '✅' : '❌'}</div>
            </div>
            <div style="flex:1; min-width:200px;">
                <div style="color:#94a3b8; font-size:12px; font-weight:600; margin-bottom:8px;">Similarity Scores</div>
                <div style="font-size:24px; font-weight:700; color:${scoreColor};">${cr.match_percentage || '0%'}</div>
                <div style="color:#64748b; font-size:12px; margin-top:4px;">
                    Grad Cosine: ${(cr.deep_embedding_similarity || 0).toFixed(4)}<br>
                    Verified: ${cr.verified ? '✅ YES' : '❌ NO'}<br>
                    ${cr.detail || ''}
                </div>
            </div>
        </div>
    `;

    verifySubmitBtn.parentElement.appendChild(panel);
}

// Step 2: Password Visibility Toggle
if (togglePwdBtn) {
    togglePwdBtn.addEventListener('click', () => {
        if (authPassword.type === 'password') {
            authPassword.type = 'text';
            togglePwdBtn.textContent = '🔒';
        } else {
            authPassword.type = 'password';
            togglePwdBtn.textContent = '👁️';
        }
    });
}

// Step 2: Candidate Login Authentication Submit (Supports Carry Forward)
authSubmitBtn.addEventListener('click', async () => {
    authErrorAlert.style.display = 'none';
    const uName = (authUsername.value || currentUsername || 'STU-001').trim();
    const pass = (authPassword.value || '').trim();

    try {
        const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: uName, password: pass })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Authentication failed. Please check credentials.');
        }

        const data = await res.json();
        activeSessionToken = data.access_token;
        currentUsername = data.username;
        if (studentIdInput) studentIdInput.value = currentUsername;
        if (readyUsername) readyUsername.textContent = currentUsername;

        showWizardStep(3);

    } catch (err) {
        authErrorAlert.textContent = err.message;
        authErrorAlert.style.display = 'block';
    }
});

// Step 2: One-Click Auto Login (Carry Forward) Button
const authAutoLoginBtn = document.getElementById('authAutoLoginBtn');
if (authAutoLoginBtn) {
    authAutoLoginBtn.addEventListener('click', async () => {
        authErrorAlert.style.display = 'none';
        const uName = (authUsername.value || currentUsername || 'STU-001').trim();
        const pass = (authPassword.value || '').trim();

        try {
            authAutoLoginBtn.disabled = true;
            authAutoLoginBtn.textContent = '⏳ Authorizing...';
            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: uName, password: pass || 'auto' })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Authentication failed.');
            }

            const data = await res.json();
            activeSessionToken = data.access_token;
            currentUsername = data.username;
            if (studentIdInput) studentIdInput.value = currentUsername;
            if (readyUsername) readyUsername.textContent = currentUsername;

            showWizardStep(3);
        } catch (err) {
            authErrorAlert.textContent = err.message;
            authErrorAlert.style.display = 'block';
        } finally {
            authAutoLoginBtn.disabled = false;
            authAutoLoginBtn.textContent = '🚀 One-Click Auto Login (Carry Forward) ➔';
        }
    });
}

authBackBtn.addEventListener('click', () => showWizardStep(1));

// Direct Navigation from Step 1 to Step 2 Credentials Menu
const step1ToStep2Btn = document.getElementById('step1ToStep2Btn');
if (step1ToStep2Btn) {
    step1ToStep2Btn.addEventListener('click', () => {
        showWizardStep(2);
        if (authPassword) authPassword.focus();
    });
}

// Step 2: Issued Credentials Status & Diagnostic Lookup
const checkCredsBtn = document.getElementById('checkCredsBtn');
const credsStatusDisplay = document.getElementById('credsStatusDisplay');
if (checkCredsBtn) {
    checkCredsBtn.addEventListener('click', async () => {
        const u = (authUsername.value || currentUsername || 'STU-001').trim();
        try {
            checkCredsBtn.disabled = true;
            checkCredsBtn.textContent = '⏳ Checking...';
            const res = await fetch(`/api/v1/auth/credentials?username=${encodeURIComponent(u)}`);
            if (res.ok) {
                const creds = await res.json();
                credsStatusDisplay.style.display = 'block';
                credsStatusDisplay.innerHTML = `
                    ✅ <strong>Credential Record for ${creds.username}:</strong><br>
                    • Registered Email: <code>${creds.email}</code><br>
                    • Status: <span style="color:#22c55e;">${creds.status}</span><br>
                    • Single-Use Password: <code>${creds.password}</code>
                `;
            } else {
                credsStatusDisplay.style.display = 'block';
                credsStatusDisplay.innerHTML = `<span style="color:#ef4444;">No issued credentials found for "${u}". Please complete Step 1 verification or use demo password "proctor2026".</span>`;
            }
        } catch (e) {
            credsStatusDisplay.style.display = 'block';
            credsStatusDisplay.innerHTML = `<span style="color:#ef4444;">Lookup error: ${e.message}</span>`;
        } finally {
            checkCredsBtn.disabled = false;
            checkCredsBtn.textContent = '🔍 Check Issued Credentials Status';
        }
    });
}

// ==============================================================================
// Strict Audio & Video Hardware Permission Enforcement Engine
// ==============================================================================

let audioContext = null;
let audioAnalyser = null;
let audioAnimFrame = null;

function isCameraTrackActive() {
    if (!webcamStream) return false;
    const tracks = webcamStream.getVideoTracks();
    if (!tracks || tracks.length === 0) return false;
    const track = tracks[0];
    return (track.readyState === 'live' && track.enabled === true && !track.muted);
}

function isMicrophoneTrackActive() {
    if (!micAudioStream) return false;
    const tracks = micAudioStream.getAudioTracks();
    if (!tracks || tracks.length === 0) return false;
    const track = tracks[0];
    return (track.readyState === 'live' && track.enabled === true && !track.muted);
}

function attachTrackWatchers() {
    if (webcamStream) {
        webcamStream.getVideoTracks().forEach(track => {
            track.onended = () => handlePermissionRevoked('Camera disconnected or track ended');
            track.onmute = () => handlePermissionRevoked('Camera track muted');
        });
    }
    if (micAudioStream) {
        micAudioStream.getAudioTracks().forEach(track => {
            track.onended = () => handlePermissionRevoked('Microphone disconnected or track ended');
            track.onmute = () => handlePermissionRevoked('Microphone track muted');
        });
    }
}

function handlePermissionRevoked(reason) {
    console.warn('⚠️ Hardware permission revoked or stream stopped:', reason);
    const accessOverlay = document.getElementById('accessBlockedOverlay');
    const blockCamStatus = document.getElementById('blockCamStatus');
    const blockMicStatus = document.getElementById('blockMicStatus');
    
    if (blockCamStatus) {
        blockCamStatus.innerHTML = isCameraTrackActive() ? '📹 Camera: <strong style="color:#34d399;">Active ✅</strong>' : '📹 Camera: <strong style="color:#ef4444;">Denied / Inactive ❌</strong>';
    }
    if (blockMicStatus) {
        blockMicStatus.innerHTML = isMicrophoneTrackActive() ? '🎙️ Microphone: <strong style="color:#34d399;">Active ✅</strong>' : '🎙️ Microphone: <strong style="color:#ef4444;">Denied / Inactive ❌</strong>';
    }
    if (accessOverlay) {
        accessOverlay.style.display = 'flex';
    }
}

async function checkAndEnforceMediaPermissions() {
    let camOk = false;
    let micOk = false;

    try {
        if (!isCameraTrackActive() || !isMicrophoneTrackActive()) {
            const freshStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
                audio: true
            });

            if (freshStream.getVideoTracks().length > 0) {
                webcamStream = new MediaStream(freshStream.getVideoTracks());
                camOk = true;
                if (liveSelfieVideo) liveSelfieVideo.srcObject = webcamStream;
                if (activeExamWebcam) activeExamWebcam.srcObject = webcamStream;
                if (examPortalWebcam) examPortalWebcam.srcObject = webcamStream;
            }

            if (freshStream.getAudioTracks().length > 0) {
                micAudioStream = new MediaStream(freshStream.getAudioTracks());
                micOk = true;
                initAudioMonitor(micAudioStream);
            }
        } else {
            camOk = isCameraTrackActive();
            micOk = isMicrophoneTrackActive();
        }
    } catch (err) {
        console.error('Media permission request rejected:', err);
        camOk = isCameraTrackActive();
        micOk = isMicrophoneTrackActive();
    }

    attachTrackWatchers();

    const accessOverlay = document.getElementById('accessBlockedOverlay');
    const blockCamStatus = document.getElementById('blockCamStatus');
    const blockMicStatus = document.getElementById('blockMicStatus');

    if (blockCamStatus) {
        blockCamStatus.innerHTML = camOk ? '📹 Camera: <strong style="color:#34d399;">Active ✅</strong>' : '📹 Camera: <strong style="color:#ef4444;">Denied / Inactive ❌</strong>';
    }
    if (blockMicStatus) {
        blockMicStatus.innerHTML = micOk ? '🎙️ Microphone: <strong style="color:#34d399;">Active ✅</strong>' : '🎙️ Microphone: <strong style="color:#ef4444;">Denied / Inactive ❌</strong>';
    }

    if (!camOk || !micOk) {
        if (accessOverlay) accessOverlay.style.display = 'flex';
        return false;
    } else {
        if (accessOverlay) accessOverlay.style.display = 'none';
        return true;
    }
}

// Unblock Retry Button Listener
const unblockRetryBtn = document.getElementById('unblockRetryBtn');
if (unblockRetryBtn) {
    unblockRetryBtn.addEventListener('click', async () => {
        unblockRetryBtn.disabled = true;
        unblockRetryBtn.textContent = '⏳ Requesting Camera & Mic Access...';
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            webcamStream = new MediaStream(stream.getVideoTracks());
            micAudioStream = new MediaStream(stream.getAudioTracks());
            attachTrackWatchers();
            initAudioMonitor(micAudioStream);

            if (liveSelfieVideo) liveSelfieVideo.srcObject = webcamStream;
            if (activeExamWebcam) activeExamWebcam.srcObject = webcamStream;
            if (examPortalWebcam) examPortalWebcam.srcObject = webcamStream;

            const accessOverlay = document.getElementById('accessBlockedOverlay');
            if (accessOverlay) accessOverlay.style.display = 'none';
        } catch (e) {
            alert('Hardware permissions are still denied. Please click the Lock 🔒 or Camera 📷 icon in your browser URL bar, set Camera & Microphone to Allow, and click retry.');
        } finally {
            unblockRetryBtn.disabled = false;
            unblockRetryBtn.textContent = '🔄 Re-Verify Permissions & Unblock Portal';
        }
    });
}

// Live Audio Input Level HUD
function initAudioMonitor(stream) {
    if (!stream || stream.getAudioTracks().length === 0) return;
    try {
        if (!audioContext) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioContextClass();
        }
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }

        const source = audioContext.createMediaStreamSource(stream);
        audioAnalyser = audioContext.createAnalyser();
        audioAnalyser.fftSize = 256;
        source.connect(audioAnalyser);

        const dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
        const hudAudioBar = document.getElementById('hudAudioBar');

        function renderAudio() {
            if (!audioAnalyser || !hudAudioBar) return;
            audioAnalyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            const pct = Math.min(100, Math.round((avg / 128) * 100));
            hudAudioBar.style.width = Math.max(8, pct) + '%';
            if (pct > 60) {
                hudAudioBar.style.background = '#f59e0b';
            } else {
                hudAudioBar.style.background = '#10b981';
            }
            audioAnimFrame = requestAnimationFrame(renderAudio);
        }

        if (audioAnimFrame) cancelAnimationFrame(audioAnimFrame);
        audioAnimFrame = requestAnimationFrame(renderAudio);

    } catch (e) {
        console.warn('Audio monitor init notice:', e);
    }
}

// Step 3: Rules & Violation Code Agreement Submit (Enforces Active Device Permissions)
consentSubmitBtn.addEventListener('click', async () => {
    consentErrorAlert.style.display = 'none';
    if (!consentCheckbox.checked) {
        consentErrorAlert.textContent = 'You must accept Violation Rules 1 through 5 to proceed.';
        consentErrorAlert.style.display = 'block';
        return;
    }

    consentSubmitBtn.disabled = true;
    consentSubmitBtn.textContent = '⏳ Verifying Device Permissions...';

    const mediaOk = await checkAndEnforceMediaPermissions();
    consentSubmitBtn.disabled = false;
    consentSubmitBtn.textContent = 'Accept Rules & Check Device Permissions ➔';

    if (!mediaOk) {
        return; // Halt: access blocked modal displayed
    }

    try {
        const res = await fetch('/api/v1/onboarding/consent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_token: activeSessionToken, consent_agreed: true })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Consent registration failed');
        }

        showWizardStep(4);
        runHardwareDiagnostic();

    } catch (err) {
        consentErrorAlert.textContent = err.message;
        consentErrorAlert.style.display = 'block';
    }
});

consentBackBtn.addEventListener('click', () => showWizardStep(2));

// Step 4: Hardware Diagnostics
async function runHardwareDiagnostic() {
    sysCheckErrorAlert.style.display = 'none';
    netSubText.textContent = 'Testing internet ping latency...';
    camSubText.textContent = 'Checking camera video stream...';
    micSubText.textContent = 'Checking audio microphone input...';

    const startPing = performance.now();
    let netOk = navigator.onLine;
    let latency = 0;
    try {
        await fetch('/api/v1/onboarding/status', { method: 'GET' });
        latency = Math.round(performance.now() - startPing);
    } catch {
        netOk = false;
    }

    if (netOk) {
        checkNetBadge.className = 'badge badge-passed';
        checkNetBadge.textContent = `CONNECTED (${latency}ms) ✅`;
        netSubText.textContent = `Connection Stable - Ping ${latency}ms`;
    } else {
        checkNetBadge.className = 'badge badge-failed';
        checkNetBadge.textContent = 'DISCONNECTED ❌';
        netSubText.textContent = 'Network connectivity error detected.';
    }

    let camOk = isCameraTrackActive();
    if (!camOk) {
        try {
            const freshCam = await navigator.mediaDevices.getUserMedia({ video: true });
            if (freshCam.getVideoTracks().length > 0) {
                webcamStream = freshCam;
                camOk = isCameraTrackActive();
            }
        } catch {
            camOk = false;
        }
    }

    if (camOk) {
        checkCamBadge.className = 'badge badge-passed';
        checkCamBadge.textContent = 'ACTIVE ✅';
        camSubText.textContent = 'Webcam video stream authorized and actively streaming.';
    } else {
        checkCamBadge.className = 'badge badge-failed';
        checkCamBadge.textContent = 'BLOCKED / INACTIVE ❌';
        camSubText.textContent = 'Camera stream offline, blocked, or permission revoked.';
    }

    let micOk = isMicrophoneTrackActive();
    if (!micOk) {
        try {
            const freshMic = await navigator.mediaDevices.getUserMedia({ audio: true });
            if (freshMic.getAudioTracks().length > 0) {
                micAudioStream = freshMic;
                micOk = isMicrophoneTrackActive();
            }
        } catch {
            micOk = false;
        }
    }

    if (micOk) {
        checkMicBadge.className = 'badge badge-passed';
        checkMicBadge.textContent = 'ACTIVE ✅';
        micSubText.textContent = 'Microphone audio input authorized and receiving signal.';
        initAudioMonitor(micAudioStream);
    } else {
        checkMicBadge.className = 'badge badge-failed';
        checkMicBadge.textContent = 'BLOCKED / INACTIVE ❌';
        micSubText.textContent = 'Microphone input offline, blocked, or permission revoked.';
    }

    return (netOk && camOk && micOk);
}

reverifyConnBtn.addEventListener('click', async () => {
    reverifyConnBtn.disabled = true;
    reverifyConnBtn.textContent = '⏳ Re-Verifying Hardware & Connection...';
    await runHardwareDiagnostic();
    reverifyConnBtn.disabled = false;
    reverifyConnBtn.textContent = '🔄 Re-Verify Connection & Devices';
});

// Step 4 Submit
sysCheckSubmitBtn.addEventListener('click', async () => {
    const passed = await runHardwareDiagnostic();
    if (!passed) {
        sysCheckErrorAlert.textContent = '⚠️ Hardware diagnostic failed: Camera or Microphone is blocked/inactive. You MUST unblock your camera and microphone to proceed.';
        sysCheckErrorAlert.style.display = 'block';
        handlePermissionRevoked('Diagnostic failed');
        return;
    }

    try {
        const res = await fetch('/api/v1/onboarding/readiness-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_token: activeSessionToken,
                media_api_supported: true,
                file_api_supported: true,
                screen_resolution_valid: true,
                identity_photo_provided: true
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Readiness check failed');
        }

        showWizardStep(5);

    } catch (err) {
        sysCheckErrorAlert.textContent = err.message;
        sysCheckErrorAlert.style.display = 'block';
    }
});

sysCheckBackBtn.addEventListener('click', () => showWizardStep(3));

// ==============================================================================
// Candidate Exam Video Submission & Violation Evidence Gallery Studio
// ==============================================================================

let candidateVideoFiles = [];

const candidateDropZone = document.getElementById('candidateDropZone');
const candidateVideoInput = document.getElementById('candidateVideoInput');
const selectedFilesTray = document.getElementById('selectedFilesTray');
const selectedFilesCountText = document.getElementById('selectedFilesCountText');
const selectedFilesList = document.getElementById('selectedFilesList');
const clearSelectedFilesBtn = document.getElementById('clearSelectedFilesBtn');
const evalCandidateVideosBtn = document.getElementById('evalCandidateVideosBtn');
const evalSampleFps = document.getElementById('evalSampleFps');
const evalProgressBox = document.getElementById('evalProgressBox');
const evalProgressStatusText = document.getElementById('evalProgressStatusText');

const evidenceGallerySection = document.getElementById('evidenceGallerySection');
const resultsSummaryCard = document.getElementById('resultsSummaryCard');
const evidenceCountBadge = document.getElementById('evidenceCountBadge');
const evidenceCardsGrid = document.getElementById('evidenceCardsGrid');

// Modal Elements
const evidenceInspectorModal = document.getElementById('evidenceInspectorModal');
const closeEvidenceModalBtn = document.getElementById('closeEvidenceModalBtn');
const inspectViolationBadge = document.getElementById('inspectViolationBadge');
const inspectModalTitle = document.getElementById('inspectModalTitle');
const inspectKeyframeImg = document.getElementById('inspectKeyframeImg');
const inspectTimestamp = document.getElementById('inspectTimestamp');
const inspectConfidence = document.getElementById('inspectConfidence');
const inspectObjects = document.getElementById('inspectObjects');
const inspectRuleText = document.getElementById('inspectRuleText');
const inspectDiskPath = document.getElementById('inspectDiskPath');

if (closeEvidenceModalBtn) {
    closeEvidenceModalBtn.addEventListener('click', () => {
        if (evidenceInspectorModal) evidenceInspectorModal.style.display = 'none';
    });
}

function openEvidenceInspector(frame) {
    if (!evidenceInspectorModal) return;
    inspectKeyframeImg.src = frame.evidence_url || '';
    inspectTimestamp.textContent = frame.timestamp || '00:00:00';
    inspectConfidence.textContent = `${((frame.peak_confidence || 0) * 100).toFixed(1)}% Match`;
    inspectObjects.textContent = (frame.flagged_objects && frame.flagged_objects.length) ? frame.flagged_objects.join(', ') : frame.event_type;
    inspectRuleText.textContent = frame.rule_triggered || 'Violation of exam integrity policy.';
    inspectDiskPath.textContent = frame.evidence_file || 'Saved on server';

    const evType = frame.event_type || 'VIOLATION';
    if (evType.includes('PHONE')) {
        inspectViolationBadge.className = 'badge badge-failed';
        inspectViolationBadge.textContent = '📱 MOBILE PHONE DETECTED';
    } else if (evType.includes('DEVICE')) {
        inspectViolationBadge.className = 'badge badge-failed';
        inspectViolationBadge.textContent = '💻 LAPTOP / SECONDARY DEVICE DETECTED';
    } else if (evType.includes('MULTIPLE')) {
        inspectViolationBadge.className = 'badge badge-failed';
        inspectViolationBadge.textContent = '👥 MULTIPLE PERSONS DETECTED';
    } else {
        inspectViolationBadge.className = 'badge badge-failed';
        inspectViolationBadge.textContent = '👤 CANDIDATE MISSING';
    }

    evidenceInspectorModal.style.display = 'flex';
}
window.openEvidenceInspector = openEvidenceInspector;


if (candidateDropZone && candidateVideoInput) {
    candidateDropZone.addEventListener('click', () => candidateVideoInput.click());
    candidateDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        candidateDropZone.classList.add('dragover');
    });
    candidateDropZone.addEventListener('dragleave', () => candidateDropZone.classList.remove('dragover'));
    candidateDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        candidateDropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleCandidateVideoSelection(e.dataTransfer.files);
        }
    });

    candidateVideoInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleCandidateVideoSelection(e.target.files);
        }
    });
}

function handleCandidateVideoSelection(fileList) {
    const newFiles = Array.from(fileList);
    candidateVideoFiles = candidateVideoFiles.concat(newFiles);
    renderSelectedFilesTray();
}

function renderSelectedFilesTray() {
    if (!selectedFilesTray || !selectedFilesList) return;
    if (candidateVideoFiles.length === 0) {
        selectedFilesTray.style.display = 'none';
        if (evalCandidateVideosBtn) evalCandidateVideosBtn.disabled = true;
        return;
    }

    selectedFilesTray.style.display = 'block';
    selectedFilesCountText.textContent = `${candidateVideoFiles.length} Video Recording${candidateVideoFiles.length > 1 ? 's' : ''} Selected`;
    if (evalCandidateVideosBtn) evalCandidateVideosBtn.disabled = false;

    selectedFilesList.innerHTML = candidateVideoFiles.map((file, idx) => `
        <div class="selected-file-chip">
            <span class="chip-icon">🎥</span>
            <span class="chip-name" title="${file.name}">${file.name}</span>
            <span class="chip-size">(${(file.size / (1024 * 1024)).toFixed(2)} MB)</span>
            <button type="button" class="chip-remove-btn" onclick="removeCandidateVideoFile(${idx})" title="Remove">✖</button>
        </div>
    `).join('');
}

window.removeCandidateVideoFile = function(idx) {
    candidateVideoFiles.splice(idx, 1);
    renderSelectedFilesTray();
};

if (clearSelectedFilesBtn) {
    clearSelectedFilesBtn.addEventListener('click', () => {
        candidateVideoFiles = [];
        renderSelectedFilesTray();
    });
}

// Evaluate Candidate Exam Videos for Violations
if (evalCandidateVideosBtn) {
    evalCandidateVideosBtn.addEventListener('click', async () => {
        if (candidateVideoFiles.length === 0) return;

        evalCandidateVideosBtn.disabled = true;
        if (evalProgressBox) evalProgressBox.style.display = 'block';
        if (evidenceGallerySection) evidenceGallerySection.style.display = 'none';

        const sampleFps = evalSampleFps ? evalSampleFps.value : '1.0';
        let allEvidenceFrames = [];
        let summaryReports = [];

        try {
            if (candidateVideoFiles.length === 1) {
                // Single Video Submission
                evalProgressStatusText.textContent = `Analyzing video frames at ${sampleFps} FPS... Detecting phones, laptops, and multiple persons...`;
                const file = candidateVideoFiles[0];
                const formData = new FormData();
                formData.append('file', file);
                formData.append('student_id', currentUsername);
                formData.append('student_name', `${currentUsername} Candidate`);
                formData.append('exam_id', 'MIDTERM-2026');

                const res = await fetch(`/api/v1/videos/process?sample_fps=${sampleFps}`, {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Video processing failed');
                }

                const report = await res.json();
                summaryReports.push(report);
                if (report.evidence_frames) {
                    allEvidenceFrames = allEvidenceFrames.concat(report.evidence_frames);
                }

            } else {
                // Multiple Videos (Batch Processing)
                evalProgressStatusText.textContent = `Batch processing ${candidateVideoFiles.length} video recordings at ${sampleFps} FPS...`;
                const formData = new FormData();
                candidateVideoFiles.forEach(f => formData.append('files', f));
                formData.append('student_id_prefix', currentUsername.split('-')[0] || 'STU');
                formData.append('exam_id', 'MIDTERM-2026');

                const res = await fetch(`/api/v1/videos/batch-process?sample_fps=${sampleFps}`, {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Batch video processing failed');
                }

                const batchData = await res.json();
                summaryReports = batchData.submissions || [];
                summaryReports.forEach(sub => {
                    if (sub.evidence_frames) {
                        allEvidenceFrames = allEvidenceFrames.concat(sub.evidence_frames);
                    }
                });
            }

            renderEvaluationResults(summaryReports, allEvidenceFrames);
            fetchCandidateSubmissions();

        } catch (err) {
            alert('Video Evaluation Error: ' + err.message);
        } finally {
            evalCandidateVideosBtn.disabled = false;
            if (evalProgressBox) evalProgressBox.style.display = 'none';
        }
    });
}

function renderEvaluationResults(reports, evidenceFrames) {
    if (!evidenceGallerySection) return;
    evidenceGallerySection.style.display = 'flex';

    // Compute aggregate metrics
    let totalPhoneSec = 0;
    let totalLaptopSec = 0;
    let totalPersonsSec = 0;
    let totalMissingSec = 0;
    let hasFailures = false;

    reports.forEach(r => {
        const cum = r.cumulative_durations || {};
        totalPhoneSec += (cum.PHONE_DETECTED || 0);
        totalLaptopSec += (cum.UNAUTHORIZED_DEVICE || 0);
        totalPersonsSec += (cum.MULTIPLE_PERSONS || 0);
        totalMissingSec += (cum.NO_PERSON_DETECTED || 0);
        if (r.overall_status === 'FAILED') hasFailures = true;
    });

    const overallVerdict = hasFailures ? 'FAILED' : 'PASSED';
    const verdictBadgeClass = hasFailures ? 'badge-failed' : 'badge-passed';

    // Update Results Summary Card
    resultsSummaryCard.innerHTML = `
        <div class="results-verdict-row">
            <div>
                <span style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Evaluation Verdict</span>
                <h3 style="margin: 4px 0 0; color: ${hasFailures ? '#ef4444' : '#10b981'}; font-size: 1.3rem;">
                    Overall Compliance: <span class="badge ${verdictBadgeClass}">${overallVerdict}</span>
                </h3>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.8rem; color: #94a3b8;">Files Evaluated: <strong>${reports.length}</strong></span>
                <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 2px;">Stored Evidence Frames: <strong>${evidenceFrames.length}</strong></div>
            </div>
        </div>

        <div class="results-metrics-chips">
            <div class="res-chip ${totalPhoneSec > 0 ? 'danger' : 'passed'}">
                📱 Phone Violations: <strong>${totalPhoneSec.toFixed(1)}s</strong> ${totalPhoneSec > 0 ? '❌ (Zero Tolerance)' : '✅'}
            </div>
            <div class="res-chip ${totalLaptopSec > 0 ? 'danger' : 'passed'}">
                💻 Secondary Laptops: <strong>${totalLaptopSec.toFixed(1)}s</strong> ${totalLaptopSec > 0 ? '❌ (Zero Tolerance)' : '✅'}
            </div>
            <div class="res-chip ${totalPersonsSec > 0 ? 'danger' : 'passed'}">
                👥 Double Person: <strong>${totalPersonsSec.toFixed(1)}s</strong> ${totalPersonsSec > 0 ? '❌ (Zero Tolerance)' : '✅'}
            </div>
            <div class="res-chip ${totalMissingSec > 5.0 ? 'danger' : 'passed'}">
                👤 Candidate Missing: <strong>${totalMissingSec.toFixed(1)}s</strong>
            </div>
        </div>
    `;

    // Update HUD Status indicators
    const hudPhoneStatus = document.getElementById('hudPhoneStatus');
    const hudPersonsStatus = document.getElementById('hudPersonsStatus');
    const hudLaptopStatus = document.getElementById('hudLaptopStatus');
    const hudIntegrityScore = document.getElementById('hudIntegrityScore');

    if (hudPhoneStatus) {
        hudPhoneStatus.textContent = totalPhoneSec > 0 ? `${totalPhoneSec.toFixed(1)}s Detected ❌` : '0 Detected (Clean) ✅';
        hudPhoneStatus.className = totalPhoneSec > 0 ? 'text-failed' : 'text-passed';
    }
    if (hudPersonsStatus) {
        hudPersonsStatus.textContent = totalPersonsSec > 0 ? `${totalPersonsSec.toFixed(1)}s Detected ❌` : '0 Detected (Clean) ✅';
        hudPersonsStatus.className = totalPersonsSec > 0 ? 'text-failed' : 'text-passed';
    }
    if (hudLaptopStatus) {
        hudLaptopStatus.textContent = totalLaptopSec > 0 ? `${totalLaptopSec.toFixed(1)}s Detected ❌` : '0 Detected (Clean) ✅';
        hudLaptopStatus.className = totalLaptopSec > 0 ? 'text-failed' : 'text-passed';
    }
    if (hudIntegrityScore) {
        hudIntegrityScore.textContent = hasFailures ? 'POLICY VIOLATED ❌' : '100% SECURE ✅';
        hudIntegrityScore.className = hasFailures ? 'text-failed' : 'highlight-green';
    }

    // Render Evidence Cards
    evidenceCountBadge.textContent = `${evidenceFrames.length} Evidence Keyframes Saved`;
    evidenceCountBadge.className = evidenceFrames.length > 0 ? 'badge badge-failed' : 'badge badge-passed';

    if (evidenceFrames.length === 0) {
        evidenceCardsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 32px; background: #090d16; border: 1px dashed #10b981; border-radius: 12px; text-align: center;">
                <span style="font-size: 2.2rem; display: block; margin-bottom: 8px;">🎉</span>
                <strong style="color: #34d399; font-size: 1.1rem;">Zero Violations Detected!</strong>
                <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                    All video frames analyzed were clean. Candidate maintained single presence without unauthorized mobile devices or laptops.
                </p>
            </div>
        `;
        return;
    }

    window._currentEvidenceFrames = evidenceFrames;

    evidenceCardsGrid.innerHTML = evidenceFrames.map((frame, idx) => {
        const evType = frame.event_type || 'VIOLATION';
        let tagClass = 'phone';
        let tagLabel = '📱 MOBILE PHONE';

        if (evType.includes('DEVICE')) {
            tagClass = 'laptop';
            tagLabel = '💻 LAPTOP / DEVICE';
        } else if (evType.includes('MULTIPLE')) {
            tagClass = 'persons';
            tagLabel = '👥 DOUBLE PERSON';
        } else if (evType.includes('NO_PERSON')) {
            tagClass = 'missing';
            tagLabel = '👤 CANDIDATE MISSING';
        }

        return `
            <div class="evidence-card">
                <div class="evidence-card-img-wrap" onclick="openEvidenceInspector(window._currentEvidenceFrames[${idx}])" title="Click to Inspect Keyframe">
                    <img src="${frame.evidence_url}" alt="${tagLabel}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'300\\' height=\\'180\\' viewBox=\\'0 0 300 180\\'><rect width=\\'300\\' height=\\'180\\' fill=\\'%230f172a\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'%23ef4444\\' text-anchor=\\'middle\\' font-family=\\'sans-serif\\' font-size=\\'14\\'>Evidence Frame Saved</text></svg>'">
                </div>
                <div class="evidence-card-body">
                    <span class="violation-tag ${tagClass}">${tagLabel}</span>
                    <div class="evidence-card-meta">
                        <span>⏱️ ${frame.timestamp}</span>
                        <span>🎯 ${((frame.peak_confidence || 0) * 100).toFixed(1)}% Conf</span>
                    </div>
                    <button type="button" class="btn btn-secondary btn-inspect-evidence" onclick="openEvidenceInspector(window._currentEvidenceFrames[${idx}])">
                        🔍 Inspect Keyframe Bounding Box
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function switchView(mode) {
    if (mode === 'exam') {
        if (examDeviceContainer) examDeviceContainer.style.display = 'flex';
        if (dashboardContent) dashboardContent.style.display = 'none';
        if (viewExamPortalBtn) viewExamPortalBtn.classList.add('active');
        if (viewExaminerDashBtn) viewExaminerDashBtn.classList.remove('active');
        if (navSectionBreadcrumb) navSectionBreadcrumb.textContent = 'Exam Device';
        if (navExamDeviceBtn) navExamDeviceBtn.classList.add('active');
        if (navExaminerBtn) navExaminerBtn.classList.remove('active');
        if (statusBadge) {
            statusBadge.textContent = `Exam Device Active (${currentUsername || 'Candidate'})`;
            statusBadge.className = 'status-badge passed';
        }
    } else {
        if (examDeviceContainer) examDeviceContainer.style.display = 'none';
        if (dashboardContent) dashboardContent.style.display = 'flex';
        if (viewExamPortalBtn) viewExamPortalBtn.classList.remove('active');
        if (viewExaminerDashBtn) viewExaminerDashBtn.classList.add('active');
        if (navSectionBreadcrumb) navSectionBreadcrumb.textContent = 'Examiner Dashboard';
        if (navExamDeviceBtn) navExamDeviceBtn.classList.remove('active');
        if (navExaminerBtn) navExaminerBtn.classList.add('active');
        if (statusBadge) {
            statusBadge.textContent = `Examiner Active (${currentUsername || 'Admin'})`;
            statusBadge.className = 'status-badge passed';
        }
        fetchCandidateSubmissions();
        if (typeof loadClientCompanies === 'function') loadClientCompanies();
        if (typeof fetchAdminPolicyBreaches === 'function') fetchAdminPolicyBreaches();
    }
}

if (viewExamPortalBtn) viewExamPortalBtn.addEventListener('click', () => switchView('exam'));
if (viewExaminerDashBtn) viewExaminerDashBtn.addEventListener('click', () => switchView('examiner'));
if (examSwitchToExaminerBtn) examSwitchToExaminerBtn.addEventListener('click', () => switchView('examiner'));
if (navExamDeviceBtn) navExamDeviceBtn.addEventListener('click', (e) => { e.preventDefault(); switchView('exam'); });
if (navExaminerBtn) navExaminerBtn.addEventListener('click', (e) => { e.preventDefault(); switchView('examiner'); });

let liveScannerIntervalId = null;
let liveScannerBusy = false;

function startLiveWorkspaceScanner() {
    if (liveScannerIntervalId) return;

    const scannerVideo = document.getElementById('examPortalWebcam');
    const scannerCanvas = document.getElementById('liveScannerCanvas');
    const scannerCard = document.getElementById('hudMobileScannerCard');
    const pulseDot = document.getElementById('mobileScannerPulse');
    const statusBadge = document.getElementById('mobileScannerStatusBadge');
    const chipPhoneVal = document.getElementById('chipPhoneVal');
    const chipPhoneDot = document.getElementById('chipPhoneDot');
    const chipPhoneScanner = document.getElementById('chipPhoneScanner');
    const chipLaptopVal = document.getElementById('chipLaptopVal');
    const chipLaptopDot = document.getElementById('chipLaptopDot');
    const chipLaptopScanner = document.getElementById('chipLaptopScanner');
    const chipPersonVal = document.getElementById('chipPersonVal');
    const chipPersonDot = document.getElementById('chipPersonDot');
    const chipPersonScanner = document.getElementById('chipPersonScanner');

    const hudPhoneStatus = document.getElementById('hudPhoneStatus');
    const hudPersonsStatus = document.getElementById('hudPersonsStatus');
    const hudLaptopStatus = document.getElementById('hudLaptopStatus');
    const hudIntegrityScore = document.getElementById('hudIntegrityScore');

    liveScannerIntervalId = setInterval(async () => {
        if (liveScannerBusy) return;
        if (!scannerVideo || scannerVideo.paused || scannerVideo.ended || scannerVideo.readyState < 2) return;
        if (!scannerCanvas) return;

        try {
            liveScannerBusy = true;
            const scannerCtx = scannerCanvas.getContext('2d');
            scannerCanvas.width = 320;
            scannerCanvas.height = 240;
            scannerCtx.drawImage(scannerVideo, 0, 0, 320, 240);
            const b64Data = scannerCanvas.toDataURL('image/jpeg', 0.7);

            const res = await fetch('/api/v1/sessions/scan-frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    frame_data: b64Data,
                    student_id: currentUsername || 'STU-001'
                })
            });

            if (!res.ok) {
                liveScannerBusy = false;
                return;
            }

            const data = await res.json();

            // Update tri-meter: Phone
            if (data.phone_detected) {
                if (chipPhoneVal) { chipPhoneVal.textContent = '1 Mobile Detected ❌'; chipPhoneVal.className = 'chip-val text-failed'; }
                if (chipPhoneDot) chipPhoneDot.className = 'chip-status-dot danger';
                if (chipPhoneScanner) chipPhoneScanner.className = 'tri-meter-chip alert-state';
                if (hudPhoneStatus) {
                    hudPhoneStatus.textContent = '1 Phone in Workspace ❌';
                    hudPhoneStatus.className = 'text-failed';
                }
            } else {
                if (chipPhoneVal) { chipPhoneVal.textContent = '0 Detected (Clean) ✅'; chipPhoneVal.className = 'chip-val text-passed'; }
                if (chipPhoneDot) chipPhoneDot.className = 'chip-status-dot clean';
                if (chipPhoneScanner) chipPhoneScanner.className = 'tri-meter-chip';
                if (hudPhoneStatus) {
                    hudPhoneStatus.textContent = '0 Detected (Clean) ✅';
                    hudPhoneStatus.className = 'text-passed';
                }
            }

            // Update tri-meter: Laptop
            if (data.laptop_detected) {
                if (chipLaptopVal) { chipLaptopVal.textContent = '1 Secondary Laptop ❌'; chipLaptopVal.className = 'chip-val text-failed'; }
                if (chipLaptopDot) chipLaptopDot.className = 'chip-status-dot danger';
                if (chipLaptopScanner) chipLaptopScanner.className = 'tri-meter-chip alert-state';
                if (hudLaptopStatus) {
                    hudLaptopStatus.textContent = 'Secondary Laptop in Frame ❌';
                    hudLaptopStatus.className = 'text-failed';
                }
            } else {
                if (chipLaptopVal) { chipLaptopVal.textContent = '0 Detected (Clean) ✅'; chipLaptopVal.className = 'chip-val text-passed'; }
                if (chipLaptopDot) chipLaptopDot.className = 'chip-status-dot clean';
                if (chipLaptopScanner) chipLaptopScanner.className = 'tri-meter-chip';
                if (hudLaptopStatus) {
                    hudLaptopStatus.textContent = '0 Detected (Clean) ✅';
                    hudLaptopStatus.className = 'text-passed';
                }
            }

            // Update tri-meter: Persons
            if (data.multiple_persons) {
                if (chipPersonVal) { chipPersonVal.textContent = 'Multiple Persons Detected ❌'; chipPersonVal.className = 'chip-val text-failed'; }
                if (chipPersonDot) chipPersonDot.className = 'chip-status-dot danger';
                if (chipPersonScanner) chipPersonScanner.className = 'tri-meter-chip alert-state';
                if (hudPersonsStatus) {
                    hudPersonsStatus.textContent = 'Double Person Detected ❌';
                    hudPersonsStatus.className = 'text-failed';
                }
            } else if (!data.person_present) {
                if (chipPersonVal) { chipPersonVal.textContent = 'Candidate Missing ⚠️'; chipPersonVal.className = 'chip-val text-warning'; }
                if (chipPersonDot) chipPersonDot.className = 'chip-status-dot danger';
                if (chipPersonScanner) chipPersonScanner.className = 'tri-meter-chip alert-state';
                if (hudPersonsStatus) {
                    hudPersonsStatus.textContent = 'Candidate Missing ⚠️';
                    hudPersonsStatus.className = 'text-warning';
                }
            } else {
                if (chipPersonVal) { chipPersonVal.textContent = 'Single Candidate (Clean) ✅'; chipPersonVal.className = 'chip-val text-passed'; }
                if (chipPersonDot) chipPersonDot.className = 'chip-status-dot clean';
                if (chipPersonScanner) chipPersonScanner.className = 'tri-meter-chip';
                if (hudPersonsStatus) {
                    hudPersonsStatus.textContent = 'Single Presence (Clean) ✅';
                    hudPersonsStatus.className = 'text-passed';
                }
            }

            // Overall Shield Status
            const hasViolation = data.phone_detected || data.laptop_detected || data.multiple_persons;
            if (hasViolation) {
                if (scannerCard) scannerCard.className = 'hud-mobile-shield-card violation-alert';
                if (pulseDot) pulseDot.className = 'scanner-pulse-dot danger';
                if (statusBadge) {
                    statusBadge.textContent = '⚠️ VIOLATION DETECTED';
                    statusBadge.className = 'shield-status-pill danger';
                }
                if (hudIntegrityScore) {
                    hudIntegrityScore.textContent = 'POLICY VIOLATED ❌';
                    hudIntegrityScore.className = 'text-failed';
                }

                // Dispatch AI Proctor Warning directly to Chatbot & Warning Banner
                if (typeof window.dispatchChatbotCameraWarning === 'function') {
                    window.dispatchChatbotCameraWarning(data);
                }
            } else {
                if (scannerCard) scannerCard.className = 'hud-mobile-shield-card';
                if (pulseDot) pulseDot.className = 'scanner-pulse-dot';
                if (statusBadge) {
                    statusBadge.textContent = 'ACTIVE SCANNING';
                    statusBadge.className = 'shield-status-pill clean';
                }
                if (hudIntegrityScore && (!hudPhoneStatus || !hudPhoneStatus.className.includes('failed'))) {
                    hudIntegrityScore.textContent = '100% SECURE ✅';
                    hudIntegrityScore.className = 'highlight-green';
                }
            }

        } catch (scanErr) {
            console.warn('Live workspace scan warning:', scanErr);
        } finally {
            liveScannerBusy = false;
        }
    }, 2500);
}

function activateExamPortal() {
    switchView('exam');

    if (examCandidateName) examCandidateName.textContent = currentUsername;
    if (examDeviceBadge) examDeviceBadge.textContent = 'DEV-LINUX-7112';
    if (examFaceScoreBadge) examFaceScoreBadge.textContent = `${lastFaceMatchPct} Verified`;

    // Mount camera stream to exam proctor HUD
    if (webcamStream) {
        if (examPortalWebcam) examPortalWebcam.srcObject = webcamStream;
        if (activeExamWebcam) activeExamWebcam.srcObject = webcamStream;
    }

    if (micAudioStream) {
        initAudioMonitor(micAudioStream);
    }

    // Start Real-Time Mobile Device & Gadget Shield Scanner
    startLiveWorkspaceScanner();
}

// Step 5: Launch Session (Enforces Continuous Cam & Mic Streams)
launchSessionBtn.addEventListener('click', async () => {
    launchSessionBtn.disabled = true;
    launchSessionBtn.textContent = '⏳ Checking Device Permissions...';

    const mediaOk = await checkAndEnforceMediaPermissions();
    launchSessionBtn.disabled = false;
    launchSessionBtn.textContent = '🚀 Launch Proctored Exam Portal';

    if (!mediaOk) {
        return; // Halt: access blocked modal displayed
    }

    onboardingModal.style.display = 'none';
    liveHardwareBadges.style.display = 'flex';

    activateExamPortal();
});

reopenOnboardingBtn.addEventListener('click', () => {
    onboardingModal.style.display = 'flex';
    showWizardStep(1);
});

// System Data Reset Button
resetSystemBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to reset all database submissions and serial counters?')) return;

    try {
        const res = await fetch('/api/v1/system/reset', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        location.reload();
    } catch (err) {
        alert('Reset failed: ' + err.message);
    }
});

// File Drag & Drop & Upload handling
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleSelectedFiles(e.dataTransfer.files);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleSelectedFiles(e.target.files);
    }
});

function handleSelectedFiles(fileList) {
    selectedFiles = Array.from(fileList);
    if (selectedFiles.length === 1) {
        const file = selectedFiles[0];
        fileNameText.textContent = file.name;
        fileSizeText.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        fileInfo.style.display = 'flex';

        videoPreview.src = URL.createObjectURL(file);
        videoPreviewBox.style.display = 'block';
    } else {
        fileNameText.textContent = `${selectedFiles.length} video files selected for batch analysis`;
        fileSizeText.textContent = 'Multiple Clips';
        fileInfo.style.display = 'flex';
        videoPreviewBox.style.display = 'none';
    }
    analyzeBtn.disabled = false;
}

// Analyze Candidate Video Submission
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFiles.length) return;

    loadingOverlay.style.display = 'flex';
    analyzeBtn.disabled = true;

    try {
        if (selectedFiles.length === 1) {
            const formData = new FormData();
            const sId = studentIdInput ? studentIdInput.value.trim() : currentUsername;
            const sName = studentNameInput ? studentNameInput.value.trim() : 'Candidate Name';
            const eId = examIdInput ? examIdInput.value.trim() : 'MIDTERM-2026';

            formData.append('student_id', sId || currentUsername);
            formData.append('student_name', sName);
            formData.append('exam_id', eId);

            const res = await fetch('/api/v1/videos/process?sample_fps=1.0', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) throw new Error('Video processing failed');
            await fetchCandidateSubmissions();

        } else {
            const formData = new FormData();
            selectedFiles.forEach(f => formData.append('files', f));
            formData.append('student_id_prefix', 'STU');
            const eIdBatch = examIdInput ? examIdInput.value.trim() : 'MIDTERM-2026';
            formData.append('exam_id', eIdBatch);

            const res = await fetch('/api/v1/videos/batch-process?sample_fps=1.0', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) throw new Error('Batch video processing failed');
            await fetchCandidateSubmissions();
        }
    } catch (err) {
        alert('Analysis Error: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

// Fetch Examiner Directory Submissions
async function fetchCandidateSubmissions() {
    try {
        const res = await fetch('/api/v1/candidates');
        if (!res.ok) return;

        const data = await res.json();
        renderCandidateTable(data.submissions || []);
    } catch (err) {
        console.error('Failed fetching candidates:', err);
    }
}

function renderCandidateTable(submissions) {
    if (!submissions.length) {
        candidateTableBody.innerHTML = `<tr><td colspan="6" class="empty-table-cell">No candidate submissions recorded yet. Upload an exam video on the left to evaluate.</td></tr>`;
        return;
    }

    const query = searchStudentId.value.trim().toLowerCase();
    const statusFilt = filterStatus.value;

    const filtered = submissions.filter(s => {
        const matchesQuery = !query ||
            s.student_id.toLowerCase().includes(query) ||
            (s.student_name && s.student_name.toLowerCase().includes(query)) ||
            (s.exam_id && s.exam_id.toLowerCase().includes(query));
        const matchesStatus = !statusFilt || s.overall_status === statusFilt;
        return matchesQuery && matchesStatus;
    });

    candidateTableBody.innerHTML = filtered.map(s => {
        const isPassed = s.overall_status === 'PASSED';
        const badgeClass = isPassed ? 'badge-passed' : 'badge-failed';
        return `
            <tr>
                <td><strong>${s.student_id}</strong><br><small style="color: #64748b;">${s.student_name || 'N/A'}</small></td>
                <td>${s.exam_id || 'MIDTERM'}</td>
                <td>${s.video_filename}</td>
                <td>${s.phone_duration_seconds.toFixed(1)}s</td>
                <td><span class="badge ${badgeClass}">${s.overall_status}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="inspectCandidate('${s.submission_id}')">🔍 Inspect</button>
                </td>
            </tr>
        `;
    }).join('');
}

window.inspectCandidate = async function(submissionId) {
    try {
        const res = await fetch(`/api/v1/submissions/${submissionId}`);
        if (!res.ok) return;

        const data = await res.json();
        const studentId = data.student_id || data.submission_id || 'STU-001';
        inspectTitle.textContent = `Candidate Report: ${studentId}`;

        const isPassed = data.overall_status === 'PASSED';
        const statusBadgeHTML = isPassed ?
            `<span class="badge badge-passed">PASSED ✅</span>` :
            `<span class="badge badge-failed">FAILED ❌</span>`;

        // Gather evidence frames
        let evidenceFrames = data.evidence_frames || [];
        try {
            const evRes = await fetch(`/api/v1/candidates/${encodeURIComponent(studentId)}/evidence`);
            if (evRes.ok) {
                const evData = await evRes.json();
                if (evData.evidence_frames && evData.evidence_frames.length > 0) {
                    const existingUrls = new Set(evidenceFrames.map(f => f.evidence_url));
                    evData.evidence_frames.forEach(ef => {
                        if (!existingUrls.has(ef.evidence_url)) {
                            evidenceFrames.push(ef);
                        }
                    });
                }
            }
        } catch (e) {
            console.warn('Could not fetch candidate evidence:', e);
        }

        window._drawerEvidenceFrames = evidenceFrames;

        let evidenceGalleryHTML = '';
        if (evidenceFrames.length > 0) {
            const cardsHTML = evidenceFrames.map((frame, idx) => {
                const evType = frame.event_type || 'VIOLATION';
                let tagClass = 'phone';
                let tagLabel = '📱 MOBILE PHONE';
                if (evType.includes('DEVICE') || evType.includes('LAPTOP')) {
                    tagClass = 'laptop';
                    tagLabel = '💻 2ND LAPTOP';
                } else if (evType.includes('MULTIPLE')) {
                    tagClass = 'persons';
                    tagLabel = '👥 DOUBLE PERSON';
                } else if (evType.includes('NO_PERSON')) {
                    tagClass = 'missing';
                    tagLabel = '👤 MISSING';
                }

                return `
                    <div class="drawer-evidence-card" onclick="openEvidenceInspector(window._drawerEvidenceFrames[${idx}])" title="Click to enlarge proof">
                        <img src="${frame.evidence_url}" alt="${tagLabel}" class="drawer-evidence-thumb" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'120\\'><rect width=\\'200\\' height=\\'120\\' fill=\\'%23090d16\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'%23ef4444\\' text-anchor=\\'middle\\' font-size=\\'12\\'>Proof Frame Saved</text></svg>'">
                        <div class="drawer-evidence-info">
                            <span class="drawer-evidence-tag ${tagClass}">${tagLabel}</span>
                            <div class="drawer-evidence-meta">⏱️ ${frame.timestamp || frame.created_at || 'Stored'}</div>
                        </div>
                    </div>
                `;
            }).join('');

            evidenceGalleryHTML = `
                <div class="drawer-evidence-section">
                    <div class="drawer-evidence-header">
                        <h4 class="drawer-evidence-title">📸 Stored Violation Proof Frames (${evidenceFrames.length})</h4>
                        <span class="badge badge-failed">VIOLATIONS FLAGGED</span>
                    </div>
                    <p style="font-size: 0.76rem; color: #94a3b8; margin: 0 0 8px 0;">
                        Annotated keyframes saved under <code>evidence/candidates/${studentId}/</code> highlighting unauthorized devices or persons. Click any image to view enlarged bounding box.
                    </p>
                    <div class="drawer-evidence-grid">
                        ${cardsHTML}
                    </div>
                </div>
            `;
        } else {
            evidenceGalleryHTML = `
                <div class="drawer-evidence-section">
                    <div class="drawer-evidence-header">
                        <h4 class="drawer-evidence-title">📸 Stored Violation Proof Frames</h4>
                        <span class="badge badge-passed">CLEAN RECORD</span>
                    </div>
                    <div style="padding: 16px; background: rgba(16, 185, 129, 0.1); border: 1px dashed #10b981; border-radius: 8px; text-align: center; color: #34d399; font-size: 0.82rem;">
                        🎉 Verified Clean — No violation proof frames were recorded for candidate <strong>${studentId}</strong>.
                    </div>
                </div>
            `;
        }

        drawerBody.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4>Overall Compliance Status: ${statusBadgeHTML}</h4>
                    <span style="font-size: 0.8rem; color: #64748b;">Duration: ${data.video_duration_seconds || 0}s</span>
                </div>
                <div style="background: #1e293b; padding: 12px; border-radius: 8px; font-size: 0.82rem; display: flex; flex-direction: column; gap: 6px;">
                    <div>📱 Phone Violation Duration: <strong>${data.phone_duration_seconds || 0}s</strong> (Zero Tolerance)</div>
                    <div>💻 Secondary Laptop Duration: <strong>${data.device_duration_seconds || 0}s</strong> (Zero Tolerance)</div>
                    <div>👥 Multi-Person Duration: <strong>${data.multiple_persons_duration_seconds || 0}s</strong> (Zero Tolerance)</div>
                    <div>👤 Missing Candidate Duration: <strong>${data.missing_duration_seconds || 0}s</strong></div>
                </div>
                ${evidenceGalleryHTML}
            </div>
        `;
        inspectionDrawer.style.display = 'block';
    } catch (err) {
        alert('Failed fetching candidate report: ' + err.message);
    }
};

closeDrawerBtn.addEventListener('click', () => { inspectionDrawer.style.display = 'none'; });
refreshCandidatesBtn.addEventListener('click', fetchCandidateSubmissions);
searchStudentId.addEventListener('input', fetchCandidateSubmissions);
filterStatus.addEventListener('change', fetchCandidateSubmissions);

// Initialize Onboarding Modal on Page Load
window.addEventListener('DOMContentLoaded', () => {
    onboardingModal.style.display = 'flex';
    showWizardStep(1);
});

// ==============================================================================
// AI Proctor & Policy Chatbot (Port 8000)
// Real-time camera warning delivery for phones, laptops, and double persons (Non-terminating)
// ==============================================================================
const chatbotForm = document.getElementById('chatbotForm');
const chatbotQueryInput = document.getElementById('chatbotQueryInput');
const chatbotFeed = document.getElementById('chatbotFeed');
const chatLiveWarningBanner = document.getElementById('chatLiveWarningBanner');
const liveWarningTitle = document.getElementById('liveWarningTitle');
const liveWarningText = document.getElementById('liveWarningText');
const ackChatWarningBtn = document.getElementById('ackChatWarningBtn');
const clearChatMessagesBtn = document.getElementById('clearChatMessagesBtn');
const chatbotSuggestionsTray = document.getElementById('chatbotSuggestionsTray');

// Cooldown tracker to prevent repetitive warning spam
const violationCooldowns = {
    phone: 0,
    laptop: 0,
    person: 0
};
const WARNING_COOLDOWN_MS = 7000; // 7 seconds between duplicate chatbot warnings

function appendChatMessage(sender, text, type = 'bot', timeStr = null) {
    if (!chatbotFeed) return;
    const now = new Date();
    const timeDisplay = timeStr || now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${type}-message`;

    let senderHtml = '';
    if (type === 'warning') {
        senderHtml = `<div class="bubble-sender warning">${sender}</div>`;
    } else if (type === 'bot') {
        senderHtml = `<div class="bubble-sender">${sender}</div>`;
    } else {
        senderHtml = `<div class="bubble-sender" style="color: #bfdbfe;">${sender}</div>`;
    }

    bubble.innerHTML = `
        ${senderHtml}
        <div class="bubble-text">${text}</div>
        <div class="bubble-time">${timeDisplay}</div>
    `;

    chatbotFeed.appendChild(bubble);
    chatbotFeed.scrollTop = chatbotFeed.scrollHeight;
}

// Global function called when camera scanner detects phone, laptop, or double person
window.dispatchChatbotCameraWarning = function(data) {
    const now = Date.now();

    if (data.phone_detected && (now - violationCooldowns.phone > WARNING_COOLDOWN_MS)) {
        violationCooldowns.phone = now;
        const warningMsg = data.warning_chat_message || 
            "A mobile phone was detected in your camera frame. In accordance with Section 4.2 of the Academic Integrity Code, all cellular devices are strictly prohibited. Please remove the phone immediately.\n\n🛡️ Notice: You have NOT been terminated. This is an official advisory warning.";
        
        showLiveWarningBanner("⚠️ PROCTOR WARNING: Mobile Phone in Workspace", warningMsg);
        appendChatMessage("⚠️ AI Proctor Warning (Mobile Phone)", warningMsg.replace(/\n/g, '<br>'), 'warning');
    }

    if (data.laptop_detected && (now - violationCooldowns.laptop > WARNING_COOLDOWN_MS)) {
        violationCooldowns.laptop = now;
        const warningMsg = data.warning_chat_message || 
            "An unauthorized secondary laptop or display was detected in your workspace. Pursuant to Section 4.3, auxiliary computing devices are prohibited. Please close and remove the secondary device.\n\n🛡️ Notice: You have NOT been terminated. Please adjust your workspace.";
        
        showLiveWarningBanner("⚠️ PROCTOR WARNING: Secondary Laptop Detected", warningMsg);
        appendChatMessage("⚠️ AI Proctor Warning (Secondary Laptop)", warningMsg.replace(/\n/g, '<br>'), 'warning');
    }

    if (data.multiple_persons && (now - violationCooldowns.person > WARNING_COOLDOWN_MS)) {
        violationCooldowns.person = now;
        const warningMsg = data.warning_chat_message || 
            "Multiple individuals / double person detected in your room. Under Section 5.1, examinations require solitary isolation. Please ensure all secondary individuals exit the room immediately.\n\n🛡️ Notice: You have NOT been terminated. Please restore solitary room isolation.";
        
        showLiveWarningBanner("⚠️ PROCTOR WARNING: Double Person Detected", warningMsg);
        appendChatMessage("⚠️ AI Proctor Warning (Double Person)", warningMsg.replace(/\n/g, '<br>'), 'warning');
    }
};

function showLiveWarningBanner(title, message) {
    if (!chatLiveWarningBanner) return;
    if (liveWarningTitle) liveWarningTitle.textContent = title;
    if (liveWarningText) liveWarningText.textContent = message.split('\n')[0];
    chatLiveWarningBanner.style.display = 'block';
}

if (ackChatWarningBtn) {
    ackChatWarningBtn.addEventListener('click', () => {
        if (chatLiveWarningBanner) chatLiveWarningBanner.style.display = 'none';
    });
}

if (clearChatMessagesBtn) {
    clearChatMessagesBtn.addEventListener('click', () => {
        if (chatbotFeed) {
            chatbotFeed.innerHTML = `
                <div class="chat-bubble bot-message intro">
                    <div class="bubble-sender">🤖 AI Proctor Assistant</div>
                    <div class="bubble-text">
                        Chat cleared. I am monitoring for mobile phones, secondary laptops, and double persons. Feel free to ask about any exam rules.
                        <br><br>
                        <em>🛡️ AI models do NOT terminate candidates.</em>
                    </div>
                    <div class="bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
            `;
        }
    });
}

// Handle candidate text query submit
async function handleChatSubmit(e) {
    if (e) e.preventDefault();
    if (!chatbotQueryInput) return;
    const query = chatbotQueryInput.value.trim();
    if (!query) return;

    appendChatMessage("You (Candidate)", query, 'user');
    chatbotQueryInput.value = '';

    // Show temporary typing indicator
    const typingId = 'typing-' + Date.now();
    const typingBubble = document.createElement('div');
    typingBubble.id = typingId;
    typingBubble.className = 'chat-bubble bot-message';
    typingBubble.innerHTML = '<span style="color: #94a3b8; font-style: italic;">Consulting verified examination policies...</span>';
    chatbotFeed.appendChild(typingBubble);
    chatbotFeed.scrollTop = chatbotFeed.scrollHeight;

    try {
        const res = await fetch('/api/v1/chat/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                student_id: currentUsername || 'STU-001'
            })
        });

        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        if (res.ok) {
            const data = await res.json();
            let text = data.response;
            if (data.citations && data.citations.length > 0) {
                text += `<br><br><small style="color: #38bdf8;">📚 Citation: ${data.citations.join(' | ')}</small>`;
            }
            appendChatMessage("🤖 AI Proctor Assistant", text, 'bot');
        } else {
            appendChatMessage("🤖 AI Proctor Assistant", "Sorry, I encountered an issue retrieving that policy. Standard rules apply: solitary room, no phones, no secondary laptops.", 'bot');
        }
    } catch (err) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        appendChatMessage("🤖 AI Proctor Assistant", "Connection error reaching policy knowledge base. Please adhere to quiet room and device rules.", 'bot');
    }
}

if (chatbotForm) chatbotForm.addEventListener('submit', handleChatSubmit);

// Suggestion chip clicks
if (chatbotSuggestionsTray) {
    chatbotSuggestionsTray.addEventListener('click', (e) => {
        const chip = e.target.closest('.chat-chip');
        if (!chip) return;
        const q = chip.getAttribute('data-query');
        if (q && chatbotQueryInput) {
            chatbotQueryInput.value = q;
            handleChatSubmit();
        }
    });
}

// ==============================================================================
// Multi-Company Policy RAG Breach Dossier & Evidence Gallery (Admin Only)
// ==============================================================================
const adminCompanySelect = document.getElementById('adminCompanySelect');
const refreshAdminEvidenceBtn = document.getElementById('refreshAdminEvidenceBtn');
const activeCompanyName = document.getElementById('activeCompanyName');
const activeCompanyDesc = document.getElementById('activeCompanyDesc');
const activeCompanyStrictness = document.getElementById('activeCompanyStrictness');
const adminBreachCountBadge = document.getElementById('adminBreachCountBadge');
const adminEvidenceCardsGrid = document.getElementById('adminEvidenceCardsGrid');

async function loadClientCompanies() {
    try {
        const res = await fetch('/api/v1/policies/companies');
        if (!res.ok) return;
        const data = await res.json();
        
        if (adminCompanySelect && data.companies) {
            adminCompanySelect.innerHTML = '';
            data.companies.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = `${c.name} (${c.strictness_level})`;
                if (c.id === data.active_company_id) opt.selected = true;
                adminCompanySelect.appendChild(opt);
            });
        }

        if (data.active_company) {
            updateActiveCompanyBanner(data.active_company);
        }
    } catch (err) {
        console.warn('Error loading client companies:', err);
    }
}

function updateActiveCompanyBanner(company) {
    if (activeCompanyName) activeCompanyName.textContent = company.name;
    if (activeCompanyDesc) activeCompanyDesc.textContent = company.description;
    if (activeCompanyStrictness) {
        activeCompanyStrictness.textContent = company.strictness_level;
        if (company.strictness_level === 'MAXIMUM_STRICT') {
            activeCompanyStrictness.className = 'badge badge-failed';
        } else {
            activeCompanyStrictness.className = 'badge badge-warning';
        }
    }
}

if (adminCompanySelect) {
    adminCompanySelect.addEventListener('change', async (e) => {
        const selectedId = e.target.value;
        try {
            const res = await fetch('/api/v1/policies/companies/active', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_id: selectedId })
            });
            if (res.ok) {
                const data = await res.json();
                if (data.company) {
                    updateActiveCompanyBanner(data.company);
                }
                fetchAdminPolicyBreaches();
            }
        } catch (err) {
            console.error('Failed to switch company policy:', err);
        }
    });
}

async function fetchAdminPolicyBreaches() {
    if (!adminEvidenceCardsGrid) return;
    try {
        const res = await fetch('/api/v1/admin/policy-breaches');
        if (!res.ok) return;
        const data = await res.json();

        if (adminBreachCountBadge) {
            const count = data.total_breaches || 0;
            adminBreachCountBadge.textContent = `${count} Breach${count === 1 ? '' : 'es'} Logged`;
            adminBreachCountBadge.className = (count > 0) ? 'badge badge-failed' : 'badge badge-passed';
        }

        if (!data.breaches || data.breaches.length === 0) {
            adminEvidenceCardsGrid.innerHTML = `
                <div class="empty-evidence-msg" style="grid-column: 1 / -1; padding: 30px; text-align: center; color: #64748b; background: rgba(15, 23, 42, 0.5); border-radius: 8px; border: 1px dashed #334155;">
                    No company policy breaches logged yet. Real-time webcam and video evaluations with detected phones, laptops, or secondary persons will archive annotated evidence here for Admin inspection.
                </div>
            `;
            return;
        }

        adminEvidenceCardsGrid.innerHTML = data.breaches.slice().reverse().map(b => `
            <div class="admin-evidence-card" style="background: #0f172a; border: 1px solid #ef4444; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column;">
                <div style="position: relative; width: 100%; height: 180px; background: #020617; display: flex; align-items: center; justify-content: center;">
                    ${b.evidence_url ? `<img src="${b.evidence_url}" alt="Breach Keyframe" style="width: 100%; height: 100%; object-fit: contain;">` : `<span style="color: #64748b;">No Frame Image</span>`}
                    <span style="position: absolute; top: 8px; left: 8px; background: rgba(239, 68, 68, 0.9); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">
                        ${b.violation_type.toUpperCase().replace('_', ' ')}
                    </span>
                    <span style="position: absolute; top: 8px; right: 8px; background: rgba(15, 23, 42, 0.85); color: #94a3b8; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-family: monospace;">
                        ${b.timestamp.split('T')[1] ? b.timestamp.split('T')[1].split('.')[0] : b.timestamp}
                    </span>
                </div>
                <div style="padding: 12px; flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-size: 0.82rem; font-weight: 700; color: #f8fafc;">Candidate: ${b.student_id}</span>
                            <span class="badge badge-failed" style="font-size: 0.68rem;">${b.severity}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #38bdf8; margin-bottom: 4px;">🏢 ${b.company_name}</div>
                        <div style="font-size: 0.73rem; color: #cbd5e1; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; padding: 6px 8px; border-radius: 4px; margin-bottom: 8px; font-style: italic;">
                            "${b.policy_clause}"
                        </div>
                        <div style="font-size: 0.7rem; color: #f59e0b;">
                            ⚡ Admin Action: ${b.admin_action_recommended}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Failed to fetch admin policy breaches:', err);
    }
}

if (refreshAdminEvidenceBtn) {
    refreshAdminEvidenceBtn.addEventListener('click', fetchAdminPolicyBreaches);
}

// Initial load of client companies
loadClientCompanies();


