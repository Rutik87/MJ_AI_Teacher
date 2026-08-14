class SubjectMasteryModel {
  final String subjectName;
  final int attempted;
  final int correct;
  final double masteryPercentage;
  final bool isWeakArea;
  final String recommendationMr;

  SubjectMasteryModel({
    required this.subjectName,
    required this.attempted,
    required this.correct,
    required this.masteryPercentage,
    required this.isWeakArea,
    required this.recommendationMr,
  });

  factory SubjectMasteryModel.fromJson(Map<String, dynamic> json) {
    return SubjectMasteryModel(
      subjectName: json['subject_name'] ?? 'General',
      attempted: json['attempted'] ?? 0,
      correct: json['correct'] ?? 0,
      masteryPercentage: (json['mastery_percentage'] as num?)?.toDouble() ?? 0.0,
      isWeakArea: json['is_weak_area'] ?? false,
      recommendationMr: json['recommendation_mr'] ?? '',
    );
  }
}

class ProgressModel {
  final int totalStudyMinutes;
  final int totalBooksRead;
  final int totalTestsTaken;
  final double overallAccuracy;
  final List<SubjectMasteryModel> subjectsMastery;
  final List<String> weakAreas;
  final List<Map<String, dynamic>> recentActivities;

  ProgressModel({
    required this.totalStudyMinutes,
    required this.totalBooksRead,
    required this.totalTestsTaken,
    required this.overallAccuracy,
    required this.subjectsMastery,
    required this.weakAreas,
    required this.recentActivities,
  });

  factory ProgressModel.fromJson(Map<String, dynamic> json) {
    var rawSubjects = json['subjects_mastery'] as List? ?? [];
    List<SubjectMasteryModel> mastery = rawSubjects
        .map((s) => SubjectMasteryModel.fromJson(s as Map<String, dynamic>))
        .toList();

    var rawWeak = json['weak_areas'] as List? ?? [];
    List<String> weaks = rawWeak.map((w) => w.toString()).toList();

    var rawActs = json['recent_activities'] as List? ?? [];
    List<Map<String, dynamic>> acts = rawActs
        .map((a) => Map<String, dynamic>.from(a as Map))
        .toList();

    return ProgressModel(
      totalStudyMinutes: json['total_study_minutes'] ?? 0,
      totalBooksRead: json['total_books_read'] ?? 0,
      totalTestsTaken: json['total_tests_taken'] ?? 0,
      overallAccuracy: (json['overall_accuracy'] as num?)?.toDouble() ?? 0.0,
      subjectsMastery: mastery,
      weakAreas: weaks,
      recentActivities: acts,
    );
  }
}
