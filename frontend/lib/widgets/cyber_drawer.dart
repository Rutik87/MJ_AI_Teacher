import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:frontend/screens/settings/settings_screen.dart';

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
            // 1. Drawer Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
              ),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: const Color(0xFF00E5FF).withOpacity(0.15),
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFF00E5FF), width: 1.5),
                    ),
                    child: const Center(
                      child: Icon(Icons.school_rounded, color: Color(0xFF00E5FF), size: 24),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'MPSC AI',
                          style: GoogleFonts.poppins(
                            fontSize: 18,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.0,
                            color: Colors.white,
                          ),
                        ),
                        Text(
                          'Files & ChatGPT Workspace',
                          style: GoogleFonts.poppins(
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

            const SizedBox(height: 12),

            // 2. Navigation Items (Files, Chat, Settings)
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  _buildDrawerItem(
                    context,
                    icon: Icons.folder_outlined,
                    title: '📚 Files (माझी पुस्तके)',
                    subtitle: 'PDF / TXT व्यवस्थापन व वाचन',
                    onTap: () {
                      Navigator.of(context).pop();
                      onSelectTab(0);
                    },
                  ),
                  const SizedBox(height: 6),
                  _buildDrawerItem(
                    context,
                    icon: Icons.chat_bubble_outline_rounded,
                    title: '🤖 ChatGPT (AI चॅट)',
                    subtitle: 'फाईल-आधारित MPSC प्रश्नोत्तरे',
                    onTap: () {
                      Navigator.of(context).pop();
                      onSelectTab(1);
                    },
                  ),
                  const SizedBox(height: 6),
                  _buildDrawerItem(
                    context,
                    icon: Icons.settings_outlined,
                    title: '⚙️ Settings (सेटिंग्ज)',
                    subtitle: 'सर्व्हर व भाषा पर्याय',
                    onTap: () {
                      Navigator.of(context).pop();
                      Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const SettingsScreen()),
                      );
                    },
                  ),
                ],
              ),
            ),

            // 3. Footer version badge
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'MPSC AI v2.0 • Clean Edition',
                style: GoogleFonts.poppins(
                  fontSize: 11,
                  color: Colors.white30,
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
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return BouncingWrapper(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.06)),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00E5FF), size: 22),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: Colors.white.withOpacity(0.95),
                    ),
                  ),
                  Text(
                    subtitle,
                    style: GoogleFonts.notoSansDevanagari(
                      fontSize: 11,
                      color: Colors.white38,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white24, size: 14),
          ],
        ),
      ),
    );
  }
}
