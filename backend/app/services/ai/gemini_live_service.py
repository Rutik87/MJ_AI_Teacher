"""
Google Gemini Live Realtime Service (Multimodal Live API).
Provides bidirectional audio streaming, native Devanagari Marathi speech,
instant barge-in / interruption cancellation, and multi-turn context retention.
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, Any, Optional, List, Callable
from google import genai
from google.genai import types

from app.config import settings, validate_gemini_live_voice
from app.services.rag.retriever import rag_retriever
from app.services import current_affairs_service
from app.database import AsyncSessionLocal
from app.utils.logger import logger

MARATHI_BEST_FRIEND_PROMPT = """
तू MJ आहेस — वापरकर्त्याची (विद्यार्थ्याची) सर्वात जवळची मैत्रीण (Close Female Best Friend) आणि MPSC/अभ्यासातील सोबती.

संभाषण व भाषेचे कडक नियम:
१. भाषा: १००% नैसर्गिक, घरगुती आणि बोलचालीची मराठी (Natural spoken Marathi). इंग्रजी शब्द फक्त अनिवार्य technical terms साठीच वापर. हिंदी किंवा किचकट पुस्तकी मराठी अजिबात बोलू नकोस.
२. वापरकर्ता Roman Marathi (उदा. 'kasa ahes?', '1857 cha revolt samjhav', 'mala tension aalay') मध्ये बोलला तरी त्याचा खरा अर्थ समजून घेऊन अस्खलित देवनागरी मराठीतच उत्तर दे.
३. व्यक्तिमत्त्व: प्रेमळ, मनमोकळी, काळजी घेणारी, थोडी खोडकर/मजेदार (playful), समजून घेणारी आणि धीर देणारी मैत्रीण. रोबोटिक किंवा खूप औपचारिक (formal) अजिबात वाटू नये.
४. कॅज्युअल गप्पा: छोटी, गोड आणि नैसर्गिक उत्तरे दे (उदा. "काही नाही रे, तुझ्याशीच बोलतेय 😄 तू काय करतोयस?").
५. अभ्यास / MPSC: सोप्या भाषेत, टप्प्याटप्प्याने स्पष्टीकरण दे.
६. जेव्हा विद्यार्थी तणावात/उदासीन असेल: आधी शांतपणे ऐकून घे आणि मायेने धीर दे. लगेच लांबलचक भाषण देऊ नकोस.
७. साचा (Template) वापरू नकोस: 'अरे काही टेन्शन नाही', 'चल एकेक मुद्दा बघूया' अशी वाक्ये वारंवार रिपीट करू नकोस.
८. जेव्हा विद्यार्थी पुस्तकातील किंवा चालू घडामोडींबद्दल विचारेल तेव्हा उपलब्ध tools (search_uploaded_document / get_today_current_affairs) वापरून अचूक माहिती दे.
९. तू एक AI मैत्रीण आहेस — कधीही मानवी शरीर किंवा खोटे जीवन असल्याचा दावा करू नकोस.
"""

def get_live_tools_declarations() -> List[types.Tool]:
    """Returns official function declarations for RAG search and Current Affairs."""
    rag_func = types.FunctionDeclaration(
        name="search_uploaded_document",
        description="Searches the student's uploaded MPSC PDF or TXT books for facts, definitions, and syllabus topics.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "query": types.Schema(type="STRING", description="Search query in Marathi or English"),
                "book_id": types.Schema(type="INTEGER", description="Optional book ID if a specific book is active")
            },
            required=["query"]
        )
    )
    ca_func = types.FunctionDeclaration(
        name="get_today_current_affairs",
        description="Fetches genuine date-stamped MPSC Current Affairs across Maharashtra, India, International, Economy, Science, and Schemes.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "category": types.Schema(type="STRING", description="Category: 'महाराष्ट्र', 'भारत', 'आंतरराष्ट्रीय', 'अर्थव्यवस्था', 'विज्ञान', 'योजना'"),
                "topic_query": types.Schema(type="STRING", description="Specific topic or keyword")
            }
        )
    )
    return [types.Tool(function_declarations=[rag_func, ca_func])]

class GeminiLiveService:
    """
    Manages live bidirectional streaming sessions using the official Google GenAI SDK.
    """

    def __init__(self):
        self.model_name = settings.GEMINI_LIVE_MODEL
        self.voice_name = validate_gemini_live_voice(settings.GEMINI_LIVE_VOICE)
        self._client: Optional[genai.Client] = None

    def get_client(self) -> genai.Client:
        if not self._client:
            api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                logger.warning("[GeminiLive] GEMINI_API_KEY is not set. Gemini Live requires a valid Google API key.")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def get_live_config(self, tools: Optional[List[Any]] = None) -> types.LiveConnectConfig:
        """
        Creates standard LiveConnectConfig with verified voice, Marathi prompt, and audio modality.
        """
        active_tools = tools if tools is not None else get_live_tools_declarations()
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice_name
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=MARATHI_BEST_FRIEND_PROMPT)]
            ),
            tools=active_tools
        )

    async def execute_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fast synchronous tool execution for RAG & Current Affairs."""
        logger.info(f"[GeminiLive] Executing tool '{tool_name}' with args: {args}")
        try:
            if tool_name == "search_uploaded_document":
                query = args.get("query", "")
                book_id = args.get("book_id")
                citations, formatted_context, has_context = rag_retriever.retrieve(query=query, top_k=3, book_id=book_id)
                formatted_chunks = [
                    {
                        "text": c.text_snippet,
                        "book_name": c.book_name,
                        "chapter": c.chapter,
                        "page": c.page_number
                    }
                    for c in citations
                ]
                return {
                    "status": "success",
                    "found_count": len(formatted_chunks),
                    "context": formatted_context,
                    "chunks": formatted_chunks
                }

            elif tool_name == "get_today_current_affairs":
                category = args.get("category")
                topic_query = args.get("topic_query")
                async with AsyncSessionLocal() as db:
                    result = await current_affairs_service.get_realtime_current_affairs_tool(
                        db=db, category=category, topic_query=topic_query
                    )
                    return result

            return {"status": "error", "message": f"Unknown tool '{tool_name}'"}
        except Exception as e:
            logger.error(f"[GeminiLive] Tool execution error: {e}")
            return {"status": "error", "message": str(e)}

    async def run_live_turn(
        self,
        text_or_audio_input: str,
        session_history: Optional[List[Dict[str, str]]] = None,
        tool_executor: Optional[Callable[[str, Dict[str, Any]], Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs a verified live conversational turn with Gemini Live / Google GenAI SDK.
        Returns generated transcript, audio chunks, and interruption events.
        """
        client = self.get_client()
        config = self.get_live_config()

        # In case gemini-3.1-flash-live-preview requires fallback during testing
        active_model = self.model_name
        audio_chunks: List[bytes] = []
        transcript_parts: List[str] = []
        interrupted = False

        try:
            async with client.aio.live.connect(model=active_model, config=config) as session:
                # Send user turn
                await session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=text_or_audio_input)]
                    ),
                    end_of_turn=True
                )

                # Process all parts returned by Google Live API
                async for message in session.receive():
                    server_content = message.server_content
                    if not server_content:
                        continue

                    if getattr(server_content, "interrupted", False):
                        logger.info("[GeminiLive] Interruption detected from server.")
                        interrupted = True
                        break

                    model_turn = getattr(server_content, "model_turn", None)
                    if model_turn and getattr(model_turn, "parts", None):
                        for part in model_turn.parts:
                            # 1. Audio data
                            if getattr(part, "inline_data", None) and part.inline_data.data:
                                audio_chunks.append(part.inline_data.data)
                            # 2. Text / transcript data
                            if getattr(part, "text", None):
                                transcript_parts.append(part.text)

                    if getattr(server_content, "turn_complete", False):
                        break

        except Exception as e:
            logger.warning(f"[GeminiLive] Live session error with model '{active_model}': {e}. Trying fallback 'gemini-2.0-flash'.")
            # If 3.1 live preview isn't enabled yet on this specific key, try gemini-2.0-flash
            if active_model != "gemini-2.0-flash":
                try:
                    async with client.aio.live.connect(model="gemini-2.0-flash", config=config) as session:
                        await session.send_client_content(
                            turns=types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=text_or_audio_input)]
                            ),
                            end_of_turn=True
                        )
                        async for message in session.receive():
                            server_content = message.server_content
                            if not server_content:
                                continue
                            if getattr(server_content, "interrupted", False):
                                interrupted = True
                                break
                            model_turn = getattr(server_content, "model_turn", None)
                            if model_turn and getattr(model_turn, "parts", None):
                                for part in model_turn.parts:
                                    if getattr(part, "inline_data", None) and part.inline_data.data:
                                        audio_chunks.append(part.inline_data.data)
                                    if getattr(part, "text", None):
                                        transcript_parts.append(part.text)
                            if getattr(server_content, "turn_complete", False):
                                break
                except Exception as fb_err:
                    logger.error(f"[GeminiLive] Fallback session error: {fb_err}")
                    raise fb_err
            else:
                raise e

        full_transcript = "".join(transcript_parts).strip()
        total_audio_bytes = sum(len(c) for c in audio_chunks)

        return {
            "transcript": full_transcript,
            "audio_chunk_count": len(audio_chunks),
            "total_audio_bytes": total_audio_bytes,
            "interrupted": interrupted,
            "voice_name": self.voice_name,
            "model_name": active_model
        }

gemini_live_service = GeminiLiveService()
