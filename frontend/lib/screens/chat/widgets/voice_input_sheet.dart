import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/services/speech_service.dart';

class VoiceInputSheet extends StatefulWidget {
  final Function(String) onRecognizedText;

  const VoiceInputSheet({super.key, required this.onRecognizedText});

  @override
  State<VoiceInputSheet> createState() => _VoiceInputSheetState();
}

class _VoiceInputSheetState extends State<VoiceInputSheet> with SingleTickerProviderStateMixin {
  final SpeechService _speechService = SpeechService();
  String _spokenText = '';
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);

    _startListening();
  }

  Future<void> _startListening() async {
    await _speechService.startListening(
      onResult: (text) {
        setState(() {
          _spokenText = text;
        });
      },
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    _speechService.stopListening();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.white24,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'मराठीत बोला... 🎤',
            style: GoogleFonts.notoSansDevanagari(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            'तुमचा MPSC प्रश्न स्पष्ट आवाजात बोला.',
            style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: Colors.white54),
          ),
          const SizedBox(height: 24),
          // Pulsing Mic Icon
          AnimatedBuilder(
            animation: _animController,
            builder: (context, child) {
              return Transform.scale(
                scale: 1.0 + (_animController.value * 0.15),
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.primaryColor.withOpacity(0.2),
                    border: Border.all(
                      color: AppTheme.primaryColor.withOpacity(0.8),
                      width: 2,
                    ),
                  ),
                  child: const Icon(
                    Icons.mic,
                    color: AppTheme.primaryColor,
                    size: 40,
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 24),
          // Recognized Text Preview
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.black26,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white12),
            ),
            child: Text(
              _spokenText.isNotEmpty
                  ? _spokenText
                  : 'उदा: "सत्यशोधक समाजाची उद्दिष्टे सांगा"',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 14,
                color: _spokenText.isNotEmpty ? Colors.white : Colors.white38,
              ),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('रद्द करा'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    String query = _spokenText.isNotEmpty
                        ? _spokenText
                        : '1857 च्या उठावाची कारणे सांगा';
                    widget.onRecognizedText(query);
                    Navigator.of(context).pop();
                  },
                  child: Text('विचारा (Ask)', style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
