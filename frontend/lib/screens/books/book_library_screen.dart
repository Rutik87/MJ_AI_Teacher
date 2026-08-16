import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/core/services/sync_service.dart';
import 'package:frontend/core/services/offline_book_service.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/cyber_drawer.dart';
import 'package:frontend/screens/books/book_upload_dialog.dart';
import 'package:frontend/screens/books/pdf_reader_screen.dart';
import 'package:frontend/screens/books/book_chatgpt_workspace_screen.dart';

class BookLibraryScreen extends StatefulWidget {
  const BookLibraryScreen({super.key});

  @override
  State<BookLibraryScreen> createState() => _BookLibraryScreenState();
}

class _BookLibraryScreenState extends State<BookLibraryScreen> {
  final TextEditingController _searchCtrl = TextEditingController();

  final List<String> _filters = ['सर्व', 'इतिहास', 'राज्यशास्त्र', 'अर्थशास्त्र', 'भूगोल'];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _confirmAndDeleteBook(
    BuildContext context,
    BookModel book,
    BooksProvider booksProv,
    SyncService syncService,
    OfflineBookService offlineService,
  ) {
    soundService.playBubble();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0E17),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide(color: Colors.redAccent.withOpacity(0.4)),
        ),
        title: Row(
          children: [
            const Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'पुस्तक हटवायचे आहे का?',
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '\"${book.title}\" हे पुस्तक कायमचे हटवायचे आहे का?',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.redAccent.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.redAccent.withOpacity(0.25)),
              ),
              child: Text(
                '⚠️ PDF/TXT फाईल, RAG इंडेक्स आणि चॅट संदर्भ कायमचे हटवले जातील.',
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 11.5,
                  color: Colors.white70,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              soundService.playClick();
              Navigator.of(ctx).pop();
            },
            child: Text(
              'रद्द करा (Cancel)',
              style: GoogleFonts.notoSansDevanagari(color: Colors.white60, fontSize: 12),
            ),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFD50000),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () async {
              soundService.playClick();
              Navigator.of(ctx).pop();

              if (!syncService.isOnline) {
                await syncService.queueAction(
                  actionType: 'delete_book',
                  payload: {'book_id': book.id},
                );
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('इंटरनेट कनेक्शन उपलब्ध नाही. Delete request queue केली आहे.'),
                      backgroundColor: Color(0xFF37474F),
                    ),
                  );
                }
                return;
              }

              final success = await booksProv.deleteBook(book.id);
              if (success) {
                await offlineService.removeOfflineBook(book.id);

                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('पुस्तक यशस्वीरित्या हटवले.'),
                      backgroundColor: Color(0xFF2E7D32),
                    ),
                  );
                }
              } else {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('पुस्तक हटवता आले नाही. कृपया पुन्हा प्रयत्न करा.'),
                      backgroundColor: Color(0xFFC62828),
                    ),
                  );
                }
              }
            },
            child: Text(
              'हटवा (Delete)',
              style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final booksProv = context.watch<BooksProvider>();
    final syncService = context.watch<SyncService>();
    final offlineService = context.watch<OfflineBookService>();
    final books = booksProv.books;

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      drawer: CyberDrawer(onSelectTab: (idx) {}),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: Builder(
          builder: (ctx) => IconButton(
            icon: const Icon(Icons.menu_rounded, color: Colors.white, size: 24),
            onPressed: () => Scaffold.of(ctx).openDrawer(),
          ),
        ),
        title: Text(
          '📚 Files & Books (माझी पुस्तके)',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        actions: [
          BouncingWrapper(
            onTap: () {
              soundService.playClick();
              syncService.checkConnectivityAndSync();
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: Row(
                children: [
                  Icon(
                    syncService.isOnline ? Icons.cloud_done : Icons.cloud_off,
                    color: syncService.isOnline ? const Color(0xFF00E5FF) : const Color(0xFFFF5252),
                    size: 20,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    syncService.isOnline ? 'Cloud' : 'Offline',
                    style: GoogleFonts.poppins(fontSize: 11, color: Colors.white70),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // 1. Live Search Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 6),
            child: Container(
              height: 44,
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.white12),
              ),
              child: TextField(
                controller: _searchCtrl,
                style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white),
                onChanged: (val) => booksProv.setSearchQuery(val),
                decoration: InputDecoration(
                  hintText: 'पुस्तके किंवा विषय शोधा...',
                  hintStyle: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white38),
                  prefixIcon: const Icon(Icons.search, color: Color(0xFF00E5FF), size: 20),
                  suffixIcon: _searchCtrl.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, color: Colors.white54, size: 18),
                          onPressed: () {
                            _searchCtrl.clear();
                            booksProv.setSearchQuery('');
                          },
                        )
                      : null,
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(vertical: 10),
                ),
              ),
            ),
          ),

          // 2. Filter Pills
          SizedBox(
            height: 38,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 14),
              itemCount: _filters.length,
              itemBuilder: (context, index) {
                final f = _filters[index];
                final isSelected = (f == 'सर्व' && booksProv.selectedSubject == 'All') ||
                    (f == booksProv.selectedSubject);

                return BouncingWrapper(
                  isBubbleSound: true,
                  onTap: () {
                    booksProv.setSelectedSubject(f == 'सर्व' ? 'All' : f);
                  },
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    decoration: BoxDecoration(
                      color: isSelected ? const Color(0xFF00E5FF).withOpacity(0.2) : const Color(0xFF0A0E17),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isSelected ? const Color(0xFF00E5FF) : Colors.white12,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        f,
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 11.5,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? const Color(0xFF00E5FF) : Colors.white70,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 8),

          // 3. Books List View
          Expanded(
            child: booksProv.isLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
                : books.isEmpty
                    ? _buildEmptyState(context)
                    : RefreshIndicator(
                        onRefresh: () => booksProv.fetchBooks(),
                        color: const Color(0xFF00E5FF),
                        backgroundColor: const Color(0xFF0A0E17),
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 100),
                          itemCount: books.length,
                          itemBuilder: (context, index) {
                            final book = books[index];
                            return _buildBookItemCard(
                              context,
                              book,
                              index,
                              offlineService,
                              booksProv,
                              syncService,
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),

      // 4. Floating "+ Cloud वर PDF जोडा" Gradient Button
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 60),
        child: BouncingWrapper(
          isBubbleSound: true,
          onTap: () {
            showDialog(
              context: context,
              builder: (ctx) => const BookUploadDialog(),
            );
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2979FF), Color(0xFF00E5FF)],
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF00E5FF).withOpacity(0.4),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.cloud_upload_outlined, color: Colors.black, size: 20),
                const SizedBox(width: 8),
                Text(
                  '+ फाईल जोडा (PDF / TXT Upload)',
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Colors.black,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.cloud_queue, size: 56, color: Colors.white.withOpacity(0.2)),
          const SizedBox(height: 12),
          Text(
            'कोणतीही फाईल किंवा पुस्तक सापडले नाही',
            style: GoogleFonts.notoSansDevanagari(fontSize: 14, color: Colors.white60),
          ),
          const SizedBox(height: 6),
          Text(
            'खालील बटण वापरून PDF किंवा TXT अपलोड करा',
            style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white38),
          ),
        ],
      ),
    );
  }

  Widget _buildBookItemCard(
    BuildContext context,
    BookModel book,
    int index,
    OfflineBookService offlineService,
    BooksProvider booksProv,
    SyncService syncService,
  ) {
    final isTxt = book.sourceType == 'txt' || book.originalFilename.toLowerCase().endsWith('.txt');
    final isDownloaded = offlineService.isBookDownloaded(book.id);

    return BouncingWrapper(
      onTap: () {
        soundService.playClick();
        Navigator.of(context).push(MaterialPageRoute(
          builder: (ctx) => PDFReaderScreen(book: book),
        ));
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          children: [
            // Book Icon Capsule (PDF vs TXT)
            Container(
              width: 44,
              height: 52,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: isTxt
                      ? [const Color(0xFF0091EA), const Color(0xFF00E5FF)]
                      : [const Color(0xFF2979FF), const Color(0xFF00E676)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                isTxt ? Icons.description : Icons.picture_as_pdf,
                color: Colors.white,
                size: 24,
              ),
            ),
            const SizedBox(width: 14),

            // Book Meta & Title
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          book.title,
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: isDownloaded
                              ? const Color(0xFF00E676).withOpacity(0.15)
                              : const Color(0xFF00E5FF).withOpacity(0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          isDownloaded ? '📥 Offline' : '☁️ Cloud',
                          style: GoogleFonts.poppins(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: isDownloaded ? const Color(0xFF00E676) : const Color(0xFF00E5FF),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${isTxt ? "TXT नोट्स" : "${book.totalPages} पाने"} • ${(book.fileSizeBytes / (1024 * 1024)).toStringAsFixed(2)} MB',
                    style: GoogleFonts.poppins(fontSize: 10.5, color: Colors.white54),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),

            // Actions: 1. Chat with this file | 2. Download | 3. Delete
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Chat With This File Action
                BouncingWrapper(
                  onTap: () {
                    soundService.playBubble();
                    Navigator.of(context).push(MaterialPageRoute(
                      builder: (ctx) => BookChatGPTWorkspaceScreen(
                        book: book,
                      ),
                    ));
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00E676).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFF00E676).withOpacity(0.4)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.smart_toy_outlined, color: Color(0xFF00E676), size: 16),
                        const SizedBox(width: 4),
                        Text(
                          'चॅट',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: const Color(0xFF00E676),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Download/Offline toggle
                BouncingWrapper(
                  onTap: () {
                    if (isDownloaded) {
                      offlineService.removeOfflineBook(book.id);
                    } else {
                      offlineService.downloadBookForOffline(book);
                    }
                  },
                  child: Icon(
                    isDownloaded ? Icons.download_done : Icons.download_for_offline_outlined,
                    color: isDownloaded ? const Color(0xFF00E676) : Colors.white38,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 8),

                // Delete file
                BouncingWrapper(
                  onTap: () => _confirmAndDeleteBook(
                    context,
                    book,
                    booksProv,
                    syncService,
                    offlineService,
                  ),
                  child: const Icon(
                    Icons.delete_outline,
                    color: Colors.white38,
                    size: 20,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
