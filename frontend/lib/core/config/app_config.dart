import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static const String appName = 'MPSC AI';
  static const String appVersion = '1.0.0';
  static const String tagline = 'तुमचा वैयक्तिक MPSC शिक्षक';

  // Dart define compile-time override (e.g. --dart-define=API_URL=https://mj-ai-teacher.onrender.com/api)
  static const String _compileTimeApiUrl = String.fromEnvironment('API_URL', defaultValue: '');
  static const String _compileTimeEnv = String.fromEnvironment('ENV', defaultValue: 'production');

  // Official Production HTTPS Backend URL
  static const String defaultProductionUrl = 'https://mj-ai-teacher.onrender.com/api';
  static const String _prefKeyCustomUrl = 'pref_custom_api_url';

  static String _activeUrl = '';

  static bool get isProduction => _compileTimeEnv == 'production' && !kDebugMode;

  static Future<void> initialize() async {
    // 1. Check custom user URL from SharedPreferences
    try {
      final prefs = await SharedPreferences.getInstance();
      final custom = prefs.getString(_prefKeyCustomUrl);
      if (custom != null && custom.trim().isNotEmpty) {
        _activeUrl = custom.trim();
        if (kDebugMode) {
          debugPrint('[AppConfig] Resolved API Base URL (Custom Preference): $_activeUrl');
        }
        return;
      }
    } catch (_) {}

    // 2. Check compile-time --dart-define=API_URL override
    if (_compileTimeApiUrl.isNotEmpty) {
      _activeUrl = _compileTimeApiUrl.trim();
    } else {
      // 3. Default to production cloud HTTPS backend
      _activeUrl = defaultProductionUrl;
    }

    if (kDebugMode) {
      debugPrint('[AppConfig] Resolved API Base URL: $_activeUrl');
    }
  }

  static String get apiBaseUrl => _activeUrl.isNotEmpty ? _activeUrl : defaultProductionUrl;

  static Future<void> setCustomApiUrl(String url) async {
    _activeUrl = url.trim();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKeyCustomUrl, _activeUrl);
    } catch (_) {}
    if (kDebugMode) {
      debugPrint('[AppConfig] Updated API Base URL: $_activeUrl');
    }
  }

  static Future<void> resetToDefaultUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_prefKeyCustomUrl);
    } catch (_) {}
    await initialize();
  }
}
