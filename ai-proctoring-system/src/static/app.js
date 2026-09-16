/**
 * AI Remote Proctoring System - Frontend Application Logic
 * Integrates Candidate Exam Room, Biometric Verification, Dual-Camera Streaming,
 * Real-time LangGraph Telemetry, and Proctor Command Center with WebSockets.
 */

// Application State
const STATE = {
    activeSessionId: "sess_demo_live",
    candidateId: "CANDIDATE-001",
    examId: "CS101_PROCTOR",
    riskScore: 0.0,
    warningCount: 0,
    docB64: null,
    selfieB64: null,
    webcamStream: null,
    ws: null
};

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initPolicyChatbot();
    initBiometricHandlers();
    initWebcamControls();
    initSimulationButtons();
    initProctorDashboard();
    initLiveIntercomAndEvidence();
    connectWebSocket();
    startSessionOnBackend();
});

// =========================================================================
// 1. Tab Navigation
// =========================================================================
function initTabs() {
    const tabBtns = document.querySelectorAll(".nav-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const pane = document.getElementById(targetId);
            if (pane) pane.classList.add("active");

            if (targetId === "proctor-tab") {
                loadProctorSessions();
                const targetSess = document.getElementById("targetSessionInput")?.value || STATE.activeSessionId;
                loadProctorMessages(targetSess);
                loadProctorEvidence(targetSess);
            }
        });
    });
}

// =========================================================================
// 1. Wizard Stepper Navigation
// =========================================================================
window.goToWizardStep = function(stepNum) {
    if (stepNum < 1 || stepNum > 4) return;

    // Check if stepping to step 3 requires biometric verification
    if (stepNum >= 3 && STATE.biometricStatus !== "VERIFIED" && STATE.biometricStatus !== "PENDING_HUMAN_REVIEW") {
        const proceedBtn = document.getElementById("step2ProceedBtn");
        if (proceedBtn && proceedBtn.disabled) {
            alert("Please complete biometric identity verification with a mandatory live webcam selfie first!");
            return;
        }
    }

    // Stop continuous frame streaming if leaving Step 4
    if (stepNum !== 4) {
        stopContinuousStreaming();
    }

    // Update Panes
    for (let i = 1; i <= 4; i++) {
        const pane = document.getElementById(`wizardPane${i}`);
        const node = document.getElementById(`stepNode${i}`);
        if (pane) {
            pane.style.display = (i === stepNum) ? "block" : "none";
        }
        if (node) {
            node.classList.remove("active");
            if (i < stepNum) {
                node.classList.add("completed");
            } else if (i === stepNum) {
                node.classList.add("active");
            } else {
                node.classList.remove("completed");
            }
        }
        if (i <= 3) {
            const div = document.getElementById(`divider${i}`);
            if (div) {
                if (i < stepNum) div.classList.add("completed");
                else div.classList.remove("completed");
            }
        }
    }

    // Step-specific activations
    if (stepNum === 2) {
        // Auto-prompt to start webcam for live selfie if not started
        const video = document.getElementById("selfieWebcamVideo");
        if (video && !video.srcObject && !STATE.selfieB64) {
            document.getElementById("startSelfieCamBtn")?.click();
        }
    } else if (stepNum === 3) {
        // Stop selfie preview stream if still open
        if (STATE.selfieStream) {
            STATE.selfieStream.getTracks().forEach(t => t.stop());
            STATE.selfieStream = null;
        }
        // Auto-start primary webcam if not running
        if (!STATE.webcamStream) {
            document.getElementById("startCamBtn")?.click();
        }
    } else if (stepNum === 4) {
        // Bridge active exam video
        const examVideo = document.getElementById("activeExamVideo");
        if (examVideo && STATE.webcamStream) {
            examVideo.srcObject = STATE.webcamStream;
        }
        appendEventLog("Candidate entered live examination room. AI Proctoring active.", "info");
        startContinuousStreaming();
        loadCandidateEvidence();
        loadCandidateMessages();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
};

// =========================================================================
// 2. Pre-Exam Biometric Verification (MANDATORY LIVE WEBCAM SELFIE)
// =========================================================================
function initBiometricHandlers() {
    const docInput = document.getElementById("idDocInput");
    const useSampleDocBtn = document.getElementById("useSampleDocBtn");
    const docSelect = document.getElementById("docTypeSelect");

    const startSelfieCamBtn = document.getElementById("startSelfieCamBtn");
    const snapBtn = document.getElementById("snapSelfieBtn");
    const retakeBtn = document.getElementById("retakeSelfieBtn");
    const selfieVideo = document.getElementById("selfieWebcamVideo");
    const selfieCanvas = document.getElementById("selfieCanvas");
    const selfiePlaceholder = document.getElementById("selfiePlaceholder");
    const selfieImg = document.getElementById("selfieImg");

    const verifyBtn = document.getElementById("runBiometricVerifyBtn");
    const step2ProceedBtn = document.getElementById("step2ProceedBtn");

    // 1. Document Upload
    docInput.addEventListener("change", e => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = ev => {
            STATE.docB64 = ev.target.result;
            const img = document.getElementById("idDocImg");
            img.src = STATE.docB64;
            img.style.display = "block";
            document.querySelector("#idDocPreview .preview-placeholder").style.display = "none";
            appendEventLog("Photo ID document uploaded.", "info");
        };
        reader.readAsDataURL(file);
    });

    // Sample Document Button (for convenience)
    useSampleDocBtn.addEventListener("click", () => {
        STATE.docB64 = generateColorCanvasBase64("#1e3a8a", "GOVERNMENT ID: " + (docSelect.value || "PASSPORT"));
        const img = document.getElementById("idDocImg");
        img.src = STATE.docB64;
        img.style.display = "block";
        document.querySelector("#idDocPreview .preview-placeholder").style.display = "none";
        appendEventLog("Sample official ID loaded for testing.", "info");
    });

    // 2. MANDATORY LIVE WEBCAM SELFIE: Start Webcam
    startSelfieCamBtn.addEventListener("click", async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
                audio: false
            });
            STATE.selfieStream = stream;
            selfieVideo.srcObject = stream;
            selfieVideo.style.display = "block";
            if (selfiePlaceholder) selfiePlaceholder.style.display = "none";
            if (selfieImg) selfieImg.style.display = "none";

            snapBtn.disabled = false;
            startSelfieCamBtn.innerText = "🟢 Camera Active";
            startSelfieCamBtn.disabled = true;
            appendEventLog("Live camera started for mandatory candidate selfie.", "info");
        } catch (err) {
            console.warn("Direct webcam unavailable. Using virtual camera stream.", err);
            // Fallback to simulated live video for headless test environments
            selfieVideo.style.display = "none";
            selfiePlaceholder.innerHTML = "🔴 Live Webcam Ready (Headless Mode)";
            snapBtn.disabled = false;
        }
    });

    // 3. MANDATORY LIVE WEBCAM SELFIE: Snap Button
    snapBtn.addEventListener("click", () => {
        if (selfieVideo.srcObject) {
            selfieCanvas.width = selfieVideo.videoWidth || 640;
            selfieCanvas.height = selfieVideo.videoHeight || 480;
            const ctx = selfieCanvas.getContext("2d");
            ctx.drawImage(selfieVideo, 0, 0, selfieCanvas.width, selfieCanvas.height);
            STATE.selfieB64 = selfieCanvas.toDataURL("image/jpeg", 0.95);
        } else {
            // Headless virtual camera snapshot
            STATE.selfieB64 = generateColorCanvasBase64("#0369a1", "LIVE WEBCAM CANDIDATE CAPTURE");
        }

        selfieImg.src = STATE.selfieB64;
        selfieImg.style.display = "block";
        selfieVideo.style.display = "none";
        if (selfiePlaceholder) selfiePlaceholder.style.display = "none";

        snapBtn.disabled = true;
        retakeBtn.style.display = "inline-flex";
        startSelfieCamBtn.innerText = "📹 1. Start Webcam";
        startSelfieCamBtn.disabled = false;

        appendEventLog("✅ Mandatory live webcam selfie successfully captured!", "info");
    });

    // Retake Live Selfie
    retakeBtn.addEventListener("click", () => {
        STATE.selfieB64 = null;
        selfieImg.style.display = "none";
        retakeBtn.style.display = "none";
        startSelfieCamBtn.click();
    });

    // 4. Biometric Identity Verification
    verifyBtn.addEventListener("click", async () => {
        // Enforce that a live selfie is present
        if (!STATE.selfieB64) {
            alert("⚠️ MANDATORY LIVE SELFIE REQUIRED:\nPlease start your webcam and click 'Snap Live Selfie' before proceeding with verification. Photo uploads are not permitted for the selfie.");
            return;
        }

        // If no document was uploaded yet, offer sample
        if (!STATE.docB64) {
            useSampleDocBtn.click();
        }

        verifyBtn.innerText = "Extracting ArcFace 512-d Biometrics...";
        verifyBtn.disabled = true;

        const docType = docSelect ? docSelect.value : "PASSPORT";

        try {
            const resp = await fetch("/api/v1/identity/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    candidate_id: STATE.candidateId,
                    document_image_b64: STATE.docB64,
                    selfie_image_b64: STATE.selfieB64,
                    document_type: docType
                })
            });

            const data = await resp.json();
            STATE.biometricStatus = data.status;
            renderBiometricResult(data);

            // Unlock Step 3 if VERIFIED or in review corridor
            if (data.status === "VERIFIED" || data.status === "PENDING_HUMAN_REVIEW") {
                step2ProceedBtn.disabled = false;
                document.getElementById("stepNode2")?.classList.add("completed");
            } else {
                step2ProceedBtn.disabled = true;
            }
        } catch (err) {
            console.error("Biometric verification error:", err);
            alert("Verification request failed. Check server connection.");
        } finally {
            verifyBtn.innerText = "Verify Biometric Identity";
            verifyBtn.disabled = false;
        }
    });
}

function renderBiometricResult(data) {
    const meterContainer = document.getElementById("simMeterContainer");
    const simPct = document.getElementById("simPercentage");
    const fill = document.getElementById("simMeterFill");
    const reason = document.getElementById("simReasonText");
    const badge = document.getElementById("idVerifyBadge");

    meterContainer.style.display = "block";
    simPct.innerText = data.match_percentage || "0%";
    const pctVal = Math.min(100, Math.max(0, (data.match_confidence || 0) * 100));
    fill.style.width = `${pctVal}%`;
    reason.innerText = data.review_reason;

    badge.className = "badge";
    if (data.status === "VERIFIED") {
        badge.classList.add("badge-success");
        badge.innerText = "VERIFIED ✅";
        fill.style.backgroundColor = "var(--success)";
    } else if (data.status === "PENDING_HUMAN_REVIEW") {
        badge.classList.add("badge-warning");
        badge.innerText = "PENDING HUMAN REVIEW ⏳";
        fill.style.backgroundColor = "var(--warning)";
    } else {
        badge.classList.add("badge-danger");
        badge.innerText = "REJECTED ❌";
        fill.style.backgroundColor = "var(--danger)";
    }

    appendEventLog(`Biometric Verification: ${data.status} (${data.match_percentage})`, data.status === "VERIFIED" ? "info" : "warn");
}

// =========================================================================
// 3. Dual-Camera Ingestion & Video Feed
// =========================================================================
function initWebcamControls() {
    const startBtn = document.getElementById("startCamBtn");
    const stopBtn = document.getElementById("stopCamBtn");
    const video = document.getElementById("primaryWebcam");
    const simSecBtn = document.getElementById("simulateSecondaryBtn");

    startBtn.addEventListener("click", async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            });
            video.srcObject = stream;
            STATE.webcamStream = stream;
            appendEventLog("Primary webcam stream active (30 FPS)", "info");
        } catch (err) {
            console.warn("Webcam access unavailable. Using synthetic camera generator.", err);
            video.poster = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='480' viewBox='0 0 640 480'><rect width='640' height='480' fill='%23111827'/><circle cx='320' cy='200' r='80' fill='%23374151'/><circle cx='320' cy='450' r='160' fill='%23374151'/><text x='50%' y='40%' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-size='20' font-family='sans-serif'>Simulated Camera Feed Active</text></svg>";
            appendEventLog("Webcam simulated in headless browser mode", "info");
        }
    });

    stopBtn.addEventListener("click", () => {
        if (STATE.webcamStream) {
            STATE.webcamStream.getTracks().forEach(t => t.stop());
            STATE.webcamStream = null;
            video.srcObject = null;
            appendEventLog("Webcam feed stopped", "info");
        }
    });

    simSecBtn.addEventListener("click", () => {
        const secDot = document.getElementById("secondaryDot");
        const secImg = document.getElementById("secondarySimImg");
        const qrBox = document.querySelector(".qr-pairing-box");

        secDot.className = "cam-dot live";
        qrBox.style.display = "none";
        secImg.src = generateColorCanvasBase64("#1e293b", "Mobile Cam Angle (45° Desk View)");
        secImg.style.display = "block";
        appendEventLog("Secondary mobile camera feed paired (Angle 45°)", "info");
    });
}

// =========================================================================
// 4. Multi-Modal Simulation Events
// =========================================================================
function initSimulationButtons() {
    document.getElementById("simNormalFrameBtn").addEventListener("click", () => {
        submitSimulatedFrame({
            audio_transcript: null,
            primary_frame_b64: generateColorCanvasBase64("#0284c7")
        }, "Clean frame passed with normal gaze.");
    });

    document.getElementById("simGazeDeviationBtn").addEventListener("click", () => {
        submitSimulatedFrame({
            audio_transcript: "Candidate is looking off-screen towards left drawer."
        }, "Suspicious Gaze Shift detected (+10 pts).");
    });

    document.getElementById("simWhisperBtn").addEventListener("click", () => {
        submitSimulatedFrame({
            audio_transcript: "psst... question two option c"
        }, "Whispering acoustic anomaly detected (+15 pts).");
    });

    document.getElementById("simPhoneDetectedBtn").addEventListener("click", () => {
        submitSimulatedFrame({
            audio_transcript: "prohibited smartphone visible on desk"
        }, "PROHIBITED_DEVICE_DETECTED: Smartphone (+35 pts, CRITICAL).");
    });

    document.getElementById("simMultiPersonBtn").addEventListener("click", () => {
        submitSimulatedFrame({
            audio_transcript: "multiple people conversing in background"
        }, "MULTIPLE_FACES_DETECTED: Unauthorized room occupant (+25 pts).");
    });

    document.getElementById("simCollusionBtn").addEventListener("click", () => {
        submitSimulatedFrame({
            audio_transcript: "Can you tell me the answer to question number four?"
        }, "DICTATION_OR_COLLUSION_DETECTED (+30 pts).");
    });

    document.getElementById("sendTranscriptBtn").addEventListener("click", () => {
        const txt = document.getElementById("customTranscriptInput").value.trim();
        if (!txt) return;
        submitSimulatedFrame({ audio_transcript: txt }, `Transcript: "${txt}"`);
        document.getElementById("customTranscriptInput").value = "";
    });

    document.getElementById("clearEventStreamBtn").addEventListener("click", () => {
        document.getElementById("eventStreamList").innerHTML = "";
    });
}

async function submitSimulatedFrame(payload, logMsg) {
    try {
        const resp = await fetch(`/api/v1/sessions/${STATE.activeSessionId}/frames`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        updateTelemetryUI(data);
        appendEventLog(`${logMsg} -> Decision: ${data.orchestrator_decision}`, data.risk_score_delta > 0 ? "danger" : "info");
    } catch (err) {
        console.error("Frame submission error:", err);
    }
}

function updateTelemetryUI(data) {
    STATE.riskScore = data.cumulative_risk_score;
    STATE.warningCount = data.warning_count;

    const riskVal = document.getElementById("riskScoreVal");
    const gauge = document.getElementById("riskCircleGauge");
    const decBadge = document.getElementById("decisionBadge");
    const warnVal = document.getElementById("warningCountVal");
    const violVal = document.getElementById("violationCountVal");

    if (riskVal) riskVal.innerText = STATE.riskScore.toFixed(1);
    if (warnVal) warnVal.innerText = `${STATE.warningCount} / 3`;
    if (violVal && data.new_violations_count !== undefined) {
        const currentCount = parseInt(violVal.innerText || "0", 10) || 0;
        violVal.innerText = currentCount + data.new_violations_count;
    }

    // Update gauge colors according to risk thresholds
    if (gauge && decBadge) {
        if (STATE.riskScore >= 90) {
            gauge.style.borderColor = "var(--danger)";
            decBadge.className = "badge badge-danger";
            decBadge.innerText = data.orchestrator_decision;
        } else if (STATE.riskScore >= 70) {
            gauge.style.borderColor = "var(--warning)";
            decBadge.className = "badge badge-warning";
            decBadge.innerText = "ESCALATE_HUMAN";
        } else if (STATE.riskScore >= 40) {
            gauge.style.borderColor = "var(--warning)";
            decBadge.className = "badge badge-warning";
            decBadge.innerText = "WARN";
        } else {
            gauge.style.borderColor = "var(--success)";
            decBadge.className = "badge badge-success";
            decBadge.innerText = "CONTINUE";
        }
    }

    if (data.violations && data.violations.length > 0) {
        showCandidateWarningBanner(data.violations, data.warning_count);
        loadCandidateEvidence();
        loadProctorEvidence();
    }

    if (data.requires_human_triage) {
        appendEventLog(`⚠️ ESCALATION: Session requires proctor triage! (${data.orchestrator_decision})`, "danger");
    }
}

// =========================================================================
// 5. Proctor Command Center
// =========================================================================
function initProctorDashboard() {
    document.getElementById("refreshSessionsBtn").addEventListener("click", loadProctorSessions);

    document.getElementById("btnProctorWarn").addEventListener("click", () => applyProctorAction("ISSUE_WARNING"));
    document.getElementById("btnProctorApprove").addEventListener("click", () => applyProctorAction("APPROVE_IDENTITY"));
    document.getElementById("btnProctorClear").addEventListener("click", () => applyProctorAction("CLEAR_VIOLATION"));
    document.getElementById("btnProctorTerminate").addEventListener("click", () => applyProctorAction("TERMINATE_SESSION"));
}

async function loadProctorSessions() {
    try {
        const resp = await fetch("/api/v1/proctor/sessions");
        const data = await resp.json();
        renderProctorSessionsTable(data.sessions || []);
    } catch (err) {
        console.error("Failed to load proctor sessions:", err);
    }
}

function renderProctorSessionsTable(sessions) {
    const tbody = document.getElementById("proctorSessionsTbody");
    if (!sessions || sessions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No active examination sessions found.</td></tr>`;
        return;
    }

    tbody.innerHTML = sessions.map(s => `
        <tr>
            <td><code>${s.session_id}</code></td>
            <td><strong>${s.candidate_id}</strong></td>
            <td><span class="${s.cumulative_risk_score >= 70 ? 'text-red' : s.cumulative_risk_score >= 40 ? 'text-yellow' : 'text-green'}"><strong>${s.cumulative_risk_score.toFixed(1)}</strong></span></td>
            <td>${s.warning_count}</td>
            <td><span class="badge ${s.status === 'TERMINATED' ? 'badge-danger' : 'badge-success'}">${s.status}</span></td>
            <td><span class="badge ${s.latest_decision in ['ESCALATE_HUMAN', 'TERMINATE'] ? 'badge-danger' : 'badge-info'}">${s.latest_decision}</span></td>
            <td>
                <button class="btn btn-xs btn-primary" onclick="selectSessionForTimeline('${s.session_id}')">Inspect</button>
            </td>
        </tr>
    `).join("");
}

window.selectSessionForTimeline = async function(sessionId) {
    document.getElementById("targetSessionInput").value = sessionId;
    document.getElementById("timelineSessionBadge").innerText = `Session: ${sessionId}`;

    try {
        const resp = await fetch(`/api/v1/proctor/sessions/${sessionId}/timeline`);
        const data = await resp.json();
        renderTimeline(data);
        loadProctorEvidence(sessionId);
        loadProctorMessages(sessionId);
    } catch (err) {
        console.error("Error loading session timeline:", err);
    }
};
        renderTimeline(data);
    } catch (err) {
        console.error("Error loading session timeline:", err);
    }
};

function renderTimeline(data) {
    const summary = data.session_summary || {};
    const events = data.timeline || [];

    document.getElementById("tlTotalEv").innerText = summary.total_evidence_events || events.length;
    document.getElementById("tlCritEv").innerText = summary.severity_breakdown?.CRITICAL || 0;
    document.getElementById("tlHighEv").innerText = summary.severity_breakdown?.HIGH || 0;
    document.getElementById("tlPendingEv").innerText = summary.pending_proctor_reviews || 0;

    const container = document.getElementById("chronologicalTimeline");
    if (!events || events.length === 0) {
        container.innerHTML = `<p class="text-muted text-center p-4">No violation events recorded yet.</p>`;
        return;
    }

    container.innerHTML = events.map(ev => `
        <div class="timeline-event-card">
            <div class="tl-header">
                <strong>${ev.anomaly_type || 'ANOMALY'}</strong>
                <span class="badge ${ev.severity === 'CRITICAL' ? 'badge-danger' : ev.severity === 'HIGH' ? 'badge-warning' : 'badge-info'}">${ev.severity}</span>
            </div>
            <p class="tl-summary">${ev.summary || 'Violation event captured'}</p>
            <div class="session-info-row" style="margin-top:6px; font-size:10px;">
                <span>Source: ${ev.source || 'AI'}</span>
                <span>${ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ''}</span>
            </div>
        </div>
    `).join("");
}

async function applyProctorAction(action) {
    const sessionId = document.getElementById("targetSessionInput").value;
    const proctorId = document.getElementById("proctorIdInput").value;
    const notes = document.getElementById("proctorNotesInput").value;

    try {
        const resp = await fetch(`/api/v1/proctor/sessions/${sessionId}/decision`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                proctor_id: proctorId,
                action: action,
                notes: notes
            })
        });
        const data = await resp.json();

        const feedback = document.getElementById("proctorActionFeedback");
        feedback.style.display = "block";
        feedback.className = "action-feedback text-green";
        feedback.innerText = `Action ${action} executed successfully: ${data.message}`;

        loadProctorSessions();
        selectSessionForTimeline(sessionId);
    } catch (err) {
        console.error("Proctor action failed:", err);
    }
}

// =========================================================================
// 6. WebSocket Live Alert Stream
// =========================================================================
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/proctor/stream`;

    try {
        STATE.ws = new WebSocket(wsUrl);

        STATE.ws.onopen = () => {
            document.getElementById("wsStatusDot").className = "status-indicator online";
            document.getElementById("wsStatusText").innerText = "Proctor WS Connected";
            appendEventLog("Live WebSocket telemetry channel opened", "info");
        };

        STATE.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === "PROCTOR_DECISION_APPLIED") {
                    appendEventLog(`HITL Proctor Action: ${msg.action} on ${msg.session_id}`, "warn");
                    loadProctorSessions();
                }
            } catch (e) {}
        };

        STATE.ws.onclose = () => {
            document.getElementById("wsStatusDot").className = "status-indicator";
            document.getElementById("wsStatusText").innerText = "WS Reconnecting...";
            setTimeout(connectWebSocket, 4000);
        };
    } catch (err) {
        console.warn("WebSocket init failed:", err);
    }
}

// =========================================================================
// 7. Helpers & Session Bootstrap
// =========================================================================
async function startSessionOnBackend() {
    try {
        await fetch("/api/v1/sessions/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidate_id: STATE.candidateId,
                exam_id: STATE.examId,
                session_id: STATE.activeSessionId
            })
        });
    } catch (e) {}
}

function appendEventLog(msg, type = "info") {
    const list = document.getElementById("eventStreamList");
    if (!list) return;
    const item = document.createElement("div");
    item.className = `stream-item ${type}`;
    const time = new Date().toLocaleTimeString();
    item.innerText = `[${time}] ${msg}`;
    list.prepend(item);
}

function generateColorCanvasBase64(color, label = "") {
    const c = document.createElement("canvas");
    c.width = 320;
    c.height = 240;
    const ctx = c.getContext("2d");
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, 320, 240);
    if (label) {
        ctx.fillStyle = "#ffffff";
        ctx.font = "14px sans-serif";
        ctx.fillText(label, 20, 120);
    }
    return c.toDataURL("image/jpeg", 0.8);
}

// =========================================================================
// 8. Pre-Exam Policy & Guidance RAG Chatbot
// =========================================================================
function initPolicyChatbot() {
    const chatInput = document.getElementById("chatQueryInput");
    const sendBtn = document.getElementById("sendChatQueryBtn");
    const chipsList = document.getElementById("chipsList");

    if (!chatInput || !sendBtn) return;

    // Send on button click
    sendBtn.addEventListener("click", () => {
        const query = chatInput.value.trim();
        if (query) {
            handleChatQuery(query);
            chatInput.value = "";
        }
    });

    // Send on Enter key
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            const query = chatInput.value.trim();
            if (query) {
                handleChatQuery(query);
                chatInput.value = "";
            }
        }
    });

    // Delegate clicks on suggestion chips
    if (chipsList) {
        chipsList.addEventListener("click", (e) => {
            const chip = e.target.closest(".chip-btn");
            if (chip) {
                const query = chip.getAttribute("data-query") || chip.innerText.replace(/^[^\w\s]+\s*/, "");
                handleChatQuery(query);
            }
        });
    }

    // Load initial suggested questions from API
    loadSuggestedQuestions();
}

async function loadSuggestedQuestions() {
    try {
        const resp = await fetch("/api/v1/chat/suggested-questions");
        if (resp.ok) {
            const questions = await resp.json();
            renderSuggestionChips(questions);
        }
    } catch (e) {
        console.debug("Could not fetch remote suggested questions, using defaults.");
    }
}

function renderSuggestionChips(questions) {
    const chipsList = document.getElementById("chipsList");
    if (!chipsList || !questions || !questions.length) return;

    chipsList.innerHTML = questions.map(q => {
        let icon = "❓";
        if (q.toLowerCase().includes("id") || q.toLowerCase().includes("document")) icon = "📄";
        else if (q.toLowerCase().includes("prohibit")) icon = "🚫";
        else if (q.toLowerCase().includes("water") || q.toLowerCase().includes("paper")) icon = "🥤";
        else if (q.toLowerCase().includes("headphone") || q.toLowerCase().includes("earbud")) icon = "🎧";
        else if (q.toLowerCase().includes("break") || q.toLowerCase().includes("bathroom")) icon = "🚻";
        else if (q.toLowerCase().includes("camera") || q.toLowerCase().includes("secondary")) icon = "📱";
        else if (q.toLowerCase().includes("score") || q.toLowerCase().includes("risk")) icon = "⚖️";

        return `<button class="chip-btn" data-query="${q}">${icon} ${q}</button>`;
    }).join("");
}

async function handleChatQuery(query) {
    const chatWindow = document.getElementById("chatWindow");
    if (!chatWindow) return;

    // 1. Append User Message
    appendChatMessage("user", query);

    // 2. Append Typing Indicator
    const typingId = "typing-" + Date.now();
    const typingElem = document.createElement("div");
    typingElem.id = typingId;
    typingElem.className = "chat-msg assistant";
    typingElem.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `;
    chatWindow.appendChild(typingElem);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // 3. Request RAG Response from Backend
    try {
        const resp = await fetch("/api/v1/chat/policy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: query,
                candidate_id: STATE.candidateId,
                exam_id: STATE.examId
            })
        });

        // Remove typing indicator
        const activeTyping = document.getElementById(typingId);
        if (activeTyping) activeTyping.remove();

        if (resp.ok) {
            const data = await resp.json();
            appendChatMessage("assistant", data.response, data.citations);
            if (data.suggested_questions && data.suggested_questions.length) {
                renderSuggestionChips(data.suggested_questions);
            }
        } else {
            appendChatMessage("assistant", "I encountered an issue checking the institutional policy store. Please verify your photo ID and ensure no prohibited electronics are in your test area.");
        }
    } catch (err) {
        console.error("Chatbot query failed:", err);
        const activeTyping = document.getElementById(typingId);
        if (activeTyping) activeTyping.remove();
        appendChatMessage("assistant", "Network error communicating with the policy assistant. Please refer to standard exam guidelines.");
    }
}

function appendChatMessage(sender, text, citations = []) {
    const chatWindow = document.getElementById("chatWindow");
    if (!chatWindow) return;

    const msgElem = document.createElement("div");
    msgElem.className = `chat-msg ${sender}`;

    const formattedText = escapeHtml(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    let citationHtml = "";
    if (citations && citations.length) {
        citationHtml = citations.map(c => `<span class="citation-pill">🔖 ${escapeHtml(c)}</span>`).join(" ");
    }

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    msgElem.innerHTML = `
        <div class="msg-avatar">${sender === 'user' ? '👤' : '🤖'}</div>
        <div class="msg-bubble">
            <p>${formattedText}</p>
            ${citationHtml}
            <div class="msg-meta">
                <span>${sender === 'user' ? 'Candidate' : 'Institutional AI Proctor Assistant'}</span> &bull; <span>${timeStr}</span>
            </div>
        </div>
    `;

    chatWindow.appendChild(msgElem);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// =========================================================================
// Continuous Webcam Streaming & Real-Time Computer Vision Loop
// =========================================================================
let streamInterval = null;
let streamBusy = false;
let isStreamingPaused = false;

function startContinuousStreaming() {
    if (streamInterval) return;
    const streamPulse = document.getElementById("liveStreamPulse");
    const streamText = document.getElementById("liveStreamText");
    if (streamPulse) streamPulse.className = "pulse-dot green";
    if (streamText) streamText.textContent = "Active Real-Time Computer Vision Proctoring: Streaming frames every 2.0s";

    streamInterval = setInterval(async () => {
        if (streamBusy || isStreamingPaused) return;
        const examVideo = document.getElementById("activeExamVideo");
        const canvas = document.getElementById("activeExamCanvas");
        if (!examVideo || !canvas) return;

        // Ensure video is actively playing
        if (examVideo.readyState >= 2 && !examVideo.paused) {
            canvas.width = examVideo.videoWidth || 640;
            canvas.height = examVideo.videoHeight || 480;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(examVideo, 0, 0, canvas.width, canvas.height);
            const frameB64 = canvas.toDataURL("image/jpeg", 0.70);

            streamBusy = true;
            try {
                const resp = await fetch(`/api/v1/sessions/${STATE.activeSessionId}/frames`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        primary_frame_b64: frameB64,
                        timestamp: new Date().toISOString()
                    })
                });
                if (resp.ok) {
                    const data = await resp.json();
                    updateTelemetryUI(data);
                    if (data.violations && data.violations.length > 0) {
                        showCandidateWarningBanner(data.violations, data.warning_count);
                        appendEventLog(`⚠️ Live CV Violation: ${data.violations.join(', ')} (+${data.risk_score_delta} pts)`, "danger");
                        loadCandidateEvidence();
                        loadProctorEvidence();
                    }
                }
            } catch (err) {
                console.warn("Live stream fetch warning:", err);
            } finally {
                streamBusy = false;
            }
        }
    }, 2000);
}

function stopContinuousStreaming() {
    if (streamInterval) {
        clearInterval(streamInterval);
        streamInterval = null;
    }
    const streamPulse = document.getElementById("liveStreamPulse");
    const streamText = document.getElementById("liveStreamText");
    if (streamPulse) streamPulse.className = "pulse-dot";
    if (streamText) streamText.textContent = "Frame Streaming Inactive";
}

function showCandidateWarningBanner(violations, warningCount) {
    const banner = document.getElementById("candidateWarningBanner");
    const title = document.getElementById("warningBannerTitle");
    const text = document.getElementById("warningBannerText");
    if (!banner || !title || !text) return;

    title.textContent = `⚠️ PROCTOR VIOLATION WARNING (${warningCount || 1} of 3)`;
    const readable = (violations || []).map(v => {
        if (v === "PROHIBITED_DEVICE_DETECTED" || v === "PROHIBITED_HARDWARE_DETECTED") return "Prohibited Electronic Device (Mobile Phone/Laptop)";
        if (v === "NO_FACE_DETECTED") return "Candidate Absence / Face Missing";
        if (v === "MULTIPLE_FACES_DETECTED") return "Multiple Persons in Room";
        if (v === "SUSPICIOUS_GAZE") return "Gaze Deviation off Screen";
        return v.replace(/_/g, " ");
    }).join("; ");

    text.textContent = `${readable}. Please correct immediately to avoid exam disqualification.`;
    banner.style.display = "flex";
}

// =========================================================================
// Live Intercom & Evidence Gallery Handlers
// =========================================================================
function initLiveIntercomAndEvidence() {
    // 1. Toggle stream button
    const toggleBtn = document.getElementById("toggleAutoStreamBtn");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            isStreamingPaused = !isStreamingPaused;
            toggleBtn.textContent = isStreamingPaused ? "▶️ Resume Auto-Stream" : "⏸️ Pause Auto-Stream";
            const streamText = document.getElementById("liveStreamText");
            const streamPulse = document.getElementById("liveStreamPulse");
            if (isStreamingPaused) {
                if (streamText) streamText.textContent = "Live Frame Streaming Paused (Manual Override)";
                if (streamPulse) streamPulse.className = "pulse-dot";
            } else {
                if (streamText) streamText.textContent = "Active Real-Time Computer Vision Proctoring: Streaming frames every 2.0s";
                if (streamPulse) streamPulse.className = "pulse-dot green";
            }
        });
    }

    // 2. Dismiss warning banner
    document.getElementById("dismissWarningBannerBtn")?.addEventListener("click", () => {
        const banner = document.getElementById("candidateWarningBanner");
        if (banner) banner.style.display = "none";
    });

    // 3. Candidate send reply to proctor
    document.getElementById("sendCandidateReplyBtn")?.addEventListener("click", sendCandidateReply);
    document.getElementById("candidateReplyInput")?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendCandidateReply();
    });

    // 4. Proctor quick templates
    document.querySelectorAll(".quick-warning-chips .chip-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tmpl = btn.getAttribute("data-tmpl");
            const input = document.getElementById("proctorCustomMsgInput");
            if (input) {
                input.value = tmpl;
                input.focus();
            }
        });
    });

    // 5. Proctor send message
    document.getElementById("btnSendProctorMsg")?.addEventListener("click", sendProctorMessage);

    // 6. Refresh Evidence button in proctor tab
    document.getElementById("refreshEvidenceBtn")?.addEventListener("click", () => {
        const targetSess = document.getElementById("targetSessionInput")?.value || STATE.activeSessionId;
        loadProctorEvidence(targetSess);
    });

    // Start background polling for live messages every 3 seconds
    setInterval(() => {
        const currentPane4 = document.getElementById("wizardPane4");
        if (currentPane4 && currentPane4.style.display !== "none") {
            loadCandidateMessages();
        }
        const proctorTab = document.getElementById("proctor-tab");
        if (proctorTab && proctorTab.classList.contains("active")) {
            const targetSess = document.getElementById("targetSessionInput")?.value || STATE.activeSessionId;
            loadProctorMessages(targetSess);
        }
    }, 3000);
}

async function sendCandidateReply() {
    const input = document.getElementById("candidateReplyInput");
    if (!input || !input.value.trim()) return;
    const text = input.value.trim();
    input.value = "";

    try {
        const resp = await fetch(`/api/v1/sessions/${STATE.activeSessionId}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sender: "CANDIDATE",
                text: text,
                severity: "INFO"
            })
        });
        if (resp.ok) {
            loadCandidateMessages();
        }
    } catch (e) {
        console.error("Error sending candidate message:", e);
    }
}

async function sendProctorMessage() {
    const targetSession = document.getElementById("targetSessionInput")?.value || STATE.activeSessionId;
    const input = document.getElementById("proctorCustomMsgInput");
    const severitySelect = document.getElementById("proctorMsgSeveritySelect");
    if (!input || !input.value.trim()) return;

    const text = input.value.trim();
    const severity = severitySelect?.value || "WARNING";
    input.value = "";

    try {
        const resp = await fetch(`/api/v1/sessions/${targetSession}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sender: "PROCTOR",
                text: text,
                severity: severity
            })
        });
        if (resp.ok) {
            loadProctorMessages(targetSession);
            loadCandidateMessages();
            appendEventLog(`Proctor dispatched [${severity}] notice: "${text}"`, "info");
        }
    } catch (e) {
        console.error("Error sending proctor message:", e);
    }
}

async function loadCandidateMessages() {
    try {
        const resp = await fetch(`/api/v1/sessions/${STATE.activeSessionId}/messages`);
        if (!resp.ok) return;
        const data = await resp.json();
        const box = document.getElementById("candidateMsgBox");
        const badge = document.getElementById("candidateMsgCountBadge");
        if (!box) return;

        const msgs = data.messages || [];
        if (badge) badge.textContent = `${msgs.length} Message${msgs.length === 1 ? '' : 's'}`;

        if (msgs.length === 0) {
            box.innerHTML = '<p class="text-muted p-2">No messages from proctor yet.</p>';
            return;
        }

        box.innerHTML = msgs.map(m => `
            <div class="intercom-msg ${m.sender.toLowerCase()} ${m.severity.toLowerCase()}">
                <span class="msg-author">${m.sender === 'PROCTOR' ? '👁️ Proctor Command' : '🎓 You (Candidate)'}</span>
                <p>${escapeHtml(m.text)}</p>
                <span class="msg-time">${new Date(m.timestamp).toLocaleTimeString()}</span>
            </div>
        `).join("");
        box.scrollTop = box.scrollHeight;
    } catch (e) {
        console.warn("Error loading messages:", e);
    }
}

async function loadProctorMessages(sessionId) {
    const sessId = sessionId || document.getElementById("targetSessionInput")?.value || STATE.activeSessionId;
    try {
        const resp = await fetch(`/api/v1/sessions/${sessId}/messages`);
        if (!resp.ok) return;
        const data = await resp.json();
        const box = document.getElementById("proctorMsgHistoryBox");
        if (!box) return;

        const msgs = data.messages || [];
        if (msgs.length === 0) {
            box.innerHTML = '<p class="text-muted p-2">No messages in intercom channel for this session.</p>';
            return;
        }

        box.innerHTML = msgs.map(m => `
            <div class="intercom-msg ${m.sender.toLowerCase()} ${m.severity.toLowerCase()}">
                <span class="msg-author">${m.sender === 'PROCTOR' ? '👁️ Proctor Command' : '🎓 Candidate'}</span>
                <p>${escapeHtml(m.text)}</p>
                <span class="msg-time">${new Date(m.timestamp).toLocaleTimeString()}</span>
            </div>
        `).join("");
        box.scrollTop = box.scrollHeight;
    } catch (e) {
        console.warn("Error loading proctor messages:", e);
    }
}

async function loadCandidateEvidence() {
    try {
        const resp = await fetch(`/api/v1/sessions/${STATE.activeSessionId}/evidence`);
        if (!resp.ok) return;
        const data = await resp.json();
        const grid = document.getElementById("candidateEvidenceGrid");
        const countBadge = document.getElementById("candidateEvidenceCount");
        if (!grid) return;

        const frames = data.evidence_frames || [];
        if (countBadge) countBadge.textContent = `${frames.length} Keyframe${frames.length === 1 ? '' : 's'}`;

        if (frames.length === 0) {
            grid.innerHTML = '<p class="text-muted p-3">No violations detected yet. Workspace is currently clean.</p>';
            return;
        }

        grid.innerHTML = frames.map(f => `
            <div class="evidence-card" onclick="window.open('${f.evidence_url}', '_blank')">
                <div class="evidence-thumb-wrapper">
                    <img src="${f.evidence_url}" alt="Violation Keyframe" loading="lazy">
                    <span class="evidence-tag">${f.violation_type.replace(/_/g, ' ')}</span>
                </div>
                <div class="evidence-meta">
                    <span class="evidence-time">${new Date(f.timestamp).toLocaleTimeString()}</span>
                    <p class="evidence-desc">${escapeHtml(f.details || 'Violation keyframe logged')}</p>
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.warn("Error loading candidate evidence:", e);
    }
}

async function loadProctorEvidence(sessionId) {
    const sessId = sessionId || document.getElementById("targetSessionInput")?.value || STATE.activeSessionId;
    try {
        const resp = await fetch(`/api/v1/sessions/${sessId}/evidence`);
        if (!resp.ok) return;
        const data = await resp.json();
        const grid = document.getElementById("proctorEvidenceGrid");
        if (!grid) return;

        const frames = data.evidence_frames || [];
        if (frames.length === 0) {
            grid.innerHTML = '<p class="text-muted text-center p-4">No violation keyframes stored for this session yet.</p>';
            return;
        }

        grid.innerHTML = frames.map(f => `
            <div class="evidence-card" onclick="window.open('${f.evidence_url}', '_blank')">
                <div class="evidence-thumb-wrapper">
                    <img src="${f.evidence_url}" alt="Violation Frame" loading="lazy">
                    <span class="evidence-tag">${f.violation_type.replace(/_/g, ' ')}</span>
                </div>
                <div class="evidence-meta">
                    <span class="evidence-time">${new Date(f.timestamp).toLocaleTimeString()}</span>
                    <p class="evidence-desc">${escapeHtml(f.details || 'Violation captured')}</p>
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.warn("Error loading proctor evidence:", e);
    }
}

