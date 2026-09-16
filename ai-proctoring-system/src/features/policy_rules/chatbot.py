"""
Pre-Exam Policy & Required Documentation RAG Chatbot Service
Empowers candidates with authoritative, instant answers on exam rules,
prohibited items, acceptable ID documentation, and technical setup.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.core.gemini_client import get_gemini_client

logger = logging.getLogger("policy_chatbot_service")

KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")


class PolicyChatRequest(BaseModel):
    query: str = Field(..., description="Candidate's question regarding rules, documents, or setup")
    candidate_id: Optional[str] = Field(default=None, description="Optional candidate identifier")
    exam_id: Optional[str] = Field(default="DEFAULT_EXAM", description="Exam code")
    chat_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Prior conversation context")


class PolicyChatResponse(BaseModel):
    response: str
    citations: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    matched_articles: List[str] = Field(default_factory=list)


class PolicyChatbotService:
    """
    Retrieval-Augmented Generation (RAG) assistant for candidate onboarding.
    Answers candidate queries using verified institutional exam documentation.
    """

    def __init__(self, kb_file_path: Optional[str] = None):
        self.kb_file_path = kb_file_path or KB_PATH
        self.knowledge_base = self._load_knowledge_base()
        self.articles = self.knowledge_base.get("articles", [])
        self.default_suggestions = self.knowledge_base.get("suggested_questions", [])

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Loads structured articles and policy documents."""
        try:
            if os.path.exists(self.kb_file_path):
                with open(self.kb_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading knowledge base from {self.kb_file_path}: {e}")
        return {"articles": [], "suggested_questions": []}

    def retrieve_relevant_articles(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Scores knowledge articles against candidate query using lexical keyword matching,
        token overlap, and category relevance.
        """
        query_tokens = set(re.findall(r"\w+", query.lower()))
        if not query_tokens:
            return self.articles[:top_k]

        scored_articles = []
        for article in self.articles:
            score = 0
            # 1. Keywords match (high weight)
            keywords = [kw.lower() for kw in article.get("keywords", [])]
            for kw in keywords:
                kw_tokens = set(re.findall(r"\w+", kw))
                if kw_tokens.issubset(query_tokens):
                    score += 5
                elif any(t in query_tokens for t in kw_tokens):
                    score += 2

            # 2. Title match
            title_tokens = set(re.findall(r"\w+", article.get("title", "").lower()))
            overlap = query_tokens.intersection(title_tokens)
            score += len(overlap) * 3

            # 3. Content match
            content_lower = article.get("content", "").lower()
            for token in query_tokens:
                if len(token) > 3 and token in content_lower:
                    score += 1

            scored_articles.append((score, article))

        # Sort descending by relevance score
        scored_articles.sort(key=lambda x: x[0], reverse=True)

        # Select top_k with non-zero score or fallback to top articles
        matched = [art for score, art in scored_articles if score > 0][:top_k]
        if not matched and self.articles:
            matched = self.articles[:2]
        return matched

    def answer_query(self, request: PolicyChatRequest) -> PolicyChatResponse:
        """
        Processes candidate inquiry through RAG retrieval and synthesis.
        """
        query = request.query.strip()
        matched_articles = self.retrieve_relevant_articles(query)

        citations = [art.get("citation", "Institutional Policy") for art in matched_articles]
        article_titles = [art.get("title", "") for art in matched_articles]

        # Prepare context blocks
        context_blocks = "\n\n".join([
            f"### Article: {art['title']} ({art.get('citation', '')})\n{art['content']}"
            for art in matched_articles
        ])

        # Attempt Gemini 2.5 Flash Generation
        response_text = None
        try:
            gemini = get_gemini_client()
            if hasattr(gemini, "client") and gemini.client is not None:
                system_prompt = (
                    "You are the official AI Exam Proctoring Assistant. Your role is to clearly and helpfully "
                    "answer candidate questions regarding exam rules, required identification documentation, "
                    "permitted/prohibited items, and camera/mic setup before they begin their test.\n"
                    "Instructions:\n"
                    "- Answer concisely, authoritatively, and politely using ONLY the provided verified policy context.\n"
                    "- If a candidate asks about prohibited items, explicitly mention the consequences (escalation/penalties).\n"
                    "- If a candidate asks about acceptable IDs, list the official valid options clearly.\n"
                    "- Cite the policy section if applicable."
                )
                user_msg = (
                    f"Candidate Query: {query}\n\n"
                    f"Verified Policy Knowledge Base:\n{context_blocks}\n\n"
                    f"Please provide an accurate, friendly answer:"
                )
                gemini_resp = gemini.client.models.generate_content(
                    model=gemini.model_id,
                    contents=f"{system_prompt}\n\n{user_msg}"
                )
                if gemini_resp and gemini_resp.text:
                    response_text = gemini_resp.text.strip()
        except Exception as e:
            logger.debug(f"Gemini live LLM generation bypassed: {e}. Falling back to deterministic RAG synthesis.")

        # Deterministic RAG Fallback
        if not response_text:
            response_text = self._synthesize_deterministic_response(query, matched_articles)

        # Select contextual follow-up suggestions
        suggested = self._select_follow_up_suggestions(query, matched_articles)

        return PolicyChatResponse(
            response=response_text,
            citations=citations,
            suggested_questions=suggested,
            matched_articles=article_titles
        )

    def _synthesize_deterministic_response(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """
        Creates an explainable, structured policy answer directly from verified knowledge articles.
        """
        if not articles:
            return (
                "Welcome to the Examination Portal! All candidates must present a valid government-issued "
                "photo ID (Passport, Driver's License, National ID, or PAN Card). Unauthorized items including "
                "smartphones, earbuds, and notes are strictly prohibited. How may I help you with your test setup?"
            )

        top_art = articles[0]
        summary_lines = [f"**{top_art['title']}**\n\n{top_art['content']}"]

        if len(articles) > 1:
            second = articles[1]
            summary_lines.append(f"\n\n**Additional Guideline ({second['title']}):**\n{second['content']}")

        summary_lines.append(f"\n\n*Reference: {top_art.get('citation', 'Institutional Exam Regulations')}*")
        return "".join(summary_lines)

    def _select_follow_up_suggestions(self, query: str, matched_articles: List[Dict[str, Any]]) -> List[str]:
        """Chooses relevant follow-up question chips for the user."""
        all_suggestions = list(self.default_suggestions)
        # Exclude questions very similar to the query
        filtered = [
            q for q in all_suggestions
            if not any(token in q.lower() and len(token) > 4 for token in query.lower().split())
        ]
        return filtered[:4] if len(filtered) >= 4 else all_suggestions[:4]

    def get_suggested_questions(self) -> List[str]:
        """Returns the default pre-exam onboarding FAQ prompts."""
        return self.default_suggestions


# Global chatbot service instance
policy_chatbot_service = PolicyChatbotService()
