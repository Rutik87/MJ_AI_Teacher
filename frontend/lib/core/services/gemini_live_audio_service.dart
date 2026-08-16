import 'dart:async';
import 'dart:collection';
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

  final Queue<Uint8List> _audioQueue = Queue<Uint8List>();
  bool _isPlayingAudio = false;

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
    _initAudioContext();

    _audioPlayer.onPlayerStateChanged.listen((pState) {
      if (pState == PlayerState.completed || pState == PlayerState.stopped) {
        debugPrint('[LIVE][AUDIO] playback_stopped');
        _isPlayingAudio = false;
        _playNextInQueue();
      }
    });
  }

  void _initAudioContext() {
    try {
      AudioPlayer.global.setAudioContext(
        AudioContext(
          android: const AudioContextAndroid(
            isSpeakerphoneOn: true,
            stayAwake: true,
            contentType: AndroidContentType.speech,
            usageType: AndroidUsageType.assistanceNavigationGuidance,
            audioFocus: AndroidAudioFocus.gainTransientExclusive,
          ),
          iOS: AudioContextIOS(
            category: AVAudioSessionCategory.playAndRecord,
            options: const {
              AVAudioSessionOptions.defaultToSpeaker,
            },
          ),
        ),
      );
      debugPrint('[LIVE][AUDIO] AudioContext configured with isSpeakerphoneOn=true');
    } catch (e) {
      debugPrint('[LIVE][AUDIO] Error setting AudioContext: $e');
    }
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
    debugPrint('[LIVE][WS] connecting to $wsUrl');

    try {
      final uri = Uri.parse(wsUrl);
      _channel = WebSocketChannel.connect(uri);

      _wsSubscription = _channel!.stream.listen(
        (message) => _handleServerMessage(message),
        onError: (err) {
          debugPrint('[LIVE][WS] connection error: $err');
          _state = GeminiLiveState.error;
          _errorMessage = 'WebSocket कनेक्शन त्रुटी: $err';
          notifyListeners();
        },
        onDone: () {
          debugPrint('[LIVE][WS] connection closed.');
          _state = GeminiLiveState.disconnected;
          notifyListeners();
        },
      );
      debugPrint('[LIVE][WS] connected');
    } catch (e) {
      debugPrint('[LIVE][WS] connect failed: $e');
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
        debugPrint('[LIVE][WS] ready received model=${data['model']}, voice=${data['voice']}');
        startMicrophone();
      } else if (msgType == 'audio') {
        final rawB64 = data['data'] as String?;
        final mimeType = (data['mime_type'] as String? ?? '').toLowerCase();
        if (rawB64 != null && rawB64.isNotEmpty) {
          final bytes = base64.decode(rawB64);
          debugPrint('[LIVE][WS] audio_received size=${bytes.length} mime=$mimeType');
          debugPrint('[LIVE][AUDIO] buffer_received size=${bytes.length}');
          
          Uint8List playBytes;
          if (mimeType.contains('pcm')) {
            playBytes = _pcmToWav(bytes, sampleRate: 24000);
            debugPrint('[LIVE][AUDIO] pcm_decoded to wav size=${playBytes.length}');
          } else {
            playBytes = bytes;
          }

          _enqueueAudio(playBytes);
        }
      } else if (msgType == 'transcript') {
        final text = data['text'] as String? ?? '';
        _assistantTranscript += text;
        debugPrint('[LIVE][WS] transcript_received: $text');
        notifyListeners();
      } else if (msgType == 'interrupted') {
        debugPrint('[LIVE][WS] interruption_received Flushing audio buffer.');
        _purgeAudioBuffer();
        _state = GeminiLiveState.listening;
        notifyListeners();
      } else if (msgType == 'turn_complete') {
        debugPrint('[LIVE][WS] turn_complete received');
        if (!_isPlayingAudio && _audioQueue.isEmpty) {
          _state = GeminiLiveState.listening;
          notifyListeners();
        }
      } else if (msgType == 'error') {
        _errorMessage = data['message'] as String?;
        debugPrint('[LIVE][WS] error from server: $_errorMessage');
        notifyListeners();
      }
    } catch (e) {
      debugPrint('[LIVE][WS] error parsing message: $e');
    }
  }

  void _enqueueAudio(Uint8List audioBytes) {
    _audioQueue.add(audioBytes);
    if (!_isPlayingAudio) {
      _playNextInQueue();
    }
  }

  Future<void> _playNextInQueue() async {
    if (_audioQueue.isEmpty) {
      _isPlayingAudio = false;
      if (_state == GeminiLiveState.speaking) {
        _state = GeminiLiveState.listening;
        notifyListeners();
      }
      return;
    }

    _isPlayingAudio = true;
    _state = GeminiLiveState.speaking;
    notifyListeners();

    final nextChunk = _audioQueue.removeFirst();
    try {
      debugPrint('[LIVE][AUDIO] playback_started chunk_size=${nextChunk.length}');
      await _audioPlayer.play(BytesSource(nextChunk));
    } catch (e) {
      debugPrint('[LIVE][AUDIO] playback error: $e');
      _isPlayingAudio = false;
      _playNextInQueue();
    }
  }

  Future<void> startMicrophone() async {
    final hasPermission = await _audioRecorder.hasPermission();
    if (!hasPermission) {
      _errorMessage = 'मायक्रोफोन परवानगी आवश्यक आहे.';
      debugPrint('[LIVE][MIC] microphone permission denied');
      notifyListeners();
      return;
    }

    try {
      debugPrint('[LIVE][MIC] recording_started format=pcm16bits rate=16000 channels=1');
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
          debugPrint('[LIVE][MIC] chunk_received size=${chunk.length}');
          _channel!.sink.add(chunk);
          debugPrint('[LIVE][WS] audio_sent size=${chunk.length}');

          // Check if user is speaking while audio is playing (Barge-in detection)
          _updateAmplitude(chunk);
          if (_isPlayingAudio && _amplitude > 0.35) {
            debugPrint('[LIVE][MIC] user speech detected during playback -> local barge-in purge');
            _purgeAudioBuffer();
            _channel!.sink.add(json.encode({'type': 'interrupted'}));
          }
        }
      });
    } catch (e) {
      debugPrint('[LIVE][MIC] stream start failed: $e');
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
    header.setUint8(0, 0x52); // 'R'
    header.setUint8(1, 0x49); // 'I'
    header.setUint8(2, 0x46); // 'F'
    header.setUint8(3, 0x46); // 'F'
    header.setUint32(4, totalAudioLen, Endian.little);
    header.setUint8(8, 0x57); // 'W'
    header.setUint8(9, 0x41); // 'A'
    header.setUint8(10, 0x56); // 'V'
    header.setUint8(11, 0x45); // 'E'
    header.setUint8(12, 0x66); // 'f'
    header.setUint8(13, 0x6D); // 'm'
    header.setUint8(14, 0x74); // 't'
    header.setUint8(15, 0x20); // ' '
    header.setUint32(16, 16, Endian.little);
    header.setUint16(20, 1, Endian.little);
    header.setUint16(22, channels, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, blockAlign, Endian.little);
    header.setUint16(34, bitsPerSample, Endian.little);
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

  void _purgeAudioBuffer() {
    try {
      _audioQueue.clear();
      _isPlayingAudio = false;
      _audioPlayer.stop();
      debugPrint('[LIVE][AUDIO] buffer purged & playback stopped');
    } catch (e) {
      debugPrint('[LIVE][AUDIO] error purging buffer: $e');
    }
  }

  Future<void> sendText(String text) => sendTextTurn(text);

  Future<void> sendTextTurn(String text) async {
    if (_channel != null && text.trim().isNotEmpty) {
      _liveTranscript = text;
      _assistantTranscript = '';
      notifyListeners();
      _channel!.sink.add(json.encode({'type': 'text', 'text': text}));
      debugPrint('[LIVE][WS] audio_sent text query: $text');
    }
  }

  Future<void> disconnect() async {
    _purgeAudioBuffer();
    _audioStreamSubscription?.cancel();
    _audioStreamSubscription = null;
    await _audioRecorder.stop();

    _wsSubscription?.cancel();
    _wsSubscription = null;
    _channel?.sink.close();
    _channel = null;

    _state = GeminiLiveState.disconnected;
    _amplitude = 0.0;
    debugPrint('[LIVE][WS] disconnected');
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    _audioPlayer.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }
}
