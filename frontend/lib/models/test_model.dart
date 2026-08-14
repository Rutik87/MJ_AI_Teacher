class MCQQuestionModel {
  final int? id;
  final String questionText;
  final String optionA;
  final String optionB;
  final String optionC;
  final String optionD;
  final String correctOption;
  final String explanationMr;
  final String difficulty;
  final String? topicName;
  final String? subjectName;
  final String? sourceBook;
  final int? sourcePage;
  String? selectedOption;

  MCQQuestionModel({
    this.id,
    required this.questionText,
    required this.optionA,
    required this.optionB,
    required this.optionC,
    required this.optionD,
    required this.correctOption,
    required this.explanationMr,
    required this.difficulty,
    this.topicName,
    this.subjectName,
    this.sourceBook,
    this.sourcePage,
    this.selectedOption,
  });

  factory MCQQuestionModel.fromJson(Map<String, dynamic> json) {
    return MCQQuestionModel(
      id: json['id'] ?? json['question_id'],
      questionText: json['question_text'] ?? '',
      optionA: json['option_a'] ?? '',
      optionB: json['option_b'] ?? '',
      optionC: json['option_c'] ?? '',
      optionD: json['option_d'] ?? '',
      correctOption: json['correct_option'] ?? 'A',
      explanationMr: json['explanation_mr'] ?? '',
      difficulty: json['difficulty'] ?? 'medium',
      topicName: json['topic_name'],
      subjectName: json['subject_name'],
      sourceBook: json['source_book'] ?? json['source_book_name'],
      sourcePage: json['source_page'],
      selectedOption: json['selected_option'],
    );
  }
}

class TestResultModel {
  final int testId;
  final String title;
  final String subjectName;
  final int totalQuestions;
  final double score;
  final int correctCount;
  final int wrongCount;
  final int unattemptedCount;
  final double accuracyPercentage;
  final int timeTakenSeconds;
  final List<String> weakAreas;
  final List<MCQQuestionModel> questions;

  TestResultModel({
    required this.testId,
    required this.title,
    required this.subjectName,
    required this.totalQuestions,
    required this.score,
    required this.correctCount,
    required this.wrongCount,
    required this.unattemptedCount,
    required this.accuracyPercentage,
    required this.timeTakenSeconds,
    required this.weakAreas,
    required this.questions,
  });

  factory TestResultModel.fromJson(Map<String, dynamic> json) {
    var rawQuestions = json['questions'] as List? ?? [];
    List<MCQQuestionModel> qs = rawQuestions
        .map((q) => MCQQuestionModel.fromJson(q as Map<String, dynamic>))
        .toList();

    var rawWeak = json['weak_areas'] as List? ?? [];
    List<String> weaks = rawWeak.map((w) => w.toString()).toList();

    return TestResultModel(
      testId: json['test_id'] ?? 0,
      title: json['title'] ?? 'MPSC चाचणी',
      subjectName: json['subject_name'] ?? 'इतिहास',
      totalQuestions: json['total_questions'] ?? 0,
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      correctCount: json['correct_count'] ?? 0,
      wrongCount: json['wrong_count'] ?? 0,
      unattemptedCount: json['unattempted_count'] ?? 0,
      accuracyPercentage: (json['accuracy_percentage'] as num?)?.toDouble() ?? 0.0,
      timeTakenSeconds: json['time_taken_seconds'] ?? 0,
      weakAreas: weaks,
      questions: qs,
    );
  }
}
