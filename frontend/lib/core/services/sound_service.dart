import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:audioplayers/audioplayers.dart';

class SoundService {
  static final SoundService _instance = SoundService._internal();
  factory SoundService() => _instance;

  final AudioPlayer _player = AudioPlayer();
  Uint8List? _clickWavBytes;
  Uint8List? _bubbleWavBytes;
  bool _soundEnabled = true;
  int _lastPlayTime = 0;

  bool get soundEnabled => _soundEnabled;

  SoundService._internal() {
    _initSounds();
  }

  void toggleSound(bool enabled) {
    _soundEnabled = enabled;
  }

  void _initSounds() {
    try {
      _clickWavBytes = _generateBeepWav(frequency: 1200, durationMs: 30, sampleRate: 22050);
      _bubbleWavBytes = _generateBubbleWav(sampleRate: 22050);
    } catch (e) {
      debugPrint('Error generating sound bytes: $e');
    }
  }

  /// Non-blocking, debounced UI click sound
  void playClick() {
    if (!_soundEnabled) return;

    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _lastPlayTime < 60) return; // 60ms debounce for buttery smooth frames
    _lastPlayTime = now;

    // Haptic feedback
    try {
      HapticFeedback.selectionClick();
    } catch (_) {}

    // System sound
    try {
      SystemSound.play(SystemSoundType.click);
    } catch (_) {}

    // Non-blocking async audio play
    if (_clickWavBytes != null) {
      _player.play(BytesSource(_clickWavBytes!), volume: 0.5).catchError((_) {});
    }
  }

  /// Non-blocking liquid / bubble pop sound
  void playBubble() {
    if (!_soundEnabled) return;

    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _lastPlayTime < 60) return;
    _lastPlayTime = now;

    try {
      HapticFeedback.lightImpact();
    } catch (_) {}

    if (_bubbleWavBytes != null) {
      _player.play(BytesSource(_bubbleWavBytes!), volume: 0.6).catchError((_) {});
    }
  }

  Uint8List _generateBeepWav({required double frequency, required int durationMs, required int sampleRate}) {
    int numSamples = (sampleRate * (durationMs / 1000.0)).toInt();
    int byteRate = sampleRate * 2;
    int dataSize = numSamples * 2;
    int fileSize = 36 + dataSize;

    var header = ByteData(44);
    header.setUint8(0, 0x52); header.setUint8(1, 0x49); header.setUint8(2, 0x46); header.setUint8(3, 0x46);
    header.setUint32(4, fileSize, Endian.little);
    header.setUint8(8, 0x57); header.setUint8(9, 0x41); header.setUint8(10, 0x56); header.setUint8(11, 0x45);
    header.setUint8(12, 0x66); header.setUint8(13, 0x6D); header.setUint8(14, 0x74); header.setUint8(15, 0x20);
    header.setUint32(16, 16, Endian.little);
    header.setUint16(20, 1, Endian.little);
    header.setUint16(22, 1, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, 2, Endian.little);
    header.setUint16(34, 16, Endian.little);
    header.setUint8(36, 0x64); header.setUint8(37, 0x61); header.setUint8(38, 0x74); header.setUint8(39, 0x61);
    header.setUint32(40, dataSize, Endian.little);

    var buffer = Uint8List(44 + dataSize);
    buffer.setRange(0, 44, header.buffer.asUint8List());

    var dataView = ByteData.view(buffer.buffer, 44, dataSize);
    for (int i = 0; i < numSamples; i++) {
      double t = i / sampleRate;
      double envelope = exp(-t * 90.0);
      double sample = sin(2 * pi * frequency * t) * envelope;
      int intSample = (sample * 32767).toInt().clamp(-32768, 32767);
      dataView.setInt16(i * 2, intSample, Endian.little);
    }
    return buffer;
  }

  Uint8List _generateBubbleWav({required int sampleRate}) {
    int durationMs = 50;
    int numSamples = (sampleRate * (durationMs / 1000.0)).toInt();
    int dataSize = numSamples * 2;
    int fileSize = 36 + dataSize;

    var header = ByteData(44);
    header.setUint8(0, 0x52); header.setUint8(1, 0x49); header.setUint8(2, 0x46); header.setUint8(3, 0x46);
    header.setUint32(4, fileSize, Endian.little);
    header.setUint8(8, 0x57); header.setUint8(9, 0x41); header.setUint8(10, 0x56); header.setUint8(11, 0x45);
    header.setUint8(12, 0x66); header.setUint8(13, 0x6D); header.setUint8(14, 0x74); header.setUint8(15, 0x20);
    header.setUint32(16, 16, Endian.little);
    header.setUint16(20, 1, Endian.little);
    header.setUint16(22, 1, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, sampleRate * 2, Endian.little);
    header.setUint16(32, 2, Endian.little);
    header.setUint16(34, 16, Endian.little);
    header.setUint8(36, 0x64); header.setUint8(37, 0x61); header.setUint8(38, 0x74); header.setUint8(39, 0x61);
    header.setUint32(40, dataSize, Endian.little);

    var buffer = Uint8List(44 + dataSize);
    buffer.setRange(0, 44, header.buffer.asUint8List());

    var dataView = ByteData.view(buffer.buffer, 44, dataSize);
    for (int i = 0; i < numSamples; i++) {
      double t = i / sampleRate;
      double freq = 450.0 + (t / (durationMs / 1000.0)) * 750.0;
      double envelope = sin(pi * (i / numSamples)) * exp(-t * 30.0);
      double sample = sin(2 * pi * freq * t) * envelope;
      int intSample = (sample * 32767).toInt().clamp(-32768, 32767);
      dataView.setInt16(i * 2, intSample, Endian.little);
    }
    return buffer;
  }
}

final soundService = SoundService();
