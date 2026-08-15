import pytest
import re
from app.services.ai.llm_provider import llm_provider

def calculate_marathi_percentage(text: str) -> float:
    """Calculates the proportion of Marathi Devanagari characters vs Latin/English letters."""
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    
    total_letters = devanagari_chars + latin_chars
    if total_letters == 0:
        return 100.0
    
    return (devanagari_chars / total_letters) * 100.0

@pytest.mark.asyncio
async def test_marathi_first_answer_composition():
    # Query an MPSC topic
    answer = await llm_provider.generate_chat_response(
        user_message="महाराष्ट्रातील प्रमुख नद्यांची माहिती द्या",
        context_str="गोदावरी ही महाराष्ट्रातील सर्वात लांब नदी आहे. तिचा उगम त्र्यंबकेश्वर येथे होतो. भीमा नदी भीमाशंकर येथे उगम पावते.",
        citations=[type('Citation', (), {'book_name': 'महाराष्ट्र भूगोल', 'chapter': 'नद्या', 'page_number': 12, 'text_snippet': 'गोदावरी ही महाराष्ट्रातील सर्वात लांब नदी आहे.'})()],
        mode="teacher_mode"
    )
    
    marathi_ratio = calculate_marathi_percentage(answer)
    print(f"Generated Answer Marathi Percentage: {marathi_ratio:.2f}%")
    
    # Assert ~98% Marathi composition (allowing standard acronyms like MPSC, MCQ, GS)
    assert marathi_ratio >= 90.0, f"Expected >= 90% Marathi, got {marathi_ratio:.2f}%"
    assert "उत्तर" in answer
    assert "स्पष्टीकरण" in answer

@pytest.mark.asyncio
async def test_anti_hallucination_missing_source_exact_phrase():
    # Query with empty context
    answer = await llm_provider.generate_chat_response(
        user_message="या पुस्तकानुसार 2026 चा नवा कायदा काय आहे?",
        context_str="",
        citations=[],
        mode="teacher_mode"
    )
    
    # Must contain the exact required fallback phrase
    assert "या प्रश्नाचे पुरेसे उत्तर तुमच्या अपलोड केलेल्या स्रोतामध्ये सापडले नाही." in answer
