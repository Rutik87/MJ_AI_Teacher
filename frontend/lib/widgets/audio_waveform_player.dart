import 'dart:math';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';

class AudioWaveformPlayer extends StatefulWidget {
  final String title;
  final String durationText;
  final String textToSpeak;

  const AudioWaveformPlayer({
    super.key,
    this.title = 'AI Response',
    this.durationText = '01:45',
    this.textToSpeak = 'सत्यशोधक समाजाची स्थापना महात्मा ज्योतिराव फुले यांनी १८७३ मध्ये केली.',
  });

  @override
  State<AudioWaveformPlayer> createState() => _AudioWaveformPlayerState();
}

class _AudioWaveformPlayerState extends State<AudioWaveformPlayer> with SingleTickerProviderStateMixin {
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final audioService = context.watch<AudioService>();
    final isPlaying = audioService.isPlaying;

    if (isPlaying && !_animController.isAnimating) {
      _animController.repeat(reverse: true);
    } else if (!isPlaying && _animController.isAnimating) {
      _animController.stop();
    }

    return RepaintBoundary(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF0F1522),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: const Color(0xFF00E5FF).withOpacity(0.35),
            width: 1.2,
          ),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF00E5FF).withOpacity(0.12),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  widget.title,
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Colors.white70,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E5FF).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    widget.durationText,
                    style: GoogleFonts.poppins(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF00E5FF),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Waveform bars + Controls
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Previous button
                BouncingWrapper(
                  onTap: () => soundService.playClick(),
                  child: const Icon(Icons.skip_previous, color: Colors.white70, size: 22),
                ),

                // Animated Waveform Bars (12 bars instead of 18)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    child: isPlaying
                        ? AnimatedBuilder(
                            animation: _animController,
                            builder: (context, child) {
                              return Row(
                                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                                children: List.generate(12, (index) {
                                  double h = 8 + sin(_animController.value * pi + index * 0.8).abs() * 16;
                                  return Container(
                                    width: 3,
                                    height: h.clamp(4.0, 24.0),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF00E5FF),
                                      borderRadius: BorderRadius.circular(2),
                                    ),
                                  );
                                }),
                              );
                            },
                          )
                        : Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: List.generate(12, (index) {
                              double h = (sin(index * 0.7) * 6 + 10).abs();
                              return Container(
                                width: 3,
                                height: h,
                                decoration: BoxDecoration(
                                  color: Colors.white24,
                                  borderRadius: BorderRadius.circular(2),
                                ),
                              );
                            }),
                          ),
                  ),
                ),

                // Play / Pause Button with Neon Glow
                BouncingWrapper(
                  isBubbleSound: true,
                  onTap: () {
                    if (isPlaying) {
                      audioService.playPause();
                    } else {
                      audioService.speakText(widget.textToSpeak);
                    }
                  },
                  child: Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const RadialGradient(
                        colors: [Color(0xFF00E5FF), Color(0xFF0091EA)],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF00E5FF).withOpacity(0.5),
                          blurRadius: 8,
                        ),
                      ],
                    ),
                    child: Icon(
                      isPlaying ? Icons.pause : Icons.play_arrow,
                      color: Colors.black87,
                      size: 22,
                    ),
                  ),
                ),

                const SizedBox(width: 6),

                // Next button
                BouncingWrapper(
                  onTap: () => soundService.playClick(),
                  child: const Icon(Icons.skip_next, color: Colors.white70, size: 22),
                ),

                const SizedBox(width: 6),

                // Speed button
                BouncingWrapper(
                  onTap: () {
                    soundService.playClick();
                    double next = audioService.playbackSpeed >= 1.5
                        ? 0.75
                        : (audioService.playbackSpeed >= 1.25
                            ? 1.5
                            : (audioService.playbackSpeed >= 1.0 ? 1.25 : 1.0));
                    audioService.setSpeed(next);
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white10,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '${audioService.playbackSpeed}x',
                      style: GoogleFonts.poppins(fontSize: 10, color: const Color(0xFF00E5FF), fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
