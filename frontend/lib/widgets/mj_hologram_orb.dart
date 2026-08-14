import 'dart:math';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/wake_word_service.dart';

class MJHologramOrb extends StatefulWidget {
  final double size;
  final MJVoiceState state;
  final VoidCallback? onTap;

  const MJHologramOrb({
    super.key,
    this.size = 180,
    required this.state,
    this.onTap,
  });

  @override
  State<MJHologramOrb> createState() => _MJHologramOrbState();
}

class _MJHologramOrbState extends State<MJHologramOrb> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            double anim = _controller.value;
            bool isListening = widget.state == MJVoiceState.listening;
            bool isSpeaking = widget.state == MJVoiceState.speaking;
            bool isProcessing = widget.state == MJVoiceState.processing;

            return SizedBox(
              width: widget.size,
              height: widget.size,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Outer Pulsing Ripple 1 (Listening/Speaking)
                  if (isListening || isSpeaking)
                    Transform.scale(
                      scale: 1.0 + (anim * 0.3),
                      child: Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: const Color(0xFF00E5FF).withOpacity((1.0 - anim) * 0.6),
                            width: 1.8,
                          ),
                        ),
                      ),
                    ),

                  // Outer Pulsing Ripple 2 (Purple)
                  if (isListening || isSpeaking)
                    Transform.scale(
                      scale: 1.0 + (((anim + 0.5) % 1.0) * 0.3),
                      child: Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: const Color(0xFFD500F9).withOpacity((1.0 - ((anim + 0.5) % 1.0)) * 0.6),
                            width: 1.8,
                          ),
                        ),
                      ),
                    ),

                  // Central Glowing MJ Core
                  Container(
                    width: widget.size * 0.65,
                    height: widget.size * 0.65,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: isProcessing
                            ? const [Color(0xFFFF9100), Color(0xFF651FFF), Color(0xFF050811)]
                            : const [Color(0xFF00E5FF), Color(0xFF651FFF), Color(0xFF0A0E17)],
                        stops: const [0.2, 0.7, 1.0],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: (isProcessing ? const Color(0xFFFF9100) : const Color(0xFF00E5FF)).withOpacity(0.8),
                          blurRadius: 28,
                          spreadRadius: 2,
                        ),
                        BoxShadow(
                          color: const Color(0xFFD500F9).withOpacity(0.6),
                          blurRadius: 36,
                          spreadRadius: 4,
                        ),
                      ],
                      border: Border.all(
                        color: Colors.white.withOpacity(0.9),
                        width: 2.0,
                      ),
                    ),
                    child: Center(
                      child: isSpeaking
                          ? _buildWaveformVisualizer(anim)
                          : isListening
                              ? const Icon(Icons.mic, color: Colors.white, size: 40)
                              : isProcessing
                                  ? const SizedBox(
                                      width: 28,
                                      height: 28,
                                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                                    )
                                  : Text(
                                      'MJ',
                                      style: GoogleFonts.poppins(
                                        fontSize: 26,
                                        fontWeight: FontWeight.w900,
                                        color: Colors.white,
                                        letterSpacing: 1.5,
                                      ),
                                    ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildWaveformVisualizer(double anim) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(5, (index) {
        double height = 8 + (sin(anim * 2 * pi + (index * 0.8)).abs() * 22);
        return Container(
          width: 4,
          height: height,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(2),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF00E5FF).withOpacity(0.8),
                blurRadius: 4,
              ),
            ],
          ),
        );
      }),
    );
  }
}
