import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:frontend/models/chat_message.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/screens/books/pdf_reader_screen.dart';

class SourceCitationCard extends StatelessWidget {
  final SourceCitationModel citation;

  const SourceCitationCard({super.key, required this.citation});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 6, bottom: 4),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFFF6F00).withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFF6F00).withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.menu_book, color: Color(0xFFFF8F00), size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  citation.bookName,
                  style: GoogleFonts.poppins(fontSize: 12, fontWeight: FontWeight.bold, color: const Color(0xFFFFB74D)),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.white10,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'पान क्र. ${citation.pageNumber}',
                  style: GoogleFonts.notoSansDevanagari(fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          if (citation.chapter != null && citation.chapter!.isNotEmpty && citation.chapter != 'General') ...[
            const SizedBox(height: 2),
            Text(
              'प्रकरण: ${citation.chapter}',
              style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
            ),
          ],
          const SizedBox(height: 4),
          Text(
            '"${citation.textSnippet}"',
            style: GoogleFonts.notoSansDevanagari(
              fontSize: 11,
              fontStyle: FontStyle.italic,
              color: Colors.white60,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 6),
          Align(
            alignment: Alignment.centerRight,
            child: InkWell(
              onTap: () {
                final booksProv = context.read<BooksProvider>();
                final matchedBook = booksProv.allBooks.firstWhere(
                  (b) => b.id == citation.bookId || b.title == citation.bookName,
                  orElse: () => booksProv.allBooks.isNotEmpty ? booksProv.allBooks.first : booksProv.allBooks.first,
                );
                Navigator.of(context).push(MaterialPageRoute(
                  builder: (ctx) => PDFReaderScreen(
                    book: matchedBook,
                    initialPage: citation.pageNumber,
                  ),
                ));
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.open_in_new, size: 12, color: Color(0xFF64B5F6)),
                    const SizedBox(width: 4),
                    Text(
                      'PDF मध्ये हे पान उघडा',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 11,
                        color: const Color(0xFF64B5F6),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
