"""
Unit & Integration Tests for Pre-Exam Policy & Documentation RAG Chatbot
Validates knowledge retrieval, answer synthesis, citations, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.features.policy_rules.chatbot import (
    policy_chatbot_service,
    PolicyChatRequest
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestPolicyChatbotService:
    """Validates the RAG retrieval and synthesis service."""

    def test_retrieve_articles_for_id_documents(self):
        query = "What photo IDs and documents do I need to bring for the exam?"
        matched = policy_chatbot_service.retrieve_relevant_articles(query)
        assert len(matched) > 0
        titles = [a["title"] for a in matched]
        assert any("Identification" in t or "Biometric" in t for t in titles)

    def test_retrieve_articles_for_prohibited_devices(self):
        query = "Can I bring my smartphone or wear wireless earbuds?"
        matched = policy_chatbot_service.retrieve_relevant_articles(query)
        assert len(matched) > 0
        titles = [a["title"] for a in matched]
        assert any("Prohibited" in t for t in titles)

    def test_retrieve_articles_for_allowed_items(self):
        query = "Is it okay to have blank scratch paper and a clear water bottle?"
        matched = policy_chatbot_service.retrieve_relevant_articles(query)
        assert len(matched) > 0
        titles = [a["title"] for a in matched]
        assert any("Authorized" in t or "Permitted" in t for t in titles)

    def test_answer_query_returns_citations_and_suggestions(self):
        req = PolicyChatRequest(
            query="Can I take an unscheduled bathroom break?",
            candidate_id="TEST_CANDIDATE"
        )
        resp = policy_chatbot_service.answer_query(req)
        assert resp.response is not None
        assert len(resp.response) > 20
        assert len(resp.citations) > 0
        assert len(resp.suggested_questions) > 0


class TestPolicyChatApiEndpoints:
    """Validates FastAPI REST endpoints for the chatbot."""

    def test_chat_policy_endpoint_success(self, client):
        payload = {
            "query": "What are the rules regarding mobile phones and smartwatches?",
            "candidate_id": "CANDIDATE_CHAT_01"
        }
        resp = client.post("/api/v1/chat/policy", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "citations" in data
        assert "suggested_questions" in data
        assert len(data["citations"]) > 0

    def test_chat_suggested_questions_endpoint(self, client):
        resp = client.get("/api/v1/chat/suggested-questions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        assert any("photo ID" in q or "prohibited" in q.lower() for q in data)
