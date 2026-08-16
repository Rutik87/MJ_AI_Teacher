import pytest
from unittest.mock import patch, MagicMock
from app.services.ai.providers import OpenAIProvider
from app.services.ai.llm_provider import LLMProvider
from app.services.ai.prompts import MPSC_TEACHER_SYSTEM_PROMPT, CHATGPT_ANSWER_FORMATTER_INSTRUCTIONS

def test_chatgpt_answer_formatter_blocks():
    """Verifies that all required Marathi formatted blocks are present in prompt instructions."""
    required_blocks = [
        "📌 **उत्तर**",
        "🧠 **सोप्या भाषेत**",
        "📚 **सविस्तर स्पष्टीकरण**",
        "🎯 **MPSC साठी महत्त्वाचे**",
        "✅ **मुख्य मुद्दे**",
        "❓ **संभाव्य MCQ**",
        "⚠️ **गोंधळाचे मुद्दे**",
        "📝 **लक्षात ठेवण्याची ट्रिक**",
        "📖 **स्रोत / पुस्तक / अध्याय / पान**"
    ]
    for block in required_blocks:
        assert block in CHATGPT_ANSWER_FORMATTER_INSTRUCTIONS
        assert block in MPSC_TEACHER_SYSTEM_PROMPT

def test_openai_provider_initialization():
    prov = OpenAIProvider(api_key="sk-test-key-1234567890", model="gpt-4o-mini")
    assert prov.provider_name == "ChatGPT OpenAI (gpt-4o-mini)"
    assert prov._masked_key() == "sk-t***7890"

@pytest.mark.asyncio
async def test_openai_provider_mock_completion():
    prov = OpenAIProvider(api_key="sk-test-key-1234567890", model="gpt-4o-mini")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "📌 **उत्तर**\n१८५७ चा उठाव हा भारताचा पहिला स्वातंत्र्यलढा मानला जातो."
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await prov.generate_completion(prompt="1857 revolt samjhav")
        assert res is not None
        assert "📌 **उत्तर**" in res
        assert "१८५७ चा उठाव" in res

@pytest.mark.asyncio
async def test_llm_provider_prioritizes_openai():
    llm = LLMProvider()
    with patch.object(llm.openai_provider, "generate_completion", return_value="📌 **उत्तर**\nChatGPT Test"):
        with patch("app.config.settings.OPENAI_API_KEY", "sk-test"):
            res, prov = await llm._execute_with_provider("Test query", system_prompt="Test")
            assert "ChatGPT" in prov
            assert "📌 **उत्तर**" in res
