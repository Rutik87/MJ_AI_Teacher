import 'dart:math';
import 'package:flutter/material.dart';

class CyberRobotAvatar extends StatefulWidget {
  final double size;

  const CyberRobotAvatar({super.key, this.size = 130});

  @override
  State<CyberRobotAvatar> createState() => _CyberRobotAvatarState();
}

class _CyberRobotAvatarState extends State<CyberRobotAvatar> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _floatAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    )..repeat(reverse: true);

    _floatAnimation = Tween<double>(begin: -4, end: 4).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOutSine),
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
      child: AnimatedBuilder(
        animation: _floatAnimation,
        builder: (context, child) {
          return Transform.translate(
            offset: Offset(0, _floatAnimation.value),
            child: Container(
              width: widget.size,
              height: widget.size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF00E5FF).withOpacity(0.35),
                    blurRadius: 24,
                    spreadRadius: 2,
                  ),
                  BoxShadow(
                    color: const Color(0xFF9C27B0).withOpacity(0.35),
                    blurRadius: 32,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Outer Hologram Ring
                  Container(
                    width: widget.size,
                    height: widget.size,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFF00E5FF).withOpacity(0.5),
                        width: 1.5,
                      ),
                    ),
                  ),

                  // Robot Head
                  Container(
                    width: widget.size * 0.78,
                    height: widget.size * 0.72,
                    decoration: BoxDecoration(
                      color: const Color(0xFF0A0F1E),
                      borderRadius: BorderRadius.circular(widget.size * 0.36),
                      border: Border.all(
                        color: const Color(0xFF7B1FA2).withOpacity(0.8),
                        width: 2,
                      ),
                    ),
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        // Visor Screen
                        Container(
                          width: widget.size * 0.62,
                          height: widget.size * 0.38,
                          decoration: BoxDecoration(
                            color: const Color(0xFF050811),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: const Color(0xFF00E5FF).withOpacity(0.6),
                              width: 1.5,
                            ),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              // Left Eye
                              _buildGlowingEye(),
                              // Right Eye
                              _buildGlowingEye(),
                            ],
                          ),
                        ),

                        // Antenna Top
                        Positioned(
                          top: -6,
                          child: Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: const Color(0xFF00E5FF),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(0xFF00E5FF).withOpacity(0.8),
                                  blurRadius: 8,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Robot Ear Headphones
                  Positioned(
                    left: 2,
                    child: _buildHeadphone(),
                  ),
                  Positioned(
                    right: 2,
                    child: _buildHeadphone(),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildGlowingEye() {
    return Container(
      width: 12,
      height: 12,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: const Color(0xFF00E5FF),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00E5FF).withOpacity(0.9),
            blurRadius: 10,
            spreadRadius: 1,
          ),
        ],
      ),
    );
  }

  Widget _buildHeadphone() {
    return Container(
      width: 14,
      height: 28,
      decoration: BoxDecoration(
        color: const Color(0xFF7B1FA2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF00E5FF), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF7B1FA2).withOpacity(0.6),
            blurRadius: 6,
          ),
        ],
      ),
    );
  }
}
