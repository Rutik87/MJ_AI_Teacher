import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/chat_message.dart';
import 'package:frontend/models/book.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/cyber_drawer.dart';

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
          _scrollController.position.maxScrollExtent + 150,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showAttachFileDialog(BuildContext context) {
    final booksProv = context.read<BooksProvider>();
    final chatProv = context.read<ChatProvider>();
    final books = booksProv.allBooks;

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0A0E17),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => SafeArea(
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
                      '📎 चॅटसाठी फाईल जोडा (Attach File)',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    if (chatProv.hasAttachments)
                      TextButton(
                        onPressed: () {
                          chatProv.clearAttachedBooks();
                          setModalState(() {});
                        },
                        child: Text(
                          'सर्व काढा (Clear)',
                          style: GoogleFonts.notoSansDevanagari(color: Colors.redAccent, fontSize: 12),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                if (books.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 24),
                    child: Center(
                      child: Text(
                        'कोणतीही फाईल उपलब्ध नाही. प्रथम "Files" टॅबमध्ये PDF/TXT अपलोड करा.',
                        style: GoogleFonts.notoSansDevanagari(color: Colors.white54, fontSize: 13),
                        textAlign: TextAlign.center,
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
                        final isAttached = chatProv.attachedBooks.any((ab) => ab.id == b.id);
                        return ListTile(
                          leading: Icon(
                            b.sourceType == 'txt' ? Icons.description : Icons.picture_as_pdf,
                            color: isAttached ? const Color(0xFF00E5FF) : const Color(0xFF2979FF),
                          ),
                          title: Text(
                            b.title,
                            style: GoogleFonts.notoSansDevanagari(
                              fontSize: 13,
                              fontWeight: isAttached ? FontWeight.bold : FontWeight.normal,
                              color: Colors.white,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(
                            '${b.sourceType.toUpperCase()} • ${b.formattedFileSize}',
                            style: GoogleFonts.poppins(fontSize: 11, color: Colors.white54),
                          ),
                          trailing: isAttached
                              ? const Icon(Icons.check_circle, color: Color(0xFF00E5FF), size: 22)
                              : const Icon(Icons.add_circle_outline, color: Colors.white30, size: 22),
                          onTap: () {
                            soundService.playClick();
                            if (isAttached) {
                              chatProv.removeAttachedBook(b.id);
                            } else {
                              chatProv.attachBook(b);
                            }
                            setModalState(() {});
                          },
                        );
                      },
                    ),
                  ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00E5FF),
                      foregroundColor: Colors.black,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () => Navigator.of(ctx).pop(),
                    child: Text(
                      'पूर्ण झाले (${chatProv.attachedBooks.length} जोडल्या)',
                      style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showSessionsDrawer(BuildContext context) {
    final chatProv = context.read<ChatProvider>();
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0A0E17),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Container(
          height: MediaQuery.of(context).size.height * 0.65,
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '💬 मागील चर्चा (Chat History)',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add_comment_outlined, color: Color(0xFF00E5FF)),
                    tooltip: 'नवीन चर्चा',
                    onPressed: () {
                      chatProv.startNewSession();
                      Navigator.of(ctx).pop();
                    },
                  ),
                ],
              ),
              const Divider(color: Colors.white12),
              Expanded(
                child: chatProv.sessions.isEmpty
                    ? Center(
                        child: Text(
                          'कोणतीही मागील चर्चा आढळली नाही.',
                          style: GoogleFonts.notoSansDevanagari(color: Colors.white54, fontSize: 13),
                        ),
                      )
                    : ListView.builder(
                        itemCount: chatProv.sessions.length,
                        itemBuilder: (ctx, i) {
                          final s = chatProv.sessions[i];
                          final isCurrent = chatProv.currentSessionId == s.id;
                          return ListTile(
                            leading: Icon(
                              Icons.chat_bubble_outline_rounded,
                              color: isCurrent ? const Color(0xFF00E5FF) : Colors.white38,
                            ),
                            title: Text(
                              s.title,
                              style: GoogleFonts.notoSansDevanagari(
                                fontSize: 13,
                                fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                                color: isCurrent ? const Color(0xFF00E5FF) : Colors.white,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              s.createdAt.isNotEmpty ? s.createdAt.split("T").first : "",
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

  void _saveAsArtifact(BuildContext context, ChatMessageModel msg) async {
    soundService.playClick();
    final chatProv = context.read<ChatProvider>();
    final titleCtrl = TextEditingController(text: 'MPSC Revision Sheet');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0E17),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: Color(0xFF00E5FF), width: 1.2),
        ),
        title: Text(
          '📄 फाईल म्हणून लायब्ररीमध्ये सेव्ह करा',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 15,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'हे उत्तर कायमचे PDF फाईल म्हणून तुमच्या Study Library मध्ये साठवले जाईल.',
              style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white70),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: titleCtrl,
              style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white),
              decoration: InputDecoration(
                hintText: 'शीर्षक प्रविष्ट करा',
                hintStyle: GoogleFonts.notoSansDevanagari(color: Colors.white38),
                filled: true,
                fillColor: const Color(0xFF141C2B),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
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
              backgroundColor: const Color(0xFF00E5FF),
              foregroundColor: Colors.black,
            ),
            onPressed: () async {
              Navigator.of(ctx).pop();
              final res = await chatProv.generateArtifact(
                title: titleCtrl.text.trim(),
                content: msg.message,
                artifactType: 'pdf',
              );
              if (res != null && context.mounted) {
                context.read<BooksProvider>().fetchBooks();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('✨ फाईल सेव्ह झाली: ${res["title"]} (Library मध्ये उपलब्ध)'),
                    backgroundColor: const Color(0xFF00E5FF),
                  ),
                );
              }
            },
            child: Text('PDF तयार करा', style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chatProv = context.watch<ChatProvider>();

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
        title: Row(
          children: [
            const Icon(Icons.smart_toy_rounded, color: Color(0xFF00E5FF), size: 20),
            const SizedBox(width: 8),
            Text(
              'ChatGPT Workspace',
              style: GoogleFonts.poppins(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history_rounded, color: Colors.white70, size: 22),
            tooltip: 'मागील चर्चा',
            onPressed: () => _showSessionsDrawer(context),
          ),
          IconButton(
            icon: const Icon(Icons.add_comment_outlined, color: Color(0xFF00E5FF), size: 22),
            tooltip: 'नवीन चर्चा (New Chat)',
            onPressed: () {
              soundService.playClick();
              chatProv.startNewSession();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // 1. Attached Files Capsule Strip (if any)
          if (chatProv.hasAttachments)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              color: const Color(0xFF0A0E17),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    Text(
                      'जोडलेली फाईल्स:',
                      style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white54),
                    ),
                    const SizedBox(width: 8),
                    ...chatProv.attachedBooks.map((b) => Container(
                          margin: const EdgeInsets.only(right: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00E5FF).withOpacity(0.15),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                b.sourceType == 'txt' ? Icons.description : Icons.picture_as_pdf,
                                color: const Color(0xFF00E5FF),
                                size: 14,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                b.title,
                                style: GoogleFonts.notoSansDevanagari(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Colors.white,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(width: 4),
                              GestureDetector(
                                onTap: () => chatProv.removeAttachedBook(b.id),
                                child: const Icon(Icons.close, size: 14, color: Colors.white70),
                              ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ),

          // 2. Message Stream Area
          Expanded(
            child: chatProv.messages.isEmpty
                ? _buildEmptyChatPlaceholder(context)
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
                    itemCount: chatProv.messages.length,
                    itemBuilder: (ctx, idx) {
                      final msg = chatProv.messages[idx];
                      return _buildMessageBubble(context, msg);
                    },
                  ),
          ),

          if (chatProv.isLoading)
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(color: Color(0xFF00E5FF), strokeWidth: 2),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    'ChatGPT उत्तर तयार करत आहे...',
                    style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white60),
                  ),
                ],
              ),
            ),

          // 3. Message Input Bar with Attachment Button
          Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
            decoration: BoxDecoration(
              color: const Color(0xFF0A0E17),
              border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
            ),
            child: SafeArea(
              top: false,
              child: Row(
                children: [
                  // Attachment button
                  BouncingWrapper(
                    onTap: () {
                      soundService.playClick();
                      _showAttachFileDialog(context);
                    },
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: chatProv.hasAttachments
                            ? const Color(0xFF00E5FF).withOpacity(0.2)
                            : const Color(0xFF141C2B),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: chatProv.hasAttachments ? const Color(0xFF00E5FF) : Colors.white12,
                        ),
                      ),
                      child: Icon(
                        Icons.attach_file_rounded,
                        color: chatProv.hasAttachments ? const Color(0xFF00E5FF) : Colors.white70,
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Text input
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF141C2B),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: Colors.white.withOpacity(0.1)),
                      ),
                      child: TextField(
                        controller: _textController,
                        style: GoogleFonts.notoSansDevanagari(fontSize: 13.5, color: Colors.white),
                        maxLines: 4,
                        minLines: 1,
                        decoration: InputDecoration(
                          hintText: chatProv.hasAttachments
                              ? 'जोडलेल्या फाईलबद्दल काहीही विचारा...'
                              : 'MPSC बद्दल कोणताही प्रश्न विचारा...',
                          hintStyle: GoogleFonts.notoSansDevanagari(fontSize: 12.5, color: Colors.white38),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onSubmitted: (val) => _sendMessage(val),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Send button
                  BouncingWrapper(
                    onTap: () => _sendMessage(_textController.text),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color(0xFF00E5FF), Color(0xFF2979FF)],
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: const Center(
                        child: Icon(Icons.arrow_upward_rounded, color: Colors.black, size: 22),
                      ),
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

  Widget _buildMessageBubble(BuildContext context, ChatMessageModel msg) {
    final isUser = msg.sender == 'user';

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!isUser) ...[
                Container(
                  width: 30,
                  height: 30,
                  margin: const EdgeInsets.only(right: 8, top: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E5FF).withOpacity(0.15),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
                  ),
                  child: const Center(
                    child: Icon(Icons.smart_toy_rounded, color: Color(0xFF00E5FF), size: 16),
                  ),
                ),
              ],
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: isUser ? const Color(0xFF1E3A8A).withOpacity(0.5) : const Color(0xFF0A0E17),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isUser
                          ? const Color(0xFF2979FF).withOpacity(0.4)
                          : const Color(0xFF00E5FF).withOpacity(0.2),
                    ),
                  ),
                  child: isUser
                      ? Text(
                          msg.message,
                          style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white, height: 1.4),
                        )
                      : MarkdownBody(
                          data: msg.message,
                          styleSheet: MarkdownStyleSheet(
                            p: GoogleFonts.notoSansDevanagari(fontSize: 13, height: 1.5, color: Colors.white.withOpacity(0.95)),
                            strong: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold, color: const Color(0xFF00E5FF)),
                            h3: GoogleFonts.notoSansDevanagari(fontSize: 14, fontWeight: FontWeight.bold, color: const Color(0xFFFFD54F)),
                            tableBody: GoogleFonts.notoSansDevanagari(fontSize: 11.5, color: Colors.white70),
                            tableHead: GoogleFonts.notoSansDevanagari(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ),
                ),
              ),
            ],
          ),

          // Citation & Artifact Generation buttons for AI answers
          if (!isUser && msg.message.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(left: 38, top: 4),
              child: Row(
                children: [
                  if (msg.sources.isNotEmpty) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00E5FF).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '📖 ${msg.sources.first.bookName} (पान ${msg.sources.first.pageNumber})',
                        style: GoogleFonts.notoSansDevanagari(fontSize: 10, color: const Color(0xFF00E5FF)),
                      ),
                    ),
                    const SizedBox(width: 8),
                  ],
                  BouncingWrapper(
                    onTap: () => _saveAsArtifact(context, msg),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFD54F).withOpacity(0.12),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFFFD54F).withOpacity(0.3)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.save_alt_rounded, color: Color(0xFFFFD54F), size: 12),
                          const SizedBox(width: 4),
                          Text(
                            'Save to Library',
                            style: GoogleFonts.poppins(fontSize: 10, color: const Color(0xFFFFD54F), fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildEmptyChatPlaceholder(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.12),
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF00E5FF), width: 1.2),
              ),
              child: const Center(
                child: Icon(Icons.smart_toy_rounded, color: Color(0xFF00E5FF), size: 30),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'MPSC ChatGPT Workspace',
              style: GoogleFonts.poppins(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 6),
            Text(
              'कोणतीही PDF/TXT फाईल जोडा (📎) आणि संपूर्ण फाईलबद्दल काहीही विचारा.',
              style: GoogleFonts.notoSansDevanagari(fontSize: 12.5, color: Colors.white54),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                _buildPromptChip('1857 च्या उठावाची कारणे समजाव'),
                _buildPromptChip('या पुस्तकात एकूण किती chapters आहेत?'),
                _buildPromptChip('महत्त्वाच्या ऐतिहासिक तारखांची यादी दे'),
                _buildPromptChip('MPSC साठी 30 सराव MCQ बनव'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPromptChip(String label) {
    return BouncingWrapper(
      onTap: () {
        _textController.text = label;
        _sendMessage(label);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
        ),
        child: Text(
          label,
          style: GoogleFonts.notoSansDevanagari(fontSize: 11.5, color: const Color(0xFF00E5FF)),
        ),
      ),
    );
  }
}
