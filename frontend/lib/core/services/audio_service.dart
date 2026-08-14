import 'package:flutter/foundation.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';

class AudioService extends ChangeNotifier {
  final AudioPlayer _player = AudioPlayer();
  PlayerState _playerState = PlayerState.stopped;
  String? _currentAudioUrl;
  double _playbackSpeed = 1.0;
  bool _isLoading = false;

  PlayerState get playerState => _playerState;
  bool get isPlaying => _playerState == PlayerState.playing;
  bool get isLoading => _isLoading;
  double get playbackSpeed => _playbackSpeed;
  String? get currentAudioUrl => _currentAudioUrl;

  AudioService() {
    _player.onPlayerStateChanged.listen((state) {
      _playerState = state;
      notifyListeners();
    });
  }

  Future<void> speakText(String text, {double speed = 1.0}) async {
    try {
      _isLoading = true;
      notifyListeners();

      // Call backend TTS endpoint
      final response = await ApiClient.post(
        ApiEndpoints.voiceSpeak,
        body: {
          'text': text,
          'speed': speed,
          'lang': 'mr',
        },
      );

      if (response.isSuccess && response.data != null) {
        String relativeUrl = response.data['audio_url'];
        // Build full URL
        String fullUrl = relativeUrl.startsWith('http') 
            ? relativeUrl 
            : '${ApiEndpoints.baseUrl.replaceAll('/api', '')}$relativeUrl';

        _currentAudioUrl = fullUrl;
        _playbackSpeed = speed;

        await _player.setPlaybackRate(speed);
        await _player.play(UrlSource(fullUrl));
      }
    } catch (e) {
      debugPrint('AudioService Error: $e');
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
