import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class SpeechService extends ChangeNotifier {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  bool _isAvailable = false;
  String _recognizedWords = '';
  String _currentLocaleId = 'mr_IN';

  bool get isListening => _isListening;
  bool get isAvailable => _isAvailable;
  String get recognizedWords => _recognizedWords;

  Future<bool> initSpeech() async {
    try {
      _isAvailable = await _speech.initialize(
        onStatus: (status) {
          if (status == 'done' || status == 'notListening') {
            _isListening = false;
            notifyListeners();
          }
        },
        onError: (errorNotification) {
          debugPrint('Speech recognition error: $errorNotification');
          _isListening = false;
          notifyListeners();
        },
      );
      notifyListeners();
      return _isAvailable;
    } catch (e) {
      debugPrint('Speech init failed: $e');
      _isAvailable = false;
      return false;
    }
  }

  Future<void> startListening({Function(String)? onResult}) async {
    if (!_isAvailable) {
      bool initialized = await initSpeech();
      if (!initialized) return;
    }

    _recognizedWords = '';
    _isListening = true;
    notifyListeners();

    try {
      await _speech.listen(
        localeId: _currentLocaleId,
        onResult: (result) {
          _recognizedWords = result.recognizedWords;
          if (onResult != null) {
            onResult(_recognizedWords);
          }
          notifyListeners();
        },
      );
    } catch (e) {
      debugPrint('Start listening error: $e');
      _isListening = false;
      notifyListeners();
    }
  }

  Future<void> stopListening() async {
    await _speech.stop();
    _isListening = false;
    notifyListeners();
  }
}
