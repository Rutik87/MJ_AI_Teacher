class CurrentAffairModel {
  final int id;
  final String titleMr;
  final String summaryMr;
  final String mpscRelevanceMr;
  final List<String> importantFacts;
  final String topic;
  final String sourceName;
  final String sourceUrl;
  final DateTime publishedAt;
  final DateTime updatedAt;
  final String verificationState; // 'verified', 'cross_checked', 'developing', 'unverified'
  final int importanceScore;
  bool isBookmarked;

  CurrentAffairModel({
    required this.id,
    required this.titleMr,
    required this.summaryMr,
    required this.mpscRelevanceMr,
    required this.importantFacts,
    required this.topic,
    required this.sourceName,
    required this.sourceUrl,
    required this.publishedAt,
    required this.updatedAt,
    required this.verificationState,
    required this.importanceScore,
    this.isBookmarked = false,
  });

  factory CurrentAffairModel.fromJson(Map<String, dynamic> json) {
    var rawFacts = json['important_facts'] as List? ?? [];
    List<String> parsedFacts = rawFacts.map((f) => f.toString()).toList();

    DateTime pubDate = DateTime.tryParse(json['published_at'] ?? '') ?? DateTime.now();
    DateTime upDate = DateTime.tryParse(json['updated_at'] ?? '') ?? DateTime.now();

    return CurrentAffairModel(
      id: json['id'] ?? 0,
      titleMr: json['title_mr'] ?? '',
      summaryMr: json['summary_mr'] ?? '',
      mpscRelevanceMr: json['mpsc_relevance_mr'] ?? '',
      importantFacts: parsedFacts,
      topic: json['topic'] ?? 'महाराष्ट्र',
      sourceName: json['source_name'] ?? 'शासकीय वृत्त',
      sourceUrl: json['source_url'] ?? '',
      publishedAt: pubDate,
      updatedAt: upDate,
      verificationState: json['verification_state'] ?? 'verified',
      importanceScore: json['importance_score'] ?? 5,
      isBookmarked: json['is_bookmarked'] ?? false,
    );
  }
}

class CurrentAffairMCQModel {
  final int id;
  final int articleId;
  final String questionMr;
  final String optionA;
  final String optionB;
  final String optionC;
  final String optionD;
  final String correctOption;
  final String explanationMr;

  CurrentAffairMCQModel({
    required this.id,
    required this.articleId,
    required this.questionMr,
    required this.optionA,
    required this.optionB,
    required this.optionC,
    required this.optionD,
    required this.correctOption,
    required this.explanationMr,
  });

  factory CurrentAffairMCQModel.fromJson(Map<String, dynamic> json) {
    return CurrentAffairMCQModel(
      id: json['id'] ?? 0,
      articleId: json['article_id'] ?? 0,
      questionMr: json['question_mr'] ?? '',
      optionA: json['option_a'] ?? '',
      optionB: json['option_b'] ?? '',
      optionC: json['option_c'] ?? '',
      optionD: json['option_d'] ?? '',
      correctOption: json['correct_option'] ?? 'A',
      explanationMr: json['explanation_mr'] ?? '',
    );
  }
}
