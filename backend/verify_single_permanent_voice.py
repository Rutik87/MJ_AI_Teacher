import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import settings
from app.services.voice_service import voice_service

TEST_SENTENCES = [
    {
        "id": 1,
        "category": "Warm / Conversational",
        "text": "अरे, काळजी करू नकोस. चला एकेक मुद्दा समजून घेऊया.",
        "emotion": "friendly",
        "speed": 1.0,
        "intensity": 0.6
    },
    {
        "id": 2,
        "category": "Historical / Academic",
        "text": "1857 च्या उठावाची मुख्य कारणे आपण सोप्या पद्धतीने पाहूया.",
        "emotion": "explaining",
        "speed": 0.95,
        "intensity": 0.5
    },
    {
        "id": 3,
        "category": "Exam High-Yield Focus",
        "text": "हा मुद्दा MPSC परीक्षेसाठी खूप महत्त्वाचा आहे.",
        "emotion": "encouraging",
        "speed": 1.0,
        "intensity": 0.7
    },
    {
        "id": 4,
        "category": "Empathetic Dialogue",
        "text": "मला समजत नाही. काही हरकत नाही, आपण पुन्हा सोप्या पद्धतीने पाहूया.",
        "emotion": "empathetic",
        "speed": 0.92,
        "intensity": 0.8
    },
    {
        "id": 5,
        "category": "Celebration / Motivation",
        "text": "खूप छान! तुझं हे उत्तर अगदी बरोबर आहे.",
        "emotion": "happy",
        "speed": 1.05,
        "intensity": 0.85
    }
]

async def verify_single_voice():
    print("=" * 80)
    print("       MPSC AI: SINGLE AUTHORIZED PERMANENT MJ VOICE VERIFICATION")
    print("          'हा माझ्या AI चा एकच कायमचा आवाज आहे.'")
    print("=" * 80 + "\n")

    profile = voice_service.get_voice_profile()
    print(f"Voice Profile Info:")
    print(f"   • Profile ID     : {profile['voice_profile_id']}")
    print(f"   • Display Name   : {profile['name']}")
    print(f"   • Language       : {profile['language']}")
    print(f"   • Authorized Flag: {profile['is_authorized']}")
    print(f"   • Voice Identity : {profile['identity_statement']}")
    print(f"   • Emotions Count : {len(profile['emotions_supported'])} supported\n")

    all_passed = True
    cache_dir = Path(settings.AUDIO_CACHE_PATH)

    for sent in TEST_SENTENCES:
        print(f"--------------------------------------------------------------------------------")
        print(f"Test Sentence #{sent['id']} [{sent['category']}]:")
        print(f"   Original Text   : \"{sent['text']}\"")
        print(f"   Emotion / Speed : {sent['emotion']} (speed={sent['speed']}x, intensity={sent['intensity']})")

        res = await voice_service.generate_voice(
            text=sent["text"],
            emotion=sent["emotion"],
            speed=sent["speed"],
            intensity=sent["intensity"]
        )

        audio_file = cache_dir / os.path.basename(res["audio_url"]) if res.get("audio_url") else None
        file_size = audio_file.stat().st_size if audio_file and audio_file.exists() else 0
        is_success = res["success"] and file_size > 1000 and res["voice_profile_id"] == "mj_primary"

        if not is_success:
            all_passed = False

        print(f"   Normalized Text : \"{res['normalized_text']}\"")
        print(f"   Voice Profile   : {res['voice_profile_id']} (Speaker: {res['speaker']})")
        print(f"   Audio URL       : {res['audio_url']} ({file_size} bytes)")
        print(f"   Audio Duration  : {res['duration_seconds']}s")
        print(f"   Verification    : {'PASS (100% Single Authorized MJ Voice ✓)' if is_success else 'FAIL'}")

    print("\n" + "=" * 80)
    print(f"FINAL VOICE TEST RESULT: {'ALL 5 TEST SENTENCES VERIFIED & PASSED (100% SUCCESS)' if all_passed else 'FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(verify_single_voice())
