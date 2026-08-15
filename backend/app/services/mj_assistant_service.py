import re
import random
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import current_affairs_service
from app.services.rag.retriever import rag_retriever
from app.services.ai.llm_provider import llm_provider
from app.services.voice_service import voice_service
from app.services.speech.marathi_normalizer import MarathiPronunciationNormalizer
from app.utils.logger import logger

# Contextual activation greetings
ACTIVATION_GREETINGS = [
    "हं बोल ना 😄",
    "अरे हाँ, MJ इथेच आहे 😄 काय झालं?",
    "हो सांग, काय चाललंय?",
    "हं, ऐकतेय 😊 बोल!",
    "अरे बोल ना, काय विचारतोयस?"
]

# Friendly supportive responses for casual and mood inquiries
CASUAL_RESPONSES = {
    "mood_off": [
        "अरे मग 10-15 मिनिटांपासून सुरू करूया ना 😄 पूर्ण दिवसाचा विचार करून tension घेऊ नकोस. आधी कोणता सोपा विषय घ्यायचा?",
        "होतं असं कधी कधी! चल एक काम कर, एक ग्लास पाणी पी आणि आपण फक्त 10 मिनिटे हलकासा topic बघू."
    ],
    "general_chat": [
        "मी मस्त आहे! तू सांग, आजचा अभ्यास कसा चाललाय?",
        "हो, बोल ना! मी इथेच आहे तुझ्यासोबत अभ्यास करायला आणि गप्पा मारायला 😄",
        "अरे मी एक नंबर! आज आपण कोणता टॉपिक फोडायचा?"
    ],
    "bored": [
        "अरे कंटाळा आलाय का? मग थोडा वेळ चालू घडामोडींचे रंजक प्रश्न बघूया किंवा 5 मिनिटांचा ब्रेक घेऊया?"
    ],
    "encouragement": [
        "अरे टेन्शन नको घेऊ, तू छान अभ्यास करतोयस! एक-एक पॉईंट शांतपणे बघूया 😄",
        "काही हरकत नाही, सुरुवात थोडी कठीण वाटते पण आपण एकत्र सोपं करूया!"
    ]
}


def clean_text_for_speech(text: str) -> str:
    """Cleans markdown, asterisks, brackets, and bullet symbols for natural voice synthesis."""
    t = re.sub(r'#{1,6}\s*', '', text)
    t = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', t)
    t = re.sub(r'•\s*', '', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'`[^`]*`', '', t)
    t = re.sub(r'http\S+', '', t)
    t = re.sub(r'\n+', ' ', t).strip()
    return MarathiPronunciationNormalizer.normalize_text(t)


def resolve_context_topic(
    current_query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, Optional[str]]:
    """
    Detects pronouns (त्याची, तो, हा, या, revolt, it, this) and resolves them
    using recent conversation history.
    """
    if not conversation_history:
        return current_query, None

    pronoun_triggers = ["त्याची", "त्याचे", "त्याचा", "त्यात", "तो", "ती", "ते", "हा", "ही", "हे", "त्याबद्दल", "याची", "याचे", "याचा"]
    query_lower = current_query.lower()

    needs_resolution = any(p in current_query.split() or p in query_lower for p in pronoun_triggers)

    recent_topic = None
    for msg in reversed(conversation_history[-4:]):
        text = msg.get("text", "")
        # Extract potential topic words
        words = [w for w in text.split() if len(w) > 3 and not any(p in w for p in ["आहे", "नाही", "काय", "कसे", "सांग"])]
        if words:
            recent_topic = " ".join(words[:4])
            break

    if needs_resolution and recent_topic:
        resolved_query = f"{current_query} (संदर्भ: {recent_topic})"
        return resolved_query, recent_topic

    return current_query, recent_topic


async def process_mj_conversation(
    user_query: str,
    db: AsyncSession,
    book_id: Optional[int] = None,
    current_page: Optional[int] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    preferred_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified Conversational Brain for the Single MJ Persona across all screens.
    Handles wake word, emotion classification, mode routing, RAG grounding, and single-voice TTS.
    """
    raw_query = user_query.strip()
    query_lower = raw_query.lower()

    # 1. Wake word detection & standalone activations
    wake_patterns = ["are mj", "arre mj", "hey mj", "ऐक mj", "mj", "अरे mj", "हे mj"]
    is_wake_word_only = False
    
    for pat in wake_patterns:
        if query_lower == pat or query_lower == f"{pat}!" or query_lower == f"{pat}?":
            is_wake_word_only = True
            break
        elif query_lower.startswith(pat):
            raw_query = raw_query[len(pat):].strip(",!?. ")
            query_lower = raw_query.lower()
            break

    if is_wake_word_only or not raw_query:
        greeting = random.choice(ACTIVATION_GREETINGS)
        speech_text = clean_text_for_speech(greeting)
        voice_res = await voice_service.generate_voice(speech_text, emotion="friendly")
        return {
            "reply_text": greeting,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "activation",
            "mode": "FRIEND",
            "emotion": "friendly",
            "action": "keep_listening",
            "sources": []
        }

    # 2. Interruption Handling
    if any(w in query_lower for w in ["थांब", "stop", "शांत", "बस", "चूप"]):
        reply = "हो थांबले 😊 सांग पुढं काय करायचं?"
        speech_text = clean_text_for_speech(reply)
        voice_res = await voice_service.generate_voice(speech_text, emotion="calm")
        return {
            "reply_text": reply,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "interruption",
            "mode": "CASUAL",
            "emotion": "calm",
            "action": "stop",
            "sources": []
        }

    # 3. Resolve context and pronouns from conversation history
    resolved_query, last_topic = resolve_context_topic(raw_query, conversation_history)

    # 4. Casual Chat & Empathy Intent (FRIEND Mode)
    if any(w in query_lower for w in ["mood नाही", "मूड नाही", "इच्छा नाही", "कंटाळा", "समजत नाही", "काही समजत नाही", "mood off", "samjat nahi", "kahi samjat nahi", "kantala", "bored"]):
        reply = random.choice(CASUAL_RESPONSES["mood_off"])
        speech_text = clean_text_for_speech(reply)
        voice_res = await voice_service.generate_voice(speech_text, emotion="empathetic", speed=0.92)
        return {
            "reply_text": reply,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "casual_empathy",
            "mode": "FRIEND",
            "emotion": "empathetic",
            "action": "continue_chat",
            "sources": []
        }

    if any(w in query_lower for w in ["काय चाललंय", "कशी आहेस", "काय करतेस", "बोल ना", "जेवलीस का", "kasa ahes", "kashi ahes", "kay chalalay", "kasa chalay", "bol na", "how are you"]):
        reply = random.choice(CASUAL_RESPONSES["general_chat"])
        speech_text = clean_text_for_speech(reply)
        voice_res = await voice_service.generate_voice(speech_text, emotion="friendly", speed=1.0)
        return {
            "reply_text": reply,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "casual_chat",
            "mode": "CASUAL",
            "emotion": "friendly",
            "action": "continue_chat",
            "sources": []
        }

    # 5. Study Planner Intent (STUDY Mode)
    if any(w in query_lower for w in ["काय अभ्यास करू", "अभ्यास काय करू", "study plan", "नियोजन", "वेळापत्रक", "अभ्यास करूया", "abhyas karuya", "abhyas karu", "study karuya", "study"]):
        reply = (
            "चल, आजचा प्लॅन बघूया! आज तुझ्या वेळापत्रकानुसार राज्यघटनेची (Polity) उजळणी बाकी आहे "
            "आणि इतिहासाचे 20 MCQs सोडवायचे आहेत. आधी 20 मिनिटे राज्यघटना करूया का? 😄"
        )
        speech_text = clean_text_for_speech(reply)
        voice_res = await voice_service.generate_voice(speech_text, emotion="encouraging", speed=0.96)
        return {
            "reply_text": reply,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "study_planner",
            "mode": "STUDY",
            "emotion": "encouraging",
            "action": "navigate_plan",
            "sources": []
        }

    # 6. Current Affairs Intent (CURRENT_AFFAIRS Mode)
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
            speech_text = clean_text_for_speech(speech)
            voice_res = await voice_service.generate_voice(speech_text, emotion="explaining", speed=0.95)
            return {
                "reply_text": reply,
                "speech_text": speech_text,
                "audio_url": voice_res.get("audio_url"),
                "intent": "current_affairs",
                "mode": "CURRENT_AFFAIRS",
                "emotion": "explaining",
                "action": "continue_chat",
                "sources": [{"book_name": top.source_name, "page_number": 1, "chapter": top.topic}]
            }

    # 7. Test / Quiz Request Intent (TEST Mode)
    if any(w in query_lower for w in ["test घे", "चाचणी घे", "mcq विचार", "प्रश्न विचार", "क्विझ"]):
        reply = "नक्कीच! आपण सराव चाचणी सुरू करूया. विषय कोणता निवडायचा — इतिहास की राज्यघटना? 📝"
        speech_text = clean_text_for_speech(reply)
        voice_res = await voice_service.generate_voice(speech_text, emotion="happy", speed=1.0)
        return {
            "reply_text": reply,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "test_request",
            "mode": "TEST",
            "emotion": "happy",
            "action": "open_test",
            "sources": []
        }

    # 8. Revision Intent (REVISION Mode)
    if any(w in query_lower for w in ["revision", "उजळणी", "रिव्हिजन", "रिवाईज"]):
        reply = "चला, आपण 3 महत्त्वाच्या मुद्द्यांमध्ये झटपट उजळणी करूया! तू कुठल्या घटकाची उजळणी करायची ते सांग."
        speech_text = clean_text_for_speech(reply)
        voice_res = await voice_service.generate_voice(speech_text, emotion="encouraging", speed=0.95)
        return {
            "reply_text": reply,
            "speech_text": speech_text,
            "audio_url": voice_res.get("audio_url"),
            "intent": "revision",
            "mode": "REVISION",
            "emotion": "encouraging",
            "action": "continue_chat",
            "sources": []
        }

    # 9. MPSC Academic Question (RAG Retrieval + Grounded Teacher Generation)
    citations, context_str, has_context = rag_retriever.retrieve(
        query=resolved_query,
        top_k=3,
        book_id=book_id
    )

    if has_context and citations:
        answer = await llm_provider.generate_chat_response(
            user_message=f"मित्रासारख्या सोप्या मराठीत समजावून सांग: {resolved_query}",
            context_str=context_str,
            citations=citations,
            mode="teacher_mode",
            history=conversation_history
        )
        friendly_prefix = "चल, हा भाग सोप्या भाषेत समजून घेऊया! 😄\n\n"
        final_reply = friendly_prefix + answer
        emotion = "explaining"
    else:
        # If user explicitly asked about their book/file and no context was retrieved
        if book_id is not None or any(w in query_lower for w in ["माझ्या पुस्तकात", "माझ्या नोट्स", "पुस्तकानुसार", "फाईलमध्ये", "notes", "book"]):
            final_reply = "या प्रश्नाचे पुरेसे उत्तर तुमच्या अपलोड केलेल्या स्रोतामध्ये सापडले नाही."
            emotion = "neutral"
        else:
            answer = await llm_provider.generate_chat_response(
                user_message=resolved_query,
                context_str="",
                citations=[],
                mode="teacher_mode",
                history=conversation_history
            )
            final_reply = "अरे काही टेन्शन नाही! चल, हा टॉपिक बघूया:\n\n" + answer
            emotion = "encouraging"

    speech_text = clean_text_for_speech(final_reply)
    voice_res = await voice_service.generate_voice(speech_text, emotion=emotion, speed=0.95)
    audio_url = voice_res.get("audio_url")

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
        "audio_url": audio_url,
        "intent": "mpsc_academic",
        "mode": "STUDY",
        "emotion": emotion,
        "action": "continue_chat",
        "sources": sources_list
    }
