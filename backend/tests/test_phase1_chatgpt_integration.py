import pytest
from unittest.mock import patch, MagicMock
from app.services.ai.providers import OpenAIProvider
from app.services.ai.llm_provider import LLMProvider
from app.services.ai.agent import mpsc_agent
from app.services.ai.prompts import (
    MPSC_TEACHER_SYSTEM_PROMPT,
    CHATGPT_ANSWER_FORMATTER_INSTRUCTIONS,
    EXAM_MODE_SYSTEM_PROMPT,
    PYQ_ANALYSIS_PROMPT
)
from app.config import settings

# 1. Normal Marathi question
@pytest.mark.asyncio
async def test_normal_marathi_chat():
    llm = LLMProvider()
    llm.openai_provider.api_key = "sk-test-key-12345678"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "📌 **उत्तर**\nनमस्कार! मी MJ आहे. MPSC च्या अभ्यासात मी तुला मदत करेन."}}]
    }
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await llm.openai_provider.generate_completion(prompt="नमस्कार, तू कोण आहेस?")
        assert res is not None
        assert "📌 **उत्तर**" in res
        assert "नमस्कार" in res

# 2. Roman Marathi question
@pytest.mark.asyncio
async def test_roman_marathi_understanding():
    llm = LLMProvider()
    llm.openai_provider.api_key = "sk-test-key-12345678"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "📌 **उत्तर**\n१८५७ च्या उठावाची मुख्य कारणे राजकीय, सामाजिक, धार्मिक व लष्करी होती."}}]
    }
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await llm.openai_provider.generate_completion(prompt="1857 cha revolt mala samjhav")
        assert res is not None
        assert "१८५७ च्या उठावा" in res

# 3. MPSC question & formatting
@pytest.mark.asyncio
async def test_mpsc_structured_formatting():
    llm = LLMProvider()
    llm.openai_provider.api_key = "sk-test-key-12345678"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": (
                    "📌 **उत्तर**\nकलम ३२४ अन्वये निवडणूक आयोगाची तरतूद आहे.\n\n"
                    "🎯 **MPSC साठी महत्त्वाचे**\n- कलम ३२४: रचना व अधिकार\n\n"
                    "❓ **संभाव्य MCQ**\nभारतीय निवडणूक आयोगाची तरतूद कोणत्या कलमात आहे?\n(A) कलम ३२४ (B) कलम २८०"
                )
            }
        }]
    }
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await llm.openai_provider.generate_completion(prompt="निवडणूक आयोग कलम कोणते आहे?")
        assert res is not None
        assert "📌 **उत्तर**" in res
        assert "🎯 **MPSC साठी महत्त्वाचे**" in res
        assert "❓ **संभाव्य MCQ**" in res

# 4. PDF/RAG Grounded Question
@pytest.mark.asyncio
async def test_rag_grounded_answer():
    with patch("app.services.rag.retriever.rag_retriever.retrieve") as mock_retrieve:
        mock_citation = MagicMock()
        mock_citation.book_name = "आधुनिक भारताचा इतिहास"
        mock_citation.chapter = "अध्याय १"
        mock_citation.page_number = 15
        mock_citation.text_snippet = "लॉर्ड डलहौसीने दत्तक वारसा नामंजूर धोरण लागू केले."
        mock_retrieve.return_value = ([mock_citation], "लॉर्ड डलहौसीने दत्तक वारसा नामंजूर धोरण लागू केले.", True)

        with patch("app.services.ai.llm_provider.LLMProvider.generate_chat_response", return_value="📌 **उत्तर**\nलॉर्ड डलहौसीने दत्तक विधान नामंजूर केले.\n📖 **स्रोत**: आधुनिक भारताचा इतिहास, पान १५"):
            result = await mpsc_agent.execute(
                user_message="माझ्या पुस्तकात डलहौसीबद्दल काय दिले आहे?",
                book_id=1
            )
            assert result["has_context"] is True
            assert len(result["citations"]) == 1
            assert "📖 **स्रोत**" in result["answer"]

# 5. PYQ Question
@pytest.mark.asyncio
async def test_pyq_question_analysis():
    assert "PYQ" in PYQ_ANALYSIS_PROMPT
    assert "आयोगाचे आवडते पॅटर्न" in PYQ_ANALYSIS_PROMPT

# 6. Citation Verification
def test_citation_structure():
    assert "📖 **स्रोत / पुस्तक / अध्याय / पान**" in CHATGPT_ANSWER_FORMATTER_INSTRUCTIONS

# 7. No-Source Question
@pytest.mark.asyncio
async def test_no_source_guardrail():
    assert "तुमच्या अपलोड केलेल्या स्रोतामध्ये या प्रश्नाचे पुरेसे उत्तर सापडले नाही." in MPSC_TEACHER_SYSTEM_PROMPT

# 8. OpenAI API Failure and Fallback
@pytest.mark.asyncio
async def test_openai_failure_fallback():
    llm = LLMProvider()
    with patch.object(llm.openai_provider, "generate_completion", return_value=None):
        with patch.object(llm.openrouter_provider, "generate_completion", return_value="Fallback Response"):
            res, prov = await llm._execute_with_provider(prompt="Test prompt", system_prompt="")
            assert res == "Fallback Response"

# 9. Rate-Limit Handling (429)
@pytest.mark.asyncio
async def test_openai_rate_limit_handling():
    prov = OpenAIProvider(api_key="sk-test-12345678", model="gpt-4o-mini")
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit reached"
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await prov.generate_completion(prompt="Test")
        assert res is None

# 10. Secret-Leak Check
def test_secret_leak_protection():
    prov = OpenAIProvider(api_key="sk-proj-super-secret-api-key-12345678", model="gpt-4o-mini")
    masked = prov._masked_key()
    assert "super-secret" not in masked
    assert masked.startswith("sk-p")
    assert masked.endswith("5678")
