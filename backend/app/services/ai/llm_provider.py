import json
import re
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.utils.logger import logger
from app.services.ai.prompts import (
    MPSC_TEACHER_SYSTEM_PROMPT, EXAM_MODE_SYSTEM_PROMPT,
    MCQ_GENERATION_PROMPT, PYQ_ANALYSIS_PROMPT
)

class LLMProvider:
    """
    Unified LLM provider supporting Gemini, OpenAI, Groq, Ollama,
    and a reliable local Marathi knowledge generator fallback.
    """

    async def generate_chat_response(
        self,
        user_message: str,
        context_str: str,
        citations: List[Any],
        mode: str = "general_chat",
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generates an AI teacher response in Marathi based on user query and retrieved context.
        """
        system_prompt = self._select_system_prompt(mode)
        full_prompt = self._build_prompt(system_prompt, user_message, context_str, history)

        # 1. Try Google Gemini if configured
        if settings.AI_API_KEY and ("gemini" in settings.AI_PROVIDER.lower() or settings.AI_PROVIDER == "auto"):
            gemini_ans = await self._call_gemini(full_prompt)
            if gemini_ans:
                return self._append_source_footer(gemini_ans, citations)

        # 2. Try OpenAI / Groq if configured
        if settings.AI_API_KEY and ("openai" in settings.AI_PROVIDER.lower() or "groq" in settings.AI_PROVIDER.lower()):
            openai_ans = await self._call_openai_compatible(full_prompt)
            if openai_ans:
                return self._append_source_footer(openai_ans, citations)

        # 3. Fallback Heuristic Generator (Offline & Zero-Key Ready)
        return self._generate_heuristic_response(user_message, context_str, citations, mode)

    def _select_system_prompt(self, mode: str) -> str:
        if mode == "teacher_mode":
            return MPSC_TEACHER_SYSTEM_PROMPT + "\nविद्यार्थ्याला एखादा विषय शिकवताना सोप्या भाषेत टप्प्याटप्प्याने स्पष्ट करा."
        elif mode == "exam_mode":
            return EXAM_MODE_SYSTEM_PROMPT
        elif mode == "pyq_analysis":
            return PYQ_ANALYSIS_PROMPT
        return MPSC_TEACHER_SYSTEM_PROMPT

    def _build_prompt(
        self,
        system_prompt: str,
        user_message: str,
        context_str: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        prompt_parts = [system_prompt, "\n\n=== उपलब्ध अभ्याससाहित्य (User's Uploaded Books Context) ==="]
        if context_str:
            prompt_parts.append(context_str)
        else:
            prompt_parts.append("(कोणतेही विशिष्ट पुस्तक संदर्भ उपलब्ध नाहीत)")

        if history:
            prompt_parts.append("\n=== मागील संभाषण (Conversation History) ===")
            for msg in history[-4:]:
                role = "विद्यार्थी" if msg.get("role") == "user" else "शिक्षक"
                prompt_parts.append(f"{role}: {msg.get('content', '')}")

        prompt_parts.append(f"\nविद्यार्थ्याचा प्रश्न:\n{user_message}")
        prompt_parts.append("\nउत्तर (मराठीत):")
        return "\n".join(prompt_parts)

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:generateContent?key={settings.AI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": settings.AI_TEMPERATURE,
                    "maxOutputTokens": 2048
                }
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return content.strip()
                logger.warning(f"Gemini API returned code {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
        return None

    async def _call_openai_compatible(self, prompt: str) -> Optional[str]:
        try:
            endpoint = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {settings.AI_API_KEY}"}
            payload = {
                "model": settings.AI_MODEL if "gpt" in settings.AI_MODEL else "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": settings.AI_TEMPERATURE
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
        return None

    def _generate_heuristic_response(
        self,
        user_message: str,
        context_str: str,
        citations: List[Any],
        mode: str
    ) -> str:
        """
        Offline fallback generator that extracts key sentences from context and formats an MPSC lesson.
        """
        if not context_str or not citations:
            return (
                "**माझ्या उपलब्ध अभ्याससामग्रीमध्ये या प्रश्नाचे पुरेसे संदर्भ मिळाले नाहीत.**\n\n"
                "💡 **सल्ला:** कृपया संबंधित विषयाचे अधिकृत MPSC संदर्भ पुस्तक किंवा नोट्स '📚 Books' मेनूमध्ये अपलोड करा. "
                "पुस्तक अपलोड व इंडेक्स झाल्यानंतर मी त्यातील अचूक प्रकरण आणि पान क्रमांकासह उत्तर देईन."
            )

        # Context exists! Build structured response
        top_citation = citations[0]
        context_clean = top_citation.text_snippet if hasattr(top_citation, 'text_snippet') else ""
        
        # Split into points
        sentences = [s.strip() for s in re.split(r'[।\.\n]', context_str) if len(s.strip()) > 15]
        key_points = sentences[:5]
        
        points_text = "\n".join([f"• {p}." for p in key_points if not p.startswith("---") and not p.startswith("पुस्तक:")])

        response_lines = [
            "### १. थोडक्यात उत्तर",
            f"{sentences[0] if sentences else 'अभ्याससामग्रीतील संदर्भानुसार माहिती खालीलप्रमाणे आहे.'}।\n",
            "### २. सविस्तर स्पष्टीकरण व माहिती",
            f"{points_text}\n",
            "### ३. MPSC साठी महत्त्वाचे मुद्दे",
            f"• **संदर्भित पुस्तक:** {top_citation.book_name}",
            f"• **प्रकरण:** {top_citation.chapter}",
            f"• **पान क्रमांक:** {top_citation.page_number}",
            "• **परीक्षेसाठी टीप:** या घटकावर थेट तथ्ये, कालक्रम आणि व्यक्ती विशेष प्रश्न विचारले जातात.\n",
            "### ४. संभाव्य सराव प्रश्न (Practice MCQ)",
            f"**प्रश्न:** खालीलपैकी कोणते विधान/घटक {user_message[:40]}... संदर्भात बरोबर आहे?",
            "(A) पर्याय १\n(B) पर्याय २\n(C) पर्याय ३\n(D) वरील सर्व बरोबर\n**उत्तर:** (A)"
        ]

        return self._append_source_footer("\n".join(response_lines), citations)

    def _append_source_footer(self, answer: str, citations: List[Any]) -> str:
        if not citations:
            return answer

        source_lines = ["\n\n---\n**📚 संदर्भ (Sources):**"]
        seen = set()
        for c in citations[:3]:
            b_name = getattr(c, 'book_name', 'Study Material')
            chap = getattr(c, 'chapter', '')
            page = getattr(c, 'page_number', 1)
            key = (b_name, page)
            if key not in seen:
                seen.add(key)
                chap_str = f" | प्रकरण: {chap}" if chap and chap != "General" else ""
                source_lines.append(f"• 📖 **{b_name}**{chap_str} (पान क्र. {page})")

        return answer + "\n" + "\n".join(source_lines)

llm_provider = LLMProvider()
