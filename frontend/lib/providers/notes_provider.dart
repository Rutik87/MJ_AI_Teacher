import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/handwritten_note.dart';

class NotesProvider extends ChangeNotifier {
  final Map<int, HandwrittenNoteModel> _bookNotes = {};
  bool _isGenerating = false;
  String _currentStepMessage = '';
  double _currentProgress = 0.0;
  String? _errorMessage;
  Timer? _pollingTimer;

  bool get isGenerating => _isGenerating;
  String get currentStepMessage => _currentStepMessage;
  double get currentProgress => _currentProgress;
  String? get errorMessage => _errorMessage;

  HandwrittenNoteModel? getNoteForBook(int bookId) => _bookNotes[bookId];

  Future<HandwrittenNoteModel?> fetchNotesStatus(int bookId) async {
    try {
      final response = await ApiClient.get(ApiEndpoints.notesStatus(bookId));
      if (response.isSuccess && response.data != null) {
        final note = HandwrittenNoteModel.fromJson(response.data as Map<String, dynamic>);
        _bookNotes[bookId] = note;
        notifyListeners();
        return note;
      }
    } catch (e) {
      debugPrint('[NotesProvider] Fetch status error: $e');
    }
    return null;
  }

  Future<bool> generateNotes(int bookId) async {
    _isGenerating = true;
    _errorMessage = null;
    _currentProgress = 0.1;
    _currentStepMessage = 'Content वाचत आहे...';
    notifyListeners();

    // Start simulated progress indicator while server analyzes complete document
    _startProgressSimulation();

    try {
      final response = await ApiClient.post(
        ApiEndpoints.notesGenerate(bookId),
        body: {},
      );

      _stopProgressSimulation();

      if (response.isSuccess && response.data != null) {
        _currentProgress = 1.0;
        _currentStepMessage = 'Notes तयार आहेत 🎉';
        
        final updatedNote = await fetchNotesStatus(bookId);
        _isGenerating = false;
        notifyListeners();
        return updatedNote != null && updatedNote.hasNotes;
      } else {
        _errorMessage = response.errorMessage ?? 'Notes तयार करताना त्रुटी आली.';
        _isGenerating = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _stopProgressSimulation();
      _errorMessage = 'संपर्क त्रुटी: $e';
      _isGenerating = false;
      notifyListeners();
      return false;
    }
  }

  void _startProgressSimulation() {
    _pollingTimer?.cancel();
    final steps = [
      {'progress': 0.15, 'msg': 'Content वाचत आहे...'},
      {'progress': 0.35, 'msg': 'Chapter समजून घेत आहे...'},
      {'progress': 0.60, 'msg': 'Important points तयार करत आहे...'},
      {'progress': 0.80, 'msg': 'Diagrams व Tables तयार करत आहे...'},
      {'progress': 0.92, 'msg': 'Handwritten Notes तयार करत आहे...'},
    ];
    int stepIdx = 0;

    _pollingTimer = Timer.periodic(const Duration(milliseconds: 2500), (timer) {
      if (stepIdx < steps.length && _isGenerating) {
        _currentProgress = steps[stepIdx]['progress'] as double;
        _currentStepMessage = steps[stepIdx]['msg'] as String;
        stepIdx++;
        notifyListeners();
      }
    });
  }

  void _stopProgressSimulation() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }

  Future<bool> deleteNotes(int bookId) async {
    try {
      final response = await ApiClient.delete(ApiEndpoints.notesDelete(bookId));
      if (response.isSuccess) {
        _bookNotes.remove(bookId);
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('[NotesProvider] Delete error: $e');
    }
    return false;
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }
}
