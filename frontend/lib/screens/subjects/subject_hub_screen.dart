import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';

class SubjectHubScreen extends StatelessWidget {
  final Function(int) onNavigateTab;

  const SubjectHubScreen({super.key, required this.onNavigateTab});

  static final List<Map<String, dynamic>> subjectsList = [
    {'title': 'इतिहास', 'icon': Icons.history_edu, 'color': Color(0xFFFF5252)},
    {'title': 'भूगोल', 'icon': Icons.public, 'color': Color(0xFF00E5FF)},
    {'title': 'राज्यशास्त्र', 'icon': Icons.account_balance, 'color': Color(0xFF2979FF)},
    {'title': 'अर्थशास्त्र', 'icon': Icons.trending_up, 'color': Color(0xFFD500F9)},
    {'title': 'महाराष्ट्र विशेष', 'icon': Icons.castle, 'color': Color(0xFFFF9100)},
    {'title': 'सामान्य विज्ञान', 'icon': Icons.science, 'color': Color(0xFF00E676)},
    {'title': 'पर्यावरण', 'icon': Icons.eco, 'color': Color(0xFF76FF03)},
    {'title': 'चालू घडामोडी', 'icon': Icons.newspaper, 'color': Color(0xFFFF4081)},
    {'title': 'नागरीक शास्त्र', 'icon': Icons.gavel, 'color': Color(0xFF00B0FF)},
    {'title': 'गणित', 'icon': Icons.calculate, 'color': Color(0xFFFFD600)},
    {'title': 'बुद्धिमत्ता', 'icon': Icons.psychology, 'color': Color(0xFFE040FB)},
    {'title': 'PYQ संच', 'icon': Icons.folder_special, 'color': Color(0xFF00E5FF)},
    {'title': 'Notes', 'icon': Icons.sticky_note_2, 'color': Color(0xFF69F0AE)},
    {'title': 'इतर', 'icon': Icons.more_horiz, 'color': Colors.white70},
  ];

  @override
  Widget build(BuildContext context) {
    final booksProv = context.read<BooksProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        title: Text(
          'विषय',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: GridView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 90),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 0.95,
        ),
        itemCount: subjectsList.length,
        itemBuilder: (context, index) {
          final s = subjectsList[index];
          final Color color = s['color'] as Color;

          return BouncingWrapper(
            isBubbleSound: true,
            onTap: () {
              booksProv.setSelectedSubject(s['title']);
              onNavigateTab(2); // Go to Books Library
            },
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: color.withOpacity(0.4),
                  width: 1.2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: color.withOpacity(0.18),
                    blurRadius: 10,
                  ),
                ],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: color.withOpacity(0.15),
                    ),
                    child: Icon(s['icon'] as IconData, color: color, size: 24),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    s['title'] as String,
                    textAlign: TextAlign.center,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
