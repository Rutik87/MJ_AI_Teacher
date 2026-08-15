import re
from typing import Dict

# Marathi cardinal numbers 0-99
MARATHI_NUMBERS_0_TO_99: Dict[int, str] = {
    0: "शून्य", 1: "एक", 2: "दोन", 3: "तीन", 4: "चार", 5: "पाच",
    6: "सहा", 7: "सात", 8: "आठ", 9: "नऊ", 10: "दहा",
    11: "अकरा", 12: "बारा", 13: "तेरा", 14: "चौदा", 15: "पंधरा",
    16: "सोळा", 17: "सतरा", 18: "अठरा", 19: "एकोणीस", 20: "वीस",
    21: "एकवीस", 22: "बावीस", 23: "तेवीस", 24: "चोवीस", 25: "पंचवीस",
    26: "सव्वीस", 27: "सत्तावीस", 28: "अठ्ठावीस", 29: "एकोणतीस", 30: "तीस",
    31: "एकतीस", 32: "बत्तीस", 33: "तेहतीस", 34: "चौतीस", 35: "पस्तीस",
    36: "छत्तीस", 37: "सदतीस", 38: "अडतीस", 39: "एकेचाळीस", 40: "चाळीस",
    41: "एक्केचाळीस", 42: "बेचाळीस", 43: "त्रेचाळीस", 44: "चव्वेचाळीस", 45: "पंचेचाळीस",
    46: "सेहेचाळीस", 47: "सत्तेचाळीस", 48: "अठ्ठेचाळीस", 49: "एकोणपन्नास", 50: "पन्नास",
    51: "एक्कावन्न", 52: "बावन्न", 53: "त्रेपन्न", 54: "चौपन्न", 55: "पंचावन्न",
    56: "छप्पन्न", 57: "सत्तावन्न", 58: "अठ्ठावन्न", 59: "एकोणसाठ", 60: "साठ",
    61: "एकसष्ठ", 62: "बासष्ठ", 63: "त्रेसष्ठ", 64: "चौसष्ठ", 65: "पासष्ठ",
    66: "सहासष्ठ", 67: "सदुसष्ठ", 68: "अडुसष्ठ", 69: "एकोणसत्तर", 70: "सत्तर",
    71: "एकाहत्तर", 72: "बाहत्तर", 73: "त्र्याहत्तर", 74: "चौहत्तर", 75: "पंच्याहत्तर",
    76: "शहात्तर", 77: "सत्याहत्तर", 78: "अठ्ठ्याहत्तर", 79: "एकोणऐंशी", 80: "ऐंशी",
    81: "एक्याऐंशी", 82: "ब्याऐंशी", 83: "त्र्याऐंशी", 84: "चौऱ्याऐंशी", 85: "पंच्याऐंशी",
    86: "शहाऐंशी", 87: "सत्त्याऐंशी", 88: "अठ्ठ्याऐंशी", 89: "एकोणनव्वद", 90: "नव्वद",
    91: "एक्याण्णव", 92: "ब्याण्णव", 93: "त्र्याण्णव", 94: "चौऱ्याण्णव", 95: "पंच्याण्णव",
    96: "शहाण्णव", 97: "सत्त्याण्णव", 98: "अठ्ठ्याण्णव", 99: "नऊ्याण्णव"
}

# Devanagari digit mapping
DEV_DIGIT_MAP = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

# Common MPSC & Exam abbreviations to Marathi phonetics
EXAM_ABBREVIATIONS: Dict[str, str] = {
    "MPSC": "एमपीएससी",
    "UPSC": "यूपीएससी",
    "PYQ": "पीवायक्यू",
    "PYQS": "पीवायक्यूस",
    "MCQ": "एमसीक्यू",
    "MCQS": "एमसीक्यूस",
    "PDF": "पीडीएफ",
    "TXT": "टीएक्सटी",
    "ICT": "आयसीटी",
    "SMC": "एसएमसी",
    "RAG": "रॅग",
    "AI": "एआय",
    "STT": "एसटीटी",
    "TTS": "टीटीएस",
    "IAS": "आयएएस",
    "IPS": "आयपीएस",
    "IFS": "आयएफएस",
    "PSI": "पीएसआय",
    "STI": "एसटीआय",
    "ASO": "एएसओ",
    "GST": "जीएसटी",
    "RBI": "आरबीआय",
    "SBI": "एसबीआय",
    "ISRO": "इस्रो",
    "DRDO": "डीआरडीओ",
    "WHO": "डब्ल्यूएचओ",
    "UN": "यूएन",
    "UNO": "यूएनओ",
    "SSC": "एसएससी",
    "HSC": "एचएससी",
    "NCERT": "एनसीईआरटी",
    "SCERT": "एससीईआरटी",
    "GS": "जीएस",
    "CSAT": "सीसॅट"
}

# Common Latin-script Marathi/English hybrid terms to natural Marathi
LATIN_MARATHI_TERMS: Dict[str, str] = {
    "arre": "अरे",
    "are": "अरे",
    "aaj": "आज",
    "kay": "काय",
    "abhyas": "अभ्यास",
    "karaycha": "करायचा",
    "karu": "करू",
    "kasa": "कसा",
    "kashi": "कशी",
    "kashe": "कशे",
    "kiti": "किती",
    "kuthlya": "कुठल्या",
    "kuthla": "कुठला",
    "kuthli": "कुठली",
    "kuthe": "कुठे",
    "madhye": "मध्ये",
    "madhe": "मध्ये",
    "samjhav": "समजाव",
    "samjun": "समजून",
    "gheu": "घेऊ",
    "gheuya": "घेऊया",
    "baghu": "बघू",
    "baghuya": "बघूया",
    "nako": "नको",
    "chal": "चल",
    "chala": "चला",
    "sang": "सांग",
    "sanga": "सांगा",
    "bol": "बोल",
    "bola": "बोला",
    "aahe": "आहे",
    "aahet": "आहेत",
    "hota": "होता",
    "hoti": "होती",
    "hote": "होते",
    "cha": "चा",
    "chi": "ची",
    "che": "चे",
    "var": "वर",
    "marathi": "मराठी",
    "ek": "एक",
    "ek-ek": "एक-एक",
    "tu": "तू",
    "tula": "तुला",
    "tuzha": "तुझा",
    "tuzhi": "तुझी",
    "tuzhe": "तुझे",
    "mi": "मी",
    "mala": "मला",
    "majha": "माझा",
    "majhi": "माझी",
    "majhe": "माझे",
    "amhi": "आम्ही",
    "aplyala": "आपल्याला",
    "apan": "आपण",
    "ha": "हा",
    "hi": "ही",
    "he": "हे",
    "ya": "या",
    "tya": "त्या",
    "tyacha": "त्याचा",
    "tyachi": "त्याची",
    "tyache": "त्याचे",
    "asha": "अशा",
    "padhatine": "पद्धतीने",
    "lakshat": "लक्षात",
    "thev": "ठेव",
    "thevuya": "ठेवूया",
    "visarlo": "विसरलो",
    "visarli": "विसरली",
    "visarloy": "विसरलोय",
    "kahi": "काही",
    "problem": "प्रॉब्लेम",
    "tension": "टेन्शन",
    "revolt": "रिव्होल्ट",
    "simple": "सिंपल",
    "question": "क्वेश्चन",
    "questions": "क्वेश्चन्स",
    "topic": "टॉपिक",
    "topics": "टॉपिक्स",
    "point": "पॉईंट",
    "points": "पॉईंट्स",
    "correct": "करेक्ट",
    "answer": "आन्सर",
    "option": "ऑप्शन",
    "options": "ऑप्शन्स",
    "revision": "रिव्हिजन",
    "test": "टेस्ट",
    "history": "हिस्ट्री",
    "geography": "जिओग्राफी",
    "polity": "पॉलिटी",
    "economics": "इकॉनॉमिक्स",
    "science": "सायन्स",
    "plan": "प्लॅन",
    "basic": "बेसिक",
    "ready": "रेडी",
    "start": "स्टार्ट",
    "stop": "स्टॉप",
    "break": "ब्रेक",
    "score": "स्कोअर",
    "notes": "नोट्स",
    "book": "बुक",
    "books": "बुक्स",
    "page": "पेज",
    "chapter": "चॅप्टर"
}


class MarathiPronunciationNormalizer:
    """
    Normalizes numbers, years, percentages, abbreviations, and mixed code-switched text
    into natural phonetic Marathi text for clear and smooth speech synthesis.
    """

    @classmethod
    def number_to_marathi_words(cls, n: int) -> str:
        """Converts an integer (0-9999999) to Marathi words."""
        if n in MARATHI_NUMBERS_0_TO_99:
            return MARATHI_NUMBERS_0_TO_99[n]

        # Year handling (e.g. 1857 -> अठराशे सत्तावन्न, 1947 -> एकोणीसशे सेहेचाळीस)
        if 1100 <= n <= 1999:
            hundreds = n // 100
            remainder = n % 100
            hundred_str = f"{MARATHI_NUMBERS_0_TO_99.get(hundreds, str(hundreds))}शे"
            if remainder == 0:
                return hundred_str
            rem_str = MARATHI_NUMBERS_0_TO_99.get(remainder, str(remainder))
            return f"{hundred_str} {rem_str}"

        if 2000 <= n <= 2099:
            remainder = n % 100
            if remainder == 0:
                return "दोन हजार"
            rem_str = MARATHI_NUMBERS_0_TO_99.get(remainder, str(remainder))
            return f"दोन हजार {rem_str}"

        # General hundreds (100-999)
        if 100 <= n <= 999:
            hundreds = n // 100
            remainder = n % 100
            if hundreds == 1:
                h_str = "एकशे" if remainder > 0 else "शंभर"
            else:
                h_str = f"{MARATHI_NUMBERS_0_TO_99.get(hundreds, str(hundreds))}शे"
            
            if remainder == 0:
                return h_str
            return f"{h_str} {MARATHI_NUMBERS_0_TO_99.get(remainder, str(remainder))}"

        # Thousands (1,000 to 99,999)
        if 1000 <= n <= 99999:
            thousands = n // 1000
            remainder = n % 1000
            t_str = f"{MARATHI_NUMBERS_0_TO_99.get(thousands, str(thousands))} हजार"
            if remainder == 0:
                return t_str
            return f"{t_str} {cls.number_to_marathi_words(remainder)}"

        # Lakhs (1,00,000 to 99,99,999)
        if 100000 <= n <= 9999999:
            lakhs = n // 100000
            remainder = n % 100000
            l_str = f"{MARATHI_NUMBERS_0_TO_99.get(lakhs, str(lakhs))} लाख"
            if remainder == 0:
                return l_str
            return f"{l_str} {cls.number_to_marathi_words(remainder)}"

        return str(n)

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Main entry point: cleans markdown, converts abbreviations, numbers, percentages,
        and Roman/Latin terms to smooth Marathi pronunciation.
        """
        if not text:
            return ""

        # 1. Clean Markdown formatting & non-speech characters
        t = re.sub(r'#{1,6}\s*', '', text)
        t = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', t)
        t = re.sub(r'•\s*', '', t)
        t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
        t = re.sub(r'`[^`]*`', '', t)
        t = re.sub(r'http\S+', '', t)
        t = re.sub(r'[\r\t]', ' ', t)

        # 2. Convert Devanagari digits to Latin digits temporarily for uniform parsing
        for dev, lat in DEV_DIGIT_MAP.items():
            t = t.replace(dev, lat)

        # 3. Percentages (e.g. 50% -> पन्नास टक्के, 68% -> अडुसष्ठ टक्के)
        def replace_percentage(match):
            val = int(match.group(1))
            return f"{cls.number_to_marathi_words(val)} टक्के"
        t = re.sub(r'\b(\d{1,4})%', replace_percentage, t)

        # 4. Number ranges (e.g. 10-15 -> दहा ते पंधरा, 3-4 -> तीन ते चार)
        def replace_range(match):
            n1 = int(match.group(1))
            n2 = int(match.group(2))
            return f"{cls.number_to_marathi_words(n1)} ते {cls.number_to_marathi_words(n2)}"
        t = re.sub(r'\b(\d{1,4})\s*-\s*(\d{1,4})\b', replace_range, t)

        # 5. Options formatting (e.g. Option B / पर्याय B / (B) -> ऑप्शन बी / पर्याय बी)
        t = re.sub(r'\boption\s*([A-Da-d])\b', lambda m: f"ऑप्शन {m.group(1).upper()}", t, flags=re.IGNORECASE)
        t = re.sub(r'\bपर्याय\s*([A-Da-d])\b', lambda m: f"पर्याय {m.group(1).upper()}", t, flags=re.IGNORECASE)
        
        # Single English letters representing options (A, B, C, D)
        letter_phonetics = {'A': 'ए', 'B': 'बी', 'C': 'सी', 'D': 'डी'}
        for letter, phon in letter_phonetics.items():
            t = re.sub(rf'\b{letter}\b', phon, t)
            t = re.sub(rf'\({letter}\)', f"({phon})", t)

        # 6. Standalone Integers to Marathi Words
        def replace_number(match):
            val = int(match.group(0))
            if val < 10000000:
                return cls.number_to_marathi_words(val)
            return match.group(0)
        t = re.sub(r'\b\d+\b', replace_number, t)

        # 7. Convert Upper-case Exam Abbreviations
        for abbr, phonetic in EXAM_ABBREVIATIONS.items():
            t = re.sub(rf'\b{abbr}\b', phonetic, t, flags=re.IGNORECASE)

        # 8. Convert Common Latin Marathi / Hybrid Words
        words = t.split()
        normalized_words = []
        for word in words:
            punct_start = ""
            punct_end = ""
            w = word
            while w and w[0] in ".,!?:;\"'()[]{}":
                punct_start += w[0]
                w = w[1:]
            while w and w[-1] in ".,!?:;\"'()[]{}":
                punct_end = w[-1] + punct_end
                w = w[:-1]

            w_lower = w.lower()
            if w_lower in LATIN_MARATHI_TERMS:
                repl = LATIN_MARATHI_TERMS[w_lower]
                normalized_words.append(f"{punct_start}{repl}{punct_end}")
            else:
                normalized_words.append(word)

        t = " ".join(normalized_words)

        # 9. Clean excessive spaces
        t = re.sub(r'\s+', ' ', t).strip()

        return t
