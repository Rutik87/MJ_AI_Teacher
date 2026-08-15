import pytest
from app.services.speech.marathi_normalizer import MarathiPronunciationNormalizer

def test_number_and_year_normalization():
    # Standalone numbers
    assert "शून्य" in MarathiPronunciationNormalizer.normalize_text("0")
    assert "एक" in MarathiPronunciationNormalizer.normalize_text("1")
    assert "दहा" in MarathiPronunciationNormalizer.normalize_text("10")
    assert "वीस" in MarathiPronunciationNormalizer.normalize_text("20")
    assert "शंभर" in MarathiPronunciationNormalizer.normalize_text("100")

    # Historical years
    year_1857 = MarathiPronunciationNormalizer.normalize_text("1857 चा उठाव")
    assert "अठराशे सत्तावन्न" in year_1857
    assert "चा उठाव" in year_1857

    year_1947 = MarathiPronunciationNormalizer.normalize_text("1947 मध्ये स्वातंत्र्य")
    assert "एकोणीसशे सत्तेचाळीस" in year_1947

    year_2024 = MarathiPronunciationNormalizer.normalize_text("2024 ची परीक्षा")
    assert "दोन हजार चोवीस" in year_2024

def test_percentages_and_ranges():
    percent_text = MarathiPronunciationNormalizer.normalize_text("तयारी 68% झाली आहे.")
    assert "टक्के" in percent_text

    range_text = MarathiPronunciationNormalizer.normalize_text("10-15 मिनिटे अभ्यास करू.")
    assert "दहा ते पंधरा" in range_text

def test_exam_abbreviations():
    abbr_text = MarathiPronunciationNormalizer.normalize_text("MPSC आणि UPSC चे PYQs आणि MCQs सोडवा.")
    assert "एमपीएससी" in abbr_text
    assert "यूपीएससी" in abbr_text
    assert "पीवायक्यूस" in abbr_text
    assert "एमसीक्यूस" in abbr_text

    pdf_text = MarathiPronunciationNormalizer.normalize_text("ही PDF फाईल वाचा.")
    assert "पीडीएफ" in pdf_text

def test_mixed_marathi_english_code_switching():
    # Sentence 1: "Are, aaj kay abhyas karaycha?"
    s1 = MarathiPronunciationNormalizer.normalize_text("Are, aaj kay abhyas karaycha?")
    assert "अरे" in s1
    assert "आज" in s1
    assert "काय" in s1
    assert "अभ्यास" in s1
    assert "करायचा" in s1

    # Sentence 2: "1857 cha revolt simple Marathi madhye samjhav."
    s2 = MarathiPronunciationNormalizer.normalize_text("1857 cha revolt simple Marathi madhye samjhav.")
    assert "अठराशे सत्तावन्न" in s2
    assert "रिव्होल्ट" in s2
    assert "सिंपल" in s2
    assert "मध्ये" in s2
    assert "समजाव" in s2

    # Sentence 4: "Arre tension nako gheu, ek-ek point baghuya."
    s4 = MarathiPronunciationNormalizer.normalize_text("Arre tension nako gheu, ek-ek point baghuya.")
    assert "अरे" in s4
    assert "टेन्शन" in s4
    assert "नको" in s4
    assert "घेऊ" in s4
    assert "पॉईंट" in s4
    assert "बघूया" in s4

    # Sentence 5: "Ya question cha correct answer option B aahe."
    s5 = MarathiPronunciationNormalizer.normalize_text("Ya question cha correct answer option B aahe.")
    assert "या" in s5
    assert "क्वेश्चन" in s5
    assert "करेक्ट" in s5
    assert "आन्सर" in s5
    assert "ऑप्शन बी" in s5
    assert "आहे" in s5
