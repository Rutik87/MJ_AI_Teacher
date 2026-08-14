import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/test_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/tests/test_taking_screen.dart';

class TestHomeScreen extends StatefulWidget {
  const TestHomeScreen({super.key});

  @override
  State<TestHomeScreen> createState() => _TestHomeScreenState();
}

class _TestHomeScreenState extends State<TestHomeScreen> {
  String _selectedSubject = 'इतिहास';
  String _selectedTopic = '1857 चा उठाव';
  int _questionCount = 20;
  String _selectedDifficulty = 'मध्यम';
  String _selectedType = 'AI Generated';

  final List<String> _subjects = ['इतिहास', 'राज्यशास्त्र', 'भूगोल', 'अर्थशास्त्र', 'सामान्य विज्ञान'];
  final List<String> _topics = ['1857 चा उठाव', 'सत्यशोधक समाज', 'मूलभूत अधिकार', 'महाराष्ट्राचे पठार', 'पंचवार्षिक योजना'];
  final List<String> _difficulties = ['सोपा (Easy)', 'मध्यम (Medium)', 'कठीण (Hard)'];

  void _startTest() async {
    soundService.playBubble();
    final prov = context.read<TestProvider>();
    final success = await prov.startNewTest(
      subjectName: _selectedSubject,
      topicName: _selectedTopic,
      count: _questionCount,
    );

    if (success && mounted && prov.activeTest != null) {
      Navigator.of(context).push(MaterialPageRoute(
        builder: (ctx) => TestTakingScreen(test: prov.activeTest!),
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final testProv = context.watch<TestProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        title: Text(
          'AI चाचणी तयार करा',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 17,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 90),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Subject Select
            _buildLabel('विषय'),
            _buildDropdown(
              value: _selectedSubject,
              items: _subjects,
              onChanged: (val) => setState(() => _selectedSubject = val!),
            ),

            const SizedBox(height: 18),

            // 2. Topic Select
            _buildLabel('टॉपिक'),
            _buildDropdown(
              value: _selectedTopic,
              items: _topics,
              onChanged: (val) => setState(() => _selectedTopic = val!),
            ),

            const SizedBox(height: 18),

            // 3. Question Count Counter
            _buildLabel('प्रश्नांची संख्या'),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.white12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  BouncingWrapper(
                    onTap: () {
                      if (_questionCount > 5) {
                        soundService.playClick();
                        setState(() => _questionCount -= 5);
                      }
                    },
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white10,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.remove, color: Colors.white, size: 20),
                    ),
                  ),
                  Text(
                    '$_questionCount',
                    style: GoogleFonts.poppins(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF00E5FF),
                    ),
                  ),
                  BouncingWrapper(
                    onTap: () {
                      if (_questionCount < 50) {
                        soundService.playClick();
                        setState(() => _questionCount += 5);
                      }
                    },
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00E5FF).withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.add, color: Color(0xFF00E5FF), size: 20),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // 4. Difficulty
            _buildLabel('अवघडपणा'),
            _buildDropdown(
              value: _selectedDifficulty,
              items: _difficulties,
              onChanged: (val) => setState(() => _selectedDifficulty = val!),
            ),

            const SizedBox(height: 18),

            // 5. Question Type
            _buildLabel('प्रश्न प्रकार'),
            _buildDropdown(
              value: _selectedType,
              items: ['AI Generated', 'मागील परीक्षांचे (PYQ)', 'मिश्र (Mixed)'],
              onChanged: (val) => setState(() => _selectedType = val!),
            ),

            const SizedBox(height: 36),

            // 6. Start Test Button
            BouncingWrapper(
              isBubbleSound: true,
              onTap: testProv.isLoading ? null : _startTest,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2979FF), Color(0xFF651FFF)],
                  ),
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF2979FF).withOpacity(0.5),
                      blurRadius: 16,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Center(
                  child: testProv.isLoading
                      ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                        )
                      : Text(
                          'चाचणी सुरू करा',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: GoogleFonts.notoSansDevanagari(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: Colors.white70,
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required String value,
    required List<String> items,
    required ValueChanged<String?> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E17),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white12),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: items.contains(value) ? value : items.first,
          isExpanded: true,
          dropdownColor: const Color(0xFF0A0E17),
          style: GoogleFonts.notoSansDevanagari(color: Colors.white, fontSize: 14),
          icon: const Icon(Icons.keyboard_arrow_down, color: Color(0xFF00E5FF)),
          items: items.map((item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Text(item),
            );
          }).toList(),
          onChanged: (val) {
            soundService.playClick();
            onChanged(val);
          },
        ),
      ),
    );
  }
}
