import re
import random
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import current_affairs_service
from app.services.rag.retriever import rag_retriever
from app.services.ai.llm_provider import llm_provider

ACTIVATION_GREETINGS = [
    "हं बोल ना 😄",
    "अरे हाँ, MJ इथेच आहे 😄 काय झालं?",
    "हो सांग, काय चाललंय?",
    "हं, ऐकतेय 😊 बोल!",
    "अरे बोल ना, काय विचारतोयस?"
]

CASUAL_RESPONSES = {
    "mood_off": [
        "अरे मग 10-15 मिनिटांपासून सुरू करूया ना 😄 पूर्ण दिवसाचा विचार करून tension घेऊ नकोस. आधी कोणता सोपा विषय घ्यायचा?",
        "होतं असं कधी कधी! चल एक काम कर, एक ग्लास पाणी पी आणि आपण फक्त 10 मिनिटे हलकासा topic बघू."
    ],
    "general_chat": [
        "मी मस्त आहे! तू सांग, आजचा अभ्यास कसा चाललाय?",
        "हो, बोल ना! मी इथेच आहे तुझ्यासोबत अभ्यास करायला आणि गप्पा मारायला 😄"
    ],
    "bored": [
        "अरे कंटाळा आलाय का? मग थोडा वेळ चालू घडामोडींचे रंजक प्रश्न बघूया किंवा 5 मिनिटांचा ब्रेक घेऊया?"
    ]
}

def clean_text_for_tts(text: str) -> str:
    """Removes markdown symbols, hashtags, asterisks, and bullets for natural Marathi speech."""
    t = re.sub(r'#{1,6}\s*', '', text)  # remove headings
    t = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', t)  # remove bold/italic
    t = re.sub(r'•\s*', '', t)  # remove bullets
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)  # remove links
    t = re.sub(r'`[^`]*`', '', t)  # remove inline code
    t = re.sub(r'\n+', ' ', t).strip()
    return t

async def process_mj_conversation(
    user_query: str,
    db: AsyncSession,
    book_id: Optional[int] = None,
    current_page: Optional[int] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    query_lower = user_query.strip().lower()

    # 1. Wake word detection & standalone activations
    wake_patterns = ["are mj", "hey mj", "ऐक mj", "mj", "अरे mj", "हे mj"]
    is_wake_word_only = False
    for pat in wake_patterns:
        if query_lower == pat or query_lower == f"{pat}!" or query_lower == f"{pat}?":
            is_wake_word_only = True
            break
        elif query_lower.startswith(pat):
            user_query = user_query[len(pat):].strip(",!?. ")
            query_lower = user_query.lower()
            break

    if is_wake_word_only or not user_query.strip():
        greeting = random.choice(ACTIVATION_GREETINGS)
        return {
            "reply_text": greeting,
            "speech_text": greeting,
            "intent": "activation",
            "action": "keep_listening",
            "sources": []
        }

    # 2. Interruption handling
    if "थांब" in query_lower or "stop" in query_lower or "शांत" in query_lower:
        return {
            "reply_text": "हो थांबले 😊 सांग पुढं काय करायचं?",
            "speech_text": "हो थांबले सांग पुढं काय करायचं?",
            "intent": "interruption",
            "action": "stop",
            "sources": []
        }

    # 3. Casual Mood / Best Friend Empathy
    if any(w in query_lower for w in ["mood नाही", "मूड नाही", "इच्छा नाही", "कंटाळा"]):
        reply = random.choice(CASUAL_RESPONSES["mood_off"])
        return {
            "reply_text": reply,
            "speech_text": clean_text_for_tts(reply),
            "intent": "casual_empathy",
            "action": "continue_chat",
            "sources": []
        }

    if any(w in query_lower for w in ["काय चाललंय", "कशी आहेस", "काय करतेस", "बोल ना"]):
        reply = random.choice(CASUAL_RESPONSES["general_chat"])
        return {
            "reply_text": reply,
            "speech_text": clean_text_for_tts(reply),
            "intent": "casual_chat",
            "action": "continue_chat",
            "sources": []
        }

    # 4. Study Planner Intent
    if any(w in query_lower for w in ["काय अभ्यास करू", "अभ्यास काय करू", "study plan", "नियोजन"]):
        reply = (
            "चल, आजचा प्लॅन बघूया! आज तुझ्या वेळापत्रकानुसार राज्यघटनेची (Polity) उजळणी बाकी आहे "
            "आणि इतिहासाचे 20 MCQs सोडवायचे आहेत. आधी 20 मिनिटे राज्यघटना करूया का? 😄"
        )
        return {
            "reply_text": reply,
            "speech_text": clean_text_for_tts(reply),
            "intent": "study_planner",
            "action": "navigate_plan",
            "sources": []
        }

    # 5. Current Affairs Intent
    if any(w in query_lower for w in ["current affairs", "चालू घडामोडी", "आजच्या बातम्या", "ताज्या बातम्या"]):
        articles = await current_affairs_service.get_current_affairs(db, topic="सर्व")
        if articles:
            top = articles[0]
            reply = (
                f"आजची सर्वात महत्त्वाची घडामोड आहे: '{top.title_mr}'.\n\n"
                f"थोडक्यात माहिती: {top.summary_mr}\n\n"
                f"MPSC दृष्टीने: {top.mpsc_relevance_mr}"
            )
            speech = f"आजची महत्त्वाची घडामोड आहे {top.title_mr}. {top.summary_mr} यावर आणखी प्रश्न सोडवायचा का?"
            return {
                "reply_text": reply,
                "speech_text": clean_text_for_tts(speech),
                "intent": "current_affairs",
                "action": "continue_chat",
                "sources": [{"book_name": top.source_name, "page_number": 1, "chapter": top.topic}]
            }

    # 6. Test / Quiz Intent
    if any(w in query_lower for w in ["test घे", "चाचणी घे", "mcq विचार", "प्रश्न विचार"]):
        reply = "नक्कीच! आपण 10 प्रश्नांची सराव चाचणी सुरू करूया. विषय कोणता निवडायचा — इतिहास की राज्यघटना? 📝"
        return {
            "reply_text": reply,
            "speech_text": clean_text_for_tts(reply),
            "intent": "test_request",
            "action": "open_test",
            "sources": []
        }

    # 7. MPSC Academic Question (RAG with Friendly Best Friend Tone)
    citations, context_str, has_context = rag_retriever.retrieve(
        query=user_query,
        top_k=3,
        book_id=book_id
    )

    if has_context and citations:
        answer = llm_provider.generate_answer(
            prompt=f"मित्रासारख्या सोप्या मराठीत समजावून सांग: {user_query}",
            context=context_str,
            mode="teacher_mode"
        )
    else:
        answer = llm_provider.generate_answer(
            prompt=f"सोप्या भाषेत समजावून सांग: {user_query}",
            context="",
            mode="general_chat"
        )

    friendly_prefix = "चल, हा भाग सोप्या भाषेत समजून घेऊया! 😄\n\n"
    final_reply = friendly_prefix + answer

    speech_text = clean_text_for_tts(final_reply)

    sources_list = [
        {
            "book_name": c.book_name,
            "page_number": c.page_number,
            "chapter": c.chapter,
            "text_snippet": c.text_snippet
        }
        for c in citations
    ]

    return {
        "reply_text": final_reply,
        "speech_text": speech_text,
        "intent": "mpsc_academic",
        "action": "continue_chat",
        "sources": sources_list
    }
