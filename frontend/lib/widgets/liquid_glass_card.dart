import 'package:flutter/material.dart';

enum GlowVariant { blue, redBlue, cyan, purple, gold }

class LiquidGlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double borderRadius;
  final GlowVariant variant;
  final VoidCallback? onTap;
  final double? width;
  final double? height;

  const LiquidGlassCard({
    super.key,
    required this.child,
    this.padding,
    this.margin,
    this.borderRadius = 20,
    this.variant = GlowVariant.redBlue,
    this.onTap,
    this.width,
    this.height,
  });

  Color get _borderColor {
    switch (variant) {
      case GlowVariant.redBlue:
        return const Color(0xFF00E5FF);
      case GlowVariant.blue:
        return const Color(0xFF00B0FF);
      case GlowVariant.cyan:
        return const Color(0xFF00E5FF);
      case GlowVariant.purple:
        return const Color(0xFFD500F9);
      case GlowVariant.gold:
        return const Color(0xFFFFD600);
    }
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Container(
        width: width,
        height: height,
        margin: margin ?? const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF0F1522),
          borderRadius: BorderRadius.circular(borderRadius),
          border: Border.all(
            color: _borderColor.withOpacity(0.4),
            width: 1.2,
          ),
          boxShadow: [
            BoxShadow(
              color: _borderColor.withOpacity(0.18),
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Padding(
          padding: padding ?? const EdgeInsets.all(16),
          child: child,
        ),
      ),
    );
  }
}
