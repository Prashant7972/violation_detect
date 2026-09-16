"""
Policy & Documentation Chatbot Endpoints (API v1)
Provides interactive RAG-powered guidance on exam rules, documentation requirements,
and technical workspace preparation for candidates prior to exam start.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status

from src.features.policy_rules.chatbot import (
    PolicyChatRequest,
    PolicyChatResponse,
    policy_chatbot_service
)

logger = logging.getLogger("policy_chat_api")

router = APIRouter(prefix="/chat", tags=["Policy & Guidance Chatbot"])


@router.post("/policy", response_model=PolicyChatResponse)
def ask_policy_chatbot(payload: PolicyChatRequest):
    """
    Submits candidate questions about exam rules, acceptable IDs, permitted items, or camera setup.
    Retrieves grounded institutional policy chunks and generates an authoritative response.
    """
    try:
        response = policy_chatbot_service.answer_query(payload)
        return response
    except Exception as e:
        logger.error(f"Error processing policy chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot failed to process request: {str(e)}"
        )


@router.get("/suggested-questions", response_model=List[str])
def get_suggested_questions():
    """
    Returns curated pre-exam FAQ prompt questions for rapid candidate onboarding.
    """
    return policy_chatbot_service.get_suggested_questions()
