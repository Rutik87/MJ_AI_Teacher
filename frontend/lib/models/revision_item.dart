class RevisionItemModel {
  final int id;
  final String title;
  final String keyFact;
  final String subjectName;
  final String? topicName;
  final String? sourceBook;
  final int? sourcePage;
  final int repetitionCount;
  final int intervalDays;
  final int confidenceLevel;
  final String lastReviewed;
  final String nextReviewDue;
  final bool isDue;

  RevisionItemModel({
    required this.id,
    required this.title,
    required this.keyFact,
    required this.subjectName,
    this.topicName,
    this.sourceBook,
    this.sourcePage,
    required this.repetitionCount,
    required this.intervalDays,
    required this.confidenceLevel,
    required this.lastReviewed,
    required this.nextReviewDue,
    required this.isDue,
  });

  factory RevisionItemModel.fromJson(Map<String, dynamic> json) {
    return RevisionItemModel(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      keyFact: json['key_fact'] ?? '',
      subjectName: json['subject_name'] ?? 'इतिहास',
      topicName: json['topic_name'],
      sourceBook: json['source_book'],
      sourcePage: json['source_page'],
      repetitionCount: json['repetition_count'] ?? 0,
      intervalDays: json['interval_days'] ?? 1,
      confidenceLevel: json['confidence_level'] ?? 1,
      lastReviewed: json['last_reviewed'] ?? '',
      nextReviewDue: json['next_review_due'] ?? '',
      isDue: json['is_due'] ?? false,
    );
  }
}

class RevisionSummaryModel {
  final int totalItems;
  final int dueTodayCount;
  final int masteredCount;
  final List<RevisionItemModel> dueItems;

  RevisionSummaryModel({
    required this.totalItems,
    required this.dueTodayCount,
    required this.masteredCount,
    required this.dueItems,
  });

  factory RevisionSummaryModel.fromJson(Map<String, dynamic> json) {
    var rawItems = json['due_items'] as List? ?? [];
    List<RevisionItemModel> items = rawItems
        .map((i) => RevisionItemModel.fromJson(i as Map<String, dynamic>))
        .toList();

    return RevisionSummaryModel(
      totalItems: json['total_items'] ?? 0,
      dueTodayCount: json['due_today_count'] ?? 0,
      masteredCount: json['mastered_count'] ?? 0,
      dueItems: items,
    );
  }
}
