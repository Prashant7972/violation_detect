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
                "admin_action": "Review annotated mobile phone keyframe. Candidate received non-terminating warning.",
                "allowed": False
            },
            "LAPTOP": {
                "clause": "TechHire Hardware Protocol Sec. 4.3",
                "severity": "HIGH",
                "rule": "Secondary laptop or external display prohibited. Only authorized single primary laptop permitted.",
                "admin_action": "Check for unauthorized second screen/IDE sharing in admin evidence.",
                "allowed": False
            },
            "PERSON": {
                "clause": "TechHire Workspace Isolation Sec. 5.1",
                "severity": "HIGH",
                "rule": "Solitary Room Policy: Secondary persons / double occupants strictly forbidden.",
                "admin_action": "Inspect multi-occupant keyframe evidence. Solitary isolation warning dispatched.",
                "allowed": False
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
                "admin_action": "Escalate to Center Superintendant via Admin Evidence Gallery.",
                "allowed": False
            },
            "LAPTOP": {
                "clause": "NTA Technical Standard Sec. 2.4",
                "severity": "HIGH",
                "rule": "Auxiliary computing machines or dual laptops strictly barred.",
                "admin_action": "Verify device bounding box in Admin Portal.",
                "allowed": False
            },
            "PERSON": {
                "clause": "NTA Room Security Protocol Sec. 3.2",
                "severity": "HIGH",
                "rule": "No unauthorized invigilator or secondary person in testing chamber.",
                "admin_action": "Examine intruder snapshot in Admin Dossier.",
                "allowed": False
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
                "admin_action": "Compliance officer must audit evidence keyframe.",
                "allowed": False
            },
            "LAPTOP": {
                "clause": "FinTech InfoSec Protocol 3.9",
                "severity": "HIGH",
                "rule": "Unauthorized secondary computing node detected.",
                "admin_action": "Inspect peripheral device layout in Admin Panel.",
                "allowed": False
            },
            "PERSON": {
                "clause": "FinTech Solitary Policy 2.1",
                "severity": "HIGH",
                "rule": "Secondary person presents insider collusion risk. Isolation required.",
                "admin_action": "Review multi-person audit proof.",
                "allowed": False
            }
        }
    }
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
PERSISTED_POLICIES_FILE = os.path.join(DATA_DIR, "persisted_policies.json")


class Port8000PolicyChatbot:
    """
    RAG-powered policy chatbot service with strict non-termination guarantees.
    Supports client company-specific policies and private admin evidence collection.
    """

    def __init__(self):
        self.articles = list(KB_DATA["articles"])
        self.suggested_questions = list(KB_DATA["suggested_questions"])
        self.active_company_id = "techhire_global"
        self.admin_policy_breaches = []
        self._load_persisted_state()

    def _load_persisted_state(self):
        """Loads persisted client policies and active company from disk."""
        try:
            if os.path.exists(PERSISTED_POLICIES_FILE):
                with open(PERSISTED_POLICIES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "client_companies" in data and isinstance(data["client_companies"], dict):
                        CLIENT_COMPANIES.update(data["client_companies"])
                    if "active_company_id" in data and data["active_company_id"] in CLIENT_COMPANIES:
                        self.active_company_id = data["active_company_id"]
                    if "custom_articles" in data and isinstance(data["custom_articles"], list):
                        existing_ids = {a.get("id") for a in self.articles}
                        for art in data["custom_articles"]:
                            if art.get("id") not in existing_ids:
                                self.articles.append(art)
                                existing_ids.add(art.get("id"))
                logger.info(f"Loaded persisted policies. Active company: {self.active_company_id}")
        except Exception as e:
            logger.warning(f"Failed to load persisted policies: {e}")

    def _save_persisted_state(self):
        """Saves current client policies and active company to disk."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            custom_articles = [a for a in self.articles if a.get("category") == "CLIENT_POLICY"]
            payload = {
                "active_company_id": self.active_company_id,
                "client_companies": CLIENT_COMPANIES,
                "custom_articles": custom_articles
            }
            with open(PERSISTED_POLICIES_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            logger.info(f"Saved persisted policies. Active company: {self.active_company_id}")
        except Exception as e:
            logger.warning(f"Failed to save persisted policies: {e}")

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
            self._save_persisted_state()
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

    def get_admin_breaches(self, student_id: Optional[str] = None, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves violation evidence dossiers for Administrator view."""
        results = self.admin_policy_breaches
        if student_id:
            results = [b for b in results if b["student_id"] == student_id]
        if company_id:
            results = [b for b in results if b["company_id"] == company_id]
        return results

    def is_violation_prohibited(self, violation_type: str) -> bool:
        """
        Determines whether an observed event/device is PROHIBITED (breach)
        or PERMITTED (allowed) under the active client company's RAG policy.
        Returns True if PROHIBITED (is a violation).
        Returns False if ALLOWED (not a violation).
        """
        active_comp = self.get_active_company()
        policies = active_comp.get("policies", {})
        v_upper = violation_type.upper()

        if "NO_PERSON" in v_upper or "MISSING" in v_upper:
            return True
        elif "PHONE" in v_upper or "MOBILE" in v_upper:
            policy_item = policies.get("PHONE", {})
        elif "LAPTOP" in v_upper or "DEVICE" in v_upper:
            policy_item = policies.get("LAPTOP", {})
        elif "PERSON" in v_upper or "DOUBLE" in v_upper:
            policy_item = policies.get("PERSON", {})
        else:
            return True

        # If policy explicitly defines allowed=True, then it is NOT a violation
        return not policy_item.get("allowed", False)

    def parse_policy_text(self, text: str) -> Dict[str, Any]:
        """
        Dynamically extracts device/proctoring permissions (Phone, Laptop, Person)
        from raw policy documents, bylaws, or natural language prompts.
        Handles lists, exemptions ('except the mobile laptop all'), direct allowances,
        and explicit strictness overrides.
        """
        if not text or not text.strip():
            return {
                "phone_allowed": False,
                "laptop_allowed": False,
                "person_allowed": False,
                "phone_explicitly_set": False,
                "laptop_explicitly_set": False,
                "person_explicitly_set": False
            }

        t = text.lower()
        
        phone_terms = ["mobile", "phone", "cellphone", "cell phone", "smartphone", "cellular"]
        laptop_terms = ["laptop", "screen", "monitor", "dual display", "tablet", "ipad", "auxiliary display", "secondary machine", "second computer", "device", "devices"]
        person_terms = ["person", "people", "group", "companion", "helper", "double person", "secondary person", "roommate"]

        def contains_term(segment: str, terms: List[str]) -> bool:
            for term in terms:
                if re.search(r"\b" + re.escape(term) + r"s?\b", segment):
                    return True
            return False

        phone_allowed = False
        laptop_allowed = False
        person_allowed = False
        phone_explicit = False
        laptop_explicit = False
        person_explicit = False

        # 1. Multi-item exemption segments: "except <items>", "excluding <items>", etc.
        exempt_matches = re.finditer(r"(?:except|excluding|apart from|other than|besides|omission of)\s+([^.;\n]+)", t)
        for m in exempt_matches:
            raw_seg = m.group(1)
            # Cut off at trailing boundary words
            clean_seg = re.split(r"\b(?:all\s+other|all\s+the\s+other|all|others|everything|the\s+rest|flag\s+them|failed)\b", raw_seg)[0]
            if contains_term(clean_seg, phone_terms):
                phone_allowed = True
                phone_explicit = True
            if contains_term(clean_seg, laptop_terms):
                laptop_allowed = True
                laptop_explicit = True
            if contains_term(clean_seg, person_terms):
                person_allowed = True
                person_explicit = True

        # 2. Positive permission phrases
        for term in phone_terms:
            if re.search(rf"\b(allow|allowed|permit|permitted|authorized|exempt|acceptable)\b[^\.\n;]{{0,35}}\b{term}\b", t) or \
               re.search(rf"\b{term}\b[^\.\n;]{{0,35}}\b(allowed|permitted|authorized|exempt|acceptable)\b", t) or \
               re.search(rf"(?:don\x27?t|do not)\s+(?:flag|penalize|fail)[^\.\n;]{{0,35}}\b{term}\b", t):
                if not re.search(rf"\bnot\s+(?:allowed|permitted)\b[^\.\n;]{{0,35}}\b{term}\b", t) and \
                   not re.search(rf"\b{term}\b[^\.\n;]{{0,35}}\bnot\s+(?:allowed|permitted)\b", t):
                    phone_allowed = True
                    phone_explicit = True

        for term in ["laptop", "screen", "monitor", "dual display", "tablet", "auxiliary"]:
            if re.search(rf"\b(allow|allowed|permit|permitted|authorized|exempt|acceptable)\b[^\.\n;]{{0,35}}\b{term}\b", t) or \
               re.search(rf"\b{term}\b[^\.\n;]{{0,35}}\b(allowed|permitted|authorized|exempt|acceptable)\b", t) or \
               re.search(rf"(?:don\x27?t|do not)\s+(?:flag|penalize|fail)[^\.\n;]{{0,35}}\b{term}\b", t):
                if not re.search(rf"\bnot\s+(?:allowed|permitted)\b[^\.\n;]{{0,35}}\b{term}\b", t) and \
                   not re.search(rf"\b{term}\b[^\.\n;]{{0,35}}\bnot\s+(?:allowed|permitted)\b", t):
                    laptop_allowed = True
                    laptop_explicit = True

        for term in person_terms:
            if re.search(rf"\b(allow|allowed|permit|permitted|authorized|exempt|acceptable)\b[^\.\n;]{{0,35}}\b{term}\b", t) or \
               re.search(rf"\b{term}\b[^\.\n;]{{0,35}}\b(allowed|permitted|authorized|exempt|acceptable)\b", t) or \
               re.search(rf"(?:don\x27?t|do not)\s+(?:flag|penalize|fail)[^\.\n;]{{0,35}}\b{term}\b", t):
                if not re.search(rf"\bnot\s+(?:allowed|permitted)\b[^\.\n;]{{0,35}}\b{term}\b", t) and \
                   not re.search(rf"\b{term}\b[^\.\n;]{{0,35}}\bnot\s+(?:allowed|permitted)\b", t):
                    person_allowed = True
                    person_explicit = True

        # 3. Explicit prohibition patterns override ONLY if that term is NOT in an exemption segment
        exempt_texts = " ".join(m.group(1) for m in re.finditer(r"(?:except|excluding|apart from|other than|besides)\s+([^.;\n]+)", t))
        
        if re.search(r"\b(strictly\s+prohibit|prohibited|banned|forbidden|zero\s*tolerance)\b[^\.\n;]{{0,35}}\b(phone|mobile)\b", t) or \
           re.search(r"\b(phone|mobile)\b[^\.\n;]{{0,35}}\b(strictly\s+prohibit|prohibited|banned|forbidden)\b", t):
            if not contains_term(exempt_texts, phone_terms):
                phone_allowed = False
                phone_explicit = True

        if re.search(r"\b(strictly\s+prohibit|prohibited|banned|forbidden|zero\s*tolerance)\b[^\.\n;]{{0,35}}\blaptop\b", t) or \
           re.search(r"\blaptop\b[^\.\n;]{{0,35}}\b(strictly\s+prohibit|prohibited|banned|forbidden)\b", t):
            if not contains_term(exempt_texts, laptop_terms):
                laptop_allowed = False
                laptop_explicit = True

        if re.search(r"\b(strictly\s+prohibit|prohibited|banned|forbidden|zero\s*tolerance|solitary|isolation)\b[^\.\n;]{{0,35}}\b(person|people)\b", t):
            if not contains_term(exempt_texts, person_terms):
                person_allowed = False
                person_explicit = True

        return {
            "phone_allowed": phone_allowed,
            "laptop_allowed": laptop_allowed,
            "person_allowed": person_allowed,
            "phone_explicitly_set": phone_explicit,
            "laptop_explicitly_set": laptop_explicit,
            "person_explicitly_set": person_explicit
        }

    def ingest_policy_document(
        self,
        company_name: str,
        industry: str = "Technology",
        strictness: str = "HIGH",
        document_text: str = "",
        document_filename: Optional[str] = None,
        file_b64: Optional[str] = None,
        phone_allowed: Optional[bool] = None,
        laptop_allowed: Optional[bool] = None,
        person_allowed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Ingests an administrative client company policy document,
        dynamically extracts and defines violation/breach rules (Phone, Laptop, Person, etc.),
        supports custom device permissions (allowed vs prohibited),
        registers the company into the multi-client policy registry, and activates it.
        """
        import base64
        import time

        raw_text = (document_text or "").strip()

        # Handle base64 file if provided
        if file_b64:
            try:
                clean_b64 = file_b64
                if "," in file_b64:
                    clean_b64 = file_b64.split(",", 1)[1]
                decoded_bytes = base64.b64decode(clean_b64)
                
                # Check for PDF stream or extract strings
                if decoded_bytes.startswith(b"%PDF"):
                    pdf_text_parts = re.findall(rb"\((.*?)\)", decoded_bytes)
                    pdf_strings = [p.decode("latin-1", errors="ignore") for p in pdf_text_parts if len(p) > 2]
                    extracted_pdf = " ".join(pdf_strings)
                    if len(extracted_pdf.strip()) > 30:
                        raw_text = (raw_text + "\n" + extracted_pdf).strip()
                    else:
                        raw_text = (raw_text + f"\n[Ingested PDF Document: {document_filename or 'policy.pdf'}]").strip()
                else:
                    try:
                        decoded_str = decoded_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        decoded_str = decoded_bytes.decode("latin-1", errors="ignore")
                    raw_text = (raw_text + "\n" + decoded_str).strip()
            except Exception as e:
                logger.warning(f"Error decoding base64 policy file: {e}")

        if not raw_text:
            raw_text = f"Standard integrity bylaws and proctoring regulations for {company_name}."

        # Unique company ID slug
        slug = re.sub(r"[^a-z0-9]+", "_", company_name.lower().strip()).strip("_")
        if not slug:
            slug = f"company_{int(time.time())}"
        company_id = slug

        # Intelligent permission analysis from document text
        parsed_permissions = self.parse_policy_text(raw_text)

        # Reconcile explicit parameters vs text-extracted permissions
        if phone_allowed is None or parsed_permissions.get("phone_explicitly_set"):
            phone_allowed = parsed_permissions["phone_allowed"]
        elif phone_allowed is False and parsed_permissions.get("phone_allowed") is True:
            phone_allowed = True

        if laptop_allowed is None or parsed_permissions.get("laptop_explicitly_set"):
            laptop_allowed = parsed_permissions["laptop_allowed"]
        elif laptop_allowed is False and parsed_permissions.get("laptop_allowed") is True:
            laptop_allowed = True

        if person_allowed is None or parsed_permissions.get("person_explicitly_set"):
            person_allowed = parsed_permissions["person_allowed"]
        elif person_allowed is False and parsed_permissions.get("person_allowed") is True:
            person_allowed = True

        # Parse and define breach rules from document text
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        def find_relevant_clause(keywords: List[str], default_clause: str, default_rule: str, default_action: str, is_allowed: bool) -> Dict[str, Any]:
            if is_allowed:
                return {
                    "clause": f"{company_name} Policy Sec. 2.0 (Authorized {keywords[0].title()})",
                    "severity": "ALLOWED",
                    "rule": f"{keywords[0].title()} usage is authorized/permitted under client policy. Detection will NOT be treated as a violation or archived as breach evidence.",
                    "admin_action": f"{keywords[0].title()} permitted by client policy. No violation logged.",
                    "allowed": True
                }

            matched_lines = []
            for line in lines:
                lower = line.lower()
                if any(kw in lower for kw in keywords):
                    matched_lines.append(line)
            
            clause_heading = default_clause
            rule_text = default_rule
            admin_action = default_action

            if matched_lines:
                for ml in matched_lines:
                    clause_match = re.search(r"(section\s+[\d\.]+|clause\s+[\d\.]+|rule\s+[\d\.]+|article\s+[\d\.]+)", ml, re.IGNORECASE)
                    if clause_match:
                        clause_heading = f"{company_name} {clause_match.group(1).title()}"
                        break
                
                # When searching for a prohibition rule, NEVER quote an exemption clause (e.g. "except mobile laptop all")
                prohibition_lines = [
                    ml for ml in matched_lines
                    if not re.search(r"\b(except|excluding|apart from|other than|besides|omission of|allowed|permitted|authorized|exempt)\b", ml, re.IGNORECASE)
                ]
                if prohibition_lines:
                    candidate_rule = " ".join(prohibition_lines[:2])
                    if len(candidate_rule) > 15:
                        rule_text = candidate_rule[:280]

            return {
                "clause": clause_heading,
                "severity": "CRITICAL" if ("phone" in keywords[0] or strictness == "MAXIMUM_STRICT") else "HIGH",
                "rule": rule_text,
                "admin_action": admin_action,
                "allowed": False
            }

        phone_policy = find_relevant_clause(
            keywords=["phone", "mobile", "smartphone", "cellular", "calling"],
            default_clause=f"{company_name} Integrity Bylaw Sec. 4.2",
            default_rule="Zero-Tolerance Mobile Devices: Cellular phones and electronic gadgets are strictly banned in testing room.",
            default_action="Inspect annotated mobile phone evidence keyframe in Admin Dossier.",
            is_allowed=phone_allowed
        )

        laptop_policy = find_relevant_clause(
            keywords=["laptop", "screen", "monitor", "dual display", "tablet", "auxiliary", "second computer"],
            default_clause=f"{company_name} Workstation Standard Sec. 4.3",
            default_rule="Secondary Display / Machine Prohibition: Only the approved primary examination laptop may be active.",
            default_action="Verify secondary display / dual machine layout in Admin Evidence Gallery.",
            is_allowed=laptop_allowed
        )

        person_policy = find_relevant_clause(
            keywords=["person", "persons", "alone", "solitary", "intruder", "helper", "occupant", "room", "whisper"],
            default_clause=f"{company_name} Solitary Isolation Protocol Sec. 5.1",
            default_rule="Strict Solitary Isolation: Secondary individuals, assistants, or observers in the room are prohibited.",
            default_action="Audit multi-occupant snapshot and room isolation compliance.",
            is_allowed=person_allowed
        )

        defined_policies = {
            "PHONE": phone_policy,
            "LAPTOP": laptop_policy,
            "PERSON": person_policy
        }

        allowed_names = [k for k, v in defined_policies.items() if v.get("allowed")]
        prohibited_names = [k for k, v in defined_policies.items() if not v.get("allowed")]

        doc_summary = (
            f"Successfully parsed policy document ({len(raw_text)} chars). "
            f"Allowed items: {', '.join(allowed_names) if allowed_names else 'None (Strict)'}. "
            f"Prohibited violations: {', '.join(prohibited_names)}. "
            f"Enforcing {strictness} standards for {company_name}."
        )

        # Register in CLIENT_COMPANIES
        company_profile = {
            "id": company_id,
            "name": company_name,
            "industry": industry,
            "strictness": strictness,
            "description": f"Ingested policy document ({document_filename or 'uploaded document'}). Enforces {strictness} rules for {industry}.",
            "policies": defined_policies,
            "document_summary": doc_summary,
            "raw_text_snippet": raw_text[:500]
        }

        CLIENT_COMPANIES[company_id] = company_profile
        self.set_active_company(company_id)

        # Ingest into chatbot articles so candidate chatbot is grounded in this document
        new_article = {
            "id": f"RULE-{company_id.upper()}",
            "category": "CLIENT_POLICY",
            "title": f"{company_name} Examination Regulations",
            "keywords": [company_name.lower(), "client", "custom policy", "bylaws", "rules"],
            "content": f"Policy for {company_name}: {phone_policy['rule']} {laptop_policy['rule']} {person_policy['rule']}",
            "citation": f"{company_name} Code of Conduct"
        }
        self.articles.append(new_article)
        self._save_persisted_state()

        return {
            "success": True,
            "company_id": company_id,
            "company_name": company_name,
            "strictness": strictness,
            "document_summary": doc_summary,
            "defined_breaches": defined_policies,
            "active_company": company_profile,
            "message": f"Policy document for '{company_name}' ingested successfully. Defined breach rules are now active."
        }


# Global instance
policy_chatbot = Port8000PolicyChatbot()
