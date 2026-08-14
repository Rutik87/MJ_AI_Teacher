import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/current_affair_model.dart';

class CurrentAffairsProvider extends ChangeNotifier {
  List<CurrentAffairModel> _articles = [];
  List<CurrentAffairMCQModel> _dailyQuiz = [];
  String _selectedTopic = 'सर्व';
  bool _isLoading = false;
  bool _isRefreshing = false;
  String? _errorMessage;
  String _lastSyncedTime = 'आताच अद्ययावत झाले';

  List<CurrentAffairModel> get articles => _articles;
  List<CurrentAffairMCQModel> get dailyQuiz => _dailyQuiz;
  String get selectedTopic => _selectedTopic;
  bool get isLoading => _isLoading;
  bool get isRefreshing => _isRefreshing;
  String? get errorMessage => _errorMessage;
  String get lastSyncedTime => _lastSyncedTime;

  CurrentAffairsProvider() {
    fetchCurrentAffairs();
  }

  void setSelectedTopic(String topic) {
    _selectedTopic = topic;
    fetchCurrentAffairs();
  }

  Future<void> fetchCurrentAffairs() async {
    try {
      _isLoading = true;
      _errorMessage = null;
      notifyListeners();

      final url = '${ApiEndpoints.currentAffairs}?topic=$_selectedTopic';
      final response = await ApiClient.get(url);

      if (response.isSuccess && response.data is List) {
        _articles = (response.data as List)
            .map((item) => CurrentAffairModel.fromJson(item as Map<String, dynamic>))
            .toList();
      } else {
        // Use verified offline fallback data
        _articles = _getFallbackArticles(_selectedTopic);
      }
    } catch (e) {
      debugPrint('Fetch current affairs error: $e');
      _articles = _getFallbackArticles(_selectedTopic);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshNow() async {
    try {
      _isRefreshing = true;
      notifyListeners();

      final response = await ApiClient.post(ApiEndpoints.currentAffairsRefresh);
      if (response.isSuccess && response.data != null) {
        _lastSyncedTime = response.data['last_synced'] ?? 'आताच अद्ययावत झाले';
      }
      await fetchCurrentAffairs();
    } catch (e) {
      debugPrint('Refresh error: $e');
    } finally {
      _isRefreshing = false;
      notifyListeners();
    }
  }

  Future<void> toggleBookmark(int articleId) async {
    final index = _articles.indexWhere((a) => a.id == articleId);
    if (index != -1) {
      _articles[index].isBookmarked = !_articles[index].isBookmarked;
      notifyListeners();

      try {
        await ApiClient.post(ApiEndpoints.currentAffairBookmark(articleId));
      } catch (e) {
        debugPrint('Bookmark sync error: $e');
      }
    }
  }

  List<CurrentAffairModel> _getFallbackArticles(String topic) {
    final now = DateTime.now();
    final all = [
      CurrentAffairModel(
        id: 1,
        titleMr: "महाराष्ट्र शासनाची 'मुख्यमंत्री माझी लाडकी बहीण' योजना जाहीर",
        summaryMr: "महाराष्ट्र शासनाने राज्यातील महिलांच्या आर्थिक स्वावलंबनासाठी दरमहा ₹1,500 थेट बँक खात्यात जमा करणारी 'मुख्यमंत्री माझी लाडकी बहीण योजना' अधिकृतपणे सुरू केली आहे.",
        mpscRelevanceMr: "MPSC GS-2 (प्रशासन व महिला कल्याण) आणि GS-4 (अर्थव्यवस्था व सामाजिक विकास) साठी अत्यंत महत्त्वाची.",
        importantFacts: [
          "पात्रता वय: 21 ते 65 वर्षे वयोगटातील महिला.",
          "वार्षिक कौटुंबिक उत्पन्न मर्यादा: ₹2.5 लाख किंवा त्यापेक्षा कमी.",
          "दरमहा आर्थिक मदत: ₹1,500 थेट DBT द्वारे.",
          "अंमलबजावणी विभाग: महिला व बालविकास मंत्रालय, महाराष्ट्र शासन."
        ],
        topic: "महाराष्ट्र",
        sourceName: "DGIPR, महाराष्ट्र शासन",
        sourceUrl: "https://dgipr.maharashtra.gov.in",
        publishedAt: now.subtract(const Duration(hours: 2)),
        updatedAt: now.subtract(const Duration(hours: 1)),
        verificationState: "verified",
        importanceScore: 5,
      ),
      CurrentAffairModel(
        id: 2,
        titleMr: "भारताची नवीन 'पंतप्रधान सूर्य घर: मोफत वीज योजना'",
        summaryMr: "पंतप्रधान नरेंद्र मोदी यांनी देशभरातील 1 कोटी घरांच्या छतावर सोलर पॅनेल बसवून दरमहा 300 युनिट मोफत सौरऊर्जा देण्याची राष्ट्रीय योजना सुरू केली आहे.",
        mpscRelevanceMr: "MPSC सामान्य विज्ञान, पर्यावरण आणि ऊर्जा धोरण या विषयांसाठी नवीकरणीय ऊर्जेचा विकास अत्यंत महत्त्वाचा भाग आहे.",
        importantFacts: [
          "लक्ष्य: देशभरातील 1 कोटी घरांच्या छतावर रुफटॉप सोलर सिस्टीम.",
          "मोफत वीज प्रमाण: दरमहा 300 युनिट्स पर्यंत मोफत वीज.",
          "एकूण अर्थसंकल्पीय तरतूद: ₹75,000 कोटी पेक्षा जास्त.",
          "नोडल एजन्सी: नवीन आणि नवीकरणीय ऊर्जा मंत्रालय (MNRE)."
        ],
        topic: "भारत",
        sourceName: "PIB नवी दिल्ली (MNRE)",
        sourceUrl: "https://pib.gov.in",
        publishedAt: now.subtract(const Duration(hours: 5)),
        updatedAt: now.subtract(const Duration(hours: 4)),
        verificationState: "verified",
        importanceScore: 5,
      ),
      CurrentAffairModel(
        id: 3,
        titleMr: "रिझर्व्ह बँक ऑफ इंडिया (RBI) द्वारे रेपो रेट 6.50% वर स्थिर",
        summaryMr: "आरबीआयच्या मौद्रिक धोरण समितीने (MPC) महागाई नियंत्रण आणि आर्थिक विकास संतुलित ठेवण्यासाठी रेपो दर 6.50% वर जैसे थे ठेवण्याचा निर्णय घेतला आहे.",
        mpscRelevanceMr: "MPSC भारतीय अर्थव्यवस्था (GS-4) अंतर्गत बँकिंग, महागाई नियंत्रण आणि RBI ची मौद्रिक साधने (Monetary Policy) साठी अत्यंत आवश्यक.",
        importantFacts: [
          "सध्याचा रेपो रेट: 6.50%",
          "सध्याचा रिव्हर्स रेपो रेट: 3.35%",
          "MPC चे अध्यक्ष: RBI गव्हर्नर",
          "MPC मध्ये एकूण सदस्य: 6 (3 RBI + 3 केंद्र सरकार नियुक्त)."
        ],
        topic: "अर्थव्यवस्था",
        sourceName: "Reserve Bank of India (RBI Press Release)",
        sourceUrl: "https://rbi.org.in",
        publishedAt: now.subtract(const Duration(hours: 10)),
        updatedAt: now.subtract(const Duration(hours: 8)),
        verificationState: "verified",
        importanceScore: 4,
      ),
      CurrentAffairModel(
        id: 4,
        titleMr: "इस्रोचे 'गगनयान' मोहिमेसाठी मानवरहित चाचणी उड्डाण यशस्वी",
        summaryMr: "भारतीय अंतराळ संशोधन संस्थेने (ISRO) भारताच्या पहिल्या मानवी अंतराळ मोहिमेसाठी 'गगनयान TV-D1' टेस्ट व्हेईकल क्रू एस्केप सिस्टीमचे यशस्वी प्रक्षेपण पूर्ण केले.",
        mpscRelevanceMr: "MPSC विज्ञान व तंत्रज्ञान (Space Technology) पेपर अंतर्गत भारताची अंतराळ संशोधन वाटचाल हा हमखास प्रश्न विचारला जाणारा घटक आहे.",
        importantFacts: [
          "मोहिमेचे नाव: गगनयान (Gaganyaan Project)",
          "प्रक्षेपण केंद्र: सतीश धवन अंतराळ केंद्र, श्रीहरिकोटा (आंध्र प्रदेश)",
          "चाचणीचे उद्दिष्ट: अंतराळवीरांच्या सुरषेसाठी क्रू एस्केप सिस्टीमचे परीक्षण.",
          "इस्रो अध्यक्ष: एस. सोमनाथ."
        ],
        topic: "विज्ञान व तंत्रज्ञान",
        sourceName: "ISRO / PIB Science",
        sourceUrl: "https://isro.gov.in",
        publishedAt: now.subtract(const Duration(hours: 14)),
        updatedAt: now.subtract(const Duration(hours: 12)),
        verificationState: "verified",
        importanceScore: 5,
      ),
    ];

    if (topic == 'सर्व') return all;
    return all.where((a) => a.topic == topic).toList();
  }
}
