import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/books/book_chatgpt_workspace_screen.dart';

class PDFReaderScreen extends StatefulWidget {
  final BookModel book;
  final int initialPage;

  const PDFReaderScreen({
    super.key,
    required this.book,
    this.initialPage = 1,
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
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
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
                '$_currentPage / ${widget.book.totalPages > 0 ? widget.book.totalPages : 1}',
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
                  width: double.infinity,
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
                        widget.book.title,
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFF00E5FF),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'विषय: ${widget.book.subjectName} • ${widget.book.totalPages} पाने',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 12,
                          color: Colors.white70,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 14),

                // Content Box
                Container(
                  width: double.infinity,
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
                        '📖 वाचन विभाग (Reading Pane)',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFF00E676),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'या फाईलमधील मजकूर AI द्वारे RAG प्रणालीमध्ये इंडेक्स झाला आहे. '
                        'कोणत्याही मुद्द्याचे विश्लेषण, MCQ, सारांश किंवा स्पष्टीकरणासाठी खालील "🤖 ChatGPT" बटण वापरा.',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 13,
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

          // Bottom Floating Toolbar (हायलाईट, बुकमार्क, ChatGPT)
          Positioned(
            left: 20,
            right: 20,
            bottom: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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
                    icon: _isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                    label: 'बुकमार्क',
                    onTap: () {
                      soundService.playBubble();
                      setState(() => _isBookmarked = !_isBookmarked);
                    },
                  ),
                  _buildToolbarItem(
                    icon: Icons.smart_toy_outlined,
                    label: 'ChatGPT सोबत चर्चा',
                    isSpecial: true,
                    onTap: () {
                      soundService.playBubble();
                      Navigator.of(context).push(MaterialPageRoute(
                        builder: (ctx) => BookChatGPTWorkspaceScreen(
                          book: widget.book,
                        ),
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
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: isSpecial
            ? BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.18),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF00E5FF)),
              )
            : null,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: isSpecial ? const Color(0xFF00E5FF) : Colors.white70, size: 18),
            const SizedBox(width: 6),
            Text(
              label,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 11,
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
