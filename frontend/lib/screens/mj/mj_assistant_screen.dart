import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/gemini_live_audio_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/core/services/wake_word_service.dart';
import 'package:frontend/providers/mj_voice_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/mj_hologram_orb.dart';

class MJAssistantScreen extends StatefulWidget {
  final Function(int)? onNavigateTab;

  const MJAssistantScreen({super.key, this.onNavigateTab});

  @override
  State<MJAssistantScreen> createState() => _MJAssistantScreenState();
}

class _MJAssistantScreenState extends State<MJAssistantScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (WidgetsBinding.instance.runtimeType.toString().contains('Test')) {
        return;
      }
      final liveService = context.read<GeminiLiveAudioService>();
      final mjProv = context.read<MJVoiceProvider>();
      liveService.connect(bookId: mjProv.activeBookId);
    });
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
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

  void _submitTextMessage(String query) {
    if (query.trim().isEmpty) return;
    final liveService = context.read<GeminiLiveAudioService>();
    final mjProv = context.read<MJVoiceProvider>();

    _textController.clear();
    liveService.sendText(query.trim());

    mjProv.addMessage(MJMessage(
      text: query.trim(),
      isUser: true,
      timestamp: DateTime.now(),
    ));

    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final liveService = context.watch<GeminiLiveAudioService>();
    final mjProv = context.watch<MJVoiceProvider>();

    String statusText;
    Color statusColor;

    switch (liveService.state) {
      case GeminiLiveState.connecting:
        statusText = "Gemini Live शी जोडत आहे...";
        statusColor = const Color(0xFFFFB300);
        break;
      case GeminiLiveState.listening:
        statusText = liveService.liveTranscript.isNotEmpty
            ? liveService.liveTranscript
            : "ऐकत आहे... बोला! 🎙️";
        statusColor = const Color(0xFF00E5FF);
        break;
      case GeminiLiveState.speaking:
        statusText = "MJ बोलत आहे... 🔊";
        statusColor = const Color(0xFF00E676);
        break;
      case GeminiLiveState.interrupted:
        statusText = "थांबले! ऐकत आहे... 😊";
        statusColor = const Color(0xFFE040FB);
        break;
      case GeminiLiveState.error:
        statusText = liveService.errorMessage ?? "कनेक्शन त्रुटी आली.";
        statusColor = Colors.redAccent;
        break;
      case GeminiLiveState.disconnected:
      default:
        statusText = "पुन्हा जोडण्यासाठी टॅप करा 🔄";
        statusColor = Colors.white60;
        break;
    }

    MJVoiceState orbState;
    switch (liveService.state) {
      case GeminiLiveState.listening:
        orbState = MJVoiceState.listening;
        break;
      case GeminiLiveState.speaking:
        orbState = MJVoiceState.speaking;
        break;
      case GeminiLiveState.connecting:
        orbState = MJVoiceState.processing;
        break;
      case GeminiLiveState.interrupted:
        orbState = MJVoiceState.stopped;
        break;
      default:
        orbState = MJVoiceState.idle;
        break;
    }

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: BouncingWrapper(
          onTap: () {
            soundService.playClick();
            if (Navigator.of(context).canPop()) {
              Navigator.of(context).pop();
            } else if (widget.onNavigateTab != null) {
              widget.onNavigateTab!(0);
            }
          },
          child: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: liveService.isConnected ? const Color(0xFF00E676) : Colors.amber,
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'MJ Live Assistant',
                  style: GoogleFonts.poppins(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                Text(
                  'Gemini 3.1 Live • Aoede Voice',
                  style: GoogleFonts.poppins(fontSize: 10, color: const Color(0xFF00E5FF)),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              liveService.isConnected ? Icons.cloud_done : Icons.cloud_off,
              color: liveService.isConnected ? const Color(0xFF00E676) : Colors.white38,
              size: 20,
            ),
            onPressed: () {
              if (!liveService.isConnected) {
                liveService.connect();
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          const SizedBox(height: 10),

          // Central Audio-Reactive Hologram Orb
          Center(
            child: MJHologramOrb(
              size: 160,
              state: orbState,
              onTap: () {
                soundService.playBubble();
                if (liveService.isConnected) {
                  liveService.startMicrophone();
                } else {
                  liveService.connect();
                }
              },
            ),
          ),

          const SizedBox(height: 12),

          // Live State Indicator Pill
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: statusColor.withOpacity(0.4)),
            ),
            child: Text(
              statusText,
              textAlign: TextAlign.center,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: statusColor,
              ),
            ),
          ),

          const SizedBox(height: 12),

          // Live Transcript & Conversation History
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: mjProv.messages.length + (liveService.assistantTranscript.isNotEmpty ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == mjProv.messages.length && liveService.assistantTranscript.isNotEmpty) {
                  // Live streaming assistant bubble
                  return _buildMessageBubble(
                    MJMessage(
                      text: liveService.assistantTranscript,
                      isUser: false,
                      timestamp: DateTime.now(),
                    ),
                    isLive: true,
                  );
                }

                final msg = mjProv.messages[index];
                return _buildMessageBubble(msg);
              },
            ),
          ),

          // Bottom Controls & Input Bar
          Container(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            decoration: BoxDecoration(
              color: const Color(0xFF0A0E17),
              border: Border(top: BorderSide(color: Colors.white.withOpacity(0.06))),
            ),
            child: Row(
              children: [
                // Instant Barge-In / Stop Button
                BouncingWrapper(
                  onTap: () {
                    soundService.playClick();
                    liveService.connect();
                  },
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.white.withOpacity(0.08),
                    ),
                    child: const Icon(Icons.stop_circle_outlined, color: Colors.redAccent, size: 22),
                  ),
                ),
                const SizedBox(width: 10),

                // Text input box
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
                      style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white),
                      decoration: InputDecoration(
                        hintText: 'मराठीत किंवा Roman मध्ये लिहा...',
                        hintStyle: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white38),
                        border: InputBorder.none,
                      ),
                      onSubmitted: _submitTextMessage,
                    ),
                  ),
                ),
                const SizedBox(width: 10),

                // Send Button
                BouncingWrapper(
                  isBubbleSound: true,
                  onTap: () => _submitTextMessage(_textController.text),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(colors: [Color(0xFF00E5FF), Color(0xFF7B1FA2)]),
                    ),
                    child: const Icon(Icons.send, color: Colors.white, size: 18),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(MJMessage msg, {bool isLive = false}) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: const BoxConstraints(maxWidth: 290),
        decoration: BoxDecoration(
          color: msg.isUser
              ? const Color(0xFF1A3B66)
              : isLive
                  ? const Color(0xFF16253B)
                  : const Color(0xFF121824),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: msg.isUser
                ? const Color(0xFF00E5FF).withOpacity(0.3)
                : isLive
                    ? const Color(0xFF00E676).withOpacity(0.4)
                    : Colors.white.withOpacity(0.08),
          ),
        ),
        child: Text(
          msg.text,
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 13,
            color: Colors.white.withOpacity(0.95),
            height: 1.4,
          ),
        ),
      ),
    );
  }
}
