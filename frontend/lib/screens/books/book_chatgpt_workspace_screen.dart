import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/models/book_model.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/widgets/common/bouncing_wrapper.dart';

class BookChatGPTWorkspaceScreen extends StatefulWidget {
  final BookModel book;

  const BookChatGPTWorkspaceScreen({
    super.key,
    required this.book,
  });

  @override
  State<BookChatGPTWorkspaceScreen> createState() => _BookChatGPTWorkspaceScreenState();
}

class _BookChatGPTWorkspaceScreenState extends State<BookChatGPTWorkspaceScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  List<Map<String, dynamic>> _messages = [];
  bool _isLoadingHistory = true;
  bool _isSending = false;
  String _selectedScope = 'entire_book'; // 'entire_book', 'chapter', 'pages'
  int? _selectedChapterId;
  int? _pageStart;
  int? _pageEnd;

  final List<Map<String, dynamic>> _quickActions = [
    {'icon': '📝', 'label': 'Notes बनवा', 'prompt': 'या पुस्तकातील महत्त्वाच्या मुद्द्यांच्या संक्षिप्त Notes बनव.'},
    {'icon': '❓', 'label': '30 MPSC MCQs', 'prompt': 'या पुस्तकातून MPSC परीक्षेसाठी 30 संभाव्य MCQs आणि स्पष्टीकरण तयार कर.'},
    {'icon': '🎯', 'label': 'MPSC Points', 'prompt': 'MPSC परीक्षेसाठी अति-महत्त्वाचे मुख्य मुद्दे काढ.'},
    {'icon': '📌', 'label': 'सोप्या भाषेत Summary', 'prompt': 'हा संपूर्ण मजकूर अत्यंत सोप्या मराठीत समजावून सांग.'},
    {'icon': '📅', 'label': 'महत्त्वाच्या तारखा', 'prompt': 'या पुस्तकातील सर्व महत्त्वाच्या ऐतिहासिक तारखा आणि कालक्रम तक्त्यामध्ये दाखव.'},
    {'icon': '🔄', 'label': 'Revision Sheet', 'prompt': 'परीक्षेच्या आदल्या दिवशी वाचण्यासाठी २ पानांची Quick Revision Sheet तयार कर.'},
  ];

  @override
  void initState() {
    super.initState();
    _fetchChatHistory();
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _fetchChatHistory() async {
    setState(() => _isLoadingHistory = true);
    try {
      final url = Uri.parse('${ApiEndpoints.baseUrl}/books/${widget.book.id}/chat/history?user_id=1');
      final resp = await http.get(url);
      if (resp.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(resp.bodyBytes));
        setState(() {
          _messages = data.map((m) => {
            'sender': m['sender'] ?? 'user',
            'message': m['message'] ?? '',
            'output_type': m['output_type'] ?? 'chat',
            'sources': m['sources'] ?? [],
            'pdf_url': m['pdf_url'],
          }).toList();
        });
      }
    } catch (e) {
      debugPrint('[BookChatGPT] Error fetching history: $e');
    } finally {
      setState(() => _isLoadingHistory = false);
      _scrollToBottom();
    }
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty || _isSending) return;

    final userMsg = text.trim();
    _textController.clear();

    setState(() {
      _messages.add({
        'sender': 'user',
        'message': userMsg,
        'output_type': 'chat',
        'sources': [],
      });
      _isSending = true;
    });
    _scrollToBottom();
    soundService.playClick();

    try {
      final url = Uri.parse('${ApiEndpoints.baseUrl}/books/${widget.book.id}/chat');
      final body = {
        'message': userMsg,
        'chapter_id': _selectedChapterId,
        'page_start': _pageStart,
        'page_end': _pageEnd,
        'user_id': 1,
      };

      final resp = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(body),
      );

      if (resp.statusCode == 200) {
        final data = json.decode(utf8.decode(resp.bodyBytes));
        setState(() {
          _messages.add({
            'sender': 'ai',
            'message': data['answer'] ?? '',
            'output_type': data['output_type'] ?? 'chat',
            'sources': data['source_citations'] ?? [],
            'pdf_url': data['pdf_url'],
          });
        });
        soundService.playBubble();
      } else {
        setState(() {
          _messages.add({
            'sender': 'ai',
            'message': 'उत्तर मिळवताना त्रुटी आली. कृपया पुन्हा प्रयत्न करा.',
            'output_type': 'chat',
            'sources': [],
          });
        });
      }
    } catch (e) {
      debugPrint('[BookChatGPT] Send error: $e');
      setState(() {
        _messages.add({
          'sender': 'ai',
          'message': 'इंटरनेट किंवा सर्व्हर कनेक्शन त्रुटी: $e',
          'output_type': 'chat',
          'sources': [],
        });
      });
    } finally {
      setState(() => _isSending = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _clearHistory() async {
    try {
      final url = Uri.parse('${ApiEndpoints.baseUrl}/books/${widget.book.id}/chat/history?user_id=1');
      await http.delete(url);
      setState(() => _messages.clear());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('या पुस्तकाची Chat History साफ झाली.')),
        );
      }
    } catch (e) {
      debugPrint('[BookChatGPT] Clear history error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF070B11),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D1424),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 18, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text('🤖 ', style: TextStyle(fontSize: 16)),
                Expanded(
                  child: Text(
                    'ChatGPT • ${widget.book.title}',
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            Text(
              '${widget.book.subjectName} • Common RAG Grounded',
              style: GoogleFonts.poppins(fontSize: 10, color: const Color(0xFF00E5FF)),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined, size: 20, color: Colors.white54),
            tooltip: 'Clear Chat History',
            onPressed: () => _showClearDialog(),
          ),
        ],
      ),
      body: Column(
        children: [
          // 1. Scope Selector & Book Info Bar
          _buildScopeSelectorBar(),

          // 2. Chat Messages List
          Expanded(
            child: _isLoadingHistory
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
                : _messages.isEmpty
                    ? _buildWelcomeScreen()
                    : _buildMessagesList(),
          ),

          // 3. Quick Actions Carousel
          _buildQuickActionsBar(),

          // 4. Input Composer
          _buildComposer(),
        ],
      ),
    );
  }

  Widget _buildScopeSelectorBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: const BoxDecoration(
        color: Color(0xFF0A0E17),
        border: Border(bottom: BorderSide(color: Colors.white10)),
      ),
      child: Row(
        children: [
          const Icon(Icons.filter_alt_outlined, size: 14, color: Color(0xFF00E5FF)),
          const SizedBox(width: 6),
          Text(
            'अभ्यास क्षेत्र (Scope):',
            style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF00E5FF).withOpacity(0.12),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
            ),
            child: Text(
              '📚 संपूर्ण पुस्तक (${widget.book.totalPages > 0 ? "${widget.book.totalPages} पाने" : "Full Book"})',
              style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: const Color(0xFF00E5FF), fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeScreen() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF0E1726),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.2)),
            ),
            child: Column(
              children: [
                const Icon(Icons.auto_stories, size: 42, color: Color(0xFF00E5FF)),
                const SizedBox(height: 10),
                Text(
                  'या पुस्तकासाठी ChatGPT Workspace',
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'तुम्ही या पुस्तकाबद्दल कोणताही प्रश्न विचारू शकता, नोट्स, MCQs किंवा उजळणी तक्ता बनवून घेऊ शकता.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white60),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              '⚡ Quick Actions (सुरुवात करण्यासाठी क्लिक करा):',
              style: GoogleFonts.notoSansDevanagari(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white70),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _quickActions.map((qa) {
              return BouncingWrapper(
                onTap: () => _sendMessage(qa['prompt']),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0E1726),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(qa['icon'], style: const TextStyle(fontSize: 14)),
                      const SizedBox(width: 6),
                      Text(
                        qa['label'],
                        style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildMessagesList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      itemCount: _messages.length + (_isSending ? 1 : 0),
      itemBuilder: (context, idx) {
        if (idx == _messages.length && _isSending) {
          return _buildThinkingBubble();
        }
        final msg = _messages[idx];
        final isUser = msg['sender'] == 'user';
        return _buildMessageBubble(msg, isUser);
      },
    );
  }

  Widget _buildMessageBubble(Map<String, dynamic> msg, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.88),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF007791) : const Color(0xFF0E1726),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isUser ? const Color(0xFF00E5FF).withOpacity(0.3) : Colors.white12,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.smart_toy, size: 14, color: Color(0xFF00E5FF)),
                  const SizedBox(width: 4),
                  Text(
                    'ChatGPT • Grounded Answer',
                    style: GoogleFonts.poppins(fontSize: 10, color: const Color(0xFF00E5FF), fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            if (!isUser) const SizedBox(height: 6),
            MarkdownBody(
              data: msg['message'] ?? '',
              styleSheet: MarkdownStyleSheet(
                p: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white, height: 1.45),
                strong: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold, color: const Color(0xFF00E5FF)),
                h1: GoogleFonts.notoSansDevanagari(fontSize: 16, fontWeight: FontWeight.bold, color: const Color(0xFF00E5FF)),
                h2: GoogleFonts.notoSansDevanagari(fontSize: 14, fontWeight: FontWeight.bold, color: const Color(0xFFFFD54F)),
                tableBody: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
                tableHead: GoogleFonts.notoSansDevanagari(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
            // Citations
            if (!isUser && msg['sources'] != null && (msg['sources'] as List).isNotEmpty) ...[
              const SizedBox(height: 8),
              const Divider(color: Colors.white12, height: 1),
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: (msg['sources'] as List).map((s) {
                  final page = s['page_number'];
                  final ch = s['chapter'] ?? '';
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '📖 पान क्र. $page ${ch.isNotEmpty ? "($ch)" : ""}',
                      style: GoogleFonts.notoSansDevanagari(fontSize: 10, color: Colors.white60),
                    ),
                  );
                }).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildThinkingBubble() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xFF0E1726),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00E5FF)),
            ),
            const SizedBox(width: 8),
            Text(
              'ChatGPT विचार करत आहे व संदर्भ शोधत आहे...',
              style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActionsBar() {
    return Container(
      height: 38,
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: _quickActions.length,
        itemBuilder: (context, idx) {
          final qa = _quickActions[idx];
          return Padding(
            padding: const EdgeInsets.only(right: 6),
            child: BouncingWrapper(
              onTap: () => _sendMessage(qa['prompt']),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFF0E1726),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.white12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(qa['icon'], style: const TextStyle(fontSize: 12)),
                    const SizedBox(width: 4),
                    Text(
                      qa['label'],
                      style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildComposer() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: const BoxDecoration(
        color: Color(0xFF0D1424),
        border: Border(top: BorderSide(color: Colors.white12)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(
                  color: const Color(0xFF141E33),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: Colors.white12),
                ),
                child: TextField(
                  controller: _textController,
                  style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'या पुस्तकाबद्दल विचारा किंवा आज्ञा द्या...',
                    hintStyle: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white38),
                    border: InputBorder.none,
                  ),
                  onSubmitted: (val) => _sendMessage(val),
                ),
              ),
            ),
            const SizedBox(width: 8),
            BouncingWrapper(
              onTap: () => _sendMessage(_textController.text),
              child: Container(
                width: 42,
                height: 42,
                decoration: const BoxDecoration(
                  color: Color(0xFF00E5FF),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.send_rounded, size: 20, color: Colors.black),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showClearDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0E1726),
        title: Text('Chat History साफ करायची का?', style: GoogleFonts.notoSansDevanagari(color: Colors.white)),
        content: Text('या पुस्तकाची सर्व मागील चर्चा हटवली जाईल.', style: GoogleFonts.notoSansDevanagari(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('रद्द करा'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _clearHistory();
            },
            child: const Text('हटवा', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
  }
}
