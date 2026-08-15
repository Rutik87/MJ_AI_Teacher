import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

from app.config import settings
from app.services.tts.voice_engine import mj_voice_engine
from app.services.speech.marathi_normalizer import MarathiPronunciationNormalizer

test_sentences = [
    ("Are, aaj kay abhyas karaycha?", "friendly"),
    ("1857 cha revolt simple Marathi madhye samjhav.", "explaining"),
    ("Ha question tu asha padhatine lakshat thev.", "encouraging"),
    ("Arre tension nako gheu, ek-ek point baghuya.", "empathetic"),
    ("Ya question cha correct answer option B aahe.", "happy"),
    ("Tu kuthlya topic var revision karaycha sang.", "encouraging"),
]

async def evaluate():
    print("=" * 72)
    print("MJ SINGLE AUTHORIZED VOICE: 6-SENTENCE PHONETIC & SYNTHESIS EVALUATION")
    print("=" * 72 + "\n")
    
    all_passed = True
    cache_dir = Path(settings.AUDIO_CACHE_PATH)
    
    for i, (orig, emotion) in enumerate(test_sentences, 1):
        normalized = MarathiPronunciationNormalizer.normalize_text(orig)
        url, duration = await mj_voice_engine.synthesize_speech(orig, emotion=emotion)
        
        filepath = cache_dir / os.path.basename(url) if url else None
        size = filepath.stat().st_size if filepath and filepath.exists() else 0
        is_pass = size > 1000 and url is not None
        if not is_pass:
            all_passed = False
        
        print(f"Test Sentence #{i}:")
        print(f"   Original Input : \"{orig}\"")
        print(f"   Phonetic Text  : \"{normalized}\"")
        print(f"   Emotion Tag    : {emotion}")
        print(f"   Audio URL      : {url}")
        print(f"   Duration       : {round(duration, 2)}s")
        print(f"   Audio Size     : {size} bytes")
        print(f"   Evaluation     : {'PASS (Synthesized & Verified ✓)' if is_pass else 'FAIL'}\n")
    
    print("=" * 72)
    print(f"OVERALL VOICE EVALUATION RESULT: {'ALL 6 SENTENCES PASSED (100% SUCCESS)' if all_passed else 'FAILED'}")
    print("=" * 72)

if __name__ == "__main__":
    asyncio.run(evaluate())
