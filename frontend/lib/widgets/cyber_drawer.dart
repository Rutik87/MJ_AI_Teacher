import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/widgets/neon_brain_hologram.dart';

class CyberDrawer extends StatelessWidget {
  final Function(int) onSelectTab;

  const CyberDrawer({super.key, required this.onSelectTab});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: const Color(0xFF070B14),
      child: SafeArea(
        child: Column(
          children: [
            // 1. Drawer Header (Screen 15 with Neon Brain Avatar)
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
              ),
              child: Row(
                children: [
                  const NeonBrainHologram(size: 48),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'MPSC AI',
                          style: GoogleFonts.poppins(
                            fontSize: 16,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.0,
                            color: Colors.white,
                          ),
                        ),
                        Text(
                          'तुमचा वैयक्तिक शिक्षक',
                          style: GoogleFonts.notoSansDevanagari(
                            fontSize: 11,
                            color: const Color(0xFF00E5FF),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // 2. Navigation Items (Screen 15)
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                children: [
                  _buildDrawerItem(context, icon: Icons.home_outlined, title: 'Home', index: 0),
                  _buildDrawerItem(context, icon: Icons.mic_external_on, title: 'MJ Voice सोबती', index: 10),
                  _buildDrawerItem(context, icon: Icons.psychology_outlined, title: 'AI शिक्षक', index: 1),
                  _buildDrawerItem(context, icon: Icons.menu_book_outlined, title: 'माझी पुस्तके', index: 2),
                  _buildDrawerItem(context, icon: Icons.quiz_outlined, title: 'AI चाचणी', index: 3),
                  _buildDrawerItem(context, icon: Icons.newspaper, title: 'चालू घडामोडी', index: 9),
                  _buildDrawerItem(context, icon: Icons.history_edu, title: 'PYQ', index: 4),
                  _buildDrawerItem(context, icon: Icons.repeat, title: 'Revision', index: 5),
                  _buildDrawerItem(context, icon: Icons.analytics_outlined, title: 'प्रगती', index: 6),
                  _buildDrawerItem(context, icon: Icons.bookmark_border, title: 'Bookmarks', index: 5),
                  _buildDrawerItem(context, icon: Icons.settings_outlined, title: 'सेटिंग्ज', index: 7),
                ],
              ),
            ),

            // 3. Log Out Item
            Padding(
              padding: const EdgeInsets.all(12),
              child: BouncingWrapper(
                onTap: () {
                  soundService.playClick();
                  Navigator.of(context).pop();
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.04),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.logout, color: Color(0xFFFF5252), size: 18),
                      const SizedBox(width: 12),
                      Text(
                        'Log Out',
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFFFF5252),
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

  Widget _buildDrawerItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required int index,
  }) {
    return BouncingWrapper(
      onTap: () {
        soundService.playClick();
        Navigator.of(context).pop();
        onSelectTab(index);
      },
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 2),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00E5FF), size: 20),
            const SizedBox(width: 14),
            Text(
              title,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: Colors.white.withOpacity(0.9),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
