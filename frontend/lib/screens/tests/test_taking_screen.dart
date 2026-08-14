import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/test_model.dart';
import 'package:frontend/providers/test_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/tests/test_result_screen.dart';

class TestTakingScreen extends StatefulWidget {
  final TestResultModel test;

  const TestTakingScreen({super.key, required this.test});

  @override
  State<TestTakingScreen> createState() => _TestTakingScreenState();
}

class _TestTakingScreenState extends State<TestTakingScreen> {
  int _currentIndex = 0;
  final Map<int, String> _userAnswers = {};
  late DateTime _endDeadline;
  int _secondsLeft = 14 * 60 + 32; // 14:32 default
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _endDeadline = DateTime.now().add(Duration(seconds: _secondsLeft));
    _startTimer();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(milliseconds: 500), (t) {
      final diff = _endDeadline.difference(DateTime.now()).inSeconds;
      if (diff > 0) {
        if (mounted && diff != _secondsLeft) {
          setState(() => _secondsLeft = diff);
        }
      } else {
        _timer?.cancel();
        if (mounted) {
          setState(() => _secondsLeft = 0);
          _submitTest();
        }
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String get _formattedTime {
    int minutes = _secondsLeft ~/ 60;
    int seconds = _secondsLeft % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  void _selectOption(int qId, String opt) {
    soundService.playClick();
    setState(() {
      _userAnswers[qId] = opt;
    });
  }

  void _submitTest() async {
    _timer?.cancel();
    final prov = context.read<TestProvider>();
    final success = await prov.submitTest();
    if (success && mounted && prov.completedResult != null) {
      Navigator.of(context).pushReplacement(MaterialPageRoute(
        builder: (ctx) => TestResultScreen(result: prov.completedResult!),
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final questions = widget.test.questions.isNotEmpty
        ? widget.test.questions
        : [
            MCQQuestionModel(
              id: 1,
              questionText: 'खालीलपैकी 1857 च्या उठावाचे नेतृत्व कोणी केले?',
              optionA: 'नाना साहेब पेशवे',
              optionB: 'तात्या टोपे',
              optionC: 'बहादूर शाह झफर',
              optionD: 'राणी लक्ष्मीबाई',
              correctOption: 'B',
              explanationMr: 'तात्या टोपे यांनी १८५७ च्या उठावात महत्त्वपूर्ण नेतृत्व केले.',
              difficulty: 'medium',
            ),
          ];

    final currentQ = questions[_currentIndex.clamp(0, questions.length - 1)];
    final selectedOpt = _userAnswers[currentQ.id ?? 0];

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        leading: BouncingWrapper(
          onTap: () {
            soundService.playClick();
            Navigator.of(context).pop();
          },
          child: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: Text(
          '${_currentIndex + 1} / ${questions.length}',
          style: GoogleFonts.poppins(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF0D1424),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
            ),
            child: Row(
              children: [
                const Icon(Icons.timer_outlined, color: Color(0xFF00E5FF), size: 16),
                const SizedBox(width: 4),
                Text(
                  _formattedTime,
                  style: GoogleFonts.poppins(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF00E5FF),
                  ),
                ),
              ],
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(
            value: (_currentIndex + 1) / questions.length,
            backgroundColor: Colors.white12,
            color: const Color(0xFF00E5FF),
            minHeight: 3,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 100),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Question Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: Colors.white12),
              ),
              child: Text(
                currentQ.questionText,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  height: 1.4,
                ),
              ),
            ),

            const SizedBox(height: 20),

            // 4 Options
            _buildOptionCard(currentQ.id ?? 0, 'A', currentQ.optionA, selectedOpt == 'A'),
            _buildOptionCard(currentQ.id ?? 0, 'B', currentQ.optionB, selectedOpt == 'B'),
            _buildOptionCard(currentQ.id ?? 0, 'C', currentQ.optionC, selectedOpt == 'C'),
            _buildOptionCard(currentQ.id ?? 0, 'D', currentQ.optionD, selectedOpt == 'D'),
          ],
        ),
      ),

      // Bottom Navigation Toolbar (मागील, सोडा, पुढील)
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF070B14).withOpacity(0.95),
          border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
        ),
        child: SafeArea(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Previous
              BouncingWrapper(
                onTap: _currentIndex > 0
                    ? () {
                        soundService.playClick();
                        setState(() => _currentIndex--);
                      }
                    : null,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1424),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    'मागील',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 13,
                      color: _currentIndex > 0 ? Colors.white : Colors.white24,
                    ),
                  ),
                ),
              ),

              // Skip
              BouncingWrapper(
                onTap: () {
                  soundService.playClick();
                  if (_currentIndex < questions.length - 1) {
                    setState(() => _currentIndex++);
                  }
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1424),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    'सोडा',
                    style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white70),
                  ),
                ),
              ),

              // Next / Submit
              BouncingWrapper(
                isBubbleSound: true,
                onTap: () {
                  if (_currentIndex < questions.length - 1) {
                    soundService.playClick();
                    setState(() => _currentIndex++);
                  } else {
                    _submitTest();
                  }
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 10),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2979FF), Color(0xFF651FFF)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2979FF).withOpacity(0.4),
                        blurRadius: 10,
                      ),
                    ],
                  ),
                  child: Text(
                    _currentIndex < questions.length - 1 ? 'पुढील' : 'निकाल पहा',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOptionCard(int qId, String optKey, String optText, bool isSelected) {
    return BouncingWrapper(
      onTap: () => _selectOption(qId, optKey),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00E676).withOpacity(0.12) : const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? const Color(0xFF00E676) : Colors.white12,
            width: isSelected ? 1.5 : 1.0,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: const Color(0xFF00E676).withOpacity(0.3),
                    blurRadius: 12,
                  ),
                ]
              : null,
        ),
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? const Color(0xFF00E676) : Colors.white10,
                border: Border.all(
                  color: isSelected ? const Color(0xFF00E676) : Colors.white24,
                ),
              ),
              child: Center(
                child: Text(
                  optKey,
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: isSelected ? Colors.black : Colors.white,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                optText,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 14,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? Colors.white : Colors.white.withOpacity(0.85),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
