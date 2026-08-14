import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/providers/mj_voice_provider.dart';
import 'package:frontend/screens/mj/mj_assistant_screen.dart';

class PDFReaderScreen extends StatefulWidget {
  final BookModel book;
  final int initialPage;

  const PDFReaderScreen({
    super.key,
    required this.book,
    this.initialPage = 124,
  });

  @override
  State<PDFReaderScreen> createState() => _PDFReaderScreenState();
}

class _PDFReaderScreenState extends State<PDFReaderScreen> {
  late int _currentPage;
  bool _isBookmarked = false;
  bool _isHighlighted = false;

  @override
  void initState() {
    super.initState();
    _currentPage = widget.initialPage;
  }

  @override
  Widget build(BuildContext context) {
    final audioService = context.watch<AudioService>();

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: BouncingWrapper(
          onTap: () {
            soundService.playClick();
            Navigator.of(context).pop();
          },
          child: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: Text(
          widget.book.title,
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 15,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        actions: [
          BouncingWrapper(
            onTap: () {
              soundService.playBubble();
              setState(() => _isBookmarked = !_isBookmarked);
            },
            child: Icon(
              _isBookmarked ? Icons.bookmark : Icons.bookmark_border,
              color: _isBookmarked ? const Color(0xFF00E5FF) : Colors.white70,
            ),
          ),
          const SizedBox(width: 10),
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 14),
              child: Text(
                '$_currentPage / ${widget.book.totalPages > 0 ? widget.book.totalPages : 512}',
                style: GoogleFonts.poppins(fontSize: 11, color: Colors.white60),
              ),
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Reader Content
          SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 110),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Title Heading
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0E17),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withOpacity(0.08)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'मूलभूत अधिकार (Fundamental Rights)',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFF00E5FF),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'भारतीय राज्यघटनेतील मूलभूत अधिकार हे नागरिकांना दिलेले महत्त्वाचे हक्क आहेत जे भाग ३ (कलम १२ ते ३५) मध्ये नमूद केले आहेत.',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 14,
                          height: 1.6,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 14),

                // Article 14 Section
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0E17),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: _isHighlighted ? const Color(0xFFFFD600) : Colors.white.withOpacity(0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'कलम १४ : कायद्यापुढील समानता',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFF9C27B0),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'कायद्यापुढे सर्व नागरिक समान आहेत आणि सर्वांना कायद्याचे समान संरक्षण मिळण्याचा मूलभूत हक्क आहे.\n\n'
                        '१. कायद्यापुढे समानता (Equality before Law) - ही संकल्पना ब्रिटिश घटनेवरून घेतली आहे.\n'
                        '२. कायद्याचे समान संरक्षण (Equal Protection of Laws) - ही संकल्पना अमेरिकन घटनेवरून घेतली आहे.',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 13.5,
                          height: 1.6,
                          color: Colors.white.withOpacity(0.85),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Bottom Floating Toolbar (Screen 5: हायलाईट, शोधा, बुकमार्क, AI ला विचारा)
          Positioned(
            left: 16,
            right: 16,
            bottom: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0F1E).withOpacity(0.95),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF00E5FF).withOpacity(0.2),
                    blurRadius: 16,
                  ),
                ],
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildToolbarItem(
                    icon: Icons.format_paint,
                    label: 'हायलाईट',
                    onTap: () {
                      soundService.playBubble();
                      setState(() => _isHighlighted = !_isHighlighted);
                    },
                  ),
                  _buildToolbarItem(
                    icon: Icons.search,
                    label: 'शोधा',
                    onTap: () => soundService.playClick(),
                  ),
                  _buildToolbarItem(
                    icon: _isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                    label: 'बुकमार्क',
                    onTap: () {
                      soundService.playBubble();
                      setState(() => _isBookmarked = !_isBookmarked);
                    },
                  ),
                  _buildToolbarItem(
                    icon: Icons.psychology,
                    label: 'AI ला विचारा',
                    isSpecial: true,
                    onTap: () {
                      soundService.playBubble();
                      final mjProv = context.read<MJVoiceProvider>();
                      mjProv.setContext(bookId: widget.book.id, currentPage: _currentPage);
                      Navigator.of(context).push(MaterialPageRoute(
                        builder: (ctx) => const MJAssistantScreen(),
                      ));
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildToolbarItem({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool isSpecial = false,
  }) {
    return BouncingWrapper(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: isSpecial
            ? BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.18),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF00E5FF)),
              )
            : null,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: isSpecial ? const Color(0xFF00E5FF) : Colors.white70, size: 20),
            const SizedBox(height: 2),
            Text(
              label,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 10,
                color: isSpecial ? const Color(0xFF00E5FF) : Colors.white70,
                fontWeight: isSpecial ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
