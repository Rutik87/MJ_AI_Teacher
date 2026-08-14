import 'package:flutter/material.dart';

class NeonDropletBadge extends StatefulWidget {
  final double size;
  final IconData icon;
  final Color primaryColor;
  final VoidCallback? onTap;

  const NeonDropletBadge({
    super.key,
    this.size = 56,
    this.icon = Icons.play_arrow,
    this.primaryColor = const Color(0xFF00E5FF),
    this.onTap,
  });

  @override
  State<NeonDropletBadge> createState() => _NeonDropletBadgeState();
}

class _NeonDropletBadgeState extends State<NeonDropletBadge> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
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
          animation: _pulseAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _pulseAnimation.value,
              child: Container(
                width: widget.size,
                height: widget.size,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      widget.primaryColor,
                      const Color(0xFF0D47A1),
                      const Color(0xFF080C14),
                    ],
                    stops: const [0.3, 0.75, 1.0],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: widget.primaryColor.withOpacity(0.45),
                      blurRadius: 8,
                      spreadRadius: 1,
                    ),
                  ],
                  border: Border.all(
                    color: Colors.white70,
                    width: 1.3,
                  ),
                ),
                child: Center(
                  child: Icon(
                    widget.icon,
                    color: Colors.white,
                    size: widget.size * 0.45,
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
