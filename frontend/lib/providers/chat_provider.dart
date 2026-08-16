import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/models/chat_message.dart';

class ChatProvider extends ChangeNotifier {
  List<ChatMessageModel> _messages = [];
  List<ChatSessionModel> _sessions = [];
  int? _currentSessionId;
  List<BookModel> _attachedBooks = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<ChatMessageModel> get messages => _messages;
  List<ChatSessionModel> get sessions => _sessions;
  int? get currentSessionId => _currentSessionId;
  List<BookModel> get attachedBooks => _attachedBooks;
  bool get hasAttachments => _attachedBooks.isNotEmpty;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  ChatProvider() {
    fetchSessions();
  }

  void attachBook(BookModel book) {
    if (!_attachedBooks.any((b) => b.id == book.id)) {
      _attachedBooks.add(book);
      notifyListeners();
    }
  }

  void removeAttachedBook(int bookId) {
    _attachedBooks.removeWhere((b) => b.id == bookId);
    notifyListeners();
  }

  void clearAttachedBooks() {
    _attachedBooks.clear();
    notifyListeners();
  }

  Future<void> fetchSessions() async {
    try {
      final response = await ApiClient.get(ApiEndpoints.chatSessions);
      if (response.isSuccess && response.data is List) {
        _sessions = (response.data as List)
            .map((item) => ChatSessionModel.fromJson(item as Map<String, dynamic>))
            .toList();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Fetch sessions error: $e');
    }
  }

  Future<void> loadSession(int sessionId) async {
    try {
      _isLoading = true;
      _currentSessionId = sessionId;
      _messages = [];
      _errorMessage = null;
      notifyListeners();

      final response = await ApiClient.get(ApiEndpoints.chatSessionMessages(sessionId));
      if (response.isSuccess && response.data is List) {
        _messages = (response.data as List)
            .map((item) => ChatMessageModel.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      _errorMessage = 'संभाषण लोड करण्यात त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> startNewSession({String title = 'नवीन चर्चा', BookModel? initialBook}) async {
    _currentSessionId = null;
    _attachedBooks.clear();
    if (initialBook != null) {
      _attachedBooks.add(initialBook);
    }
    _messages = [];
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> deleteSession(int sessionId) async {
    try {
      await ApiClient.delete('${ApiEndpoints.baseUrl}/chat/sessions/$sessionId');
      _sessions.removeWhere((s) => s.id == sessionId);
      if (_currentSessionId == sessionId) {
        startNewSession();
      }
      notifyListeners();
    } catch (e) {
      debugPrint('Delete session error: $e');
    }
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final tempUserMsg = ChatMessageModel(
      id: DateTime.now().millisecondsSinceEpoch,
      sender: 'user',
      message: text.trim(),
      sources: [],
      mode: 'general_chat',
      hasAudio: false,
      createdAt: DateTime.now().toIso8601String(),
    );
    _messages.add(tempUserMsg);
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final payload = {
        'session_id': _currentSessionId,
        'message': text.trim(),
        'mode': 'general_chat',
        'book_ids': _attachedBooks.map((b) => b.id).toList(),
      };

      final response = await ApiClient.post(
        ApiEndpoints.chatMessage,
        body: payload,
      );

      if (response.isSuccess && response.data != null) {
        final data = response.data as Map<String, dynamic>;
        final aiMsg = ChatMessageModel.fromJson(data);
        _messages.add(aiMsg);
        if (data['session_id'] != null) {
          _currentSessionId = data['session_id'];
        }
        fetchSessions();
      } else {
        _errorMessage = response.errorMessage ?? 'ChatGPT कडून प्रतिसाद मिळाला नाही.';
      }
    } catch (e) {
      _errorMessage = 'संपर्क त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>?> generateArtifact({
    required String title,
    required String content,
    required String artifactType, // 'pdf' or 'txt'
    int? sourceBookId,
  }) async {
    try {
      final payload = {
        'session_id': _currentSessionId,
        'source_book_id': sourceBookId ?? (_attachedBooks.isNotEmpty ? _attachedBooks.first.id : null),
        'title': title,
        'content': content,
        'artifact_type': artifactType,
      };

      final response = await ApiClient.post(
        '${ApiEndpoints.baseUrl}/chat/generate-artifact',
        body: payload,
      );

      if (response.isSuccess && response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      debugPrint('Generate artifact error: $e');
      return null;
    }
  }
}
