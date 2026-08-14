import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/book.dart';

class BooksProvider extends ChangeNotifier {
  List<BookModel> _books = [];
  String _selectedSubject = 'All';
  String _searchQuery = '';
  bool _isLoading = false;
  String? _errorMessage;
  Timer? _statusPollingTimer;

  List<BookModel> get books => _filteredBooks();
  List<BookModel> get allBooks => _books;
  String get selectedSubject => _selectedSubject;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  BooksProvider() {
    fetchBooks();
  }

  void setSelectedSubject(String subject) {
    _selectedSubject = subject;
    notifyListeners();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  List<BookModel> _filteredBooks() {
    return _books.where((b) {
      final matchesSubject = _selectedSubject == 'All' || b.subjectName == _selectedSubject;
      final matchesSearch = _searchQuery.isEmpty ||
          b.title.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          b.subjectName.toLowerCase().contains(_searchQuery.toLowerCase());
      return matchesSubject && matchesSearch;
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
        _errorMessage = response.errorMessage ?? 'पुस्तके आणण्यात त्रुटी आली.';
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
        ApiEndpoints.books + '/upload',
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

  void _checkActiveProcessing() {
    bool hasActive = _books.any((b) => b.status != 'completed' && b.status != 'failed');
    if (hasActive && (_statusPollingTimer == null || !_statusPollingTimer!.isActive)) {
      _statusPollingTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
        _pollActiveBooks();
      });
    }
  }

  void _startStatusPolling(int bookId) {
    _statusPollingTimer?.cancel();
    _statusPollingTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      final response = await ApiClient.get(ApiEndpoints.bookStatus(bookId));
      if (response.isSuccess && response.data != null) {
        final statusData = response.data;
        int idx = _books.indexWhere((b) => b.id == bookId);
        if (idx != -1) {
          BookModel old = _books[idx];
          _books[idx] = BookModel(
            id: old.id,
            title: old.title,
            originalFilename: old.originalFilename,
            subjectId: old.subjectId,
            subjectName: old.subjectName,
            totalPages: statusData['total_pages'] ?? old.totalPages,
            fileSizeBytes: old.fileSizeBytes,
            isScanned: old.isScanned,
            status: statusData['status'] ?? old.status,
            statusMessage: statusData['status_message'] ?? old.statusMessage,
            progressPercent: (statusData['progress_percent'] as num?)?.toDouble() ?? old.progressPercent,
            currentPageProcessing: statusData['current_page'] ?? old.currentPageProcessing,
            totalChunks: old.totalChunks,
            isIndexed: statusData['is_indexed'] ?? old.isIndexed,
            createdAt: old.createdAt,
          );
          notifyListeners();

          if (statusData['status'] == 'completed' || statusData['status'] == 'failed') {
            timer.cancel();
          }
        }
      }
    });
  }

  Future<void> _pollActiveBooks() async {
    bool anyStillActive = false;
    for (int i = 0; i < _books.length; i++) {
      if (_books[i].status != 'completed' && _books[i].status != 'failed') {
        anyStillActive = true;
        final response = await ApiClient.get(ApiEndpoints.bookStatus(_books[i].id));
        if (response.isSuccess && response.data != null) {
          final s = response.data;
          BookModel old = _books[i];
          _books[i] = BookModel(
            id: old.id,
            title: old.title,
            originalFilename: old.originalFilename,
            subjectId: old.subjectId,
            subjectName: old.subjectName,
            totalPages: s['total_pages'] ?? old.totalPages,
            fileSizeBytes: old.fileSizeBytes,
            isScanned: old.isScanned,
            status: s['status'] ?? old.status,
            statusMessage: s['status_message'] ?? old.statusMessage,
            progressPercent: (s['progress_percent'] as num?)?.toDouble() ?? old.progressPercent,
            currentPageProcessing: s['current_page'] ?? old.currentPageProcessing,
            totalChunks: old.totalChunks,
            isIndexed: s['is_indexed'] ?? old.isIndexed,
            createdAt: old.createdAt,
          );
        }
      }
    }
    notifyListeners();
    if (!anyStillActive) {
      _statusPollingTimer?.cancel();
    }
  }

  Future<bool> deleteBook(int bookId) async {
    final response = await ApiClient.delete('${ApiEndpoints.books}/$bookId');
    if (response.isSuccess) {
      _books.removeWhere((b) => b.id == bookId);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> renameBook(int bookId, String newTitle, String? newSubject) async {
    final response = await ApiClient.patch(
      '${ApiEndpoints.books}/$bookId',
      body: {'title': newTitle, 'subject_name': newSubject},
    );
    if (response.isSuccess && response.data != null) {
      int idx = _books.indexWhere((b) => b.id == bookId);
      if (idx != -1) {
        _books[idx] = BookModel.fromJson(response.data as Map<String, dynamic>);
        notifyListeners();
      }
      return true;
    }
    return false;
  }

  Future<String> getPageContent(int bookId, int page) async {
    try {
      final response = await ApiClient.get(ApiEndpoints.bookPage(bookId, page));
      if (response.isSuccess && response.data != null) {
        return response.data['text_content'] ?? response.data['content'] ?? '';
      }
    } catch (_) {}
    return '';
  }

  @override
  void dispose() {
    _statusPollingTimer?.cancel();
    super.dispose();
  }
}
