import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/schedule_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/cyber_drawer.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  void _showAddSlotDialog(BuildContext context, {int? editIndex, ScheduleSlotModel? existingSlot}) {
    final timeCtrl = TextEditingController(text: existingSlot?.timeSlot ?? '07:00 AM - 09:00 AM');
    final subjectCtrl = TextEditingController(text: existingSlot?.subject ?? 'राज्यशास्त्र');
    final topicCtrl = TextEditingController(text: existingSlot?.topic ?? 'मूलभूत हक्क व कर्तव्ये');
    final activityCtrl = TextEditingController(text: existingSlot?.activity ?? 'वाचन व नोट्स');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0E17),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: Color(0xFF00E5FF), width: 1.2),
        ),
        title: Text(
          editIndex != null ? 'स्लॉट संपादित करा' : 'नवीन अभ्यास स्लॉट जोडा',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildDialogField(label: 'वेळ (Time Slot)', controller: timeCtrl, hint: 'उदा. 07:00 AM - 09:00 AM'),
              const SizedBox(height: 10),
              _buildDialogField(label: 'विषय (Subject)', controller: subjectCtrl, hint: 'उदा. इतिहास / राज्यशास्त्र'),
              const SizedBox(height: 10),
              _buildDialogField(label: 'घटक / प्रकरण (Topic)', controller: topicCtrl, hint: 'उदा. १८५७ चा उठाव'),
              const SizedBox(height: 10),
              _buildDialogField(label: 'कृती (Activity)', controller: activityCtrl, hint: 'उदा. वाचन / MCQ सराव'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(
              'रद्द करा',
              style: GoogleFonts.notoSansDevanagari(color: Colors.white60),
            ),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00E5FF),
              foregroundColor: Colors.black,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              soundService.playClick();
              final slot = ScheduleSlotModel(
                timeSlot: timeCtrl.text.trim(),
                subject: subjectCtrl.text.trim(),
                topic: topicCtrl.text.trim(),
                activity: activityCtrl.text.trim(),
              );
              final schedProv = context.read<ScheduleProvider>();
              if (editIndex != null) {
                schedProv.updateSlot(editIndex, slot);
              } else {
                schedProv.addSlot(slot);
              }
              Navigator.of(ctx).pop();
            },
            child: Text(
              editIndex != null ? 'अपडेट करा' : 'जोडा',
              style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  void _showEditPlanDialog(BuildContext context) {
    final schedProv = context.read<ScheduleProvider>();
    final examCtrl = TextEditingController(text: schedProv.targetExam);
    final hoursCtrl = TextEditingController(text: schedProv.dailyStudyHours.toString());
    final dateCtrl = TextEditingController(text: schedProv.examDate);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0E17),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: Color(0xFF00E5FF), width: 1.2),
        ),
        title: Text(
          '🎯 लक्ष्य व दैनिक तास बदला',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildDialogField(label: 'लक्ष्य परीक्षा (Target Exam)', controller: examCtrl, hint: 'उदा. MPSC राज्यसेवा'),
            const SizedBox(height: 10),
            _buildDialogField(label: 'दैनिक अभ्यासाचे तास (Daily Hours)', controller: hoursCtrl, hint: 'उदा. 6.0'),
            const SizedBox(height: 10),
            _buildDialogField(label: 'परीक्षेची अंदाजित तारीख (YYYY-MM-DD)', controller: dateCtrl, hint: '2026-11-15'),
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
            onPressed: () {
              soundService.playClick();
              final hours = double.tryParse(hoursCtrl.text.trim()) ?? 6.0;
              schedProv.updateTargetExam(examCtrl.text.trim(), hours, dateCtrl.text.trim());
              Navigator.of(ctx).pop();
            },
            child: Text('सेव्ह करा', style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildDialogField({
    required String label,
    required TextEditingController controller,
    required String hint,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: const Color(0xFF00E5FF), fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          decoration: BoxDecoration(
            color: const Color(0xFF141C2B),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.white12),
          ),
          child: TextField(
            controller: controller,
            style: GoogleFonts.notoSansDevanagari(fontSize: 12.5, color: Colors.white),
            decoration: InputDecoration(
              hintText: hint,
              hintStyle: GoogleFonts.notoSansDevanagari(fontSize: 11.5, color: Colors.white30),
              border: InputBorder.none,
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(vertical: 8),
            ),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final schedProv = context.watch<ScheduleProvider>();

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
        title: Text(
          '🗓️ Study Schedule & Planner',
          style: GoogleFonts.poppins(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline, color: Color(0xFF00E5FF), size: 22),
            tooltip: 'नवीन स्लॉट जोडा',
            onPressed: () => _showAddSlotDialog(context),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => schedProv.fetchSchedule(),
        color: const Color(0xFF00E5FF),
        backgroundColor: const Color(0xFF0A0E17),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 100),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Target Exam & Daily Hours Header Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0A0E17), Color(0xFF141E33)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            schedProv.targetExam,
                            style: GoogleFonts.notoSansDevanagari(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        BouncingWrapper(
                          onTap: () => _showEditPlanDialog(context),
                          child: const Icon(Icons.edit_outlined, color: Color(0xFF00E5FF), size: 18),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        _buildBadge('⏱️ ${schedProv.dailyStudyHours.toInt()} तास / दिवस'),
                        const SizedBox(width: 8),
                        _buildBadge('📅 परीक्षा: ${schedProv.examDate}'),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // 2. AI Schedule Analyzer Action Button
              BouncingWrapper(
                onTap: () {
                  soundService.playClick();
                  schedProv.analyzeScheduleWithChatGPT();
                },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2979FF), Color(0xFF7B1FA2)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2979FF).withOpacity(0.4),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      schedProv.isAnalyzing
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        schedProv.isAnalyzing
                            ? 'ChatGPT वेळापत्रकाचे विश्लेषण करत आहे...'
                            : '🤖 ChatGPT द्वारे वेळापत्रक तपासा व सुधारा',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // 3. AI Analysis Results Card (if generated)
              if (schedProv.aiAnalysisMarkdown != null) ...[
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0E17),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.smart_toy_rounded, color: Color(0xFF00E5FF), size: 18),
                              const SizedBox(width: 6),
                              Text(
                                'ChatGPT मार्गदर्शन व शिफारस',
                                style: GoogleFonts.notoSansDevanagari(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: const Color(0xFF00E5FF),
                                ),
                              ),
                            ],
                          ),
                          IconButton(
                            icon: const Icon(Icons.refresh, color: Colors.white54, size: 18),
                            onPressed: () => schedProv.analyzeScheduleWithChatGPT(),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      MarkdownBody(
                        data: schedProv.aiAnalysisMarkdown!,
                        styleSheet: MarkdownStyleSheet(
                          p: GoogleFonts.notoSansDevanagari(fontSize: 12.5, height: 1.5, color: Colors.white.withOpacity(0.95)),
                          strong: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold, color: const Color(0xFF00E5FF)),
                          h3: GoogleFonts.notoSansDevanagari(fontSize: 14, fontWeight: FontWeight.bold, color: const Color(0xFFFFD54F)),
                          tableBody: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
                          tableHead: GoogleFonts.notoSansDevanagari(fontSize: 11.5, fontWeight: FontWeight.bold, color: Colors.white),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 18),

              // 4. Daily Timetable Slots Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '📋 दैनिक वेळापत्रक (Daily Slots)',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.white70,
                    ),
                  ),
                  TextButton.icon(
                    onPressed: () => _showAddSlotDialog(context),
                    icon: const Icon(Icons.add, size: 16, color: Color(0xFF00E5FF)),
                    label: Text(
                      'स्लॉट जोडा',
                      style: GoogleFonts.notoSansDevanagari(fontSize: 12, color: const Color(0xFF00E5FF)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              if (schedProv.slots.isEmpty)
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0E17),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Center(
                    child: Text(
                      'कोणताही स्लॉट जोडलेला नाही. वर दिलेले "+ स्लॉट जोडा" बटण वापरा.',
                      style: GoogleFonts.notoSansDevanagari(color: Colors.white54, fontSize: 12),
                    ),
                  ),
                )
              else
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: schedProv.slots.length,
                  itemBuilder: (ctx, index) {
                    final slot = schedProv.slots[index];
                    return _buildSlotCard(context, slot, index);
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBadge(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFF00E5FF).withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: GoogleFonts.notoSansDevanagari(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: const Color(0xFF00E5FF),
        ),
      ),
    );
  }

  Widget _buildSlotCard(BuildContext context, ScheduleSlotModel slot, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E17),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: const Color(0xFF2979FF).withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFF2979FF).withOpacity(0.4)),
            ),
            child: Text(
              slot.timeSlot,
              style: GoogleFonts.poppins(
                fontSize: 10.5,
                fontWeight: FontWeight.bold,
                color: const Color(0xFF00E5FF),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  slot.subject,
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Text(
                  '${slot.topic} • ${slot.activity}',
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 11,
                    color: Colors.white60,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.edit_outlined, color: Colors.white38, size: 18),
            onPressed: () => _showAddSlotDialog(context, editIndex: index, existingSlot: slot),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.white38, size: 18),
            onPressed: () => context.read<ScheduleProvider>().removeSlot(index),
          ),
        ],
      ),
    );
  }
}
