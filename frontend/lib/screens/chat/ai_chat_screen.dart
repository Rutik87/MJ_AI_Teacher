import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/chat_message.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/cyber_drawer.dart';
import 'package:frontend/screens/books/pdf_reader_screen.dart';

class AIChatScreen extends StatefulWidget {
  const AIChatScreen({super.key});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage(String text) {
    if (text.trim().isEmpty) return;
    soundService.playClick();
    _textController.clear();
    context.read<ChatProvider>().sendMessage(text.trim());
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent + 120,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showAttachFileDialog(BuildContext context) {
    final booksProv = context.read<BooksProvider>();
    final chatProv = context.read<ChatProvider>();
    final books = booksProv.books;

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0A0E17),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '📎 चॅटसाठी पुस्तक/फाईल जोडा',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  if (chatProv.selectedBookFilter != null)
                    TextButton(
                      onPressed: () {
                        chatProv.clearBookFilter();
                        Navigator.of(ctx).pop();
                      },
                      child: Text(
                        'काढून टाका (Clear)',
                        style: GoogleFonts.notoSansDevanagari(color: Colors.redAccent, fontSize: 12),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 10),
              if (books.isEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 20),
                  child: Center(
                    child: Text(
                      'कोणतीही फाईल उपलब्ध नाही. प्रथम "Files" मध्ये PDF अपलोड करा.',
                      style: GoogleFonts.notoSansDevanagari(color: Colors.white54, fontSize: 13),
                    ),
                  ),
                )
              else
                Flexible(
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: books.length,
                    itemBuilder: (ctx, i) {
                      final b = books[i];
                      final isSelected = chatProv.selectedBookFilter == b.id;
                      return ListTile(
                        leading: Icon(
                          b.sourceType == 'txt' ? Icons.description : Icons.picture_as_pdf,
                          color: isSelected ? const Color(0xFF00E5FF) : const Color(0xFF2979FF),
                        ),
                        title: Text(
                          b.title,
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 13,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            color: Colors.white,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(
                          '${b.subject} • ${b.totalPages} पाने',
                          style: GoogleFonts.poppins(fontSize: 11, color: Colors.white54),
                        ),
                        trailing: isSelected
                            ? const Icon(Icons.check_circle, color: Color(0xFF00E5FF), size: 20)
                            : null,
                        onTap: () {
                          chatProv.setBookFilter(b.id, bookTitle: b.title);
                          Navigator.of(ctx).pop();
                        },
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  void _showHistoryDrawer(BuildContext context) {
    final chatProv = context.read<ChatProvider>();
    final sessions = chatProv.sessions;

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0A0E17),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '⏱️ मागील संभाषणे (Chat History)',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add_comment_outlined, color: Color(0xFF00E5FF), size: 22),
                    tooltip: 'नवीन चॅट सुरू करा',
                    onPressed: () {
                      chatProv.startNewSession();
                      Navigator.of(ctx).pop();
                    },
                  ),
                ],
              ),
              const SizedBox(height: 10),
              if (sessions.isEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24),
                  child: Center(
                    child: Text(
                      'कोणतीही मागील चर्चा सापडली नाही.',
                      style: GoogleFonts.notoSansDevanagari(color: Colors.white54, fontSize: 13),
                    ),
                  ),
                )
              else
                Flexible(
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: sessions.length,
                    itemBuilder: (ctx, i) {
                      final s = sessions[i];
                      final isCurrent = chatProv.currentSessionId == s.id;
                      return ListTile(
                        leading: Icon(
                          Icons.chat_bubble_outline_rounded,
                          color: isCurrent ? const Color(0xFF00E5FF) : Colors.white38,
                          size: 20,
                        ),
                        title: Text(
                          s.title,
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 13,
                            fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                            color: Colors.white,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(
                          '${s.messageCount} संदेश • ${s.updatedAt.split("T").first}',
                          style: GoogleFonts.poppins(fontSize: 10.5, color: Colors.white38),
                        ),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete_outline, color: Colors.white24, size: 18),
                          onPressed: () => chatProv.deleteSession(s.id),
                        ),
                        onTap: () {
                          chatProv.loadSession(s.id);
                          Navigator.of(ctx).pop();
                        },
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chatProv = context.watch<ChatProvider>();
    final messages = chatProv.messages;

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
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF00E5FF), Color(0xFF00B0FF)],
                ),
              ),
              child: const Center(
                child: Icon(Icons.smart_toy_rounded, color: Colors.black, size: 18),
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ChatGPT Workspace',
                  style: GoogleFonts.poppins(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Text(
                  'MPSC अभ्यास सहाय्यक',
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 10.5,
                    color: const Color(0xFF00E5FF),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          // History Button
          IconButton(
            icon: const Icon(Icons.history_rounded, color: Colors.white70, size: 22),
            tooltip: 'चॅट इतिहास (History)',
            onPressed: () => _showHistoryDrawer(context),
          ),
          // New Chat Button
          IconButton(
            icon: const Icon(Icons.add_comment_outlined, color: Color(0xFF00E5FF), size: 22),
            tooltip: 'नवीन चॅट (New Chat)',
            onPressed: () {
              soundService.playClick();
              chatProv.startNewSession();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Attached File Banner (if a file is attached)
          if (chatProv.selectedBookFilter != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: const Color(0xFF00E5FF).withOpacity(0.1),
              child: Row(
                children: [
                  const Icon(Icons.attach_file, color: Color(0xFF00E5FF), size: 16),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'जोडलेली फाईल: ${chatProv.selectedBookTitle ?? "निवडलेले पुस्तक"}',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF00E5FF),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => chatProv.clearBookFilter(),
                    child: const Icon(Icons.close, color: Colors.white70, size: 16),
                  ),
                ],
              ),
            ),

          // Messages List or Empty Starter
          Expanded(
            child: messages.isEmpty
                ? _buildEmptyChatStarter(context)
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final msg = messages[index];
                      return _buildChatBubble(msg);
                    },
                  ),
          ),

          // Input Bar: Attachment + Input Field + Send Button
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFF0A0E17).withOpacity(0.98),
              border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
            ),
            child: SafeArea(
              top: false,
              child: Row(
                children: [
                  // Attach File Button
                  BouncingWrapper(
                    isBubbleSound: true,
                    onTap: () => _showAttachFileDialog(context),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: chatProv.selectedBookFilter != null
                            ? const Color(0xFF00E5FF).withOpacity(0.2)
                            : Colors.white.withOpacity(0.05),
                        border: Border.all(
                          color: chatProv.selectedBookFilter != null
                              ? const Color(0xFF00E5FF)
                              : Colors.white12,
                        ),
                      ),
                      child: Icon(
                        Icons.attach_file,
                        color: chatProv.selectedBookFilter != null
                            ? const Color(0xFF00E5FF)
                            : Colors.white70,
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Text Input Field
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF141C2B),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: TextField(
                        controller: _textController,
                        style: GoogleFonts.notoSansDevanagari(color: Colors.white, fontSize: 13.5),
                        decoration: InputDecoration(
                          hintText: chatProv.selectedBookFilter != null
                              ? 'या फाईलबाबत प्रश्न विचारा...'
                              : 'MPSC चा कोणताही प्रश्न विचारा...',
                          hintStyle: GoogleFonts.notoSansDevanagari(color: Colors.white38, fontSize: 12.5),
                          border: InputBorder.none,
                          isDense: true,
                          contentPadding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onSubmitted: _sendMessage,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Send Button
                  BouncingWrapper(
                    isBubbleSound: true,
                    onTap: () => _sendMessage(_textController.text),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          colors: [Color(0xFF00E5FF), Color(0xFF2979FF)],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF00E5FF).withOpacity(0.4),
                            blurRadius: 10,
                          ),
                        ],
                      ),
                      child: chatProv.isLoading
                          ? const Padding(
                              padding: EdgeInsets.all(10),
                              child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2),
                            )
                          : const Icon(Icons.send_rounded, color: Colors.black, size: 18),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyChatStarter(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF00E5FF).withOpacity(0.12),
                border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
              ),
              child: const Icon(Icons.smart_toy_rounded, color: Color(0xFF00E5FF), size: 32),
            ),
            const SizedBox(height: 16),
            Text(
              'ChatGPT MPSC Workspace',
              style: GoogleFonts.poppins(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'कोणताही MPSC विषय किंवा अपलोड केलेली फाईल निवडून प्रश्न विचारा.',
              textAlign: TextAlign.center,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 12.5,
                color: Colors.white60,
              ),
            ),
            const SizedBox(height: 20),

            // Quick Prompt Chips
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                _buildPromptChip('1857 चा उठाव समजाव'),
                _buildPromptChip('भारतीय राज्यघटनेची मूलभूत वैशिष्ट्ये सांगा'),
                _buildPromptChip('महाराष्ट्रातील प्रमुख नद्या व उपनद्या'),
                _buildPromptChip('MPSC पूर्व परीक्षेचे नियोजन कसे करावे?'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPromptChip(String prompt) {
    return BouncingWrapper(
      onTap: () {
        _textController.text = prompt;
        _sendMessage(prompt);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white12),
        ),
        child: Text(
          prompt,
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 12,
            color: const Color(0xFF00E5FF),
          ),
        ),
      ),
    );
  }

  Widget _buildChatBubble(ChatMessageModel message) {
    final bool isUser = message.sender == 'user';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 30,
              height: 30,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(colors: [Color(0xFF00E5FF), Color(0xFF00B0FF)]),
              ),
              child: const Icon(Icons.smart_toy_rounded, color: Colors.black, size: 16),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isUser ? const Color(0xFF2979FF).withOpacity(0.85) : const Color(0xFF0A0E17),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft: Radius.circular(isUser ? 18 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 18),
                ),
                border: Border.all(
                  color: isUser ? const Color(0xFF2979FF) : const Color(0xFF00E5FF).withOpacity(0.3),
                  width: 1.0,
                ),
                boxShadow: [
                  BoxShadow(
                    color: (isUser ? const Color(0xFF2979FF) : const Color(0xFF00E5FF)).withOpacity(0.15),
                    blurRadius: 10,
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isUser ? 'तुम्ही' : 'ChatGPT',
                    style: GoogleFonts.poppins(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isUser ? Colors.white70 : const Color(0xFF00E5FF),
                    ),
                  ),
                  const SizedBox(height: 6),
                  MarkdownBody(
                    data: message.message,
                    styleSheet: MarkdownStyleSheet(
                      p: GoogleFonts.notoSansDevanagari(
                        fontSize: 13.5,
                        height: 1.5,
                        color: Colors.white.withOpacity(0.95),
                      ),
                      strong: GoogleFonts.notoSansDevanagari(
                        fontSize: 13.5,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF00E5FF),
                      ),
                    ),
                  ),

                  // Sources citations
                  if (message.sources.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF050811),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.white10),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '📖 स्रोत (${message.sources.length}):',
                            style: GoogleFonts.notoSansDevanagari(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: const Color(0xFF00E5FF),
                            ),
                          ),
                          ...message.sources.map((s) => Text(
                                '• ${s.bookName} (पान क्र. ${s.pageNumber})',
                                style: GoogleFonts.notoSansDevanagari(fontSize: 10, color: Colors.white70),
                              )),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
