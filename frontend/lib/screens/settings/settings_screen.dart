import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/core/services/sync_service.dart';
import 'package:frontend/core/services/offline_book_service.dart';
import 'package:frontend/widgets/bouncing_wrapper.dart';
import 'package:provider/provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _ttsEnabled = true;
  bool _darkMode = true;
  String _pingResult = '';

  void _showApiUrlDialog(BuildContext context) {
    final ctrl = TextEditingController(text: AppConfig.apiBaseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0A0E17),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0xFF00E5FF), width: 1.2),
        ),
        title: Text(
          'Cloud Backend URL',
          style: GoogleFonts.poppins(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Production HTTPS Backend URL टाका:',
              style: GoogleFonts.notoSansDevanagari(color: Colors.white70, fontSize: 12),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: ctrl,
              style: GoogleFonts.poppins(color: Colors.white, fontSize: 12.5),
              decoration: InputDecoration(
                filled: true,
                fillColor: const Color(0xFF141C2B),
                hintText: 'https://api.yourdomain.com/api',
                hintStyle: GoogleFonts.poppins(color: Colors.white38, fontSize: 12),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () async {
              await AppConfig.resetToDefaultUrl();
              Navigator.of(ctx).pop();
              setState(() {});
            },
            child: Text('Default', style: GoogleFonts.poppins(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00E5FF),
              foregroundColor: Colors.black,
            ),
            onPressed: () async {
              if (ctrl.text.trim().isNotEmpty) {
                await AppConfig.setCustomApiUrl(ctrl.text.trim());
              }
              Navigator.of(ctx).pop();
              setState(() {});
            },
            child: Text('Save URL', style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final syncService = context.watch<SyncService>();
    final offlineService = context.watch<OfflineBookService>();

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // Pure 100% Pitch Black
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: Text(
          'सेटिंग्ज (Settings)',
          style: GoogleFonts.notoSansDevanagari(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 110),
        children: [
          // 1. Cloud Architecture Status Card
          Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF0A1224), Color(0xFF140D24)],
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          syncService.isOnline ? Icons.cloud_done : Icons.cloud_off,
                          color: syncService.isOnline ? const Color(0xFF00E676) : const Color(0xFFFF5252),
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Cloud-First Architecture',
                          style: GoogleFonts.poppins(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: (syncService.isOnline ? const Color(0xFF00E676) : const Color(0xFFFF5252)).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        syncService.isOnline ? 'Online' : 'Offline',
                        style: GoogleFonts.poppins(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: syncService.isOnline ? const Color(0xFF00E676) : const Color(0xFFFF5252),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'API: ${AppConfig.apiBaseUrl}',
                  style: GoogleFonts.poppins(fontSize: 10.5, color: Colors.white60),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: BouncingWrapper(
                        onTap: () => _showApiUrlDialog(context),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00E5FF).withOpacity(0.12),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
                          ),
                          child: Center(
                            child: Text(
                              'Change Cloud URL',
                              style: GoogleFonts.poppins(fontSize: 11, color: const Color(0xFF00E5FF)),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: BouncingWrapper(
                        onTap: () async {
                          soundService.playClick();
                          await syncService.checkConnectivityAndSync();
                          setState(() {
                            _pingResult = syncService.isOnline ? 'Connected ✅' : 'Failed ❌';
                          });
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFFD500F9).withOpacity(0.12),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: const Color(0xFFD500F9).withOpacity(0.3)),
                          ),
                          child: Center(
                            child: Text(
                              _pingResult.isNotEmpty ? _pingResult : 'Test Ping ⚡',
                              style: GoogleFonts.poppins(fontSize: 11, color: const Color(0xFFD500F9)),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          _buildActionItem(
            icon: Icons.language,
            title: 'भाषा (Language)',
            trailingText: 'मराठी',
            onTap: () {},
          ),
          _buildActionItem(
            icon: Icons.psychology,
            title: 'AI उत्तर शैली',
            trailingText: 'विस्तृत व संदर्भासहित',
            onTap: () {},
          ),
          _buildSwitchItem(
            icon: Icons.volume_up,
            title: 'आवाज (Cloud TTS)',
            value: _ttsEnabled,
            onChanged: (val) {
              soundService.playClick();
              setState(() => _ttsEnabled = val);
            },
          ),
          _buildActionItem(
            icon: Icons.speed,
            title: 'आवाज गती (Speech Speed)',
            trailingText: '1.0x',
            onTap: () {},
          ),
          _buildSwitchItem(
            icon: Icons.dark_mode,
            title: 'Pure AMOLED Dark Mode',
            value: _darkMode,
            onChanged: (val) {
              soundService.playClick();
              setState(() => _darkMode = val);
            },
          ),
          _buildActionItem(
            icon: Icons.sd_storage,
            title: 'Offline Storage',
            trailingText: '${offlineService.downloadedBookIds.length} Books Cache',
            onTap: () async {
              await offlineService.clearAllOfflineBooks();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('ऑफलाईन कॅशे रिकामी केली!')),
              );
            },
          ),
          _buildActionItem(
            icon: Icons.smart_toy,
            title: 'AI Inference Engine',
            trailingText: 'Cloud Server (High Performance)',
            onTap: () {},
          ),
          _buildActionItem(
            icon: Icons.security,
            title: 'Data & Privacy (Zero Secrets on Phone)',
            trailingText: 'Secure',
            onTap: () {},
          ),
        ],
      ),
    );
  }

  Widget _buildActionItem({
    required IconData icon,
    required String title,
    required String trailingText,
    required VoidCallback onTap,
  }) {
    return BouncingWrapper(
      onTap: () {
        soundService.playClick();
        onTap();
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: const Color(0xFF0A0E17),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00E5FF), size: 20),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                title,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 13.5,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
              ),
            ),
            if (trailingText.isNotEmpty)
              Text(
                trailingText,
                style: GoogleFonts.notoSansDevanagari(
                  fontSize: 12,
                  color: Colors.white60,
                ),
              ),
            const SizedBox(width: 6),
            const Icon(Icons.arrow_forward_ios, size: 13, color: Colors.white38),
          ],
        ),
      ),
    );
  }

  Widget _buildSwitchItem({
    required IconData icon,
    required String title,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E17),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF00E5FF), size: 20),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              title,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 13.5,
                fontWeight: FontWeight.w500,
                color: Colors.white,
              ),
            ),
          ),
          Switch(
            value: value,
            activeColor: const Color(0xFF00E5FF),
            activeTrackColor: const Color(0xFF00E5FF).withOpacity(0.4),
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
