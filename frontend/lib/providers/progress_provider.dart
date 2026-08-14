import 'package:flutter/foundation.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';
import 'package:frontend/models/progress_model.dart';

class ProgressProvider extends ChangeNotifier {
  ProgressModel? _progress;
  bool _isLoading = false;
  String? _errorMessage;

  ProgressModel? get progress => _progress;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  ProgressProvider() {
    fetchProgress();
  }

  Future<void> fetchProgress() async {
    try {
      _isLoading = true;
      _errorMessage = null;
      notifyListeners();

      final response = await ApiClient.get(ApiEndpoints.progressSummary);
      if (response.isSuccess && response.data != null) {
        _progress = ProgressModel.fromJson(response.data as Map<String, dynamic>);
      } else {
        _errorMessage = response.errorMessage ?? 'प्रगती तपशील आणण्यात त्रुटी.';
      }
    } catch (e) {
      _errorMessage = 'त्रुटी: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
