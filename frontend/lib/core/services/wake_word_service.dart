import 'dart:async';
import 'package:flutter/foundation.dart';

enum MJVoiceState {
  idle,
  listening,
  processing,
  speaking,
  stopped,
}

class WakeWordService extends ChangeNotifier {
  MJVoiceState _state = MJVoiceState.idle;
  bool _isWakeWordActive = true;
  Timer? _conversationKeepAliveTimer;
  int _activeSecondsRemaining = 0;

  MJVoiceState get state => _state;
  bool get isWakeWordActive => _isWakeWordActive;
  int get activeSecondsRemaining => _activeSecondsRemaining;
  bool get isInActiveSession => _activeSecondsRemaining > 0;

  void setState(MJVoiceState newState) {
    _state = newState;
    notifyListeners();
  }

  void toggleWakeWord(bool enabled) {
    _isWakeWordActive = enabled;
    notifyListeners();
  }

  void startKeepAliveWindow({int durationSeconds = 25}) {
    _conversationKeepAliveTimer?.cancel();
    _activeSecondsRemaining = durationSeconds;
    notifyListeners();

    _conversationKeepAliveTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_activeSecondsRemaining > 0) {
        _activeSecondsRemaining--;
        notifyListeners();
      } else {
        timer.cancel();
        _state = MJVoiceState.idle;
        notifyListeners();
      }
    });
  }

  void resetKeepAlive() {
    _conversationKeepAliveTimer?.cancel();
    _activeSecondsRemaining = 0;
    _state = MJVoiceState.idle;
    notifyListeners();
  }

  bool isWakeWord(String text) {
    final lower = text.trim().toLowerCase();
    final triggers = ["are mj", "hey mj", "ऐक mj", "mj", "अरे mj", "हे mj"];
    return triggers.any((t) => lower.startsWith(t) || lower == t);
  }

  bool isInterruption(String text) {
    final lower = text.trim().toLowerCase();
    return lower.contains("थांब") || lower.contains("stop") || lower.contains("शांत");
  }

  @override
  void dispose() {
    _conversationKeepAliveTimer?.cancel();
    super.dispose();
  }
}
