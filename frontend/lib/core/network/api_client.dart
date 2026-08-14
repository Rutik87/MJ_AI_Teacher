import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:frontend/core/constants/api_endpoints.dart';

class ApiResponse<T> {
  final bool isSuccess;
  final T? data;
  final String? errorMessage;
  final int statusCode;

  ApiResponse({
    required this.isSuccess,
    this.data,
    this.errorMessage,
    required this.statusCode,
  });
}

class ApiClient {
  static final http.Client _client = http.Client();

  static Future<ApiResponse<dynamic>> get(String url) async {
    try {
      final response = await _client.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        return ApiResponse(isSuccess: true, data: decoded, statusCode: response.statusCode);
      } else {
        return ApiResponse(
          isSuccess: false,
          errorMessage: _extractError(response),
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'सर्व्हरशी संपर्क होऊ शकला नाही: $e',
        statusCode: 500,
      );
    }
  }

  static Future<ApiResponse<dynamic>> post(String url, {Map<String, dynamic>? body}) async {
    try {
      final response = await _client.post(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
        body: body != null ? jsonEncode(body) : null,
      ).timeout(const Duration(seconds: 40));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        return ApiResponse(isSuccess: true, data: decoded, statusCode: response.statusCode);
      } else {
        return ApiResponse(
          isSuccess: false,
          errorMessage: _extractError(response),
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'सर्व्हरशी संपर्क होऊ शकला नाही: $e',
        statusCode: 500,
      );
    }
  }

  static Future<ApiResponse<dynamic>> patch(String url, {Map<String, dynamic>? body}) async {
    try {
      final response = await _client.patch(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
        body: body != null ? jsonEncode(body) : null,
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        return ApiResponse(isSuccess: true, data: decoded, statusCode: response.statusCode);
      } else {
        return ApiResponse(
          isSuccess: false,
          errorMessage: _extractError(response),
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'अपडेट करण्यात त्रुटी: $e',
        statusCode: 500,
      );
    }
  }

  static Future<ApiResponse<dynamic>> delete(String url) async {
    try {
      final response = await _client.delete(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        return ApiResponse(isSuccess: true, data: decoded, statusCode: response.statusCode);
      } else {
        return ApiResponse(
          isSuccess: false,
          errorMessage: _extractError(response),
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'हटवण्यात त्रुटी: $e',
        statusCode: 500,
      );
    }
  }

  static Future<ApiResponse<dynamic>> uploadFile(
    String url, {
    required String filePath,
    required String fieldName,
    Map<String, String>? fields,
    Uint8List? fileBytes,
    String? filename,
  }) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse(url));
      
      if (fields != null) {
        request.fields.addAll(fields);
      }

      if (kIsWeb && fileBytes != null) {
        request.files.add(http.MultipartFile.fromBytes(
          fieldName,
          fileBytes,
          filename: filename ?? 'document.pdf',
        ));
      } else if (filePath.isNotEmpty) {
        request.files.add(await http.MultipartFile.fromPath(
          fieldName,
          filePath,
          filename: filename,
        ));
      } else if (fileBytes != null) {
        request.files.add(http.MultipartFile.fromBytes(
          fieldName,
          fileBytes,
          filename: filename ?? 'document.pdf',
        ));
      }

      final streamedResponse = await request.send().timeout(const Duration(seconds: 120));
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        return ApiResponse(isSuccess: true, data: decoded, statusCode: response.statusCode);
      } else {
        return ApiResponse(
          isSuccess: false,
          errorMessage: _extractError(response),
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'फाईल अपलोड करताना त्रुटी: $e',
        statusCode: 500,
      );
    }
  }

  static String _extractError(http.Response response) {
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded.containsKey('detail')) {
        return decoded['detail'].toString();
      }
    } catch (_) {}
    return 'सर्व्हर त्रुटी (Code ${response.statusCode})';
  }
}
