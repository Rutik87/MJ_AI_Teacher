import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:record/record.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:frontend/core/constants/api_endpoints.dart';

enum GeminiLiveState {
  disconnected,
  connecting,
  ready,
  listening,
  speaking,
  interrupted,
  error
}

class GeminiLiveAudioService extends ChangeNotifier {
  final AudioRecorder _audioRecorder = AudioRecorder();
  final AudioPlayer _audioPlayer = AudioPlayer();

  WebSocketChannel? _channel;
  StreamSubscription? _wsSubscription;
  StreamSubscription<RecordState>? _recordStateSubscription;
  StreamSubscription<List<int>>? _audioStreamSubscription;

  GeminiLiveState _state = GeminiLiveState.disconnected;
  String _liveTranscript = '';
  String _assistantTranscript = '';
  double _amplitude = 0.0;
  String? _errorMessage;

  GeminiLiveState get state => _state;
  String get liveTranscript => _liveTranscript;
  String get assistantTranscript => _assistantTranscript;
  double get amplitude => _amplitude;
  String? get errorMessage => _errorMessage;
  bool get isConnected => _state == GeminiLiveState.ready || _state == GeminiLiveState.listening || _state == GeminiLiveState.speaking;

  GeminiLiveAudioService() {
    _audioPlayer.onPlayerStateChanged.listen((pState) {
      if (pState == PlayerState.completed || pState == PlayerState.stopped) {
        if (_state == GeminiLiveState.speaking) {
          _state = GeminiLiveState.listening;
          notifyListeners();
        }
      }
    });
  }

  String _getWebSocketUrl() {
    String base = ApiEndpoints.baseUrl.trim();
    if (base.startsWith('https://')) {
      base = 'wss://${base.substring(8)}';
    } else if (base.startsWith('http://')) {
      base = 'ws://${base.substring(7)}';
    }
    while (base.endsWith('/')) {
      base = base.substring(0, base.length - 1);
    }
    return '$base/mj/live-ws';
  }

  Future<void> connect({int? bookId}) async {
    if (isConnected) return;

    _state = GeminiLiveState.connecting;
    _errorMessage = null;
    notifyListeners();

    final wsUrl = _getWebSocketUrl();
    debugPrint('[GeminiLiveAudioService] Connecting to WS: $wsUrl');

    try {
      final uri = Uri.parse(wsUrl);
      _channel = WebSocketChannel.connect(uri);

      _wsSubscription = _channel!.stream.listen(
        (message) => _handleServerMessage(message),
        onError: (err) {
          debugPrint('[GeminiLiveAudioService] WS error: $err');
          _state = GeminiLiveState.error;
          _errorMessage = 'WebSocket कनेक्शन त्रुटी: $err';
          notifyListeners();
        },
        onDone: () {
          debugPrint('[GeminiLiveAudioService] WS connection closed.');
          _state = GeminiLiveState.disconnected;
          notifyListeners();
        },
      );
    } catch (e) {
      debugPrint('[GeminiLiveAudioService] Connect failed: $e');
      _state = GeminiLiveState.error;
      _errorMessage = 'कनेक्ट करता आले नाही: $e';
      notifyListeners();
    }
  }

  void _handleServerMessage(dynamic message) {
    try {
      final Map<String, dynamic> data = json.decode(message.toString());
      final msgType = data['type'] as String?;

      if (msgType == 'ready') {
        _state = GeminiLiveState.ready;
        debugPrint('[GeminiLiveAudioService] Gemini Live is ready (Model: ${data['model']}, Voice: ${data['voice']})');
        startMicrophone();
      } else if (msgType == 'audio') {
        final rawB64 = data['data'] as String?;
        final mimeType = (data['mime_type'] as String? ?? '').toLowerCase();
        if (rawB64 != null && rawB64.isNotEmpty) {
          _state = GeminiLiveState.speaking;
          final bytes = base64.decode(rawB64);
          if (mimeType.contains('pcm')) {
            _playAudioBytes(bytes);
          } else {
            _audioPlayer.play(BytesSource(bytes));
          }
        }
      } else if (msgType == 'transcript') {
        final text = data['text'] as String? ?? '';
        _assistantTranscript += text;
        notifyListeners();
      } else if (msgType == 'interrupted') {
        // Instant Barge-In Cancellation
        debugPrint('[GeminiLiveAudioService] Barge-in interruption received! Flushing audio buffer.');
        _purgeAudioBuffer();
        _state = GeminiLiveState.listening;
        notifyListeners();
      } else if (msgType == 'turn_complete') {
        if (_state != GeminiLiveState.speaking) {
          _state = GeminiLiveState.listening;
        }
        notifyListeners();
      } else if (msgType == 'error') {
        _errorMessage = data['message'] as String?;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('[GeminiLiveAudioService] Error parsing server message: $e');
    }
  }

  Future<void> startMicrophone() async {
    final hasPermission = await _audioRecorder.hasPermission();
    if (!hasPermission) {
      _errorMessage = 'मायक्रोफोन परवानगी आवश्यक आहे.';
      notifyListeners();
      return;
    }

    try {
      final stream = await _audioRecorder.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
        ),
      );

      _state = GeminiLiveState.listening;
      notifyListeners();

      _audioStreamSubscription?.cancel();
      _audioStreamSubscription = stream.listen((chunk) {
        if (_channel != null && chunk.isNotEmpty) {
          // Send raw binary PCM audio frame to backend
          _channel!.sink.add(chunk);

          // Update amplitude for orb animation
          _updateAmplitude(chunk);
        }
      });
    } catch (e) {
      debugPrint('[GeminiLiveAudioService] Mic stream start failed: $e');
    }
  }

  void _updateAmplitude(List<int> chunk) {
    if (chunk.isEmpty) return;
    int sum = 0;
    for (int i = 0; i < chunk.length; i += 2) {
      if (i + 1 < chunk.length) {
        int sample = chunk[i] | (chunk[i + 1] << 8);
        if (sample > 32767) sample -= 65536;
        sum += sample.abs();
      }
    }
    double avg = sum / (chunk.length / 2);
    _amplitude = (avg / 12000.0).clamp(0.0, 1.0);
    notifyListeners();
  }

  Uint8List _pcmToWav(Uint8List pcmBytes, {int sampleRate = 24000, int channels = 1, int bitsPerSample = 16}) {
    final byteRate = sampleRate * channels * (bitsPerSample ~/ 8);
    final blockAlign = channels * (bitsPerSample ~/ 8);
    final totalDataLen = pcmBytes.length;
    final totalAudioLen = totalDataLen + 36;

    final header = ByteData(44);
    // RIFF chunk descriptor
    header.setUint8(0, 0x52); // 'R'
    header.setUint8(1, 0x49); // 'I'
    header.setUint8(2, 0x46); // 'F'
    header.setUint8(3, 0x46); // 'F'
    header.setUint32(4, totalAudioLen, Endian.little);
    header.setUint8(8, 0x57); // 'W'
    header.setUint8(9, 0x41); // 'A'
    header.setUint8(10, 0x56); // 'V'
    header.setUint8(11, 0x45); // 'E'
    // 'fmt ' sub-chunk
    header.setUint8(12, 0x66); // 'f'
    header.setUint8(13, 0x6D); // 'm'
    header.setUint8(14, 0x74); // 't'
    header.setUint8(15, 0x20); // ' '
    header.setUint32(16, 16, Endian.little); // Subchunk1Size (16 for PCM)
    header.setUint16(20, 1, Endian.little);  // AudioFormat (1 for PCM)
    header.setUint16(22, channels, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, blockAlign, Endian.little);
    header.setUint16(34, bitsPerSample, Endian.little);
    // 'data' sub-chunk
    header.setUint8(36, 0x64); // 'd'
    header.setUint8(37, 0x61); // 'a'
    header.setUint8(38, 0x74); // 't'
    header.setUint8(39, 0x61); // 'a'
    header.setUint32(40, totalDataLen, Endian.little);

    final wavBytes = Uint8List(44 + totalDataLen);
    wavBytes.setRange(0, 44, header.buffer.asUint8List());
    wavBytes.setRange(44, 44 + totalDataLen, pcmBytes);
    return wavBytes;
  }

  Future<void> _playAudioBytes(Uint8List rawBytes) async {
    try {
      final wavBytes = _pcmToWav(rawBytes, sampleRate: 24000);
      await _audioPlayer.play(BytesSource(wavBytes));
    } catch (e) {
      debugPrint('[GeminiLiveAudioService] Playback error: $e');
    }
  }

  void _purgeAudioBuffer() {
    try {
      _audioPlayer.stop();
    } catch (e) {
      debugPrint('[GeminiLiveAudioService] Stop error: $e');
    }
  }

  void sendText(String text) {
    if (_channel != null && text.trim().isNotEmpty) {
      _liveTranscript = text;
      _assistantTranscript = '';
      _channel!.sink.add(json.encode({
        'type': 'text',
        'text': text.trim()
      }));
      notifyListeners();
    }
  }

  bool _isDisposed = false;

  @override
  void notifyListeners() {
    if (!_isDisposed) {
      super.notifyListeners();
    }
  }

  Future<void> disconnect({bool notify = true}) async {
    _purgeAudioBuffer();
    await _audioStreamSubscription?.cancel();
    await _recordStateSubscription?.cancel();
    await _wsSubscription?.cancel();
    try {
      await _audioRecorder.stop();
    } catch (_) {}
    try {
      await _channel?.sink.close();
    } catch (_) {}

    _channel = null;
    _state = GeminiLiveState.disconnected;
    if (notify && !_isDisposed) {
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _isDisposed = true;
    disconnect(notify: false);
    _audioRecorder.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }
}
