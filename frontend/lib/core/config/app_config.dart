import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static const String appName = 'MPSC AI';
  static const String appVersion = '1.0.0';
  static const String tagline = 'तुमचा वैयक्तिक MPSC शिक्षक';

  // Dart define compile-time override (e.g. --dart-define=API_URL=https://your-cloud-backend.com/api)
  static const String _compileTimeApiUrl = String.fromEnvironment('API_URL', defaultValue: '');
  static const String _compileTimeEnv = String.fromEnvironment('ENV', defaultValue: 'production');

  static const String defaultProductionUrl = 'https://api.mpscai.com/api';
  static const String _prefKeyCustomUrl = 'pref_custom_api_url';

  static String _activeUrl = '';

  static bool get isProduction => _compileTimeEnv == 'production' && !kDebugMode;

  static Future<void> initialize() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final custom = prefs.getString(_prefKeyCustomUrl);
      if (custom != null && custom.trim().isNotEmpty) {
        _activeUrl = custom.trim();
        return;
      }
    } catch (_) {}

    if (_compileTimeApiUrl.isNotEmpty) {
      _activeUrl = _compileTimeApiUrl;
    } else if (kIsWeb) {
      final host = Uri.base.host.isNotEmpty ? Uri.base.host : 'localhost';
      _activeUrl = 'http://$host:8000/api';
    } else if (Platform.isAndroid) {
      // In production release, use cloud HTTPS API; in local debug, use 10.0.2.2 or LAN IP
      _activeUrl = isProduction ? defaultProductionUrl : 'http://10.0.2.2:8000/api';
    } else {
      _activeUrl = isProduction ? defaultProductionUrl : 'http://localhost:8000/api';
    }
  }

  static String get apiBaseUrl => _activeUrl.isNotEmpty ? _activeUrl : defaultProductionUrl;

  static Future<void> setCustomApiUrl(String url) async {
    _activeUrl = url.trim();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKeyCustomUrl, _activeUrl);
    } catch (_) {}
  }

  static Future<void> resetToDefaultUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_prefKeyCustomUrl);
    } catch (_) {}
    await initialize();
  }
}
