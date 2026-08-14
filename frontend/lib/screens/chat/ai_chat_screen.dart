import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/chat_message.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/chat/voice_mode_screen.dart';

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

  @override
  Widget build(BuildContext context) {
    final chatProv = context.watch<ChatProvider>();
    final audioService = context.watch<AudioService>();
    final messages = chatProv.messages;

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'AI शिक्षक',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            Text(
              'तुमचा वैयक्तिक मार्गदर्शक',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 11,
                color: const Color(0xFF00E5FF),
              ),
            ),
          ],
        ),
        actions: [
          BouncingWrapper(
            onTap: () {
              soundService.playClick();
              chatProv.startNewSession();
            },
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 14),
              child: Icon(Icons.add_comment_outlined, color: Color(0xFF00E5FF), size: 22),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Messages List or Default Starter (Screen 3)
          Expanded(
            child: messages.isEmpty
                ? _buildScreen3MockConversation(audioService)
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final msg = messages[index];
                      return _buildChatBubble(msg, audioService);
                    },
                  ),
          ),

          // Bottom Input Bar (Screen 3: Mic + Type a message... + Send)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFF0A0E17).withOpacity(0.95),
              border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
            ),
            child: SafeArea(
              top: false,
              child: Row(
                children: [
                  // Voice Mic Button
                  BouncingWrapper(
                    isBubbleSound: true,
                    onTap: () {
                      Navigator.of(context).push(MaterialPageRoute(
                        builder: (ctx) => const VoiceModeScreen(),
                      ));
                    },
                    child: Container(
                      width: 42,
                      height: 42,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF00E5FF).withOpacity(0.12),
                        border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
                      ),
                      child: const Icon(Icons.mic_none, color: Color(0xFF00E5FF), size: 22),
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
                        style: GoogleFonts.notoSansDevanagari(color: Colors.white, fontSize: 13),
                        decoration: InputDecoration(
                          hintText: 'Type a message...',
                          hintStyle: GoogleFonts.poppins(color: Colors.white38, fontSize: 12),
                          border: InputBorder.none,
                          isDense: true,
                          contentPadding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onSubmitted: _sendMessage,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Send Button (Screen 3 Purple gradient circle)
                  BouncingWrapper(
                    isBubbleSound: true,
                    onTap: () => _sendMessage(_textController.text),
                    child: Container(
                      width: 42,
                      height: 42,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          colors: [Color(0xFF7B1FA2), Color(0xFF2979FF)],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF7B1FA2).withOpacity(0.5),
                            blurRadius: 10,
                          ),
                        ],
                      ),
                      child: const Icon(Icons.send, color: Colors.white, size: 18),
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

  Widget _buildScreen3MockConversation(AudioService audioService) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      children: [
        // 1. User Bubble (Screen 3)
        Align(
          alignment: Alignment.centerRight,
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF651FFF), Color(0xFF2979FF)],
              ),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
                bottomLeft: Radius.circular(18),
                bottomRight: Radius.circular(4),
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF651FFF).withOpacity(0.3),
                  blurRadius: 10,
                ),
              ],
            ),
            child: Text(
              '1857 च्या उठावाची कारणे सांगा.',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 13.5,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
          ),
        ),

        // 2. AI Teacher Answer Card (Screen 3)
        Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF0A0E17),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(18),
              topRight: Radius.circular(18),
              bottomLeft: Radius.circular(4),
              bottomRight: Radius.circular(18),
            ),
            border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF00E5FF).withOpacity(0.12),
                blurRadius: 12,
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: const Color(0xFF00E5FF).withOpacity(0.18),
                        ),
                        child: const Icon(Icons.psychology, color: Color(0xFF00E5FF), size: 18),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'MPSC AI शिक्षक',
                        style: GoogleFonts.poppins(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFF00E5FF),
                        ),
                      ),
                    ],
                  ),
                  BouncingWrapper(
                    onTap: () {
                      soundService.playClick();
                      audioService.speakText('1857 चा उठाव ही भारतातील पहिली स्वातंत्र्य लढाई मानली जाते. मुख्य कारणे: ब्रिटिशांची अन्यायकारक धोरणे, सैन्यातील भेदभाव, शेतकऱ्यांवरील अन्याय, धार्मिक कारणे, कार्तुस प्रकरण');
                    },
                    child: Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF7B1FA2).withOpacity(0.2),
                      ),
                      child: const Icon(Icons.play_arrow, color: Color(0xFF00E5FF), size: 18),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                '1857 चा उठाव ही भारतातील पहिली स्वातंत्र्य लढाई मानली जाते. याची मुख्य कारणे खालीलप्रमाणे:',
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 13,
                  height: 1.5,
                  color: Colors.white.withOpacity(0.9),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'मुख्य कारणे:\n'
                '• ब्रिटिशांची अन्यायकारक धोरणे\n'
                '• सैन्यातील भेदभाव\n'
                '• शेतकऱ्यांवरील अन्याय\n'
                '• धार्मिक कारणे\n'
                '• कार्तुस प्रकरण',
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 13,
                  height: 1.6,
                  color: Colors.white.withOpacity(0.9),
                ),
              ),

              const SizedBox(height: 14),

              // Sources (2) Card (Screen 3)
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF050811),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white10),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'स्रोत (Sources):',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF00E5FF),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '1. महाराष्ट्राचा इतिहास - पृ. 124\n2. स्पर्धा परीक्षा नोट्स - पृ. 31',
                      style: GoogleFonts.notoSansDevanagari(
                        fontSize: 11,
                        color: Colors.white70,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildChatBubble(ChatMessageModel message, AudioService audioService) {
    final bool isUser = message.sender == 'user';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(colors: [Color(0xFF00E5FF), Color(0xFF7B1FA2)]),
              ),
              child: const Icon(Icons.psychology, color: Colors.white, size: 18),
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
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        isUser ? 'तुम्ही' : 'MPSC AI शिक्षक',
                        style: GoogleFonts.poppins(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isUser ? Colors.white70 : const Color(0xFF00E5FF),
                        ),
                      ),
                      if (!isUser)
                        BouncingWrapper(
                          onTap: () {
                            soundService.playClick();
                            audioService.speakText(message.message);
                          },
                          child: const Icon(Icons.volume_up, color: Color(0xFF00E5FF), size: 18),
                        ),
                    ],
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
                            'स्रोत (${message.sources.length}):',
                            style: GoogleFonts.notoSansDevanagari(
                              fontSize: 10,
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
