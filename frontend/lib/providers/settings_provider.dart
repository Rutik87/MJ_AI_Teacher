import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/config/app_config.dart';

class SettingsProvider extends ChangeNotifier {
  bool _isDarkMode = true;
  String _preferredLanguage = 'mr';
  bool _ttsEnabled = true;
  double _voiceSpeed = 1.0;
  String _customBackendUrl = '';

  bool get isDarkMode => _isDarkMode;
  String get preferredLanguage => _preferredLanguage;
  bool get ttsEnabled => _ttsEnabled;
  double get voiceSpeed => _voiceSpeed;
  String get customBackendUrl => _customBackendUrl;

  SettingsProvider() {
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    _isDarkMode = prefs.getBool('isDarkMode') ?? true;
    _preferredLanguage = prefs.getString('preferredLanguage') ?? 'mr';
    _ttsEnabled = prefs.getBool('ttsEnabled') ?? true;
    _voiceSpeed = prefs.getDouble('voiceSpeed') ?? 1.0;
    _customBackendUrl = prefs.getString('customBackendUrl') ?? '';
    
    if (_customBackendUrl.isNotEmpty) {
      await AppConfig.setCustomApiUrl(_customBackendUrl);
    }
    notifyListeners();
  }

  Future<void> toggleTheme(bool isDark) async {
    _isDarkMode = isDark;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isDarkMode', isDark);
    notifyListeners();
  }

  Future<void> setVoiceSpeed(double speed) async {
    _voiceSpeed = speed;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('voiceSpeed', speed);
    notifyListeners();
  }

  Future<void> setTtsEnabled(bool enabled) async {
    _ttsEnabled = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('ttsEnabled', enabled);
    notifyListeners();
  }

  Future<void> setCustomBackendUrl(String url) async {
    _customBackendUrl = url;
    if (url.isNotEmpty) {
      await AppConfig.setCustomApiUrl(url);
    } else {
      await AppConfig.resetToDefaultUrl();
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('customBackendUrl', url);
    notifyListeners();
  }
}
