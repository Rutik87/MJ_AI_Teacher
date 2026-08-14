import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/services/speech_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/holographic_voice_mic.dart';

class VoiceModeScreen extends StatefulWidget {
  const VoiceModeScreen({super.key});

  @override
  State<VoiceModeScreen> createState() => _VoiceModeScreenState();
}

class _VoiceModeScreenState extends State<VoiceModeScreen> {
  String _recognizedQuery = '';

  @override
  void initState() {
    super.initState();
    _startVoiceListening();
  }

  void _startVoiceListening() {
    final speechService = context.read<SpeechService>();
    speechService.startListening(onResult: (text) {
      if (mounted) {
        setState(() {
          _recognizedQuery = text;
        });
      }
    });
  }

  void _stopAndSubmit() {
    soundService.playClick();
    final speechService = context.read<SpeechService>();
    speechService.stopListening();
    if (_recognizedQuery.trim().isNotEmpty) {
      context.read<ChatProvider>().sendMessage(_recognizedQuery.trim());
    }
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: BouncingWrapper(
          onTap: () {
            soundService.playClick();
            Navigator.of(context).pop();
          },
          child: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: Text(
          'AI ला विचारा (Voice)',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Spacer(),

            // Giant Holographic Mic
            Center(
              child: HolographicVoiceMic(
                size: 210,
                isListening: true,
                onTap: _stopAndSubmit,
              ),
            ),

            const SizedBox(height: 36),

            // Listening status
            Text(
              'ऐकत आहे...',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: const Color(0xFF00E5FF),
                shadows: [
                  const Shadow(color: Color(0xFF00E5FF), blurRadius: 16),
                ],
              ),
            ),
            const SizedBox(height: 8),

            Text(
              _recognizedQuery.isNotEmpty ? _recognizedQuery : 'बोला तुमचा प्रश्न...',
              textAlign: TextAlign.center,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 14,
                color: Colors.white70,
              ),
            ),

            const Spacer(),

            // Stop / Close Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 24),
              child: BouncingWrapper(
                isBubbleSound: true,
                onTap: _stopAndSubmit,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF651FFF), Color(0xFFD500F9)],
                    ),
                    borderRadius: BorderRadius.circular(28),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFD500F9).withOpacity(0.5),
                        blurRadius: 16,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.close, color: Colors.white, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'थांबा व उत्तर मिळवा',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
