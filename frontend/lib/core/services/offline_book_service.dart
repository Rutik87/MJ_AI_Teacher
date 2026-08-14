import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/models/book.dart';

class OfflineBookService extends ChangeNotifier {
  static const String _prefKeyOfflineBookIds = 'offline_downloaded_book_ids';
  static const String _prefKeyBookCachePrefix = 'offline_book_cache_';
  final Set<int> _downloadedBookIds = {};
  bool _isDownloading = false;

  Set<int> get downloadedBookIds => _downloadedBookIds;
  bool get isDownloading => _isDownloading;

  OfflineBookService() {
    _loadDownloadedBookIds();
  }

  Future<void> _loadDownloadedBookIds() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final list = prefs.getStringList(_prefKeyOfflineBookIds) ?? [];
      _downloadedBookIds.clear();
      _downloadedBookIds.addAll(list.map((id) => int.tryParse(id) ?? 0).where((id) => id > 0));
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading offline books: $e');
    }
  }

  bool isBookDownloaded(int bookId) => _downloadedBookIds.contains(bookId);

  Future<void> downloadBookForOffline(BookModel book) async {
    if (_downloadedBookIds.contains(book.id)) return;

    _isDownloading = true;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      
      // Store book data and basic pages locally
      final bookJson = jsonEncode(book.toJson());
      await prefs.setString('$_prefKeyBookCachePrefix${book.id}', bookJson);

      _downloadedBookIds.add(book.id);
      await prefs.setStringList(
        _prefKeyOfflineBookIds,
        _downloadedBookIds.map((id) => id.toString()).toList(),
      );
    } catch (e) {
      debugPrint('Download book offline error: $e');
    } finally {
      _isDownloading = false;
      notifyListeners();
    }
  }

  Future<void> removeOfflineBook(int bookId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('$_prefKeyBookCachePrefix$bookId');
      _downloadedBookIds.remove(bookId);
      await prefs.setStringList(
        _prefKeyOfflineBookIds,
        _downloadedBookIds.map((id) => id.toString()).toList(),
      );
      notifyListeners();
    } catch (e) {
      debugPrint('Remove offline book error: $e');
    }
  }

  Future<void> clearAllOfflineBooks() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      for (final id in _downloadedBookIds) {
        await prefs.remove('$_prefKeyBookCachePrefix$id');
      }
      _downloadedBookIds.clear();
      await prefs.remove(_prefKeyOfflineBookIds);
      notifyListeners();
    } catch (e) {
      debugPrint('Clear all offline books error: $e');
    }
  }
}
