import 'dart:math';
import 'package:flutter/material.dart';

class NeonBrainHologram extends StatefulWidget {
  final double size;

  const NeonBrainHologram({super.key, this.size = 140});

  @override
  State<NeonBrainHologram> createState() => _NeonBrainHologramState();
}

class _NeonBrainHologramState extends State<NeonBrainHologram> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2400),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          double val = _controller.value;

          return SizedBox(
            width: widget.size,
            height: widget.size,
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Outer Cyan & Purple Glow Aura
                Container(
                  width: widget.size * 0.95,
                  height: widget.size * 0.95,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF00E5FF).withOpacity(0.35 + (val * 0.15)),
                        blurRadius: 30 + (val * 10),
                        spreadRadius: 2,
                      ),
                      BoxShadow(
                        color: const Color(0xFFD500F9).withOpacity(0.35 + (val * 0.15)),
                        blurRadius: 36 + (val * 10),
                        spreadRadius: 4,
                      ),
                    ],
                  ),
                ),

                // Brain Custom Painter
                CustomPaint(
                  size: Size(widget.size * 0.85, widget.size * 0.85),
                  painter: _BrainPainter(pulse: val),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _BrainPainter extends CustomPainter {
  final double pulse;

  _BrainPainter({required this.pulse});

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final center = Offset(w / 2, h / 2);

    // Left Hemisphere (Cyan / Electric Blue)
    final leftPaint = Paint()
      ..color = const Color(0xFF00E5FF)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    // Right Hemisphere (Neon Purple / Magenta)
    final rightPaint = Paint()
      ..color = const Color(0xFFD500F9)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final fillPaintLeft = Paint()
      ..shader = RadialGradient(
        colors: [const Color(0xFF00E5FF).withOpacity(0.2), Colors.transparent],
      ).createShader(Rect.fromCircle(center: Offset(w * 0.35, h * 0.5), radius: w * 0.4));

    final fillPaintRight = Paint()
      ..shader = RadialGradient(
        colors: [const Color(0xFFD500F9).withOpacity(0.2), Colors.transparent],
      ).createShader(Rect.fromCircle(center: Offset(w * 0.65, h * 0.5), radius: w * 0.4));

    // Draw Left Hemisphere Lobes
    Path leftPath = Path();
    leftPath.moveTo(w * 0.48, h * 0.15);
    leftPath.cubicTo(w * 0.25, h * 0.10, w * 0.10, h * 0.30, w * 0.12, h * 0.50);
    leftPath.cubicTo(w * 0.10, h * 0.65, w * 0.20, h * 0.85, w * 0.48, h * 0.85);
    canvas.drawPath(leftPath, fillPaintLeft);
    canvas.drawPath(leftPath, leftPaint);

    // Left Internal Neural Curves
    canvas.drawArc(Rect.fromLTWH(w * 0.20, h * 0.25, w * 0.25, h * 0.25), 0, pi, false, leftPaint);
    canvas.drawArc(Rect.fromLTWH(w * 0.18, h * 0.48, w * 0.25, h * 0.25), pi * 0.2, pi, false, leftPaint);

    // Draw Right Hemisphere Lobes
    Path rightPath = Path();
    rightPath.moveTo(w * 0.52, h * 0.15);
    rightPath.cubicTo(w * 0.75, h * 0.10, w * 0.90, h * 0.30, w * 0.88, h * 0.50);
    rightPath.cubicTo(w * 0.90, h * 0.65, w * 0.80, h * 0.85, w * 0.52, h * 0.85);
    canvas.drawPath(rightPath, fillPaintRight);
    canvas.drawPath(rightPath, rightPaint);

    // Right Internal Neural Curves
    canvas.drawArc(Rect.fromLTWH(w * 0.55, h * 0.25, w * 0.25, h * 0.25), 0, -pi, false, rightPaint);
    canvas.drawArc(Rect.fromLTWH(w * 0.57, h * 0.48, w * 0.25, h * 0.25), -pi * 0.2, -pi, false, rightPaint);

    // Center Connecting Neural Nodes
    final nodePaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    canvas.drawCircle(Offset(w * 0.50, h * 0.35), 2.5, nodePaint);
    canvas.drawCircle(Offset(w * 0.50, h * 0.50), 3.0, nodePaint);
    canvas.drawCircle(Offset(w * 0.50, h * 0.65), 2.5, nodePaint);
  }

  @override
  bool shouldRepaint(covariant _BrainPainter oldDelegate) => true;
}
