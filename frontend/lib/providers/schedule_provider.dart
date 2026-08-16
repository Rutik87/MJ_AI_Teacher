import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';

class ScheduleSlotModel {
  String timeSlot;
  String subject;
  String topic;
  String activity;

  ScheduleSlotModel({
    required this.timeSlot,
    required this.subject,
    required this.topic,
    required this.activity,
  });

  factory ScheduleSlotModel.fromJson(Map<String, dynamic> json) {
    return ScheduleSlotModel(
      timeSlot: json['time_slot'] ?? '',
      subject: json['subject'] ?? '',
      topic: json['topic'] ?? '',
      activity: json['activity'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'time_slot': timeSlot,
        'subject': subject,
        'topic': topic,
        'activity': activity,
      };
}

class ScheduleProvider extends ChangeNotifier {
  String _targetExam = 'MPSC राज्यसेवा / संयुक्त पूर्व परीक्षा';
  String _examDate = '2026-11-15';
  double _dailyStudyHours = 6.0;
  List<String> _primarySubjects = ['इतिहास', 'राज्यशास्त्र', 'भूगोल', 'अर्थशास्त्र'];
  List<ScheduleSlotModel> _slots = [];
  String? _aiAnalysisMarkdown;
  bool _isLoading = false;
  bool _isAnalyzing = false;
  String? _errorMessage;

  String get targetExam => _targetExam;
  String get examDate => _examDate;
  double get dailyStudyHours => _dailyStudyHours;
  List<String> get primarySubjects => _primarySubjects;
  List<ScheduleSlotModel> get slots => _slots;
  String? get aiAnalysisMarkdown => _aiAnalysisMarkdown;
  bool get isLoading => _isLoading;
  bool get isAnalyzing => _isAnalyzing;
  String? get errorMessage => _errorMessage;

  ScheduleProvider() {
    fetchSchedule();
  }

  Future<void> fetchSchedule() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiClient.get(ApiEndpoints.schedule);
      if (response.isSuccess && response.data is Map<String, dynamic>) {
        final data = response.data as Map<String, dynamic>;
        _targetExam = data['target_exam'] ?? _targetExam;
        _examDate = data['exam_date'] ?? _examDate;
        _dailyStudyHours = (data['daily_study_hours'] as num?)?.toDouble() ?? _dailyStudyHours;
        if (data['primary_subjects'] is List) {
          _primarySubjects = (data['primary_subjects'] as List).map((s) => s.toString()).toList();
        }
        if (data['slots'] is List) {
          _slots = (data['slots'] as List)
              .map((s) => ScheduleSlotModel.fromJson(s as Map<String, dynamic>))
              .toList();
        }
      }
    } catch (e) {
      _errorMessage = 'नियोजन लोड करताना त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void addSlot(ScheduleSlotModel slot) {
    _slots.add(slot);
    saveSchedule();
    notifyListeners();
  }

  void removeSlot(int index) {
    if (index >= 0 && index < _slots.length) {
      _slots.removeAt(index);
      saveSchedule();
      notifyListeners();
    }
  }

  void updateSlot(int index, ScheduleSlotModel slot) {
    if (index >= 0 && index < _slots.length) {
      _slots[index] = slot;
      saveSchedule();
      notifyListeners();
    }
  }

  void updateTargetExam(String exam, double hours, String date) {
    _targetExam = exam;
    _dailyStudyHours = hours;
    _examDate = date;
    saveSchedule();
    notifyListeners();
  }

  Future<void> saveSchedule() async {
    try {
      final payload = {
        'user_id': 1,
        'target_exam': _targetExam,
        'exam_date': _examDate,
        'daily_study_hours': _dailyStudyHours,
        'primary_subjects': _primarySubjects,
        'slots': _slots.map((s) => s.toJson()).toList(),
      };
      await ApiClient.post(ApiEndpoints.schedule, body: payload);
    } catch (e) {
      debugPrint('[ScheduleProvider] Save error: $e');
    }
  }

  Future<void> analyzeScheduleWithChatGPT({List<String>? weakSubjects}) async {
    _isAnalyzing = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final payload = {
        'user_id': 1,
        'target_exam': _targetExam,
        'daily_study_hours': _dailyStudyHours,
        'exam_date': _examDate,
        'weak_subjects': weakSubjects ?? ['अर्थशास्त्र', 'विज्ञान व तंत्रज्ञान'],
        'current_schedule': _slots.map((s) => '${s.timeSlot}: ${s.subject} (${s.topic})').join('; '),
      };

      final response = await ApiClient.post(ApiEndpoints.scheduleAnalyze, body: payload);
      if (response.isSuccess && response.data != null) {
        _aiAnalysisMarkdown = response.data['analysis_markdown'];
      } else {
        _errorMessage = response.errorMessage ?? 'विश्लेषण मिळवताना त्रुटी आली.';
      }
    } catch (e) {
      _errorMessage = 'विश्लेषण त्रुटी: $e';
    } finally {
      _isAnalyzing = false;
      notifyListeners();
    }
  }
}
