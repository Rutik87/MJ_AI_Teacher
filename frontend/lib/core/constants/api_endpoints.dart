import 'package:frontend/core/config/app_config.dart';

class ApiEndpoints {
  static String get baseUrl => AppConfig.apiBaseUrl;

  static String get health => '$baseUrl/health';
  static String get subjects => '$baseUrl/subjects';
  static String get books => '$baseUrl/books';
  static String bookStatus(int id) => '$baseUrl/books/$id/status';
  static String bookPdf(int id) => '$baseUrl/books/$id/pdf';
  static String bookPage(int id, int page) => '$baseUrl/books/$id/pages/$page';
  static String bookReindex(int id) => '$baseUrl/books/$id/reindex';

  static String get chatSessions => '$baseUrl/chat/sessions';
  static String get chatMessage => '$baseUrl/chat/message';
  static String chatSessionMessages(int id) => '$baseUrl/chat/sessions/$id/messages';

  static String get schedule => '$baseUrl/schedule';
  static String get scheduleAnalyze => '$baseUrl/schedule/analyze';

  static String get teacherTeach => '$baseUrl/teacher/teach';
  static String get teacherExamFocus => '$baseUrl/teacher/exam-focus';

  static String get generateMcqs => '$baseUrl/tests/generate-mcqs';
  static String get createTest => '$baseUrl/tests/create';
  static String testDetail(int id) => '$baseUrl/tests/$id';
  static String get submitTest => '$baseUrl/tests/submit';
  static String get testHistory => '$baseUrl/tests/history/all';
  static String get pyqAnalysis => '$baseUrl/tests/pyq-analysis';

  static String get revisionSummary => '$baseUrl/revision/summary';
  static String get revisionAdd => '$baseUrl/revision/add';
  static String get revisionReview => '$baseUrl/revision/review';

  static String get progressSummary => '$baseUrl/progress/summary';

  static String get voiceTranscribe => '$baseUrl/voice/transcribe';
  static String get voiceSpeak => '$baseUrl/voice/speak';
  static String voiceAudio(String filename) => '$baseUrl/voice/audio/$filename';

  static String get settings => '$baseUrl/settings';

  static String get currentAffairs => '$baseUrl/current-affairs/';
  static String get currentAffairsRefresh => '$baseUrl/current-affairs/refresh';
  static String get currentAffairsQuiz => '$baseUrl/current-affairs/quiz';
  static String currentAffairBookmark(int id) => '$baseUrl/current-affairs/$id/bookmark';

  static String get mjConverse => '$baseUrl/mj/converse';

  static String notesGenerate(int bookId) => '$baseUrl/notes/generate/$bookId';
  static String notesStatus(int bookId) => '$baseUrl/notes/$bookId';
  static String notesDownload(int bookId) => '$baseUrl/notes/$bookId/download';
  static String notesMarkdown(int bookId) => '$baseUrl/notes/$bookId/markdown';
  static String notesDelete(int bookId) => '$baseUrl/notes/$bookId';
}
