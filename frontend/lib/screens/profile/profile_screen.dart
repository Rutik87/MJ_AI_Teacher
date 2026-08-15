import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/progress_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/liquid_glass_card.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final progressProv = context.watch<ProgressProvider>();
    final progress = progressProv.progress;

    final int streak = progress?.streakDays ?? 0;
    final double prepPct = progress?.preparationPercentage ?? 0.0;
    final int testsTaken = progress?.totalTestsTaken ?? 0;
    final int studyMinutes = progress?.totalStudyMinutes ?? 0;
    final int questionsSolved = progress?.totalQuestionsSolved ?? 0;
    final double accuracy = progress?.overallAccuracy ?? 0.0;

    final int hours = studyMinutes ~/ 60;
    final int mins = studyMinutes % 60;
    final double dailyGoalHours = 3.0;
    final double dailyGoalMinutes = dailyGoalHours * 60;
    final double dailyProgress = (studyMinutes / dailyGoalMinutes).clamp(0.0, 1.0);

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: Text(
          'Profile',
          style: GoogleFonts.poppins(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 110),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. User Avatar & Info (Screen 13)
            Row(
              children: [
                Container(
                  width: 58,
                  height: 58,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                      colors: [Color(0xFF7B1FA2), Color(0xFF2979FF)],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF7B1FA2).withOpacity(0.5),
                        blurRadius: 12,
                      ),
                    ],
                  ),
                  child: Center(
                    child: Text(
                      'R',
                      style: GoogleFonts.poppins(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Rutik',
                      style: GoogleFonts.poppins(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    Text(
                      'MPSC Aspirant',
                      style: GoogleFonts.poppins(
                        fontSize: 12,
                        color: const Color(0xFF00E5FF),
                      ),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 20),

            // 2. 3 Real Stats Badges (Streak, प्रगती, चाचण्या) - 100% Real DB
            Row(
              children: [
                _buildStatTile('$streak', 'Streak 🔥', const Color(0xFFFF9100)),
                const SizedBox(width: 8),
                _buildStatTile('${prepPct.toStringAsFixed(0)}%', 'प्रगती', const Color(0xFF00E5FF)),
                const SizedBox(width: 8),
                _buildStatTile('$testsTaken', 'चाचण्या', const Color(0xFFD500F9)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                _buildStatTile('${hours}h ${mins}m', 'अभ्यास वेळ', const Color(0xFF00E676)),
                const SizedBox(width: 8),
                _buildStatTile('$questionsSolved', 'सोडवलेले प्रश्न', const Color(0xFFFF5252)),
                const SizedBox(width: 8),
                _buildStatTile('${accuracy.toStringAsFixed(0)}%', 'अचूकता', const Color(0xFFFFD600)),
              ],
            ),

            const SizedBox(height: 24),

            // 3. आजचे ध्येय (3 तास अभ्यास - Real State)
            Text(
              'आजचे ध्येय',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 10),

            LiquidGlassCard(
              variant: GlowVariant.purple,
              padding: const EdgeInsets.all(16),
              margin: EdgeInsets.zero,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '३ तास अभ्यास',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        '${hours}h ${mins}m / 3h (${(dailyProgress * 100).toStringAsFixed(0)}%)',
                        style: GoogleFonts.poppins(
                          fontSize: 11,
                          color: const Color(0xFF00E676),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  if (studyMinutes == 0)
                    Text(
                      'आज अजून अभ्यास केलेला नाही.',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 11,
                        color: Colors.white54,
                      ),
                    ),
                  const SizedBox(height: 8),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: dailyProgress > 0.0 ? dailyProgress : 0.001,
                      minHeight: 8,
                      backgroundColor: Colors.white12,
                      color: const Color(0xFF00E676),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // 4. परीक्षा ध्येय (MPSC राज्यसेवा 2025 - Screen 13)
            Text(
              'परीक्षा ध्येय',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 10),

            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.08)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: const Color(0xFF00E5FF).withOpacity(0.15),
                    ),
                    child: const Icon(Icons.school, color: Color(0xFF00E5FF), size: 22),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'MPSC राज्यसेवा २०२५',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        Text(
                          'पूर्व व मुख्य परीक्षा तयारी',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 11,
                            color: Colors.white54,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.white38),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatTile(String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: GoogleFonts.poppins(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 11,
                color: Colors.white70,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
