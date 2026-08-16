class BookModel {
  final int id;
  final String title;
  final String originalFilename;
  final int? subjectId;
  final String subjectName;
  final int totalPages;
  final int fileSizeBytes;
  final bool isScanned;
  final String status;
  final String statusMessage;
  final double progressPercent;
  final int currentPageProcessing;
  final int totalChunks;
  final String sourceType; // 'pdf', 'txt', 'image'
  final bool isGenerated;
  final int? sourceBookId;
  final int? chatSessionId;
  final bool isIndexed;
  final String createdAt;

  BookModel({
    required this.id,
    required this.title,
    required this.originalFilename,
    this.subjectId,
    required this.subjectName,
    required this.totalPages,
    required this.fileSizeBytes,
    required this.isScanned,
    required this.status,
    required this.statusMessage,
    required this.progressPercent,
    required this.currentPageProcessing,
    required this.totalChunks,
    this.sourceType = 'pdf',
    this.isGenerated = false,
    this.sourceBookId,
    this.chatSessionId,
    required this.isIndexed,
    required this.createdAt,
  });

  factory BookModel.fromJson(Map<String, dynamic> json) {
    final filename = json['original_filename']?.toString().toLowerCase() ?? '';
    String detectedType = json['source_type'] ?? 'pdf';
    if (filename.endsWith('.txt')) {
      detectedType = 'txt';
    } else if (filename.endsWith('.png') || filename.endsWith('.jpg') || filename.endsWith('.jpeg')) {
      detectedType = 'image';
    }

    return BookModel(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      originalFilename: json['original_filename'] ?? '',
      subjectId: json['subject_id'],
      subjectName: json['subject_name'] ?? 'General',
      totalPages: json['total_pages'] ?? 0,
      fileSizeBytes: json['file_size_bytes'] ?? 0,
      isScanned: json['is_scanned'] ?? false,
      status: json['status'] ?? 'pending',
      statusMessage: json['status_message'] ?? '',
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0.0,
      currentPageProcessing: json['current_page_processing'] ?? 0,
      totalChunks: json['total_chunks'] ?? 0,
      sourceType: detectedType,
      isGenerated: json['is_generated'] ?? false,
      sourceBookId: json['source_book_id'],
      chatSessionId: json['chat_session_id'],
      isIndexed: json['is_indexed'] ?? false,
      createdAt: json['created_at'] ?? '',
    );
  }

  String get formattedFileSize {
    if (fileSizeBytes <= 0) return '0 KB';
    final kb = fileSizeBytes / 1024;
    if (kb < 1024) return '${kb.toStringAsFixed(1)} KB';
    final mb = kb / 1024;
    return '${mb.toStringAsFixed(1)} MB';
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'original_filename': originalFilename,
        'subject_id': subjectId,
        'subject_name': subjectName,
        'total_pages': totalPages,
        'file_size_bytes': fileSizeBytes,
        'is_scanned': isScanned,
        'status': status,
        'status_message': statusMessage,
        'progress_percent': progressPercent,
        'current_page_processing': currentPageProcessing,
        'total_chunks': totalChunks,
        'source_type': sourceType,
        'is_generated': isGenerated,
        'source_book_id': sourceBookId,
        'chat_session_id': chatSessionId,
        'is_indexed': isIndexed,
        'created_at': createdAt,
      };
}
