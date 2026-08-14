import 'dart:math';
import 'package:flutter/material.dart';

class HolographicVoiceMic extends StatefulWidget {
  final double size;
  final bool isListening;
  final VoidCallback? onTap;

  const HolographicVoiceMic({
    super.key,
    this.size = 200,
    this.isListening = true,
    this.onTap,
  });

  @override
  State<HolographicVoiceMic> createState() => _HolographicVoiceMicState();
}

class _HolographicVoiceMicState extends State<HolographicVoiceMic> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
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

            return SizedBox(
              width: widget.size,
              height: widget.size,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Outer Wave Ring 1
                  if (widget.isListening)
                    Transform.scale(
                      scale: 1.0 + (anim * 0.35),
                      child: Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: const Color(0xFF00E5FF).withOpacity((1.0 - anim) * 0.6),
                            width: 2.0,
                          ),
                        ),
                      ),
                    ),

                  // Outer Wave Ring 2 (Purple)
                  if (widget.isListening)
                    Transform.scale(
                      scale: 1.0 + ((anim + 0.5) % 1.0 * 0.35),
                      child: Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: const Color(0xFFD500F9).withOpacity((1.0 - ((anim + 0.5) % 1.0)) * 0.6),
                            width: 2.0,
                          ),
                        ),
                      ),
                    ),

                  // Sunburst Spoke Gear
                  CustomPaint(
                    size: Size(widget.size * 0.85, widget.size * 0.85),
                    painter: _SunburstPainter(rotation: anim * 2 * pi),
                  ),

                  // Central Glowing Mic Button
                  Container(
                    width: widget.size * 0.52,
                    height: widget.size * 0.52,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const RadialGradient(
                        colors: [Color(0xFF00E5FF), Color(0xFF651FFF), Color(0xFF050811)],
                        stops: [0.2, 0.7, 1.0],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF00E5FF).withOpacity(0.8),
                          blurRadius: 24,
                          spreadRadius: 2,
                        ),
                        BoxShadow(
                          color: const Color(0xFFD500F9).withOpacity(0.6),
                          blurRadius: 30,
                          spreadRadius: 4,
                        ),
                      ],
                      border: Border.all(
                        color: Colors.white.withOpacity(0.9),
                        width: 2.0,
                      ),
                    ),
                    child: const Center(
                      child: Icon(
                        Icons.mic,
                        color: Colors.white,
                        size: 44,
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
}

class _SunburstPainter extends CustomPainter {
  final double rotation;

  _SunburstPainter({required this.rotation});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    int spokes = 20;

    final paint = Paint()
      ..color = const Color(0xFF00E5FF).withOpacity(0.4)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    for (int i = 0; i < spokes; i++) {
      double angle = (i * 2 * pi / spokes) + rotation;
      double x1 = center.dx + cos(angle) * (radius * 0.75);
      double y1 = center.dy + sin(angle) * (radius * 0.75);
      double x2 = center.dx + cos(angle) * radius;
      double y2 = center.dy + sin(angle) * radius;

      canvas.drawLine(Offset(x1, y1), Offset(x2, y2), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _SunburstPainter oldDelegate) => true;
}
