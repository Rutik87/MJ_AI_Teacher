import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/core/services/sync_service.dart';
import 'package:frontend/core/services/offline_book_service.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/books/book_upload_dialog.dart';
import 'package:frontend/screens/books/pdf_reader_screen.dart';

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

  @override
  Widget build(BuildContext context) {
    final booksProv = context.watch<BooksProvider>();
    final syncService = context.watch<SyncService>();
    final offlineService = context.watch<OfflineBookService>();
    final books = booksProv.books;

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: Text(
          'माझी पुस्तके',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 17,
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
          // Cloud Storage Status Banner
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: const Color(0xFF0A0E17),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.speed, color: Color(0xFF00E676), size: 14),
                    const SizedBox(width: 6),
                    Text(
                      'Cloud-First Light App (Zero Storage Overhead)',
                      style: GoogleFonts.poppins(fontSize: 10.5, color: Colors.white70),
                    ),
                  ],
                ),
                Text(
                  '${offlineService.downloadedBookIds.length} Offline',
                  style: GoogleFonts.poppins(fontSize: 10, color: const Color(0xFF00E5FF)),
                ),
              ],
            ),
          ),

          // 1. Search Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.search, color: Colors.white38, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: _searchCtrl,
                      onChanged: (val) => booksProv.setSearchQuery(val),
                      style: GoogleFonts.notoSansDevanagari(color: Colors.white, fontSize: 13),
                      decoration: InputDecoration(
                        hintText: 'पुस्तके किंवा धडा शोधा...',
                        hintStyle: GoogleFonts.notoSansDevanagari(color: Colors.white38, fontSize: 13),
                        border: InputBorder.none,
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                ],
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
                            return _buildBookItemCard(context, book, index, offlineService);
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
                const Icon(Icons.cloud_upload_outlined, color: Colors.white, size: 20),
                const SizedBox(width: 8),
                Text(
                  '+ Cloud वर PDF जोडा',
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

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.cloud_queue, size: 56, color: Colors.white.withOpacity(0.2)),
          const SizedBox(height: 12),
          Text(
            'कोणतेही पुस्तक आढळले नाही',
            style: GoogleFonts.notoSansDevanagari(fontSize: 14, color: Colors.white60),
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
  ) {
    final colors = [
      const Color(0xFF2979FF),
      const Color(0xFF00E676),
      const Color(0xFFFF9100),
      const Color(0xFFD500F9),
      const Color(0xFFFF5252),
    ];
    final color = colors[index % colors.length];
    final double percent = (book.progressPercent / 100.0).clamp(0.0, 1.0);
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
            // Book Icon Capsule
            Container(
              width: 44,
              height: 52,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [color.withOpacity(0.8), color],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.picture_as_pdf, color: Colors.white, size: 24),
            ),
            const SizedBox(width: 14),

            // Book Meta & Progress Bar
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
                  const SizedBox(height: 2),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${book.totalPages} पाने • ${(book.fileSizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB',
                        style: GoogleFonts.poppins(fontSize: 10, color: Colors.white54),
                      ),
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
                          size: 18,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // Progress Bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: percent > 0 ? percent : 0.0,
                      minHeight: 4,
                      backgroundColor: Colors.white12,
                      color: color,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 14),

            // Percent Text
            Text(
              '${(percent * 100).toInt()}%',
              style: GoogleFonts.poppins(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
