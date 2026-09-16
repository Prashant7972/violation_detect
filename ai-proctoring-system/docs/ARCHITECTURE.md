# AI Remote Proctoring System: Architecture Specification

## 1. System Overview
The AI Remote Proctoring System is a high-throughput, agentic proctoring platform designed for continuous examination monitoring. It orchestrates real-time multimodal vision, audio intelligence, policy evaluation, and explainable risk synthesis.

## 2. Technology Evolution: Bedrock vs Gemini + LangGraph

| Layer | Legacy (Amazon Bedrock) | Target (Gemini + LangGraph) | Architectural Benefit |
|---|---|---|---|
| **Agent Orchestration** | Bedrock AgentCore Runtime | **LangGraph StateGraph Engine** | Deterministic graph state transitions, built-in checkpointing (`MemorySaver`/Postgres), cyclic anomaly re-evaluation, parallel branch execution |
| **Foundation Models** | Claude 3.5 Sonnet / AWS Nova | **Google Gemini 2.5 Flash / Pro** | Native multimodal token processing (direct video, audio, image ingest), higher inference throughput, reduced token latency |
| **Vision & Face Analysis** | Amazon Rekognition | **Gemini Vision + InsightFace / OpenCV** | 512-d ArcFace facial embeddings combined with Gemini spatial reasoning for zero-shot posture, gaze, and hardware detection |
| **Audio Intelligence** | Amazon Transcribe | **Whisper / Gemini Audio** | Sub-second acoustic event classification (whispering, mechanical typing, second voice) |
| **Session State & Memory** | AgentCore Session Memory | **LangGraph Checkpointer** | Cross-frame state retention, immutable append-only violation logs, cumulative risk tracking |
| **Policy Enforcement** | Bedrock Knowledge Bases | **LangChain + ChromaDB (Vector RAG)** | Dynamic retrieval of institutional exam policies and tolerance thresholds |

## 3. High-Level Data Flow

```text
[Primary Camera (Webcam)] ──┐
[Secondary Camera (Mobile)] ┼──► Media Ingestion Stream Handler
[Microphone Audio]          ──┘           │
                                          ▼
                               LangGraph Supervisor Node
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   Vision Proctoring Node      Audio Intelligence Node        Identity Verification Node
   (Gemini 2.5 Flash Vision)   (Whisper / Gemini Audio)       (InsightFace / OpenCV)
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          ▼
                             Policy & RAG Evaluator Node
                             (ChromaDB Vector Retrieval)
                                          │
                                          ▼
                           Evidence Synthesis & Risk Scorer
                           (Cumulative Risk & Decision)
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
             Automated State Update               Human-in-the-Loop (HITL)
             (Postgres / Redis Log)               (Proctor Review Dashboard)
```

## 4. Component Boundaries & Isolation
1. **Core Runtime (`src/core`)**: Contains global settings, unified `google-genai` client, and the shared `ProctorSessionState`.
2. **Feature Modules (`src/features/*`)**: Strictly isolated domains containing their own schemas, services, LangGraph nodes, and prompts. No direct cross-feature imports.
3. **API Layer (`src/api/*`)**: FastAPI REST and WebSocket endpoints for student sessions and proctor triage dashboards.
4. **Human-in-the-Loop Safeguard**: Automated models never autonomously disqualify a candidate; severe violations escalate to `ESCALATE_HUMAN` or `PENDING_HUMAN_REVIEW`.
