import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/handwritten_note.dart';
import 'package:frontend/providers/notes_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';

class HandwrittenNotesScreen extends StatefulWidget {
  final int bookId;
  final String bookTitle;

  const HandwrittenNotesScreen({
    super.key,
    required this.bookId,
    required this.bookTitle,
  });

  @override
  State<HandwrittenNotesScreen> createState() => _HandwrittenNotesScreenState();
}

class _HandwrittenNotesScreenState extends State<HandwrittenNotesScreen> with SingleTickerProviderStateMixin {
  int _selectedChapterIndex = 0;
  TabController? _tabController;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotesProvider>().fetchNotesStatus(widget.bookId);
    });
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  void _initTabController(int count) {
    if (_tabController == null || _tabController!.length != count) {
      _tabController?.dispose();
      _tabController = TabController(length: count > 0 ? count : 1, vsync: this);
      _tabController!.addListener(() {
        if (_tabController!.indexIsChanging) {
          setState(() {
            _selectedChapterIndex = _tabController!.index;
          });
        }
      });
    }
  }

  void _confirmDelete(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF141C2B),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: Row(
          children: [
            const Icon(Icons.delete_outline, color: Colors.redAccent, size: 24),
            const SizedBox(width: 8),
            Text(
              'नोट्स हटवायच्या आहेत का?',
              style: GoogleFonts.notoSansDevanagari(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ],
        ),
        content: Text(
          'या पुस्तकासाठी तयार केलेल्या सर्व हस्तलिखित नोट्स आणि PDF फाईल कायमच्या हटवल्या जातील.',
          style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('रद्द करा', style: GoogleFonts.notoSansDevanagari(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.redAccent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () async {
              Navigator.of(ctx).pop();
              soundService.playClick();
              final success = await context.read<NotesProvider>().deleteNotes(widget.bookId);
              if (success && mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('नोट्स यशस्वीरित्या हटवण्यात आल्या.', style: GoogleFonts.notoSansDevanagari()),
                    backgroundColor: Colors.redAccent,
                  ),
                );
                Navigator.of(context).pop();
              }
            },
            child: Text('हटवा', style: GoogleFonts.notoSansDevanagari(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final notesProv = context.watch<NotesProvider>();
    final audioService = context.watch<AudioService>();
    final note = notesProv.getNoteForBook(widget.bookId);

    if (note != null && note.chapters.isNotEmpty) {
      _initTabController(note.chapters.length);
    }

    return Scaffold(
      backgroundColor: const Color(0xFF070B14),
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
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '✍️ हस्तलिखित नोट्स',
              style: GoogleFonts.notoSansDevanagari(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            Text(
              widget.bookTitle,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: const Color(0xFF00E5FF)),
            ),
          ],
        ),
        actions: [
          if (note != null && note.hasNotes) ...[
            BouncingWrapper(
              onTap: () {
                soundService.playClick();
                _confirmDelete(context);
              },
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 8),
                child: Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
              ),
            ),
          ],
        ],
      ),
      body: note == null || !note.hasNotes
          ? _buildEmptyOrLoadingState(notesProv)
          : _buildNotebookContentView(note, audioService),
    );
  }

  Widget _buildEmptyOrLoadingState(NotesProvider notesProv) {
    if (notesProv.isGenerating) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(color: Color(0xFF00E5FF)),
              const SizedBox(height: 24),
              Text(
                notesProv.currentStepMessage,
                textAlign: TextAlign.center,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFF00E5FF),
                ),
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: notesProv.currentProgress,
                backgroundColor: Colors.white10,
                color: const Color(0xFF00E5FF),
                minHeight: 6,
                borderRadius: BorderRadius.circular(4),
              ),
              const SizedBox(height: 8),
              Text(
                'संपूर्ण पुस्तकातील प्रकरणांचे विश्लेषण चालू आहे...',
                style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white54),
              ),
            ],
          ),
        ),
      );
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF00E5FF).withOpacity(0.12),
              ),
              child: const Icon(Icons.edit_note, size: 54, color: Color(0xFF00E5FF)),
            ),
            const SizedBox(height: 20),
            Text(
              'हस्तलिखित नोट्स अजून तयार केलेल्या नाहीत',
              textAlign: TextAlign.center,
              style: GoogleFonts.notoSansDevanagari(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 8),
            Text(
              'MJ AI या पुस्तकातील सर्व प्रकरणे वाचून परीक्षा-अभिमुख नोट्स तयार करेल.',
              textAlign: TextAlign.center,
              style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white60),
            ),
            const SizedBox(height: 24),
            BouncingWrapper(
              isBubbleSound: true,
              onTap: () {
                context.read<NotesProvider>().generateNotes(widget.bookId);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(25),
                  gradient: const LinearGradient(colors: [Color(0xFF00E5FF), Color(0xFF7B1FA2)]),
                ),
                child: Text(
                  '✍️ Handwritten Notes बनवा',
                  style: GoogleFonts.notoSansDevanagari(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotebookContentView(HandwrittenNoteModel note, AudioService audioService) {
    final currentCh = note.chapters[_selectedChapterIndex];

    return Column(
      children: [
        // Chapter selector tab bar
        if (note.chapters.length > 1 && _tabController != null)
          Container(
            height: 48,
            decoration: BoxDecoration(
              color: const Color(0xFF0E1524),
              border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
            ),
            child: TabBar(
              controller: _tabController,
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              indicatorColor: const Color(0xFF00E5FF),
              labelColor: const Color(0xFF00E5FF),
              unselectedLabelColor: Colors.white54,
              labelStyle: GoogleFonts.notoSansDevanagari(fontSize: 12, fontWeight: FontWeight.bold),
              unselectedLabelStyle: GoogleFonts.notoSansDevanagari(fontSize: 12),
              tabs: note.chapters.map((ch) {
                return Tab(text: 'प्रकरण ${ch.chapterNumber}');
              }).toList(),
            ),
          ),

        // Action Toolbar (Download PDF / Audio / Regenerate)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: const Color(0xFF0A0E1A),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'प्रकरण ${_selectedChapterIndex + 1} / ${note.chapters.length}',
                style: GoogleFonts.poppins(fontSize: 11, color: Colors.white60, fontWeight: FontWeight.w500),
              ),
              Row(
                children: [
                  // Audio Explain Button
                  BouncingWrapper(
                    onTap: () {
                      soundService.playClick();
                      audioService.speakText(
                        'प्रकरण ${currentCh.chapterNumber}: ${currentCh.headingMr}. ${currentCh.shortDefinitionMr}',
                        emotion: 'friendly',
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00E5FF).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.volume_up, size: 14, color: Color(0xFF00E5FF)),
                          const SizedBox(width: 4),
                          Text(
                            'MJ आवाज',
                            style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: const Color(0xFF00E5FF), fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Download PDF Button
                  BouncingWrapper(
                    onTap: () {
                      soundService.playClick();
                      if (note.pdfUrl != null) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('PDF डाऊनलोड लिंक तयार आहे!', style: GoogleFonts.notoSansDevanagari()),
                            backgroundColor: const Color(0xFF00E5FF),
                          ),
                        );
                      }
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: const Color(0xFF7B1FA2).withOpacity(0.2),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF7B1FA2).withOpacity(0.5)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.download, size: 14, color: Colors.white),
                          const SizedBox(width: 4),
                          Text(
                            'PDF',
                            style: GoogleFonts.poppins(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Scrollable Notebook Page View
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(14),
            child: _buildNotebookPage(currentCh),
          ),
        ),
      ],
    );
  }

  Widget _buildNotebookPage(NoteChapterModel ch) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFCFCFC), // Crisp white notebook paper
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Stack(
        children: [
          // Ruled Red Left Margin
          Positioned(
            left: 28,
            top: 0,
            bottom: 0,
            child: Container(
              width: 1.5,
              color: const Color(0xFFFFB4B4),
            ),
          ),

          // Notebook Content
          Padding(
            padding: const EdgeInsets.fromLTRB(42, 20, 18, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Chapter Heading
                Text(
                  ch.headingMr,
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF0D1B2A),
                    height: 1.3,
                  ),
                ),
                if (ch.subheadingMr.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(
                    ch.subheadingMr,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                      color: const Color(0xFF555555),
                    ),
                  ),
                ],
                const SizedBox(height: 14),

                // 1. Definition Box (Soft Cyan Theme)
                if (ch.shortDefinitionMr.isNotEmpty)
                  _buildCalloutBox(
                    title: '📌 व्याख्या / प्रस्तावना',
                    content: ch.shortDefinitionMr,
                    bgColor: const Color(0xFFE6F7FF),
                    borderColor: const Color(0xFF1890FF),
                    textColor: const Color(0xFF003A8C),
                  ),

                // 2. Key Points
                if (ch.keyPoints.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text(
                    '📝 मुख्य मुद्दे (Key Points):',
                    style: GoogleFonts.notoSansDevanagari(fontSize: 13, fontWeight: FontWeight.bold, color: const Color(0xFF0D1B2A)),
                  ),
                  const SizedBox(height: 6),
                  ...ch.keyPoints.map((kp) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('• ', style: TextStyle(color: Color(0xFF1890FF), fontSize: 14, fontWeight: FontWeight.bold)),
                        Expanded(
                          child: Text(
                            kp,
                            style: GoogleFonts.notoSansDevanagari(fontSize: 12.5, color: const Color(0xFF1A202C), height: 1.45),
                          ),
                        ),
                      ],
                    ),
                  )),
                ],

                // 3. Important Concepts
                if (ch.importantConcepts.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text(
                    '💡 महत्त्वाच्या संकल्पना:',
                    style: GoogleFonts.notoSansDevanagari(fontSize: 13, fontWeight: FontWeight.bold, color: const Color(0xFF0D1B2A)),
                  ),
                  const SizedBox(height: 6),
                  ...ch.importantConcepts.map((c) => Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8F9FA),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          c.titleMr,
                          style: GoogleFonts.notoSansDevanagari(fontSize: 12, fontWeight: FontWeight.bold, color: const Color(0xFF2B6CB0)),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          c.explanationMr,
                          style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: const Color(0xFF2D3748), height: 1.4),
                        ),
                      ],
                    ),
                  )),
                ],

                // 4. Comparison Table
                if (ch.table != null && ch.table!.headers.isNotEmpty && ch.table!.rows.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text(
                    '📊 ${ch.table!.titleMr}:',
                    style: GoogleFonts.notoSansDevanagari(fontSize: 13, fontWeight: FontWeight.bold, color: const Color(0xFF0D1B2A)),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFCBD5E1)),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Table(
                        border: TableBorder.all(color: const Color(0xFFE2E8F0), width: 0.8),
                        children: [
                          TableRow(
                            decoration: const BoxDecoration(color: Color(0xFFEEF2F6)),
                            children: ch.table!.headers.map((h) => Padding(
                              padding: const EdgeInsets.all(6),
                              child: Text(h, style: GoogleFonts.notoSansDevanagari(fontSize: 11, fontWeight: FontWeight.bold, color: const Color(0xFF1E293B))),
                            )).toList(),
                          ),
                          ...ch.table!.rows.map((row) => TableRow(
                            children: row.map((cell) => Padding(
                              padding: const EdgeInsets.all(6),
                              child: Text(cell, style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: const Color(0xFF334155))),
                            )).toList(),
                          )),
                        ],
                      ),
                    ),
                  ),
                ],

                // 5. Exam High-Yield Points (Amber Theme)
                if (ch.examPoints.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  _buildCalloutBox(
                    title: '🎯 MPSC परीक्षेसाठी अति-महत्त्वाचे (Exam Alert)',
                    content: ch.examPoints.join('\n\n• '),
                    bgColor: const Color(0xFFFFF7E6),
                    borderColor: const Color(0xFFFA8C16),
                    textColor: const Color(0xFF873800),
                  ),
                ],

                // 6. Quick Revision Box (Yellow Theme)
                if (ch.quickRevisionBox.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  _buildCalloutBox(
                    title: '⚡ Quick Revision (उजळणी)',
                    content: ch.quickRevisionBox.join('\n• '),
                    bgColor: const Color(0xFFFEFFE6),
                    borderColor: const Color(0xFFFAAD14),
                    textColor: const Color(0xFF614700),
                  ),
                ],

                // 7. Common Mistakes Box (Red Theme)
                if (ch.commonMistakes.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  _buildCalloutBox(
                    title: '⚠️ संभ्रम व सामान्य चुका टाळा',
                    content: ch.commonMistakes.join('\n• '),
                    bgColor: const Color(0xFFFFF1F0),
                    borderColor: const Color(0xFFFF4D4F),
                    textColor: const Color(0xFF820014),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCalloutBox({
    required String title,
    required String content,
    required Color bgColor,
    required Color borderColor,
    required Color textColor,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: borderColor, width: 1.2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: GoogleFonts.notoSansDevanagari(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: textColor,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            content,
            style: GoogleFonts.notoSansDevanagari(
              fontSize: 12,
              color: const Color(0xFF1F2937),
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}
