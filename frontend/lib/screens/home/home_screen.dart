import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/providers/progress_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/liquid_glass_card.dart';
import 'package:frontend/widgets/cyber_drawer.dart';
import 'package:frontend/screens/books/pdf_reader_screen.dart';
import 'package:frontend/screens/mj/mj_assistant_screen.dart';

class HomeScreen extends StatefulWidget {
  final Function(int) onNavigateTab;

  const HomeScreen({super.key, required this.onNavigateTab});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    final booksProv = context.watch<BooksProvider>();
    final progressProv = context.watch<ProgressProvider>();

    final progress = progressProv.progress;
    final double prepPct = progress?.preparationPercentage ?? 0.0;
    final int streak = progress?.streakDays ?? 0;
    final double progressFactor = (prepPct / 100.0).clamp(0.0, 1.0);

    final bool hasBooks = booksProv.allBooks.isNotEmpty;
    final activeBook = hasBooks ? booksProv.allBooks.first : null;

    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      drawer: CyberDrawer(onSelectTab: widget.onNavigateTab),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  'शुभ प्रभात, 👋 ',
                  style: GoogleFonts.notoSansDevanagari(fontSize: 14, color: Colors.white70),
                ),
                Text(
                  'Rutik!',
                  style: GoogleFonts.poppins(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ],
            ),
          ],
        ),
        actions: [
          BouncingWrapper(
            isBubbleSound: true,
            onTap: () {
              Navigator.of(context).push(MaterialPageRoute(
                builder: (ctx) => MJAssistantScreen(onNavigateTab: widget.onNavigateTab),
              ));
            },
            child: Container(
              margin: const EdgeInsets.only(right: 14),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF00E5FF), Color(0xFFD500F9)],
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF00E5FF).withOpacity(0.5),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: const Icon(Icons.mic, color: Colors.white, size: 20),
            ),
          ),
          BouncingWrapper(
            onTap: () {
              soundService.playClick();
              _scaffoldKey.currentState?.openDrawer();
            },
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: Icon(Icons.more_vert, color: Colors.white70, size: 22),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 100),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. तुमची तयारी Card (Screen 2) - 100% Real DB Data
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
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'तुमची तयारी',
                            style: GoogleFonts.notoSansDevanagari(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: Colors.white70,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${prepPct.toStringAsFixed(0)}%',
                            style: GoogleFonts.poppins(
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            streak > 0 ? '$streak दिवस streak 🔥' : 'अजून अभ्यास सुरू केलेला नाही.',
                            style: GoogleFonts.notoSansDevanagari(
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                              color: streak > 0 ? const Color(0xFFFF9100) : Colors.white54,
                            ),
                          ),
                        ],
                      ),

                      // Circular Gauge Ring
                      Stack(
                        alignment: Alignment.center,
                        children: [
                          SizedBox(
                            width: 60,
                            height: 60,
                            child: CircularProgressIndicator(
                              value: progressFactor,
                              strokeWidth: 6,
                              backgroundColor: Colors.white12,
                              color: const Color(0xFF00E5FF),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Bottom linear progress gradient line
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: Container(
                      height: 4,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.white12,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: progressFactor > 0.0 ? progressFactor : 0.001,
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFF00E5FF), Color(0xFF7B1FA2)],
                            ),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // 2. पुढे सुरू ठेवा Card (Screen 2) - Real Book or Clean Empty CTA
            Text(
              'पुढे सुरू ठेवा',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 10),

            LiquidGlassCard(
              variant: GlowVariant.blue,
              padding: const EdgeInsets.all(14),
              margin: EdgeInsets.zero,
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 52,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: hasBooks
                            ? [const Color(0xFF1565C0), const Color(0xFF00E5FF)]
                            : [const Color(0xFF37474F), const Color(0xFF455A64)],
                      ),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Icon(
                        hasBooks ? Icons.menu_book : Icons.library_add,
                        color: Colors.white,
                        size: 22,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          hasBooks ? activeBook!.title : 'अजून पुस्तक सुरू केलेले नाही.',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          hasBooks
                              ? '${activeBook!.subjectName} • ${activeBook.progressPercent.toStringAsFixed(0)}% पूर्ण'
                              : 'अभ्यासासाठी तुमचे पहिले PDF पुस्तक जोडा',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 11,
                            color: Colors.white60,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),

                  BouncingWrapper(
                    isBubbleSound: true,
                    onTap: () {
                      if (hasBooks) {
                        Navigator.of(context).push(MaterialPageRoute(
                          builder: (ctx) => PDFReaderScreen(book: activeBook!),
                        ));
                      } else {
                        widget.onNavigateTab(2); // Books tab
                      }
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF7B1FA2), Color(0xFF2979FF)],
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF7B1FA2).withOpacity(0.5),
                            blurRadius: 8,
                          ),
                        ],
                      ),
                      child: Text(
                        hasBooks ? 'सुरू ठेवा' : 'PDF जोडा',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 22),

            // 3. जलद प्रवेश (Quick Action Capsules matching Master Design)
            Text(
              'जलद प्रवेश',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildQuickActionTile('माझी पुस्तके', Icons.menu_book_outlined, const Color(0xFFFF5252), () => widget.onNavigateTab(2)),
                _buildQuickActionTile('AI शिक्षक', Icons.psychology_outlined, const Color(0xFF9C27B0), () => widget.onNavigateTab(1)),
                _buildQuickActionTile('चाचणी', Icons.quiz_outlined, const Color(0xFF2979FF), () => widget.onNavigateTab(3)),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildQuickActionTile('चालू घडामोडी', Icons.newspaper, const Color(0xFFFF4081), () => widget.onNavigateTab(9)),
                _buildQuickActionTile('Revision', Icons.repeat, const Color(0xFF00E5FF), () => widget.onNavigateTab(5)),
                _buildQuickActionTile('PYQ', Icons.history_edu, const Color(0xFFFF9100), () => widget.onNavigateTab(4)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActionTile(String label, IconData icon, Color color, VoidCallback onTap) {
    return Expanded(
      child: BouncingWrapper(
        isBubbleSound: true,
        onTap: onTap,
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: const Color(0xFF0A0E17),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: color.withOpacity(0.35), width: 1.0),
            boxShadow: [
              BoxShadow(
                color: color.withOpacity(0.12),
                blurRadius: 8,
              ),
            ],
          ),
          child: Column(
            children: [
              Icon(icon, color: color, size: 22),
              const SizedBox(height: 6),
              Text(
                label,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w600,
                  color: Colors.white.withOpacity(0.9),
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
