import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/test_model.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/liquid_glass_card.dart';

class TestResultScreen extends StatelessWidget {
  final TestResultModel result;

  const TestResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        leading: BouncingWrapper(
          onTap: () {
            soundService.playClick();
            Navigator.of(context).pop();
          },
          child: const Icon(Icons.close, color: Colors.white),
        ),
        title: Text(
          'चाचणी निकाल',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 17,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 90),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const SizedBox(height: 10),

            // 1. Large Glowing Circular Gauge (16 / 20)
            Center(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 150,
                    height: 150,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF00E5FF).withOpacity(0.35),
                          blurRadius: 30,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: CircularProgressIndicator(
                      value: result.totalQuestions > 0 ? (result.score / result.totalQuestions) : 0.8,
                      strokeWidth: 10,
                      backgroundColor: Colors.white12,
                      color: const Color(0xFF00E5FF),
                    ),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${result.score.toInt()} / ${result.totalQuestions}',
                        style: GoogleFonts.poppins(
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // 2. Feedback Message
            Text(
              'छान काम! 🎉',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: const Color(0xFFFFD54F),
              ),
            ),

            const SizedBox(height: 24),

            // 3. Stats Strip (योग्य, चुकी, अचूकता)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildStatBadge('योग्य', '${result.correctCount}', const Color(0xFF00E676)),
                _buildStatBadge('चुकी', '${result.wrongCount}', const Color(0xFFFF5252)),
                _buildStatBadge('अचूकता', '${result.accuracyPercentage.toStringAsFixed(0)}%', const Color(0xFF00E5FF)),
              ],
            ),

            const SizedBox(height: 30),

            // 4. विषयानुसार कामगिरी (Topic Performance)
            LiquidGlassCard(
              variant: GlowVariant.cyan,
              padding: const EdgeInsets.all(18),
              margin: EdgeInsets.zero,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'विषयानुसार कामगिरी',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 14),

                  _buildTopicProgressBar('1857 चा उठाव', 0.60, const Color(0xFF00E676)),
                  const SizedBox(height: 12),
                  _buildTopicProgressBar('स्वातंत्र्य चळवळ', 0.70, const Color(0xFF00E5FF)),
                ],
              ),
            ),

            const SizedBox(height: 32),

            // 5. Done Button
            BouncingWrapper(
              isBubbleSound: true,
              onTap: () {
                Navigator.of(context).pop();
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2979FF), Color(0xFF651FFF)],
                  ),
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF2979FF).withOpacity(0.4),
                      blurRadius: 14,
                    ),
                  ],
                ),
                child: Center(
                  child: Text(
                    'मुख्यपृष्ठावर जा',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatBadge(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          label,
          style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white60),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: GoogleFonts.poppins(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildTopicProgressBar(String topic, double progress, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '• $topic',
              style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white70),
            ),
            Text(
              '${(progress * 100).toInt()}%',
              style: GoogleFonts.poppins(fontSize: 11, fontWeight: FontWeight.bold, color: color),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 6,
            backgroundColor: Colors.white12,
            color: color,
          ),
        ),
      ],
    );
  }
}
