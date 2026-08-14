class SourceCitationModel {
  final int bookId;
  final String bookName;
  final String? subjectName;
  final String? chapter;
  final int pageNumber;
  final String textSnippet;
  final double relevanceScore;

  SourceCitationModel({
    required this.bookId,
    required this.bookName,
    this.subjectName,
    this.chapter,
    required this.pageNumber,
    required this.textSnippet,
    required this.relevanceScore,
  });

  factory SourceCitationModel.fromJson(Map<String, dynamic> json) {
    return SourceCitationModel(
      bookId: json['book_id'] ?? 0,
      bookName: json['book_name'] ?? 'Study Material',
      subjectName: json['subject_name'],
      chapter: json['chapter'],
      pageNumber: json['page_number'] ?? 1,
      textSnippet: json['text_snippet'] ?? '',
      relevanceScore: (json['relevance_score'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ChatMessageModel {
  final int id;
  final String sender; // 'user' or 'ai'
  final String message;
  final List<SourceCitationModel> sources;
  final String mode;
  final bool hasAudio;
  final String? audioUrl;
  final String createdAt;

  ChatMessageModel({
    required this.id,
    required this.sender,
    required this.message,
    required this.sources,
    required this.mode,
    required this.hasAudio,
    this.audioUrl,
    required this.createdAt,
  });

  factory ChatMessageModel.fromJson(Map<String, dynamic> json) {
    var rawSources = json['sources'] as List? ?? [];
    List<SourceCitationModel> parsedSources = rawSources
        .map((s) => SourceCitationModel.fromJson(s as Map<String, dynamic>))
        .toList();

    return ChatMessageModel(
      id: json['id'] ?? 0,
      sender: json['sender'] ?? 'user',
      message: json['message'] ?? '',
      sources: parsedSources,
      mode: json['mode'] ?? 'general_chat',
      hasAudio: json['has_audio'] ?? false,
      audioUrl: json['audio_url'],
      createdAt: json['created_at'] ?? '',
    );
  }
}

class ChatSessionModel {
  final int id;
  final String title;
  final String mode;
  final String createdAt;

  ChatSessionModel({
    required this.id,
    required this.title,
    required this.mode,
    required this.createdAt,
  });

  factory ChatSessionModel.fromJson(Map<String, dynamic> json) {
    return ChatSessionModel(
      id: json['id'] ?? 0,
      title: json['title'] ?? 'नवीन चर्चा',
      mode: json['mode'] ?? 'general_chat',
      createdAt: json['created_at'] ?? '',
    );
  }
}
