import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/tests/test_taking_screen.dart';

class PYQScreen extends StatefulWidget {
  const PYQScreen({super.key});

  @override
  State<PYQScreen> createState() => _PYQScreenState();
}

class _PYQScreenState extends State<PYQScreen> {
  final List<Map<String, dynamic>> _pyqPapers = [
    {'year': '2023 पूर्व परीक्षा', 'subject': 'इतिहास व राज्यशास्त्र', 'questions': '120 प्रश्न', 'color': Color(0xFF9C27B0)},
    {'year': '2022 पूर्व परीक्षा', 'subject': 'इतिहास व भूगोल', 'questions': '120 प्रश्न', 'color': Color(0xFFFF9100)},
    {'year': '2021 पूर्व परीक्षा', 'subject': 'राज्यघटना व अर्थशास्त्र', 'questions': '120 प्रश्न', 'color': Color(0xFF00E5FF)},
    {'year': '2020 पूर्व परीक्षा', 'subject': 'सामान्य अध्ययन पेपर १', 'questions': '120 प्रश्न', 'color': Color(0xFF7B1FA2)},
    {'year': '2019 पूर्व परीक्षा', 'subject': 'इतिहास व समाजसुधारक', 'questions': '100 प्रश्न', 'color': Color(0xFF2979FF)},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: BouncingWrapper(
          onTap: () {
            soundService.playClick();
            Navigator.of(context).pop();
          },
          child: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: Text(
          'PYQ (मागील वर्षांचे प्रश्न)',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: Column(
        children: [
          // Filter Chips Strip
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Row(
              children: [
                _buildFilterChip('वर्ष ▾'),
                const SizedBox(width: 8),
                _buildFilterChip('विषय ▾'),
                const SizedBox(width: 8),
                _buildFilterChip('स्तर ▾'),
              ],
            ),
          ),

          const SizedBox(height: 8),

          // PYQ Papers List
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 110),
              itemCount: _pyqPapers.length,
              itemBuilder: (context, index) {
                final p = _pyqPapers[index];
                final Color color = p['color'] as Color;

                return BouncingWrapper(
                  isBubbleSound: true,
                  onTap: () {
                    soundService.playClick();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('${p['year']} चाचणी सुरू होत आहे...')),
                    );
                  },
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0A0E17),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.08)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 44,
                          height: 48,
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.18),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: color.withOpacity(0.5)),
                          ),
                          child: Icon(Icons.menu_book, color: color, size: 22),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                p['year'] as String,
                                style: GoogleFonts.notoSansDevanagari(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${p['subject']} • ${p['questions']}',
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
                );
              },
            ),
          ),
        ],
      ),

      // Floating "+ PYQ जोडा" button
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 50),
        child: BouncingWrapper(
          isBubbleSound: true,
          onTap: () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('नवीन PYQ संच जोडण्यासाठी PDF लायब्ररी वापरा.')),
            );
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2979FF), Color(0xFF7B1FA2)],
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2979FF).withOpacity(0.5),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.add, color: Colors.white, size: 20),
                const SizedBox(width: 8),
                Text(
                  '+ PYQ जोडा',
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label) {
    return BouncingWrapper(
      onTap: () => soundService.playClick(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF0D1322),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white12),
        ),
        child: Text(
          label,
          style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
        ),
      ),
    );
  }
}
