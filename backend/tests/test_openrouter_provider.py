import asyncio
import pytest
from app.config import settings
from app.services.ai.providers import OpenRouterProvider, GeminiProvider, HeuristicLocalProvider
from app.services.ai.llm_provider import llm_provider
from app.services.tests.mcq_generator import mcq_generator
from app.services.mj_assistant_service import process_mj_conversation
from app.database import AsyncSessionLocal

def test_openrouter_model_safety_enforcement():
    """
    Verifies that OpenRouterProvider strictly enforces free models (openrouter/free or ending in :free)
    and overrides dangerous openrouter/auto configurations.
    """
    # Test 1: Default initialization
    p1 = OpenRouterProvider(model="openrouter/free")
    assert p1.model == "openrouter/free"
    assert "openrouter/free" in p1.provider_name

    # Test 2: Auto-override safety check
    p2 = OpenRouterProvider(model="openrouter/auto")
    assert p2.model == "openrouter/free", "openrouter/auto MUST be overridden to openrouter/free to prevent paid billing!"

    # Test 3: Specific free model suffix
    p3 = OpenRouterProvider(model="meta-llama/llama-3.3-70b-instruct:free")
    assert p3.model == "meta-llama/llama-3.3-70b-instruct:free"

    # Test 4: Model without :free suffix automatically appends :free
    p4 = OpenRouterProvider(model="deepseek/deepseek-r1")
    assert p4.model == "deepseek/deepseek-r1:free"

    print("[PASS] OpenRouter Free Model Safety Enforcement verified!")


@pytest.mark.asyncio
async def test_normal_ai_question():
    """
    Tests normal AI chat question response generation through LLMProvider abstraction.
    """
    response = await llm_provider.generate_chat_response(
        user_message="MPSC परीक्षेची तयारी कशी करावी?",
        context_str="",
        citations=[],
        mode="general_chat"
    )
    assert response is not None
    assert len(response) > 20
    print("[PASS] Normal AI Question verified!")


@pytest.mark.asyncio
async def test_rag_question():
    """
    Tests RAG context response generation through LLMProvider abstraction.
    """
    mock_context = "सत्यशोधक समाजाची स्थापना २४ सप्टेंबर १८७३ रोजी पुणे येथे महात्मा ज्योतिराव फुले यांनी केली."
    class MockCitation:
        book_name = "महाराष्ट्राचा इतिहास"
        chapter = "समाजसुधारक"
        page_number = 15
        text_snippet = mock_context

    response = await llm_provider.generate_chat_response(
        user_message="सत्यशोधक समाजाची स्थापना कोणी केली?",
        context_str=mock_context,
        citations=[MockCitation()],
        mode="teacher_mode"
    )
    assert response is not None
    assert "सत्यशोधक समाज" in response or "ज्योतिराव फुले" in response or "उत्तर" in response
    print("[PASS] RAG Question verified!")


@pytest.mark.asyncio
async def test_mcq_generation():
    """
    Tests MCQ Generation through provider abstraction.
    """
    mcqs = await mcq_generator.generate_mcqs(
        subject_name="इतिहास",
        topic_name="समाजसुधारक",
        count=2,
        difficulty="medium"
    )
    assert len(mcqs) == 2
    assert mcqs[0].question_text is not None
    assert mcqs[0].correct_option in ["A", "B", "C", "D"]
    print("[PASS] MCQ Generation verified!")


@pytest.mark.asyncio
async def test_mj_conversation():
    """
    Tests MJ Voice Assistant Conversation through provider abstraction.
    """
    async with AsyncSessionLocal() as db:
        res = await process_mj_conversation(
            user_query="Are MJ 1857 cha revolt samjhav",
            db=db
        )
        assert res is not None
        assert "reply_text" in res
        assert "speech_text" in res
        assert res["intent"] in ["activation", "mpsc_academic", "general_chat", "teacher_mode"]
        print("[PASS] MJ Voice Assistant Conversation verified!")

if __name__ == "__main__":
    test_openrouter_model_safety_enforcement()
    asyncio.run(test_normal_ai_question())
    asyncio.run(test_rag_question())
    asyncio.run(test_mcq_generation())
    asyncio.run(test_mj_conversation())
    print("\nALL OPENROUTER PROVIDER TESTS PASSED SUCCESSFULLY!")
