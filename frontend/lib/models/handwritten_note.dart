class NoteConceptModel {
  final String titleMr;
  final String explanationMr;

  NoteConceptModel({
    required this.titleMr,
    required this.explanationMr,
  });

  factory NoteConceptModel.fromJson(Map<String, dynamic> json) {
    return NoteConceptModel(
      titleMr: json['title_mr'] ?? '',
      explanationMr: json['explanation_mr'] ?? '',
    );
  }
}

class NoteTableModel {
  final String titleMr;
  final List<String> headers;
  final List<List<dynamic>> rows;

  NoteTableModel({
    required this.titleMr,
    required this.headers,
    required this.rows,
  });

  factory NoteTableModel.fromJson(Map<String, dynamic> json) {
    var rawHeaders = (json['headers'] as List? ?? []).map((e) => e.toString()).toList();
    var rawRows = (json['rows'] as List? ?? []).map((r) => (r as List? ?? []).map((c) => c.toString()).toList()).toList();
    return NoteTableModel(
      titleMr: json['title_mr'] ?? 'तुलनात्मक तक्ता',
      headers: rawHeaders,
      rows: rawRows,
    );
  }
}

class NoteChapterModel {
  final int chapterNumber;
  final String headingMr;
  final String subheadingMr;
  final String shortDefinitionMr;
  final List<NoteConceptModel> importantConcepts;
  final List<String> keyPoints;
  final List<String> examples;
  final List<String> formulasOrLaws;
  final NoteTableModel? table;
  final List<String> flowchartSteps;
  final List<String> examPoints;
  final List<String> quickRevisionBox;
  final List<String> commonMistakes;

  NoteChapterModel({
    required this.chapterNumber,
    required this.headingMr,
    required this.subheadingMr,
    required this.shortDefinitionMr,
    required this.importantConcepts,
    required this.keyPoints,
    required this.examples,
    required this.formulasOrLaws,
    this.table,
    required this.flowchartSteps,
    required this.examPoints,
    required this.quickRevisionBox,
    required this.commonMistakes,
  });

  factory NoteChapterModel.fromJson(Map<String, dynamic> json) {
    var rawConcepts = (json['important_concepts'] as List? ?? [])
        .map((c) => NoteConceptModel.fromJson(c as Map<String, dynamic>))
        .toList();

    NoteTableModel? parsedTable;
    if (json['table'] != null && json['table'] is Map) {
      parsedTable = NoteTableModel.fromJson(json['table'] as Map<String, dynamic>);
    }

    return NoteChapterModel(
      chapterNumber: json['chapter_number'] ?? 1,
      headingMr: json['heading_mr'] ?? '',
      subheadingMr: json['subheading_mr'] ?? '',
      shortDefinitionMr: json['short_definition_mr'] ?? '',
      importantConcepts: rawConcepts,
      keyPoints: (json['key_points'] as List? ?? []).map((e) => e.toString()).toList(),
      examples: (json['examples'] as List? ?? []).map((e) => e.toString()).toList(),
      formulasOrLaws: (json['formulas_or_laws'] as List? ?? []).map((e) => e.toString()).toList(),
      table: parsedTable,
      flowchartSteps: (json['flowchart_steps'] as List? ?? []).map((e) => e.toString()).toList(),
      examPoints: (json['exam_points'] as List? ?? []).map((e) => e.toString()).toList(),
      quickRevisionBox: (json['quick_revision_box'] as List? ?? []).map((e) => e.toString()).toList(),
      commonMistakes: (json['common_mistakes'] as List? ?? []).map((e) => e.toString()).toList(),
    );
  }
}

class HandwrittenNoteModel {
  final int? noteId;
  final int bookId;
  final String title;
  final String status; // 'pending', 'reading', 'analyzing', 'formatting', 'completed', 'failed', 'not_generated'
  final bool hasNotes;
  final double progressPercent;
  final String progressMessage;
  final int chapterCount;
  final int pageCount;
  final String? pdfUrl;
  final String? markdownContent;
  final String? errorMessage;
  final List<NoteChapterModel> chapters;

  HandwrittenNoteModel({
    this.noteId,
    required this.bookId,
    required this.title,
    required this.status,
    required this.hasNotes,
    required this.progressPercent,
    required this.progressMessage,
    required this.chapterCount,
    required this.pageCount,
    this.pdfUrl,
    this.markdownContent,
    this.errorMessage,
    required this.chapters,
  });

  factory HandwrittenNoteModel.fromJson(Map<String, dynamic> json) {
    var rawChapters = (json['chapters'] as List? ?? [])
        .map((c) => NoteChapterModel.fromJson(c as Map<String, dynamic>))
        .toList();

    return HandwrittenNoteModel(
      noteId: json['note_id'],
      bookId: json['book_id'] ?? 0,
      title: json['title'] ?? 'Handwritten Notes',
      status: json['status'] ?? 'not_generated',
      hasNotes: json['has_notes'] ?? (json['status'] == 'completed'),
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0.0,
      progressMessage: json['progress_message'] ?? '',
      chapterCount: json['chapter_count'] ?? rawChapters.length,
      pageCount: json['page_count'] ?? 0,
      pdfUrl: json['pdf_url'],
      markdownContent: json['markdown_content'],
      errorMessage: json['error_message'],
      chapters: rawChapters,
    );
  }
}
