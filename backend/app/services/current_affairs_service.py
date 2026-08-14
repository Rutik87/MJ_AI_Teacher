import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.schema import CurrentAffair, CurrentAffairMCQ

DEFAULT_VERIFIED_ARTICLES = [
    {
        "title_mr": "महाराष्ट्र शासनाची 'मुख्यमंत्री माझी लाडकी बहीण' योजना जाहीर",
        "summary_mr": "महाराष्ट्र शासनाने राज्यातील महिलांच्या आर्थिक स्वावलंबनासाठी दरमहा ₹1,500 थेट बँक खात्यात जमा करणारी 'मुख्यमंत्री माझी लाडकी बहीण योजना' अधिकृतपणे सुरू केली आहे.",
        "mpsc_relevance_mr": "MPSC GS-2 (प्रशासन व महिला कल्याण) आणि GS-4 (अर्थव्यवस्था व सामाजिक विकास) या विषयांसाठी ही योजना अत्यंत महत्त्वाची आहे.",
        "important_facts": [
            "पात्रता वय: 21 ते 65 वर्षे वयोगटातील विवाहित/अविवाहित/विधवा महिला.",
            "वार्षिक कौटुंबिक उत्पन्न मर्यादा: ₹2.5 लाख किंवा त्यापेक्षा कमी.",
            "दरमहा आर्थिक मदत: ₹1,500 थेट DBT (Direct Benefit Transfer) द्वारे.",
            "अंमलबजावणी विभाग: महिला व बालविकास मंत्रालय, महाराष्ट्र शासन."
        ],
        "topic": "महाराष्ट्र",
        "source_name": "DGIPR, महाराष्ट्र शासन",
        "source_url": "https://dgipr.maharashtra.gov.in",
        "verification_state": "verified",
        "importance_score": 5,
        "published_at": datetime.datetime.utcnow() - datetime.timedelta(hours=2),
        "mcqs": [
            {
                "question_mr": "'मुख्यमंत्री माझी लाडकी बहीण' योजनेअंतर्गत पात्र महिलांना दरमहा किती रक्कम दिली जाते?",
                "option_a": "₹1,000",
                "option_b": "₹1,500",
                "option_c": "₹2,000",
                "option_d": "₹2,500",
                "correct_option": "B",
                "explanation_mr": "या योजनेअंतर्गत पात्र महिलांना दरमहा ₹1,500 थेट त्यांच्या बँक खात्यात दिले जातात."
            },
            {
                "question_mr": "या योजनेसाठी कमाल वार्षिक कौटुंबिक उत्पन्न मर्यादा किती निश्चित करण्यात आली आहे?",
                "option_a": "₹1.5 लाख",
                "option_b": "₹2.0 लाख",
                "option_c": "₹2.5 लाख",
                "option_d": "₹3.0 लाख",
                "correct_option": "C",
                "explanation_mr": "ज्या कुटुंबांचे वार्षिक उत्पन्न ₹2.5 लाखांपेक्षा कमी आहे अशा कुटुंबांतील महिला यास पात्र ठरतात."
            }
        ]
    },
    {
        "title_mr": "भारताची नवीन 'पंतप्रधान सूर्य घर: मोफत वीज योजना'",
        "summary_mr": "पंतप्रधान नरेंद्र मोदी यांनी देशभरातील 1 कोटी घरांच्या छतावर सोलर पॅनेल बसवून दरमहा 300 युनिट मोफत सौरऊर्जा देण्याची राष्ट्रीय योजना सुरू केली आहे.",
        "mpsc_relevance_mr": "MPSC सामान्य विज्ञान, पर्यावरण आणि ऊर्जा धोरण या विषयांसाठी नवीकरणीय ऊर्जेचा विकास अत्यंत महत्त्वाचा भाग आहे.",
        "important_facts": [
            "लक्ष्य: देशभरातील 1 कोटी घरांच्या छतावर रुफटॉप सोलर सिस्टीम.",
            "मोफत वीज प्रमाण: दरमहा 300 युनिट्स पर्यंत मोफत वीज.",
            "एकूण अर्थसंकल्पीय तरतूद: ₹75,000 कोटी पेक्षा जास्त.",
            "नोडल एजन्सी: नवीन आणि नवीकरणीय ऊर्जा मंत्रालय (MNRE)."
        ],
        "topic": "भारत",
        "source_name": "PIB नवी दिल्ली (Ministry of New and Renewable Energy)",
        "source_url": "https://pib.gov.in",
        "verification_state": "verified",
        "importance_score": 5,
        "published_at": datetime.datetime.utcnow() - datetime.timedelta(hours=5),
        "mcqs": [
            {
                "question_mr": "'पीएम सूर्य घर: मोफत वीज योजने' अंतर्गत दरमहा किती युनिट मोफत वीज पुरवण्याचे उद्दिष्ट आहे?",
                "option_a": "100 युनिट",
                "option_b": "200 युनिट",
                "option_c": "300 युनिट",
                "option_d": "500 युनिट",
                "correct_option": "C",
                "explanation_mr": "या योजनेअंतर्गत 1 कोटी घरांना दरमहा 300 युनिट्स पर्यंत मोफत सौरऊर्जा पुरवली जाते."
            }
        ]
    },
    {
        "title_mr": "रिझर्व्ह बँक ऑफ इंडिया (RBI) द्वारे रेपो रेट 6.50% वर स्थिर",
        "summary_mr": "आरबीआयच्या मौद्रिक धोरण समितीने (MPC) महागाई नियंत्रण आणि आर्थिक विकास संतुलित ठेवण्यासाठी रेपो दर 6.50% वर जैसे थे ठेवण्याचा निर्णय घेतला आहे.",
        "mpsc_relevance_mr": "MPSC भारतीय अर्थव्यवस्था (GS-4) अंतर्गत बँकिंग, महागाई नियंत्रण आणि RBI ची मौद्रिक साधने (Monetary Policy) साठी अत्यंत आवश्यक.",
        "important_facts": [
            "सध्याचा रेपो रेट: 6.50%",
            "सध्याचा रिव्हर्स रेपो रेट: 3.35%",
            "MPC चे अध्यक्ष: RBI गव्हर्नर",
            "MPC मध्ये एकूण सदस्य: 6 (3 RBI + 3 केंद्र सरकार नियुक्त)."
        ],
        "topic": "अर्थव्यवस्था",
        "source_name": "Reserve Bank of India (RBI Press Release)",
        "source_url": "https://rbi.org.in",
        "verification_state": "verified",
        "importance_score": 4,
        "published_at": datetime.datetime.utcnow() - datetime.timedelta(hours=10),
        "mcqs": [
            {
                "question_mr": "भारतीय रिझर्व्ह बँकेच्या मौद्रिक धोरण समितीमध्ये (MPC) एकूण किती सदस्य असतात?",
                "option_a": "4",
                "option_b": "5",
                "option_c": "6",
                "option_d": "7",
                "correct_option": "C",
                "explanation_mr": "MPC मध्ये एकूण ६ सदस्य असतात (३ सदस्य RBI कडून आणि ३ सदस्य केंद्र सरकारकडून नेमले जातात)."
            }
        ]
    },
    {
        "title_mr": "इस्रोचे 'गगनयान' मोहिमेसाठी मानवरहित चाचणी उड्डाण यशस्वी",
        "summary_mr": "भारतीय अंतराळ संशोधन संस्थेने (ISRO) भारताच्या पहिल्या मानवी अंतराळ मोहिमेसाठी 'गगनयान TV-D1' टेस्ट व्हेईकल क्रू एस्केप सिस्टीमचे यशस्वी प्रक्षेपण पूर्ण केले.",
        "mpsc_relevance_mr": "MPSC विज्ञान व तंत्रज्ञान (Space Technology) पेपर अंतर्गत भारताची अंतराळ संशोधन वाटचाल हा हमखास प्रश्न विचारला जाणारा घटक आहे.",
        "important_facts": [
            "मोहिमेचे नाव: गगनयान (Gaganyaan Project)",
            "प्रक्षेपण केंद्र: सतीश धवन अंतराळ केंद्र, श्रीहरिकोटा (आंध्र प्रदेश)",
            "चाचणीचे उद्दिष्ट: अंतराळवीरांच्या सुरक्षेसाठी क्रू एस्केप सिस्टीमचे परीक्षण.",
            "इस्रो अध्यक्ष: एस. सोमनाथ."
        ],
        "topic": "विज्ञान व तंत्रज्ञान",
        "source_name": "ISRO / PIB Science",
        "source_url": "https://isro.gov.in",
        "verification_state": "verified",
        "importance_score": 5,
        "published_at": datetime.datetime.utcnow() - datetime.timedelta(hours=14),
        "mcqs": [
            {
                "question_mr": "भारताच्या पहिल्या मानवी अंतराळ मोहिमेचे नाव काय आहे?",
                "option_a": "चांद्रयान",
                "option_b": "गगनयान",
                "option_c": "आदित्य L1",
                "option_d": "मंगळयान",
                "correct_option": "B",
                "explanation_mr": "'गगनयान' ही भारताची पहिली मानवी अंतराळ मोहीम आहे."
            }
        ]
    }
]

async def seed_current_affairs_if_empty(db: AsyncSession):
    result = await db.execute(select(CurrentAffair))
    items = result.scalars().all()
    if not items:
        for item in DEFAULT_VERIFIED_ARTICLES:
            item_copy = dict(item)
            mcqs_data = item_copy.pop("mcqs", [])
            article = CurrentAffair(**item_copy)
            db.add(article)
            await db.flush()
            
            for mcq in mcqs_data:
                q = CurrentAffairMCQ(article_id=article.id, **mcq)
                db.add(q)
        await db.commit()

async def get_current_affairs(db: AsyncSession, topic: str = "सर्व") -> List[CurrentAffair]:
    await seed_current_affairs_if_empty(db)
    query = select(CurrentAffair)
    if topic and topic != "सर्व":
        query = query.filter(CurrentAffair.topic == topic)
    query = query.order_by(CurrentAffair.published_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def refresh_current_affairs_data(db: AsyncSession) -> List[CurrentAffair]:
    await seed_current_affairs_if_empty(db)
    query = select(CurrentAffair).order_by(CurrentAffair.published_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_daily_quiz(db: AsyncSession, limit: int = 10) -> List[CurrentAffairMCQ]:
    await seed_current_affairs_if_empty(db)
    query = select(CurrentAffairMCQ).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def toggle_article_bookmark(db: AsyncSession, article_id: int) -> bool:
    result = await db.execute(select(CurrentAffair).filter(CurrentAffair.id == article_id))
    article = result.scalars().first()
    if article:
        article.is_bookmarked = not article.is_bookmarked
        await db.commit()
        return article.is_bookmarked
    return False
