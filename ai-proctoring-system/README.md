# AI Remote Proctoring System (LangGraph + Gemini)

Production-grade, agentic AI remote proctoring system built with LangGraph `StateGraph` orchestration and Google Gemini 2.5 multimodal foundation models.

---

## Architecture Overview

- **Orchestration Runtime:** LangGraph `StateGraph` with parallel branching, sequential policy/evidence synthesis, and dynamic conditional edges.
- **Multimodal Foundation Models:** Google Gemini 2.5 Flash / Pro (native video, image, and audio understanding).
- **Vision & Biometrics:** 512-d ArcFace facial embeddings via InsightFace / OpenCV + zero-shot gaze/pose estimation.
- **State & Memory Checkpointing:** In-memory `MemorySaver` for testing; persistent PostgreSQL (`AsyncPostgresSaver`) for production sessions.
- **Policy Enforcement:** Vector RAG retrieval via ChromaDB and institutional rule engine (`policy_store.json`).
- **Human-in-the-Loop Safeguard:** Automated AI models never autonomously disqualify candidates; severe violations trigger proctor triage.

---

## Project Structure

```text
ai-proctoring-system/
├── docs/
│   ├── ARCHITECTURE.md          # Architectural specifications & Bedrock-to-Gemini comparison
│   ├── LANGGRAPH_WORKFLOWS.md   # StateGraph topology & state accumulator patterns
│   ├── SCOPE_AND_COMPLIANCE.md  # Tenant isolation, zero egress & privacy constraints
│   └── API_SPECIFICATION.md     # REST and WebSocket contracts
│
├── src/
│   ├── core/                    # Shared configuration, state schemas, Gemini client
│   │   ├── config.py
│   │   ├── state.py
│   │   └── gemini_client.py
│   │
│   ├── features/                # Modular, self-contained feature packages
│   │   ├── identity_verification/ # [STEP 1] ArcFace biometrics & HITL review corridor
│   │   ├── media_ingestion/       # [STEP 2] Synchronized multi-angle ring buffer
│   │   ├── vision_proctoring/     # [STEP 3] Face presence, multi-face, gaze, objects
│   │   ├── audio_intelligence/    # [STEP 4] RMS energy profiling, whisper, collusion
│   │   ├── policy_rules/          # [STEP 5] ChromaDB RAG & institutional policy engine
│   │   ├── proctor_orchestrator/  # [STEP 6] LangGraph StateGraph engine & checkpointer
│   │   └── evidence_reporting/    # [STEP 6] Timeline builder & explainable audit logs
│   │
│   └── api/                     # [STEP 7] FastAPI Gateway & Human Review Portal
│       ├── main.py              # Application entrypoint & CORS middleware
│       └── v1/
│           ├── router.py        # API v1 aggregator
│           ├── sessions.py      # Candidate session lifecycle & frame ingestion
│           ├── identity.py      # Pre-exam photo ID & selfie biometric verification
│           └── proctor_review.py# Dashboard endpoints, timeline, manual proctor actions & WS stream
│
├── tests/                       # Comprehensive automated test suites (41 tests)
│   ├── test_identity.py
│   ├── test_media_ingestion.py
│   ├── test_vision_nodes.py
│   ├── test_audio_intelligence.py
│   ├── test_policy_rules.py
│   ├── test_orchestrator_graph.py
│   └── test_api_endpoints.py
│
├── Dockerfile                   # Production container definition
└── docker-compose.yml           # Local multi-container stack (API, Redis, PostgreSQL)
```

---

## Running the System

### 1. Run the API Gateway Locally
```bash
PYTHONPATH=./ai-proctoring-system uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
```
- **Interactive OpenAPI Documentation:** `http://localhost:8001/docs`
- **Health Check Probe:** `http://localhost:8001/health`

### 2. Run via Docker Compose
```bash
docker-compose up --build
```

### 3. Run Automated Tests
```bash
# Run all 41 proctoring test suites
PYTHONPATH=./ai-proctoring-system pytest ai-proctoring-system/tests/ -v
```
