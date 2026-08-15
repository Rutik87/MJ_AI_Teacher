import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:frontend/main.dart';
import 'package:frontend/providers/books_provider.dart';
import 'package:frontend/providers/chat_provider.dart';
import 'package:frontend/providers/test_provider.dart';
import 'package:frontend/providers/revision_provider.dart';
import 'package:frontend/providers/progress_provider.dart';
import 'package:frontend/providers/current_affairs_provider.dart';
import 'package:frontend/providers/settings_provider.dart';
import 'package:frontend/providers/mj_voice_provider.dart';
import 'package:frontend/core/services/audio_service.dart';
import 'package:frontend/core/services/speech_service.dart';
import 'package:frontend/core/services/wake_word_service.dart';
import 'package:frontend/core/services/sync_service.dart';
import 'package:frontend/core/services/offline_book_service.dart';

import 'package:frontend/core/services/gemini_live_audio_service.dart';
import 'package:frontend/providers/notes_provider.dart';

void main() {
  testWidgets('MPSC AI Cloud-First Full UI & Services Smoke Test', (WidgetTester tester) async {
    await tester.pumpWidget(
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

    await tester.pump(const Duration(milliseconds: 200));

    // Verify Splash Screen
    expect(find.text('MPSC AI'), findsOneWidget);
    expect(find.text('सुरू करा (Start) →'), findsOneWidget);

    // Tap start to enter Home
    await tester.tap(find.text('सुरू करा (Start) →'));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 200));

    // Verify Home Screen elements
    expect(find.text('Rutik!'), findsOneWidget);
    expect(find.text('तुमची तयारी'), findsOneWidget);
    expect(find.text('पुढे सुरू ठेवा'), findsOneWidget);
    expect(find.text('चालू घडामोडी'), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('AI'), findsOneWidget);
    expect(find.text('Books'), findsOneWidget);
    expect(find.text('Test'), findsOneWidget);
    expect(find.text('Profile'), findsOneWidget);
  });
}
