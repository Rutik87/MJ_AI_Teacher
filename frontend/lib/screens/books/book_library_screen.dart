import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/core/services/sync_service.dart';
import 'package:frontend/core/services/offline_book_service.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/providers/chat_provider.dart';
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
  final List<String> _filters = ['All', 'PDF', 'TXT', 'Images', 'Generated'];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _showRenameDialog(BuildContext context, BookModel book) {
    final titleCtrl = TextEditingController(text: book.title);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0E17),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: Color(0xFF00E5FF), width: 1.2),
        ),
        title: Text(
          'नाव बदला (Rename File)',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        content: TextField(
          controller: titleCtrl,
          style: GoogleFonts.notoSansDevanagari(fontSize: 14, color: Colors.white),
          decoration: InputDecoration(
            hintText: 'नवीन नाव प्रविष्ट करा',
            hintStyle: GoogleFonts.notoSansDevanagari(color: Colors.white38),
            filled: true,
            fillColor: const Color(0xFF141C2B),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: BorderSide.none,
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('रद्द करा', style: GoogleFonts.notoSansDevanagari(color: Colors.white60)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00E5FF),
              foregroundColor: Colors.black,
            ),
            onPressed: () async {
              soundService.playClick();
              final newTitle = titleCtrl.text.trim();
              if (newTitle.isNotEmpty) {
                await context.read<BooksProvider>().renameBook(book.id, newTitle);
              }
              if (mounted) Navigator.of(ctx).pop();
            },
            child: Text('सेव्ह करा', style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  void _confirmAndDeleteBook(BuildContext context, BookModel book) {
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
                'फाईल हटवायची आहे का?',
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
              '\"${book.title}\" ही फाईल कायमची हटवायची आहे का?',
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
                '⚠️ फाईल, क्लाऊड स्टोरेज आणि संबंधित चॅट संदर्भ कायमचे हटवले जातील.',
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
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('रद्द करा', style: GoogleFonts.notoSansDevanagari(color: Colors.white60)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFD50000),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () async {
              soundService.playClick();
              Navigator.of(ctx).pop();
              final success = await context.read<BooksProvider>().deleteBook(book.id);
              if (success && context.mounted) {
                await context.read<OfflineBookService>().removeOfflineBook(book.id);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('फाईल यशस्वीरित्या हटवली.'),
                    backgroundColor: Color(0xFF263238),
                  ),
                );
              }
            },
            child: Text('हटवा (Delete)', style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  void _shareBookSignedUrl(BuildContext context, BookModel book) async {
    try {
      soundService.playClick();
      final res = await ApiClient.get('${ApiEndpoints.books}/${book.id}/signed-url');
      if (res.isSuccess && res.data != null) {
        final url = res.data['url'] ?? '';
        await Clipboard.setData(ClipboardData(text: url));
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('सुरक्षित डाऊनलोड लिंक कॉपी केली: $url'),
              backgroundColor: const Color(0xFF00E5FF),
            ),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('लिंक मिळवताना त्रुटी: $e'), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final booksProv = context.watch<BooksProvider>();
    final offlineService = context.watch<OfflineBookService>();

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure Pitch Black
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
          '📚 My Study Library',
          style: GoogleFonts.poppins(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.cloud_upload_outlined, color: Color(0xFF00E5FF), size: 24),
            tooltip: 'फाईल अपलोड करा (PDF / TXT)',
            onPressed: () {
              soundService.playClick();
              showDialog(
                context: context,
                builder: (_) => const BookUploadDialog(),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => booksProv.fetchBooks(),
        color: const Color(0xFF00E5FF),
        backgroundColor: const Color(0xFF0A0E17),
        child: Column(
          children: [
            // 1. Search Bar & Upload Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      height: 42,
                      decoration: BoxDecoration(
                        color: const Color(0xFF0A0E17),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white.withOpacity(0.12)),
                      ),
                      child: TextField(
                        controller: _searchCtrl,
                        onChanged: (val) => booksProv.setSearchQuery(val),
                        style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white),
                        decoration: InputDecoration(
                          hintText: 'फाईल शोधा... (Search files)',
                          hintStyle: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white38),
                          prefixIcon: const Icon(Icons.search_rounded, color: Color(0xFF00E5FF), size: 18),
                          suffixIcon: _searchCtrl.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear, size: 16, color: Colors.white54),
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
                  const SizedBox(width: 10),
                  BouncingWrapper(
                    onTap: () {
                      soundService.playClick();
                      showDialog(
                        context: context,
                        builder: (_) => const BookUploadDialog(),
                      );
                    },
                    child: Container(
                      height: 42,
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF00E5FF), Color(0xFF2979FF)],
                        ),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.add_rounded, color: Colors.black, size: 20),
                          const SizedBox(width: 4),
                          Text(
                            'Upload',
                            style: GoogleFonts.poppins(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.black,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 2. Filter Pills: All | PDF | TXT | Images | Generated
            SizedBox(
              height: 38,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _filters.length,
                itemBuilder: (ctx, idx) {
                  final f = _filters[idx];
                  final isSelected = booksProv.selectedFilter == f;
                  return GestureDetector(
                    onTap: () {
                      soundService.playClick();
                      booksProv.setFilter(f);
                    },
                    child: Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? const Color(0xFF00E5FF).withOpacity(0.18)
                            : const Color(0xFF0A0E17),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: isSelected
                              ? const Color(0xFF00E5FF)
                              : Colors.white.withOpacity(0.1),
                          width: 1.2,
                        ),
                      ),
                      child: Center(
                        child: Text(
                          f == 'All' ? 'सर्व (All)' : (f == 'Generated' ? '✨ तयार केलेल्या (Generated)' : f),
                          style: GoogleFonts.poppins(
                            fontSize: 11.5,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                            color: isSelected ? const Color(0xFF00E5FF) : Colors.white60,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 8),

            // 3. File List
            Expanded(
              child: booksProv.isLoading && booksProv.books.isEmpty
                  ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
                  : booksProv.books.isEmpty
                      ? _buildEmptyState(context)
                      : ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 90),
                          itemCount: booksProv.books.length,
                          itemBuilder: (ctx, idx) {
                            final book = booksProv.books[idx];
                            return _buildFileCard(context, book, offlineService);
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFileCard(BuildContext context, BookModel book, OfflineBookService offlineService) {
    final isOffline = offlineService.isBookDownloaded(book.id);

    IconData typeIcon;
    Color typeColor;
    if (book.isGenerated) {
      typeIcon = Icons.auto_awesome;
      typeColor = const Color(0xFFFFD54F);
    } else if (book.sourceType == 'txt') {
      typeIcon = Icons.description_outlined;
      typeColor = const Color(0xFF00E5FF);
    } else if (book.sourceType == 'image') {
      typeIcon = Icons.image_outlined;
      typeColor = const Color(0xFFE040FB);
    } else {
      typeIcon = Icons.picture_as_pdf_outlined;
      typeColor = const Color(0xFFFF5252);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E17),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: book.isGenerated
              ? const Color(0xFFFFD54F).withOpacity(0.3)
              : Colors.white.withOpacity(0.08),
          width: 1.2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Row
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: typeColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: typeColor.withOpacity(0.4)),
                ),
                child: Center(
                  child: Icon(typeIcon, color: typeColor, size: 22),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      book.title,
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Text(
                          '${book.sourceType.toUpperCase()} • ${book.formattedFileSize}',
                          style: GoogleFonts.poppins(fontSize: 11, color: Colors.white54),
                        ),
                        if (book.isGenerated) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFFD54F).withOpacity(0.2),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              'Generated',
                              style: GoogleFonts.poppins(fontSize: 9.5, color: const Color(0xFFFFD54F), fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert_rounded, color: Colors.white54, size: 20),
                color: const Color(0xFF0F172A),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                onSelected: (val) {
                  if (val == 'rename') _showRenameDialog(context, book);
                  if (val == 'share') _shareBookSignedUrl(context, book);
                  if (val == 'delete') _confirmAndDeleteBook(context, book);
                },
                itemBuilder: (ctx) => [
                  PopupMenuItem(
                    value: 'rename',
                    child: Row(
                      children: [
                        const Icon(Icons.edit_outlined, size: 16, color: Colors.white70),
                        const SizedBox(width: 8),
                        Text('नाव बदला (Rename)', style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white)),
                      ],
                    ),
                  ),
                  PopupMenuItem(
                    value: 'share',
                    child: Row(
                      children: [
                        const Icon(Icons.share_outlined, size: 16, color: Colors.white70),
                        const SizedBox(width: 8),
                        Text('शेअर / लिंक (Share Link)', style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white)),
                      ],
                    ),
                  ),
                  PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        const Icon(Icons.delete_outline, size: 16, color: Colors.redAccent),
                        const SizedBox(width: 8),
                        Text('हटवा (Delete)', style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.redAccent)),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 10),

          // Action Buttons: Open | Chat with ChatGPT | Share
          Row(
            children: [
              Expanded(
                child: BouncingWrapper(
                  onTap: () {
                    soundService.playClick();
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => PDFReaderScreen(
                          book: book,
                          initialPage: 1,
                        ),
                      ),
                    );
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF141E33),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.menu_book_rounded, color: Color(0xFF00E5FF), size: 16),
                        const SizedBox(width: 6),
                        Text(
                          'Open',
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: const Color(0xFF00E5FF),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: BouncingWrapper(
                  onTap: () {
                    soundService.playClick();
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => BookChatGPTWorkspaceScreen(book: book),
                      ),
                    );
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF2979FF), Color(0xFF7B1FA2)],
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.smart_toy_rounded, color: Colors.white, size: 16),
                        const SizedBox(width: 6),
                        Text(
                          'ChatGPT',
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              BouncingWrapper(
                onTap: () => _shareBookSignedUrl(context, book),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF141C2B),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: const Icon(Icons.share_outlined, color: Colors.white70, size: 18),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.folder_open_rounded, size: 64, color: Colors.white.withOpacity(0.2)),
          const SizedBox(height: 14),
          Text(
            'कोणतीही फाईल आढळली नाही.',
            style: GoogleFonts.notoSansDevanagari(fontSize: 14, color: Colors.white54),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00E5FF),
              foregroundColor: Colors.black,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
            onPressed: () {
              soundService.playClick();
              showDialog(context: context, builder: (_) => const BookUploadDialog());
            },
            icon: const Icon(Icons.cloud_upload_outlined, size: 18),
            label: Text(
              'पहिली फाईल अपलोड करा (Upload)',
              style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}
