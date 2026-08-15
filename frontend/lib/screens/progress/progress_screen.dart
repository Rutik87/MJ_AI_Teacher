import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/progress_provider.dart';
import 'package:frontend/models/progress_model.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/liquid_glass_card.dart';

class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final progressProv = context.watch<ProgressProvider>();
    final progress = progressProv.progress;

    final int studyMinutes = progress?.totalStudyMinutes ?? 0;
    final int hours = studyMinutes ~/ 60;
    final int mins = studyMinutes % 60;

    final List<double> weeklyHours = progress?.weeklyStudyHours ?? List.filled(7, 0.0);
    final List<FlSpot> chartSpots = List.generate(7, (i) {
      double val = i < weeklyHours.length ? weeklyHours[i] : 0.0;
      return FlSpot(i.toDouble(), val);
    });

    final List<SubjectMasteryModel> subjects = progress?.subjectsMastery ?? [];

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        title: Text(
          'प्रगती (Analytics)',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 17,
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
            // 1. अभ्यास वेळ Card - 100% Real DB Data
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
                        'एकूण अभ्यास वेळ',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: Colors.white70,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00E676).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '${hours}h ${mins}m',
                          style: GoogleFonts.poppins(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: const Color(0xFF00E676),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${hours}h ${mins}m',
                    style: GoogleFonts.poppins(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  if (studyMinutes == 0)
                    Text(
                      'अजून अभ्यास सुरू केलेला नाही.',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 11,
                        color: Colors.white54,
                      ),
                    ),

                  const SizedBox(height: 18),

                  // Glowing Activity Line Chart (Real Mon-Sun Data)
                  SizedBox(
                    height: 130,
                    child: LineChart(
                      LineChartData(
                        gridData: const FlGridData(show: false),
                        titlesData: FlTitlesData(
                          leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (val, meta) {
                                const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                                if (val.toInt() >= 0 && val.toInt() < days.length) {
                                  return Text(
                                    days[val.toInt()],
                                    style: GoogleFonts.poppins(fontSize: 10, color: Colors.white54),
                                  );
                                }
                                return const SizedBox();
                              },
                            ),
                          ),
                        ),
                        borderData: FlBorderData(show: false),
                        lineBarsData: [
                          LineChartBarData(
                            spots: chartSpots,
                            isCurved: true,
                            color: const Color(0xFF00E5FF),
                            barWidth: 3,
                            dotData: const FlDotData(show: true),
                            belowBarData: BarAreaData(
                              show: true,
                              gradient: LinearGradient(
                                colors: [
                                  const Color(0xFF00E5FF).withOpacity(0.35),
                                  Colors.transparent,
                                ],
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // 2. विषयानुसार प्रगती (Subject Performance Progress Bars - 100% Real DB)
            Text(
              'विषयानुसार प्रगती',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),

            if (subjects.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF0A0E17),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white10),
                ),
                child: Center(
                  child: Text(
                    'अजून विषयानुसार अभ्यास डेटा उपलब्ध नाही.',
                    style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white54),
                  ),
                ),
              )
            else
              ...subjects.map((s) {
                final double factor = (s.masteryPercentage / 100.0).clamp(0.0, 1.0);
                Color barColor = const Color(0xFF00E5FF);
                if (s.masteryPercentage >= 75) {
                  barColor = const Color(0xFF00E676);
                } else if (s.masteryPercentage < 50 && s.attempted > 0) {
                  barColor = const Color(0xFFFF5252);
                } else if (s.attempted == 0) {
                  barColor = const Color(0xFF546E7A);
                }
                return _buildSubjectBar(s.subjectName, factor, barColor, s.attempted);
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildSubjectBar(String subject, double value, Color color, int attempted) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E17),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                subject,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              Text(
                attempted > 0 ? '${(value * 100).toInt()}%' : '0% (सराव नाही)',
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: value > 0.0 ? value : 0.001,
              minHeight: 6,
              backgroundColor: Colors.white12,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
