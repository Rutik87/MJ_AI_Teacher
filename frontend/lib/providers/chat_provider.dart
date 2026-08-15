import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/models/chat_message.dart';

class ChatProvider extends ChangeNotifier {
  List<ChatMessageModel> _messages = [];
  List<ChatSessionModel> _sessions = [];
  int? _currentSessionId;
  String _currentMode = 'general_chat'; // general_chat, teacher_mode, exam_mode, pyq_analysis
  int? _selectedBookFilter;
  bool _isLoading = false;
  String? _errorMessage;

  List<ChatMessageModel> get messages => _messages;
  List<ChatSessionModel> get sessions => _sessions;
  int? get currentSessionId => _currentSessionId;
  String get currentMode => _currentMode;
  int? get selectedBookFilter => _selectedBookFilter;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  ChatProvider() {
    fetchSessions();
  }

  void setMode(String mode) {
    _currentMode = mode;
    notifyListeners();
  }

  void setBookFilter(int? bookId) {
    _selectedBookFilter = bookId;
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

  Future<void> startNewSession({String title = 'नवीन चर्चा', String mode = 'general_chat'}) async {
    _currentSessionId = null;
    _currentMode = mode;
    _messages = [];
    notifyListeners();
  }

  Future<void> sendMessage(
    String text, {
    AudioService? audioService,
    bool autoPlay = true,
  }) async {
    if (text.trim().isEmpty) return;

    // Add user message to UI immediately
    final tempUserMsg = ChatMessageModel(
      id: DateTime.now().millisecondsSinceEpoch,
      sender: 'user',
      message: text,
      sources: [],
      mode: _currentMode,
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
          'message': text,
          'mode': _currentMode,
          'book_id': _selectedBookFilter,
        },
      );

      if (response.isSuccess && response.data != null) {
        final aiMsg = ChatMessageModel.fromJson(response.data as Map<String, dynamic>);
        _messages.add(aiMsg);
        fetchSessions(); // update session list
        notifyListeners();

        // Automatic playback using single authorized MJ voice (mj_primary)
        if (autoPlay && audioService != null) {
          try {
            if (aiMsg.audioUrl != null && aiMsg.audioUrl!.isNotEmpty) {
              await audioService.playAudioUrl(aiMsg.audioUrl!);
            } else {
              await audioService.speakText(aiMsg.message, emotion: 'friendly');
            }
          } catch (playbackErr) {
            debugPrint('[ChatProvider] Auto-play notice: $playbackErr');
          }
        }
      } else {
        _errorMessage = response.errorMessage ?? 'AI उत्तरामध्ये त्रुटी आली.';
      }
    } catch (e) {
      _errorMessage = 'संपर्क त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> teachTopic(String topic, {String subject = 'इतिहास', String difficulty = 'medium'}) async {
    _isLoading = true;
    _currentMode = 'teacher_mode';
    notifyListeners();

    try {
      final response = await ApiClient.post(
        ApiEndpoints.teacherTeach,
        body: {
          'topic': topic,
          'subject': subject,
          'difficulty': difficulty,
        },
      );

      if (response.isSuccess && response.data != null) {
        final data = response.data;
        var rawSources = data['sources'] as List? ?? [];
        List<SourceCitationModel> citations = rawSources
            .map((s) => SourceCitationModel.fromJson(s as Map<String, dynamic>))
            .toList();

        final lessonMsg = ChatMessageModel(
          id: DateTime.now().millisecondsSinceEpoch,
          sender: 'ai',
          message: data['lesson_markdown'] ?? '',
          sources: citations,
          mode: 'teacher_mode',
          hasAudio: false,
          createdAt: DateTime.now().toIso8601String(),
        );
        _messages.add(lessonMsg);
      }
    } catch (e) {
      _errorMessage = 'शिक्षक मोड त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
