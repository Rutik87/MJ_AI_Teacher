import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/speech_service.dart';
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
  String _recognizedText = '';

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

  void _startVoiceListening() {
    soundService.playBubble();
    final wakeService = context.read<WakeWordService>();
    final speechService = context.read<SpeechService>();
    final mjProv = context.read<MJVoiceProvider>();
    final audioService = context.read<AudioService>();

    wakeService.setState(MJVoiceState.listening);

    speechService.startListening(onResult: (spoken) {
      if (mounted) {
        setState(() => _recognizedText = spoken);
      }
      if (spoken.trim().isNotEmpty) {
        // Debounce submit or full query
        Future.delayed(const Duration(milliseconds: 1400), () {
          if (mounted && _recognizedText == spoken && spoken.trim().isNotEmpty) {
            speechService.stopListening();
            _submitMessage(spoken.trim());
          }
        });
      }
    });
  }

  void _stopListeningAndSpeaking() {
    soundService.playClick();
    final wakeService = context.read<WakeWordService>();
    final speechService = context.read<SpeechService>();
    final audioService = context.read<AudioService>();

    speechService.stopListening();
    audioService.stop();
    wakeService.resetKeepAlive();
  }

  void _submitMessage(String query) {
    if (query.trim().isEmpty) return;
    final mjProv = context.read<MJVoiceProvider>();
    final audioService = context.read<AudioService>();
    final wakeService = context.read<WakeWordService>();

    setState(() => _recognizedText = '');
    _textController.clear();

    mjProv.sendMessage(
      text: query.trim(),
      audioService: audioService,
      wakeWordService: wakeService,
      onActionEvent: (action) {
        if (action == 'open_test' && widget.onNavigateTab != null) {
          widget.onNavigateTab!(3); // Go to Test
        }
      },
    );
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final mjProv = context.watch<MJVoiceProvider>();
    final wakeService = context.watch<WakeWordService>();
    final audioService = context.watch<AudioService>();

    String statusText;
    switch (wakeService.state) {
      case MJVoiceState.listening:
        statusText = _recognizedText.isNotEmpty ? _recognizedText : "ऐकतेय... बोला! 🎙️";
        break;
      case MJVoiceState.processing:
        statusText = "एक सेकंद... समजून घेतेय 💭";
        break;
      case MJVoiceState.speaking:
        statusText = "सांगतेय... 🔊";
        break;
      case MJVoiceState.stopped:
        statusText = "थांबले 😊";
        break;
      case MJVoiceState.idle:
      default:
        statusText = "बोल ना... 'Are MJ' बोलून सुरू करा 😄";
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
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'MJ',
              style: GoogleFonts.poppins(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                color: Colors.white,
                letterSpacing: 1.0,
              ),
            ),
            Text(
              'तुझी personal AI assistant',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 11,
                color: const Color(0xFF00E5FF),
              ),
            ),
          ],
        ),
        actions: [
          if (wakeService.isInActiveSession)
            Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF00E676).withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF00E676).withOpacity(0.5)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.bolt, color: Color(0xFF00E676), size: 14),
                  const SizedBox(width: 4),
                  Text(
                    '${wakeService.activeSecondsRemaining}s',
                    style: GoogleFonts.poppins(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF00E676),
                    ),
                  ),
                ],
              ),
            ),
          BouncingWrapper(
            onTap: () => mjProv.clearConversation(),
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 14),
              child: Icon(Icons.restart_alt, color: Colors.white70, size: 22),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // 1. Center Floating MJ Orb & Status Subtitle
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              children: [
                MJHologramOrb(
                  size: 140,
                  state: wakeService.state,
                  onTap: _startVoiceListening,
                ),
                const SizedBox(height: 12),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  child: Text(
                    statusText,
                    key: ValueKey(statusText),
                    textAlign: TextAlign.center,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: wakeService.state == MJVoiceState.listening
                          ? const Color(0xFF00E5FF)
                          : Colors.white70,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // 2. Multi-turn Speech Conversation Area
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
              itemCount: mjProv.messages.length,
              itemBuilder: (context, index) {
                final msg = mjProv.messages[index];
                return _buildMJChatBubble(msg, audioService);
              },
            ),
          ),

          // 3. Quick Suggestions Strip
          Container(
            height: 38,
            margin: const EdgeInsets.only(bottom: 6),
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 14),
              children: [
                _buildPromptChip('Are MJ, आज काय अभ्यास करू?'),
                _buildPromptChip('1857 चा उठाव समजाव'),
                _buildPromptChip('आजचा मूड नाहीये'),
                _buildPromptChip('चालू घडामोडी सांग'),
              ],
            ),
          ),

          // 4. Floating Voice Action Bar (Mic, Text input, Stop button)
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
                  // Stop Button
                  BouncingWrapper(
                    onTap: _stopListeningAndSpeaking,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white10,
                      ),
                      child: const Icon(Icons.stop, color: Color(0xFFFF5252), size: 20),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Text input
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
                          hintText: 'MJ ला काहीही विचार...',
                          hintStyle: GoogleFonts.notoSansDevanagari(color: Colors.white38, fontSize: 12),
                          border: InputBorder.none,
                          isDense: true,
                          contentPadding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onSubmitted: _submitMessage,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Giant Voice Mic Button
                  BouncingWrapper(
                    isBubbleSound: true,
                    onTap: () {
                      if (wakeService.state == MJVoiceState.listening) {
                        _stopListeningAndSpeaking();
                      } else {
                        _startVoiceListening();
                      }
                    },
                    child: Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          colors: [Color(0xFF00E5FF), Color(0xFFD500F9)],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF00E5FF).withOpacity(0.5),
                            blurRadius: 12,
                          ),
                        ],
                      ),
                      child: Icon(
                        wakeService.state == MJVoiceState.listening ? Icons.graphic_eq : Icons.mic,
                        color: Colors.white,
                        size: 22,
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

  Widget _buildPromptChip(String text) {
    return BouncingWrapper(
      onTap: () => _submitMessage(text),
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
        ),
        child: Text(
          text,
          style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: const Color(0xFF00E5FF)),
        ),
      ),
    );
  }

  Widget _buildMJChatBubble(MJMessage msg, AudioService audioService) {
    final isUser = msg.isUser;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
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
                gradient: LinearGradient(colors: [Color(0xFF00E5FF), Color(0xFFD500F9)]),
              ),
              child: const Center(
                child: Text('MJ', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white)),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isUser ? const Color(0xFF651FFF).withOpacity(0.85) : const Color(0xFF0D1424),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isUser ? const Color(0xFF7B1FA2) : const Color(0xFF00E5FF).withOpacity(0.25),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    msg.text,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 13,
                      height: 1.45,
                      color: Colors.white.withOpacity(0.95),
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
}
