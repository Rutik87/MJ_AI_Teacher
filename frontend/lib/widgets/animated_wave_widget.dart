import 'dart:math';
import 'package:flutter/material.dart';

class AnimatedWaveWidget extends StatefulWidget {
  final double height;
  final Color waveColor;
  final double progress;

  const AnimatedWaveWidget({
    super.key,
    this.height = 60,
    this.waveColor = const Color(0xFF00E5FF),
    this.progress = 0.5,
  });

  @override
  State<AnimatedWaveWidget> createState() => _AnimatedWaveWidgetState();
}

class _AnimatedWaveWidgetState extends State<AnimatedWaveWidget> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
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
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: CustomPaint(
              size: Size(double.infinity, widget.height),
              painter: _WavePainter(
                animationValue: _controller.value,
                waveColor: widget.waveColor,
              ),
            ),
          );
        },
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  final double animationValue;
  final Color waveColor;

  _WavePainter({required this.animationValue, required this.waveColor});

  @override
  void paint(Canvas canvas, Size size) {
    final paint1 = Paint()
      ..color = waveColor.withOpacity(0.3)
      ..style = PaintingStyle.fill;

    final paint2 = Paint()
      ..color = waveColor.withOpacity(0.65)
      ..style = PaintingStyle.fill;

    double baseHeight = size.height * 0.45;
    double waveHeight = 10.0;
    int steps = 16;
    double stepWidth = size.width / steps;

    // Layer 1
    final path1 = Path();
    path1.moveTo(0, size.height);
    path1.lineTo(0, baseHeight);
    for (int i = 0; i <= steps; i++) {
      double x = i * stepWidth;
      double angle = (i / steps * 2 * pi) + (animationValue * 2 * pi);
      double y = baseHeight + sin(angle) * waveHeight;
      path1.lineTo(x, y);
    }
    path1.lineTo(size.width, size.height);
    path1.close();
    canvas.drawPath(path1, paint1);

    // Layer 2
    final path2 = Path();
    path2.moveTo(0, size.height);
    path2.lineTo(0, baseHeight + 3);
    for (int i = 0; i <= steps; i++) {
      double x = i * stepWidth;
      double angle = (i / steps * 2 * pi) - (animationValue * 2 * pi) + pi / 2;
      double y = baseHeight + cos(angle) * (waveHeight * 0.75) + 3;
      path2.lineTo(x, y);
    }
    path2.lineTo(size.width, size.height);
    path2.close();
    canvas.drawPath(path2, paint2);

    // Floating bubbles
    final bubblePaint = Paint()..color = Colors.white.withOpacity(0.7);
    double bX1 = (size.width * 0.3 + animationValue * 40) % size.width;
    double bX2 = (size.width * 0.7 - animationValue * 30 + size.width) % size.width;
    canvas.drawCircle(Offset(bX1, baseHeight - 4), 2.5, bubblePaint);
    canvas.drawCircle(Offset(bX2, baseHeight - 8), 3.0, bubblePaint);
  }

  @override
  bool shouldRepaint(covariant _WavePainter oldDelegate) =>
      oldDelegate.animationValue != animationValue;
}
