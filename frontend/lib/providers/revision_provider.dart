import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/revision_item.dart';

class RevisionProvider extends ChangeNotifier {
  RevisionSummaryModel? _summary;
  bool _isLoading = false;
  String? _errorMessage;
  int _currentCardIndex = 0;
  bool _isCardFlipped = false;

  RevisionSummaryModel? get summary => _summary;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  int get currentCardIndex => _currentCardIndex;
  bool get isCardFlipped => _isCardFlipped;

  RevisionItemModel? get currentDueCard {
    if (_summary != null && _summary!.dueItems.isNotEmpty && _currentCardIndex < _summary!.dueItems.length) {
      return _summary!.dueItems[_currentCardIndex];
    }
    return null;
  }

  RevisionProvider() {
    fetchRevisionSummary();
  }

  void flipCard() {
    _isCardFlipped = !_isCardFlipped;
    notifyListeners();
  }

  Future<void> fetchRevisionSummary() async {
    try {
      _isLoading = true;
      _errorMessage = null;
      _isCardFlipped = false;
      notifyListeners();

      final response = await ApiClient.get(ApiEndpoints.revisionSummary);
      if (response.isSuccess && response.data != null) {
        _summary = RevisionSummaryModel.fromJson(response.data as Map<String, dynamic>);
        _currentCardIndex = 0;
      } else {
        _errorMessage = response.errorMessage ?? 'उजळणी घटक आणण्यात त्रुटी.';
      }
    } catch (e) {
      _errorMessage = 'त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> reviewCurrentCard(int rating) async {
    final card = currentDueCard;
    if (card == null) return;

    try {
      final response = await ApiClient.post(
        ApiEndpoints.revisionReview,
        body: {
          'item_id': card.id,
          'rating': rating,
        },
      );

      if (response.isSuccess) {
        _isCardFlipped = false;
        if (_currentCardIndex < (_summary?.dueItems.length ?? 0) - 1) {
          _currentCardIndex++;
        } else {
          // Re-fetch when batch is finished
          fetchRevisionSummary();
        }
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Review submit error: $e');
    }
  }

  Future<bool> addRevisionItem({
    required String title,
    required String keyFact,
    required String subjectName,
    String? topicName,
    String? sourceBook,
    int? sourcePage,
  }) async {
    try {
      final response = await ApiClient.post(
        ApiEndpoints.revisionAdd,
        body: {
          'title': title,
          'key_fact': keyFact,
          'subject_name': subjectName,
          'topic_name': topicName,
          'source_book': sourceBook,
          'source_page': sourcePage,
        },
      );

      if (response.isSuccess) {
        fetchRevisionSummary();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}
