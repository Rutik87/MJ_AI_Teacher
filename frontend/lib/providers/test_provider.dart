import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/test_model.dart';

class TestProvider extends ChangeNotifier {
  TestResultModel? _activeTest;
  TestResultModel? _completedResult;
  List<TestResultModel> _pastTests = [];
  int _currentQuestionIndex = 0;
  Map<int, String> _userAnswers = {}; // question_id -> option ('A','B','C','D')
  int _remainingSeconds = 0;
  Timer? _countdownTimer;
  bool _isLoading = false;
  String? _errorMessage;

  TestResultModel? get activeTest => _activeTest;
  TestResultModel? get completedResult => _completedResult;
  List<TestResultModel> get pastTests => _pastTests;
  int get currentQuestionIndex => _currentQuestionIndex;
  Map<int, String> get userAnswers => _userAnswers;
  int get remainingSeconds => _remainingSeconds;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  String get formattedTimer {
    int mins = _remainingSeconds ~/ 60;
    int secs = _remainingSeconds % 60;
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  Future<void> fetchHistory() async {
    try {
      final response = await ApiClient.get(ApiEndpoints.testHistory);
      if (response.isSuccess && response.data is List) {
        _pastTests = (response.data as List)
            .map((item) => TestResultModel.fromJson(item as Map<String, dynamic>))
            .toList();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Fetch past tests error: $e');
    }
  }

  Future<bool> startNewTest({
    String subjectName = 'इतिहास',
    String? topicName,
    int count = 10,
    String difficulty = 'medium',
    int durationMinutes = 15,
  }) async {
    try {
      _isLoading = true;
      _errorMessage = null;
      _currentQuestionIndex = 0;
      _userAnswers = {};
      _completedResult = null;
      notifyListeners();

      final response = await ApiClient.post(
        ApiEndpoints.createTest,
        body: {
          'title': '$subjectName सराव चाचणी',
          'subject_name': subjectName,
          'topic_name': topicName ?? 'सर्वसाधारण',
          'count': count,
          'difficulty': difficulty,
          'duration_minutes': durationMinutes,
        },
      );

      if (response.isSuccess && response.data != null) {
        _activeTest = TestResultModel.fromJson(response.data as Map<String, dynamic>);
        _remainingSeconds = durationMinutes * 60;
        _testEndTime = DateTime.now().add(Duration(minutes: durationMinutes));
        _startTimer();
        notifyListeners();
        return true;
      } else {
        _errorMessage = response.errorMessage ?? 'चाचणी तयार करण्यात त्रुटी.';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'त्रुटी: $e';
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  DateTime? _testEndTime;

  void _startTimer() {
    _countdownTimer?.cancel();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_testEndTime != null) {
        final diff = _testEndTime!.difference(DateTime.now()).inSeconds;
        if (diff > 0) {
          _remainingSeconds = diff;
          notifyListeners();
        } else {
          _remainingSeconds = 0;
          timer.cancel();
          submitTest();
        }
      } else if (_remainingSeconds > 0) {
        _remainingSeconds--;
        notifyListeners();
      } else {
        timer.cancel();
        submitTest();
      }
    });
  }

  void selectOption(int questionId, String optionKey) {
    _userAnswers[questionId] = optionKey;
    notifyListeners();
  }

  void goToQuestion(int index) {
    if (_activeTest != null && index >= 0 && index < _activeTest!.questions.length) {
      _currentQuestionIndex = index;
      notifyListeners();
    }
  }

  void nextQuestion() {
    if (_activeTest != null && _currentQuestionIndex < _activeTest!.questions.length - 1) {
      _currentQuestionIndex++;
      notifyListeners();
    }
  }

  void prevQuestion() {
    if (_currentQuestionIndex > 0) {
      _currentQuestionIndex--;
      notifyListeners();
    }
  }

  Future<bool> submitTest() async {
    if (_activeTest == null) return false;
    _countdownTimer?.cancel();

    try {
      _isLoading = true;
      notifyListeners();

      List<Map<String, dynamic>> answersList = [];
      for (var q in _activeTest!.questions) {
        int qId = q.id ?? 0;
        answersList.add({
          'question_id': qId,
          'selected_option': _userAnswers[qId],
          'time_spent_seconds': 10,
        });
      }

      final response = await ApiClient.post(
        ApiEndpoints.submitTest,
        body: {
          'test_id': _activeTest!.testId,
          'answers': answersList,
          'time_taken_seconds': (_activeTest!.totalQuestions * 60) - _remainingSeconds,
        },
      );

      if (response.isSuccess && response.data != null) {
        _completedResult = TestResultModel.fromJson(response.data as Map<String, dynamic>);
        _activeTest = null;
        fetchHistory();
        notifyListeners();
        return true;
      } else {
        _errorMessage = response.errorMessage ?? 'चाचणी सबमिट करण्यात त्रुटी.';
        return false;
      }
    } catch (e) {
      _errorMessage = 'सबमिट त्रुटी: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }
}
