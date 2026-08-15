import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/speech_service.dart';
import 'package:frontend/core/services/sound_service.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/providers/test_provider.dart';
import 'package:frontend/providers/revision_provider.dart';
import 'package:frontend/providers/progress_provider.dart';
import 'package:frontend/providers/settings_provider.dart';

import 'package:frontend/screens/splash/splash_screen.dart';
import 'package:frontend/screens/home/home_screen.dart';
import 'package:frontend/screens/chat/ai_chat_screen.dart';
import 'package:frontend/screens/books/book_library_screen.dart';
import 'package:frontend/screens/tests/test_home_screen.dart';
import 'package:frontend/screens/progress/progress_screen.dart';
import 'package:frontend/screens/profile/profile_screen.dart';
import 'package:frontend/screens/tests/pyq_screen.dart';
import 'package:frontend/screens/revision/revision_screen.dart';
import 'package:frontend/screens/subjects/subject_hub_screen.dart';
import 'package:frontend/screens/settings/settings_screen.dart';

import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/core/services/sync_service.dart';
import 'package:frontend/core/services/offline_book_service.dart';
import 'package:frontend/core/services/wake_word_service.dart';
import 'package:frontend/providers/mj_voice_provider.dart';
import 'package:frontend/screens/mj/mj_assistant_screen.dart';
import 'package:frontend/core/services/gemini_live_audio_service.dart';
import 'package:frontend/providers/current_affairs_provider.dart';
import 'package:frontend/providers/notes_provider.dart';
import 'package:frontend/screens/current_affairs/current_affairs_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppConfig.initialize();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
        ChangeNotifierProvider(create: (_) => SyncService()),
        ChangeNotifierProvider(create: (_) => OfflineBookService()),
        ChangeNotifierProvider(create: (_) => BooksProvider()),
        ChangeNotifierProvider(create: (_) => ChatProvider()),
        ChangeNotifierProvider(create: (_) => TestProvider()),
        ChangeNotifierProvider(create: (_) => RevisionProvider()),
        ChangeNotifierProvider(create: (_) => ProgressProvider()),
        ChangeNotifierProvider(create: (_) => CurrentAffairsProvider()),
        ChangeNotifierProvider(create: (_) => NotesProvider()),
        ChangeNotifierProvider(create: (_) => AudioService()),
        ChangeNotifierProvider(create: (_) => GeminiLiveAudioService()),
        ChangeNotifierProvider(create: (_) => SpeechService()),
        ChangeNotifierProvider(create: (_) => WakeWordService()),
        ChangeNotifierProvider(create: (_) => MJVoiceProvider()),
      ],
      child: const MPSCAssistantApp(),
    ),
  );
}

class MPSCAssistantApp extends StatefulWidget {
  const MPSCAssistantApp({super.key});

  @override
  State<MPSCAssistantApp> createState() => _MPSCAssistantAppState();
}

class _MPSCAssistantAppState extends State<MPSCAssistantApp> {
  bool _showSplash = true;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MPSC AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark,
      home: _showSplash
          ? SplashScreen(
              onStart: () {
                setState(() => _showSplash = false);
              },
            )
          : const MainNavigationShell(),
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;

  void _onTabSelected(int index) {
    soundService.playClick();
    setState(() {
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      HomeScreen(onNavigateTab: _onTabSelected),
      const AIChatScreen(),
      const BookLibraryScreen(),
      const TestHomeScreen(),
      const PYQScreen(),
      const RevisionScreen(),
      const ProgressScreen(),
      const SettingsScreen(),
      const ProfileScreen(),
      CurrentAffairsScreen(onNavigateTab: _onTabSelected),
      MJAssistantScreen(onNavigateTab: _onTabSelected),
      SubjectHubScreen(onNavigateTab: _onTabSelected),
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF000000), // 100% Pure Pitch Black
      extendBody: true,
      body: IndexedStack(
        index: _currentIndex.clamp(0, screens.length - 1),
        children: screens,
      ),
      bottomNavigationBar: Container(
        color: Colors.transparent, // Completely transparent bottom bar
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E17).withOpacity(0.7), // Ultra-sheer dark glass
                borderRadius: BorderRadius.circular(26),
                border: Border.all(
                  color: const Color(0xFF00E5FF).withOpacity(0.2),
                  width: 1.0,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(0, Icons.home_outlined, Icons.home, 'Home'),
                  _buildNavItem(1, Icons.psychology_outlined, Icons.psychology, 'AI'),
                  _buildNavItem(2, Icons.menu_book_outlined, Icons.menu_book, 'Books'),
                  _buildNavItem(3, Icons.quiz_outlined, Icons.quiz, 'Test'),
                  _buildNavItem(8, Icons.person_outline, Icons.person, 'Profile'),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData inactiveIcon, IconData activeIcon, String label) {
    final bool isSelected = _currentIndex == index;

    return GestureDetector(
      onTap: () => _onTabSelected(index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeInOut,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: isSelected
            ? BoxDecoration(
                color: const Color(0xFF7B1FA2).withOpacity(0.25),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: const Color(0xFF9C27B0).withOpacity(0.8),
                  width: 1.2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF9C27B0).withOpacity(0.35),
                    blurRadius: 8,
                  ),
                ],
              )
            : null,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isSelected ? activeIcon : inactiveIcon,
              color: isSelected ? const Color(0xFF00E5FF) : Colors.white54,
              size: 20,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: GoogleFonts.poppins(
                fontSize: 9.5,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w400,
                color: isSelected ? const Color(0xFF00E5FF) : Colors.white54,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
