import 'package:flutter/foundation.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';

enum MJPlaybackState {
  idle,
  preparing,
  playing,
  finished,
  error,
}

class AudioService extends ChangeNotifier {
  final AudioPlayer _player = AudioPlayer();
  PlayerState _playerState = PlayerState.stopped;
  MJPlaybackState _mjState = MJPlaybackState.idle;
  String? _currentAudioUrl;
  String? _statusMessage;
  double _playbackSpeed = 1.0;
  bool _isLoading = false;

  PlayerState get playerState => _playerState;
  MJPlaybackState get mjState => _mjState;
  bool get isPlaying => _playerState == PlayerState.playing;
  bool get isLoading => _isLoading;
  double get playbackSpeed => _playbackSpeed;
  String? get currentAudioUrl => _currentAudioUrl;
  String? get statusMessage => _statusMessage;

  AudioService() {
    _player.onPlayerStateChanged.listen((state) {
      _playerState = state;
      if (state == PlayerState.playing) {
        _mjState = MJPlaybackState.playing;
        _statusMessage = "MJ बोलत आहे... 🔊";
      } else if (state == PlayerState.completed) {
        _mjState = MJPlaybackState.finished;
        _statusMessage = "पूर्ण झाले";
      } else if (state == PlayerState.stopped) {
        if (_mjState != MJPlaybackState.error) {
          _mjState = MJPlaybackState.idle;
          _statusMessage = null;
        }
      }
      notifyListeners();
    });
  }

  /// Resolves relative or full audio URL to a fully qualified URL.
  String resolveAudioUrl(String url) {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }

    String base = ApiEndpoints.baseUrl.trim();
    // Strip trailing '/api' from base if the relative path already includes '/api'
    if (url.startsWith('/api') && base.endsWith('/api')) {
      base = base.substring(0, base.length - 4);
    }
    while (base.endsWith('/')) {
      base = base.substring(0, base.length - 1);
    }
    String cleanPath = url.startsWith('/') ? url : '/$url';
    return '$base$cleanPath';
  }

  /// Plays a direct audio URL returned from conversational endpoints (instant playback).
  Future<void> playAudioUrl(String relativeOrFullUrl, {double speed = 1.0}) async {
    try {
      _isLoading = true;
      _mjState = MJPlaybackState.preparing;
      _statusMessage = "आवाज तयार करत आहे...";
      notifyListeners();

      final fullUrl = resolveAudioUrl(relativeOrFullUrl);
      _currentAudioUrl = fullUrl;
      _playbackSpeed = speed;

      debugPrint('[AudioService] Playing MJ Voice from: $fullUrl');

      await _player.stop();
      await _player.setPlaybackRate(speed);
      await _player.play(UrlSource(fullUrl));
      
      _mjState = MJPlaybackState.playing;
      _statusMessage = "MJ बोलत आहे... 🔊";
    } catch (e) {
      debugPrint('[AudioService] Playback Error: $e');
      _mjState = MJPlaybackState.error;
      _statusMessage = "आवाज तयार करता आला नाही.";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Synthesizes text into speech on-demand using single MJ voice (mj_primary).
  Future<void> speakText(String text, {double speed = 1.0, String emotion = 'friendly'}) async {
    if (text.trim().isEmpty) return;
    try {
      _isLoading = true;
      _mjState = MJPlaybackState.preparing;
      _statusMessage = "आवाज तयार करत आहे...";
      notifyListeners();

      // Call backend unified TTS endpoint with mj_primary
      final response = await ApiClient.post(
        ApiEndpoints.voiceSpeak,
        body: {
          'text': text,
          'speed': speed,
          'lang': 'mr',
          'emotion': emotion,
          'voice_profile_id': 'mj_primary',
        },
      );

      if (response.isSuccess && response.data != null) {
        String? relativeUrl = response.data['audio_url'];
        if (relativeUrl != null && relativeUrl.isNotEmpty) {
          await playAudioUrl(relativeUrl, speed: speed);
          return;
        }
      }

      _mjState = MJPlaybackState.error;
      _statusMessage = "आवाज तयार करता आला नाही.";
    } catch (e) {
      debugPrint('[AudioService] speakText Error: $e');
      _mjState = MJPlaybackState.error;
      _statusMessage = "आवाज तयार करता आला नाही.";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> playPause() async {
    if (_playerState == PlayerState.playing) {
      await _player.pause();
    } else if (_playerState == PlayerState.paused && _currentAudioUrl != null) {
      await _player.resume();
    }
  }

  Future<void> stop() async {
    await _player.stop();
    _playerState = PlayerState.stopped;
    _mjState = MJPlaybackState.idle;
    _statusMessage = null;
    notifyListeners();
  }

  Future<void> setSpeed(double speed) async {
    _playbackSpeed = speed;
    await _player.setPlaybackRate(speed);
    notifyListeners();
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}
