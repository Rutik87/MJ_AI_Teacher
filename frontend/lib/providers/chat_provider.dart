import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/chat_message.dart';

class ChatProvider extends ChangeNotifier {
  List<ChatMessageModel> _messages = [];
  List<ChatSessionModel> _sessions = [];
  int? _currentSessionId;
  int? _selectedBookFilter;
  String? _selectedBookTitle;
  bool _isLoading = false;
  String? _errorMessage;

  List<ChatMessageModel> get messages => _messages;
  List<ChatSessionModel> get sessions => _sessions;
  int? get currentSessionId => _currentSessionId;
  int? get selectedBookFilter => _selectedBookFilter;
  String? get selectedBookTitle => _selectedBookTitle;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  ChatProvider() {
    fetchSessions();
  }

  void setBookFilter(int? bookId, {String? bookTitle}) {
    _selectedBookFilter = bookId;
    _selectedBookTitle = bookTitle;
    notifyListeners();
  }

  void clearBookFilter() {
    _selectedBookFilter = null;
    _selectedBookTitle = null;
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

  Future<void> startNewSession({String title = 'नवीन चर्चा', int? bookId, String? bookTitle}) async {
    _currentSessionId = null;
    _selectedBookFilter = bookId;
    _selectedBookTitle = bookTitle;
    _messages = [];
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> deleteSession(int sessionId) async {
    try {
      await ApiClient.delete(ApiEndpoints.chatSessionMessages(sessionId));
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

    // Add user message to UI immediately
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
      final response = await ApiClient.post(
        ApiEndpoints.chatMessage,
        body: {
          'session_id': _currentSessionId,
          'message': text.trim(),
          'mode': 'general_chat',
          'book_id': _selectedBookFilter,
        },
      );

      if (response.isSuccess && response.data != null) {
        final aiMsg = ChatMessageModel.fromJson(response.data as Map<String, dynamic>);
        _messages.add(aiMsg);
        fetchSessions(); // update session list
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
}
