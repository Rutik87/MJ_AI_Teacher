import json
import re
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.utils.logger import logger
from app.services.ai.providers import (
    BaseAIProvider, OpenAIProvider, OpenRouterProvider, GeminiProvider, HeuristicLocalProvider
)
from app.services.ai.prompts import (
    MPSC_TEACHER_SYSTEM_PROMPT, EXAM_MODE_SYSTEM_PROMPT,
    MCQ_GENERATION_PROMPT, PYQ_ANALYSIS_PROMPT
)

class LLMProvider:
    """
    Unified LLM Provider Service for MPSC AI.
    Primary AI Provider: ChatGPT OpenAI (gpt-4o-mini / gpt-4o).
    Optional Fallback: OpenRouter Free Models Router / Gemini Provider.
    Zero-Key Fallback: Heuristic Local Engine.
    """

    def __init__(self):
        self._init_providers()

    def _init_providers(self):
        self.openai_provider = OpenAIProvider()
        self.openrouter_provider = OpenRouterProvider()
        self.gemini_provider = GeminiProvider()
        self.heuristic_provider = HeuristicLocalProvider()

    def get_active_provider_name(self) -> str:
        prov_setting = settings.AI_PROVIDER.lower()
        if prov_setting == "openai" or settings.OPENAI_API_KEY:
            return self.openai_provider.provider_name
        elif prov_setting == "openrouter" or settings.OPENROUTER_API_KEY:
            return self.openrouter_provider.provider_name
        elif prov_setting == "gemini" or settings.GEMINI_API_KEY:
            return self.gemini_provider.provider_name
        return self.heuristic_provider.provider_name

    async def _execute_with_provider(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Tuple[Optional[str], str]:
        prov_setting = settings.AI_PROVIDER.lower()

        # 1. Primary ChatGPT OpenAI Provider
        if prov_setting in ["openai", "auto"] or settings.OPENAI_API_KEY:
            res = await self.openai_provider.generate_completion(
                prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens
            )
            if res:
                return res, self.openai_provider.provider_name

        # 2. Secondary OpenRouter Free Router (Fallback)
        res = await self.openrouter_provider.generate_completion(
            prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens
        )
        if res:
            return res, self.openrouter_provider.provider_name

        # 3. Optional Gemini Provider (Fallback)
        res = await self.gemini_provider.generate_completion(
            prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens
        )
        if res:
            return res, self.gemini_provider.provider_name

        # 4. Fallback Heuristic Generator (Offline / Free)
        return None, self.heuristic_provider.provider_name

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Tuple[Optional[str], str]:
        """Public method for generating completions using active or fallback provider."""
        res, prov = await self._execute_with_provider(prompt, system_prompt, temperature, max_tokens)
        return res, prov

    async def generate_chat_response(
        self,
        user_message: str,
        context_str: str,
        citations: List[Any],
        mode: str = "general_chat",
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generates an AI teacher response in Marathi based on user query and retrieved RAG context.
        """
        system_prompt = self._select_system_prompt(mode)
        full_prompt = self._build_prompt(system_prompt, user_message, context_str, history)

        response_text, provider_used = await self._execute_with_provider(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=settings.AI_TEMPERATURE
        )

        if response_text:
            return self._append_source_footer(response_text, citations)

        # Fallback to Heuristic Generator if API keys unavailable or rate limited
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
                "**या प्रश्नाचे पुरेसे उत्तर तुमच्या अपलोड केलेल्या स्रोतामध्ये सापडले नाही.**\n\n"
                "💡 **सल्ला:** कृपया संबंधित विषयाचे अधिकृत MPSC संदर्भ पुस्तक किंवा नोट्स '📚 Books' मेनूमध्ये अपलोड करा. "
                "पुस्तक अपलोड व इंडेक्स झाल्यानंतर मी त्यातील अचूक प्रकरण आणि पान क्रमांकासह उत्तर देईन."
            )

        top_citation = citations[0]
        context_clean = top_citation.text_snippet if hasattr(top_citation, 'text_snippet') else ""
        
        sentences = [s.strip() for s in re.split(r'[।\.\n]', context_str) if len(s.strip()) > 15]
        key_points = sentences[:5]
        
        points_text = "\n".join([f"• {p}." for p in key_points if not p.startswith("---") and not p.startswith("पुस्तक:")])

        response_lines = [
            "### १. थोडक्यात उत्तर",
            f"{sentences[0] if sentences else 'अभ्याससामग्रीतील संदर्भानुसार माहिती खालीलप्रमाणे आहे.'}।\n",
            "### २. सविस्तर स्पष्टीकरण व माहिती",
            f"{points_text}\n",
            "### ३. MPSC साठी महत्त्वाचे मुद्दे",
            f"• **संदर्भित पुस्तक:** {getattr(top_citation, 'book_name', 'MPSC Material')}",
            f"• **प्रकरण:** {getattr(top_citation, 'chapter', 'General')}",
            f"• **पान क्रमांक:** {getattr(top_citation, 'page_number', 1)}",
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
