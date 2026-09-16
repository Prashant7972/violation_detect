"""
Pre-Exam Policy & Real-Time Violation Warning RAG Chatbot Service (Port 8000).
Provides authoritative policy retrieval and generative warnings for exam compliance.
Strict non-termination principle: This service advises and warns candidates,
guaranteeing human oversight without automated termination.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("port8000_policy_chatbot")

KB_DATA = {
    "version": "1.0.0",
    "institution": "National Testing Agency & Institutional CBT Proctoring Board",
    "articles": [
        {
            "id": "RULE-PHONE",
            "category": "PROHIBITED_ITEMS",
            "title": "Strict Zero-Tolerance Mobile Phone Policy",
            "keywords": ["phone", "mobile", "smartphone", "cellphone", "cellular", "calling", "texting", "iphone", "android"],
            "content": "All mobile phones and cellular devices are strictly prohibited inside the active exam workspace. Candidates must ensure phones are turned off and placed completely out of sight and reach. Detection of a mobile phone triggers an immediate official Proctor Warning. Under human-in-the-loop safeguards, the candidate is NOT automatically terminated by the AI system, but must remove the device immediately to avoid disciplinary review.",
            "citation": "Academic Integrity Code Section 4.2 (Mobile Device Restrictions)"
        },
        {
            "id": "RULE-LAPTOP",
            "category": "PROHIBITED_ITEMS",
            "title": "Secondary Laptop and Unauthorized Computing Devices",
            "keywords": ["laptop", "secondary laptop", "second computer", "tablet", "ipad", "monitor", "dual screen", "external display"],
            "content": "Only the single approved primary candidate workstation is authorized for test delivery. Secondary laptops, tablets, auxiliary monitors, and unauthorized computing devices are strictly forbidden in the examination area. If a secondary laptop or screen is identified, the system issues an immediate non-terminating compliance warning instructing the candidate to close and remove the auxiliary machine.",
            "citation": "Technical Workspace Policy Section 4.3 (Auxiliary Displays & Computers)"
        },
        {
            "id": "RULE-PERSON",
            "category": "EXAM_CONDUCT",
            "title": "Solitary Room Isolation & Prohibition of Secondary Persons",
            "keywords": ["person", "persons", "double person", "two people", "multiple persons", "second person", "intruder", "helper", "friend", "room"],
            "content": "The candidate must take the examination alone in an isolated, quiet room. No secondary persons, helpers, colleagues, or room occupants are permitted in the workspace or within camera view. If a second person is detected, an immediate Proctor Warning is issued. The AI system does NOT have the authority to unilaterally terminate the candidate; rather, an urgent notice is delivered requiring the secondary individual to vacate the room immediately.",
            "citation": "Candidate Conduct Standard Section 5.1 (Room Isolation & Solitary Administration)"
        },
        {
            "id": "DOC-IDENT",
            "category": "DOCUMENTATION_AND_ID",
            "title": "Accepted Government Photo Identification",
            "keywords": ["id", "identification", "aadhaar", "pan", "pan card", "passport", "driver license", "driving license", "voter id", "document"],
            "content": "Candidates are required to present an official, valid government-issued photo identity document before taking the assessment. Acceptable IDs include: 1) Aadhaar Card, 2) Permanent Account Number (PAN) Card, 3) Driver's License, 4) Passport, 5) Voter ID Card. The document must be original, clear, and display the candidate's full legal name and photo.",
            "citation": "Candidate Verification Regulation Section 1.1"
        },
        {
            "id": "RULE-GENERAL",
            "category": "EXAM_RULES",
            "title": "General Examination Rules & Permitted Desk Items",
            "keywords": ["rules", "permitted", "allowed", "water", "scratch paper", "pen", "desk", "materials"],
            "content": "Only transparent water bottles and up to two sheets of blank scratch paper with a pen or pencil are allowed on the desk. Headphones, Bluetooth earbuds, smartwatches, and notes are strictly prohibited. Maintain camera centering and screen focus throughout the exam.",
            "citation": "CBT Operational Guidelines Section 3.1"
        },
        {
            "id": "SAFEGUARD-TERMINATION",
            "category": "SAFEGUARDS",
            "title": "Human-in-the-Loop Proctor Safeguards & Non-Termination Policy",
            "keywords": ["terminate", "termination", "disqualified", "kicked out", "cancel", "ai authority", "human proctor"],
            "content": "In accordance with ethical AI standards and examination board bylaws, automated computer vision and LLM models DO NOT have the authority to unilaterally terminate or disqualify a candidate. All flagged anomalies generate educational and compliance warnings directly to the candidate, allowing immediate workspace correction. Any severe escalation requires manual human proctor review.",
            "citation": "Ethical Proctoring Charter Section 7.4 (Candidate Protection Guarantee)"
        }
    ],
    "suggested_questions": [
        "What happens if a mobile phone is detected?",
        "Are secondary laptops or screens allowed?",
        "Can someone else be in the room during the test?",
        "Does the AI have the right to terminate my exam?",
        "What government ID documents are accepted?"
    ]
}


CLIENT_COMPANIES = {
    "techhire_global": {
        "id": "techhire_global",
        "name": "TechHire Global Enterprise Assessment",
        "industry": "Software Engineering & Tech Hiring",
        "strictness": "MAXIMUM_STRICT",
        "description": "High-stakes technical recruitment assessment with zero electronic aids and solitary isolation.",
        "policies": {
            "PHONE": {
                "clause": "TechHire Integrity Code Sec. 4.2",
                "severity": "CRITICAL",
                "rule": "Absolute Zero-Tolerance: No cell phones in room. Flagged keyframes archived to Admin Evidence Repository.",
                "admin_action": "Review annotated mobile phone keyframe. Candidate received non-terminating warning."
            },
            "LAPTOP": {
                "clause": "TechHire Hardware Protocol Sec. 4.3",
                "severity": "HIGH",
                "rule": "Secondary laptop or external display prohibited. Only authorized single primary laptop permitted.",
                "admin_action": "Check for unauthorized second screen/IDE sharing in admin evidence."
            },
            "PERSON": {
                "clause": "TechHire Workspace Isolation Sec. 5.1",
                "severity": "HIGH",
                "rule": "Solitary Room Policy: Secondary persons / double occupants strictly forbidden.",
                "admin_action": "Inspect multi-occupant keyframe evidence. Solitary isolation warning dispatched."
            }
        }
    },
    "nta_standard": {
        "id": "nta_standard",
        "name": "National Testing Agency (NTA CBT Standards)",
        "industry": "Government & Higher Education",
        "strictness": "HIGH",
        "description": "Standardized competitive entrance testing standard with strict government ID checks and device scanning.",
        "policies": {
            "PHONE": {
                "clause": "NTA Examination Rules Sec. 6.1",
                "severity": "CRITICAL",
                "rule": "Zero Tolerance: Mobile phone presence is a severe breach. Keyframe sent to Chief Examiner.",
                "admin_action": "Escalate to Center Superintendant via Admin Evidence Gallery."
            },
            "LAPTOP": {
                "clause": "NTA Technical Standard Sec. 2.4",
                "severity": "HIGH",
                "rule": "Auxiliary computing machines or dual laptops strictly barred.",
                "admin_action": "Verify device bounding box in Admin Portal."
            },
            "PERSON": {
                "clause": "NTA Room Security Protocol Sec. 3.2",
                "severity": "HIGH",
                "rule": "No unauthorized invigilator or secondary person in testing chamber.",
                "admin_action": "Examine intruder snapshot in Admin Dossier."
            }
        }
    },
    "fintech_secure": {
        "id": "fintech_secure",
        "name": "FinTech & Banking Certification Board",
        "industry": "Financial Services & Banking Compliance",
        "strictness": "REGULATORY_CRITICAL",
        "description": "Regulatory examination requiring complete device shielding and compliance audit trails.",
        "policies": {
            "PHONE": {
                "clause": "FinTech Compliance Standard 8.4",
                "severity": "CRITICAL",
                "rule": "Communication hardware breach. Frame captured for regulatory proctor review.",
                "admin_action": "Compliance officer must audit evidence keyframe."
            },
            "LAPTOP": {
                "clause": "FinTech InfoSec Protocol 3.9",
                "severity": "HIGH",
                "rule": "Unauthorized secondary computing node detected.",
                "admin_action": "Inspect peripheral device layout in Admin Panel."
            },
            "PERSON": {
                "clause": "FinTech Solitary Policy 2.1",
                "severity": "HIGH",
                "rule": "Secondary person presents insider collusion risk. Isolation required.",
                "admin_action": "Review multi-person audit proof."
            }
        }
    }
}


class Port8000PolicyChatbot:
    """
    RAG-powered policy chatbot service with strict non-termination guarantees.
    Supports client company-specific policies and private admin evidence collection.
    """

    def __init__(self):
        self.articles = KB_DATA["articles"]
        self.suggested_questions = KB_DATA["suggested_questions"]
        self.active_company_id = "techhire_global"
        self.admin_policy_breaches = []

    def retrieve_relevant_articles(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Lexical retrieval over knowledge base articles."""
        query_tokens = set(re.findall(r"\w+", query.lower()))
        if not query_tokens:
            return self.articles[:top_k]

        scored = []
        for art in self.articles:
            score = 0
            keywords = [k.lower() for k in art.get("keywords", [])]
            for kw in keywords:
                kw_tokens = set(re.findall(r"\w+", kw))
                if kw_tokens.issubset(query_tokens):
                    score += 5
                elif any(t in query_tokens for t in kw_tokens):
                    score += 2

            title_tokens = set(re.findall(r"\w+", art.get("title", "").lower()))
            score += len(query_tokens.intersection(title_tokens)) * 3

            content_lower = art.get("content", "").lower()
            for token in query_tokens:
                if len(token) > 3 and token in content_lower:
                    score += 1

            scored.append((score, art))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [art for score, art in scored if score > 0][:top_k]
        return results if results else self.articles[:top_k]

    def answer_query(self, query: str, student_id: str = "STU-001") -> Dict[str, Any]:
        """Answers candidate query with RAG citations."""
        matched = self.retrieve_relevant_articles(query, top_k=2)
        citations = [art.get("citation", "Institutional Policy") for art in matched]

        # LLM Synthesis attempt via Google Gemini if available
        llm_response = None
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                context = "\n\n".join([f"[{a['title']} - {a['citation']}]\n{a['content']}" for a in matched])
                prompt = (
                    "You are the official AI Exam Proctoring Assistant. Answer the candidate's question "
                    "clearly, concisely, and politely using ONLY the provided verified policies. Emphasize that "
                    "the AI cannot terminate candidates without human proctor review.\n\n"
                    f"Policy Context:\n{context}\n\nCandidate Question: {query}"
                )
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if resp and resp.text:
                    llm_response = resp.text.strip()
            except Exception as e:
                logger.debug(f"Gemini LLM call failed or offline: {e}")

        # Deterministic RAG Fallback
        if not llm_response:
            if matched:
                primary = matched[0]
                text_parts = [f"**{primary['title']}**\n\n{primary['content']}"]
                if len(matched) > 1:
                    secondary = matched[1]
                    text_parts.append(f"\n\n**Related Guideline ({secondary['title']}):**\n{secondary['content']}")
                text_parts.append(f"\n\n*Reference: {primary.get('citation', 'Institutional Regulations')}*")
                llm_response = "".join(text_parts)
            else:
                llm_response = (
                    "Please adhere to standard examination protocols: maintain a clean desk, no unauthorized "
                    "devices (smartphones/laptops), and test alone. Feel free to ask about any specific rule!"
                )

        return {
            "response": llm_response,
            "citations": citations,
            "suggested_questions": self.suggested_questions[:4],
            "is_warning": False
        }

    def generate_violation_warning(self, violation_type: str, student_id: str = "STU-001") -> Dict[str, Any]:
        """
        Generates an authoritative, policy-grounded warning when camera detects
        a mobile phone, secondary laptop, or double person.
        Guarantees non-termination: provides direct warning to candidate.
        """
        violation_upper = violation_type.upper()

        if "PHONE" in violation_upper or "MOBILE" in violation_upper:
            art = next((a for a in self.articles if a["id"] == "RULE-PHONE"), self.articles[0])
            title = "⚠️ PROCTOR WARNING: Mobile Phone Detected"
            message = (
                "A mobile phone or cellular device has been detected in your camera frame. "
                "In accordance with Section 4.2 of the Academic Integrity Code, all unauthorized communication "
                "devices are strictly prohibited. Please remove the phone from the workspace immediately.\n\n"
                "🛡️ Notice: You have NOT been terminated. This is an official advisory warning to correct your "
                "workspace and avoid escalating this incident to the human proctor."
            )
            citation = art.get("citation", "Academic Integrity Code Section 4.2")

        elif "LAPTOP" in violation_upper or "DEVICE" in violation_upper:
            art = next((a for a in self.articles if a["id"] == "RULE-LAPTOP"), self.articles[1])
            title = "⚠️ PROCTOR WARNING: Secondary Laptop / Screen Detected"
            message = (
                "An unauthorized secondary laptop or auxiliary display has been identified in your exam workspace. "
                "Pursuant to Section 4.3 of the Technical Workspace Policy, only your primary testing machine is permitted. "
                "Please close and remove the secondary device immediately.\n\n"
                "🛡️ Notice: You have NOT been terminated. This is an official advisory warning to adjust your "
                "hardware setup."
            )
            citation = art.get("citation", "Technical Workspace Policy Section 4.3")

        elif "PERSON" in violation_upper or "DOUBLE" in violation_upper:
            art = next((a for a in self.articles if a["id"] == "RULE-PERSON"), self.articles[2])
            title = "⚠️ PROCTOR WARNING: Double Person / Multiple Occupants Detected"
            message = (
                "Multiple individuals or a secondary person have been detected in your room. "
                "Under Section 5.1 of Candidate Conduct Standards, you must complete your examination in strict "
                "solitary isolation. Please ensure that all secondary individuals exit the room immediately.\n\n"
                "🛡️ Notice: You have NOT been terminated. This is an official advisory warning to restore room isolation."
            )
            citation = art.get("citation", "Candidate Conduct Standard Section 5.1")

        else:
            title = "⚠️ PROCTOR WARNING: Examination Policy Violation"
            message = (
                f"A workspace anomaly ({violation_type}) was flagged by the proctoring monitor. "
                "Please ensure your desk is clean, face centered, and workspace isolated.\n\n"
                "🛡️ Notice: You have NOT been terminated. Please correct your environment immediately."
            )
            citation = "Academic Integrity Code Section 7.0"

        # Attempt Gemini dynamic generation if key present
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                prompt = (
                    f"You are the official AI Exam Proctoring Assistant. A live webcam detection flagged: '{violation_type}'.\n"
                    "Generate a concise, authoritative warning for the candidate explaining the policy violation, "
                    "commanding them to rectify it immediately, and explicitly reassuring them that they are NOT terminated, "
                    "as AI models do not have termination rights without human proctor review.\n"
                    f"Policy reference: {citation}"
                )
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if resp and resp.text:
                    message = resp.text.strip()
            except Exception as e:
                logger.debug(f"Gemini LLM warning generation failed: {e}")

        return {
            "warning_title": title,
            "warning_message": message,
            "citation": citation,
            "can_terminate": False,
            "student_id": student_id,
            "is_warning": True
        }

    def list_companies(self) -> List[Dict[str, Any]]:
        """Returns all configured client company policy profiles."""
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "industry": c["industry"],
                "strictness": c["strictness"],
                "description": c["description"]
            }
            for c in CLIENT_COMPANIES.values()
        ]

    def set_active_company(self, company_id: str) -> bool:
        """Sets the active company policy for the session."""
        if company_id in CLIENT_COMPANIES:
            self.active_company_id = company_id
            return True
        return False

    def get_active_company(self) -> Dict[str, Any]:
        """Returns the currently active company policy profile."""
        return CLIENT_COMPANIES.get(self.active_company_id, CLIENT_COMPANIES["techhire_global"])

    def evaluate_breach_for_admin(self, violation_type: str, student_id: str = "STU-001") -> Dict[str, Any]:
        """
        RAG evaluation of a live camera violation against the active client company's policy.
        Prepares authoritative breach documentation for the Administrator.
        """
        company = self.get_active_company()
        v_upper = violation_type.upper()
        if "PHONE" in v_upper or "MOBILE" in v_upper:
            v_key = "PHONE"
        elif "LAPTOP" in v_upper or "DEVICE" in v_upper:
            v_key = "LAPTOP"
        else:
            v_key = "PERSON"

        rule_info = company["policies"].get(v_key, company["policies"]["PHONE"])

        return {
            "company_id": company["id"],
            "company_name": company["name"],
            "violation_type": violation_type,
            "policy_clause": rule_info["clause"],
            "severity": rule_info["severity"],
            "rule_description": rule_info["rule"],
            "admin_action_recommended": rule_info["admin_action"],
            "student_id": student_id,
            "restricted_to_admin": True
        }

    def record_admin_breach(self, student_id: str, violation_type: str, evidence_url: str) -> Dict[str, Any]:
        """
        Archives an annotated breach keyframe for the Admin ONLY.
        Associates the image with the company's RAG policy clause and timestamp.
        """
        import time
        from datetime import datetime, timezone
        dossier = self.evaluate_breach_for_admin(violation_type, student_id)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        breach_record = {
            "timestamp": now_iso,
            "student_id": student_id,
            "company_id": dossier["company_id"],
            "company_name": dossier["company_name"],
            "violation_type": violation_type,
            "policy_clause": dossier["policy_clause"],
            "severity": dossier["severity"],
            "rule_description": dossier["rule_description"],
            "evidence_url": evidence_url,
            "admin_action_recommended": dossier["admin_action_recommended"]
        }

        self.admin_policy_breaches.insert(0, breach_record)
        # Keep latest 100 in-memory
        if len(self.admin_policy_breaches) > 100:
            self.admin_policy_breaches = self.admin_policy_breaches[:100]

        return breach_record

    def get_admin_breaches(self, student_id: Optional[str] = None, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves violation evidence dossiers for Administrator view."""
        results = self.admin_policy_breaches
        if student_id:
            results = [b for b in results if b["student_id"] == student_id]
        if company_id:
            results = [b for b in results if b["company_id"] == company_id]
        return results


# Global instance
policy_chatbot = Port8000PolicyChatbot()
