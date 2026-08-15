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
  final int totalQuestionsSolved;
  final int streakDays;
  final double preparationPercentage;
  final double overallAccuracy;
  final int totalBookmarks;
  final int dueRevisionCount;
  final List<SubjectMasteryModel> subjectsMastery;
  final List<String> weakAreas;
  final List<Map<String, dynamic>> recentActivities;
  final List<double> weeklyStudyHours;

  ProgressModel({
    required this.totalStudyMinutes,
    required this.totalBooksRead,
    required this.totalTestsTaken,
    required this.totalQuestionsSolved,
    required this.streakDays,
    required this.preparationPercentage,
    required this.overallAccuracy,
    required this.totalBookmarks,
    required this.dueRevisionCount,
    required this.subjectsMastery,
    required this.weakAreas,
    required this.recentActivities,
    required this.weeklyStudyHours,
  });

  factory ProgressModel.empty() {
    return ProgressModel(
      totalStudyMinutes: 0,
      totalBooksRead: 0,
      totalTestsTaken: 0,
      totalQuestionsSolved: 0,
      streakDays: 0,
      preparationPercentage: 0.0,
      overallAccuracy: 0.0,
      totalBookmarks: 0,
      dueRevisionCount: 0,
      subjectsMastery: [],
      weakAreas: [],
      recentActivities: [],
      weeklyStudyHours: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    );
  }

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

    var rawHours = json['weekly_study_hours'] as List? ?? [];
    List<double> hours = rawHours.map((h) => (h as num).toDouble()).toList();
    if (hours.length < 7) {
      hours = List<double>.filled(7, 0.0);
    }

    return ProgressModel(
      totalStudyMinutes: json['total_study_minutes'] ?? 0,
      totalBooksRead: json['total_books_read'] ?? 0,
      totalTestsTaken: json['total_tests_taken'] ?? 0,
      totalQuestionsSolved: json['total_questions_solved'] ?? 0,
      streakDays: json['streak_days'] ?? 0,
      preparationPercentage: (json['preparation_percentage'] as num?)?.toDouble() ?? 0.0,
      overallAccuracy: (json['overall_accuracy'] as num?)?.toDouble() ?? 0.0,
      totalBookmarks: json['total_bookmarks'] ?? 0,
      dueRevisionCount: json['due_revision_count'] ?? 0,
      subjectsMastery: mastery,
      weakAreas: weaks,
      recentActivities: acts,
      weeklyStudyHours: hours,
    );
  }
}
