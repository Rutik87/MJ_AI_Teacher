import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/book.dart';

class BooksProvider extends ChangeNotifier {
  List<BookModel> _books = [];
  String _selectedFilter = 'All'; // 'All', 'PDF', 'TXT', 'Images', 'Generated'
  String _searchQuery = '';
  bool _isLoading = false;
  String? _errorMessage;
  Timer? _statusPollingTimer;

  List<BookModel> get books => _filteredBooks();
  List<BookModel> get allBooks => _books;
  String get selectedFilter => _selectedFilter;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  BooksProvider() {
    fetchBooks();
  }

  void setFilter(String filter) {
    _selectedFilter = filter;
    notifyListeners();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  List<BookModel> _filteredBooks() {
    return _books.where((b) {
      bool matchesType = true;
      if (_selectedFilter == 'PDF') {
        matchesType = b.sourceType.toLowerCase() == 'pdf' && !b.isGenerated;
      } else if (_selectedFilter == 'TXT') {
        matchesType = b.sourceType.toLowerCase() == 'txt' && !b.isGenerated;
      } else if (_selectedFilter == 'Images') {
        matchesType = b.sourceType.toLowerCase() == 'image';
      } else if (_selectedFilter == 'Generated') {
        matchesType = b.isGenerated;
      }

      final matchesSearch = _searchQuery.isEmpty ||
          b.title.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          b.originalFilename.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          b.subjectName.toLowerCase().contains(_searchQuery.toLowerCase());

      return matchesType && matchesSearch;
    }).toList();
  }

  Future<void> fetchBooks() async {
    try {
      _isLoading = true;
      _errorMessage = null;
      notifyListeners();

      final response = await ApiClient.get(ApiEndpoints.books);
      if (response.isSuccess && response.data is List) {
        _books = (response.data as List)
            .map((item) => BookModel.fromJson(item as Map<String, dynamic>))
            .toList();
        _checkActiveProcessing();
      } else {
        _errorMessage = response.errorMessage ?? 'पुस्तके लोड करताना त्रुटी आली.';
      }
    } catch (e) {
      _errorMessage = 'त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> uploadBook({
    required String filePath,
    required String title,
    required String subjectName,
    Uint8List? fileBytes,
    String? filename,
  }) async {
    try {
      _isLoading = true;
      notifyListeners();

      final response = await ApiClient.uploadFile(
        '${ApiEndpoints.books}/upload',
        filePath: filePath,
        fieldName: 'file',
        fileBytes: fileBytes,
        filename: filename,
        fields: {
          'title': title,
          'subject_name': subjectName,
        },
      );

      if (response.isSuccess && response.data != null) {
        final newBook = BookModel.fromJson(response.data as Map<String, dynamic>);
        _books.insert(0, newBook);
        _startStatusPolling(newBook.id);
        notifyListeners();
        return true;
      } else {
        _errorMessage = response.errorMessage ?? 'अपलोड अयशस्वी.';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'अपलोड त्रुटी: $e';
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> deleteBook(int bookId) async {
    try {
      final response = await ApiClient.delete('${ApiEndpoints.books}/$bookId');
      if (response.isSuccess) {
        _books.removeWhere((b) => b.id == bookId);
        notifyListeners();
        return true;
      } else {
        _errorMessage = response.errorMessage ?? 'हटवणे अयशस्वी.';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'हटवताना त्रुटी: $e';
      notifyListeners();
      return false;
    }
  }

  Future<bool> renameBook(int bookId, String newTitle) async {
    try {
      final response = await ApiClient.put(
        '${ApiEndpoints.books}/$bookId/rename',
        body: {'title': newTitle},
      );
      if (response.isSuccess) {
        final index = _books.indexWhere((b) => b.id == bookId);
        if (index != -1) {
          final old = _books[index];
          _books[index] = BookModel(
            id: old.id,
            title: newTitle,
            originalFilename: old.originalFilename,
            subjectId: old.subjectId,
            subjectName: old.subjectName,
            totalPages: old.totalPages,
            fileSizeBytes: old.fileSizeBytes,
            isScanned: old.isScanned,
            status: old.status,
            statusMessage: old.statusMessage,
            progressPercent: old.progressPercent,
            currentPageProcessing: old.currentPageProcessing,
            totalChunks: old.totalChunks,
            sourceType: old.sourceType,
            isGenerated: old.isGenerated,
            sourceBookId: old.sourceBookId,
            chatSessionId: old.chatSessionId,
            isIndexed: old.isIndexed,
            createdAt: old.createdAt,
          );
          notifyListeners();
        }
        return true;
      }
      return false;
    } catch (e) {
      _errorMessage = 'नाव बदलताना त्रुटी: $e';
      notifyListeners();
      return false;
    }
  }

  void _checkActiveProcessing() {
    final hasProcessing = _books.any((b) => b.status == 'pending' || b.status == 'processing');
    if (hasProcessing && _statusPollingTimer == null) {
      _startStatusPolling();
    }
  }

  void _startStatusPolling([int? specificBookId]) {
    _statusPollingTimer?.cancel();
    _statusPollingTimer = Timer.periodic(const Duration(seconds: 3), (timer) async {
      bool stillProcessing = false;
      for (int i = 0; i < _books.length; i++) {
        final b = _books[i];
        if (b.status == 'pending' || b.status == 'processing') {
          try {
            final res = await ApiClient.get('${ApiEndpoints.books}/${b.id}/status');
            if (res.isSuccess && res.data != null) {
              final data = res.data as Map<String, dynamic>;
              final newStatus = data['status'] ?? b.status;
              final newProgress = (data['progress_percent'] as num?)?.toDouble() ?? b.progressPercent;
              final newMsg = data['status_message'] ?? b.statusMessage;

              _books[i] = BookModel(
                id: b.id,
                title: b.title,
                originalFilename: b.originalFilename,
                subjectId: b.subjectId,
                subjectName: b.subjectName,
                totalPages: data['total_pages'] ?? b.totalPages,
                fileSizeBytes: b.fileSizeBytes,
                isScanned: b.isScanned,
                status: newStatus,
                statusMessage: newMsg,
                progressPercent: newProgress,
                currentPageProcessing: data['current_page'] ?? b.currentPageProcessing,
                totalChunks: b.totalChunks,
                sourceType: b.sourceType,
                isGenerated: b.isGenerated,
                sourceBookId: b.sourceBookId,
                chatSessionId: b.chatSessionId,
                isIndexed: newStatus == 'completed',
                createdAt: b.createdAt,
              );
              notifyListeners();

              if (newStatus == 'pending' || newStatus == 'processing') {
                stillProcessing = true;
              }
            }
          } catch (_) {}
        }
      }
      if (!stillProcessing) {
        timer.cancel();
        _statusPollingTimer = null;
      }
    });
  }

  @override
  void dispose() {
    _statusPollingTimer?.cancel();
    super.dispose();
  }
}
