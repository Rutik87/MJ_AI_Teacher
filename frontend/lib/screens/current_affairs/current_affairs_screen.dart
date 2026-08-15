import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/models/current_affair_model.dart';
import 'package:frontend/providers/current_affairs_provider.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/liquid_glass_card.dart';

class CurrentAffairsScreen extends StatelessWidget {
  final Function(int)? onNavigateTab;

  const CurrentAffairsScreen({super.key, this.onNavigateTab});

  static final List<String> _topics = [
    'सर्व',
    'महाराष्ट्र',
    'भारत',
    'अर्थव्यवस्था',
    'विज्ञान व तंत्रज्ञान',
    'पर्यावरण',
    'क्रीडा',
    'योजना'
  ];

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CurrentAffairsProvider>();
    final articles = provider.articles;
    final nowFormatted = DateFormat('d MMMM yyyy').format(DateTime.now());

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
            } else if (onNavigateTab != null) {
              onNavigateTab!(0);
            }
          },
          child: const Icon(Icons.arrow_back, color: Colors.white),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'आजचे Current Affairs',
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            Text(
              nowFormatted,
              style: GoogleFonts.poppins(
                fontSize: 11,
                color: const Color(0xFF00E5FF),
              ),
            ),
          ],
        ),
        actions: [
          BouncingWrapper(
            onTap: () => provider.refreshNow(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: provider.isRefreshing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00E5FF)),
                    )
                  : const Icon(Icons.refresh, color: Color(0xFF00E5FF), size: 22),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // 1. Sync status bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: const Color(0xFF0A0E17),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.check_circle, color: Color(0xFF00E676), size: 14),
                    const SizedBox(width: 6),
                    Text(
                      'शासकीय स्त्रोतांद्वारे सत्यापित (Verified)',
                      style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70),
                    ),
                  ],
                ),
                Text(
                  provider.lastSyncedTime,
                  style: GoogleFonts.poppins(fontSize: 10, color: Colors.white38),
                ),
              ],
            ),
          ),

          // 2. Topic Filter Chips Strip
          SizedBox(
            height: 44,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              itemCount: _topics.length,
              itemBuilder: (context, index) {
                final t = _topics[index];
                final isSelected = provider.selectedTopic == t;

                return BouncingWrapper(
                  isBubbleSound: true,
                  onTap: () => provider.setSelectedTopic(t),
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    decoration: BoxDecoration(
                      color: isSelected ? const Color(0xFF7B1FA2).withOpacity(0.35) : const Color(0xFF0D1424),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isSelected ? const Color(0xFF9C27B0) : Colors.white12,
                        width: 1.2,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        t,
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 11.5,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? const Color(0xFF00E5FF) : Colors.white60,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          // 3. Current Affairs Articles List
          Expanded(
            child: provider.isLoading
                ? const Center(
                    child: CircularProgressIndicator(color: Color(0xFF00E5FF)),
                  )
                : articles.isEmpty
                    ? Center(
                        child: Text(
                          'अजून Current Affairs sync झालेले नाहीत.',
                          style: GoogleFonts.notoSansDevanagari(fontSize: 13, color: Colors.white54),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: () => provider.refreshNow(),
                        color: const Color(0xFF00E5FF),
                        backgroundColor: const Color(0xFF0A0E17),
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 6, 16, 110),
                          itemCount: articles.length,
                          itemBuilder: (context, index) {
                            final item = articles[index];
                            return _buildArticleCard(context, item);
                          },
                        ),
                      ),
          ),
        ],
      ),

      // 4. Floating Action Button: Daily Current Affairs Quiz
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 50),
        child: BouncingWrapper(
          isBubbleSound: true,
          onTap: () {
            if (onNavigateTab != null) {
              onNavigateTab!(3); // Navigate to Test tab
            } else {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('दैनिक चालू घडामोडी सराव चाचणी सुरू होत आहे...')),
              );
            }
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2979FF), Color(0xFF7B1FA2)],
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
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.quiz, color: Colors.white, size: 20),
                const SizedBox(width: 8),
                Text(
                  'दैनिक चालू घडामोडी चाचणी',
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
      ),
    );
  }

  Widget _buildArticleCard(BuildContext context, CurrentAffairModel item) {
    final prov = context.read<CurrentAffairsProvider>();
    final timeStr = DateFormat('h:mm a').format(item.publishedAt);

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E17),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.25)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00E5FF).withOpacity(0.08),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top Tags & Verification State
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF7B1FA2).withOpacity(0.25),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF9C27B0).withOpacity(0.5)),
                ),
                child: Text(
                  item.topic,
                  style: GoogleFonts.notoSansDevanagari(
                    fontSize: 10.5,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF00E5FF),
                  ),
                ),
              ),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00E676).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '✅ Verified',
                      style: GoogleFonts.poppins(
                        fontSize: 9.5,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF00E676),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  BouncingWrapper(
                    onTap: () => prov.toggleBookmark(item.id),
                    child: Icon(
                      item.isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                      color: item.isBookmarked ? const Color(0xFF00E5FF) : Colors.white38,
                      size: 20,
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 10),

          // Title
          Text(
            item.titleMr,
            style: GoogleFonts.notoSansDevanagari(
              fontSize: 14.5,
              fontWeight: FontWeight.bold,
              color: Colors.white,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 6),

          // Summary
          Text(
            item.summaryMr,
            style: GoogleFonts.notoSansDevanagari(
              fontSize: 12.5,
              height: 1.5,
              color: Colors.white.withOpacity(0.85),
            ),
          ),

          if (item.importantFacts.isNotEmpty) ...[
            const SizedBox(height: 10),
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
                    'महत्त्वाचे मुद्दे (Facts):',
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF00E5FF),
                    ),
                  ),
                  const SizedBox(height: 4),
                  ...item.importantFacts.map((f) => Text(
                        '• $f',
                        style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white70, height: 1.4),
                      )),
                ],
              ),
            ),
          ],

          const SizedBox(height: 12),

          // Source and Actions Strip
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'स्रोत: ${item.sourceName} ($timeStr)',
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 10,
                  color: Colors.white38,
                ),
              ),
              BouncingWrapper(
                isBubbleSound: true,
                onTap: () {
                  final chat = context.read<ChatProvider>();
                  chat.sendMessage('चालू घडामोडी प्रश्न: "${item.titleMr}" या विषयावर MPSC साठी ५ महत्त्वाचे पॉईंट्स समजाव.');
                  if (onNavigateTab != null) {
                    onNavigateTab!(1); // Go to AI Chat tab
                  }
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E5FF).withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.psychology, color: Color(0xFF00E5FF), size: 14),
                      const SizedBox(width: 4),
                      Text(
                        'AI ला विचारा',
                        style: GoogleFonts.notoSansDevanagari(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFF00E5FF),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
