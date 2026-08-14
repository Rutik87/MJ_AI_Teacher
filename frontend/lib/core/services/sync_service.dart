import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/constants/api_endpoints.dart';
import 'package:frontend/core/network/api_client.dart';

class SyncAction {
  final String id;
  final String actionType; // 'bookmark', 'reading_progress', 'test_submission', 'revision_item'
  final Map<String, dynamic> payload;
  final DateTime createdAt;

  SyncAction({
    required this.id,
    required this.actionType,
    required this.payload,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'action_type': actionType,
        'payload': payload,
        'created_at': createdAt.toIso8601String(),
      };

  factory SyncAction.fromJson(Map<String, dynamic> json) => SyncAction(
        id: json['id'] ?? '',
        actionType: json['action_type'] ?? '',
        payload: json['payload'] as Map<String, dynamic>? ?? {},
        createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
      );
}

class SyncService extends ChangeNotifier {
  static const String _prefKeyQueue = 'sync_pending_queue';
  final List<SyncAction> _pendingQueue = [];
  bool _isOnline = true;
  bool _isSyncing = false;
  DateTime? _lastSyncedAt;
  Timer? _periodicCheckTimer;

  bool get isOnline => _isOnline;
  bool get isSyncing => _isSyncing;
  DateTime? get lastSyncedAt => _lastSyncedAt;
  int get pendingCount => _pendingQueue.length;

  SyncService() {
    _loadQueueFromStorage();
    _startPeriodicHealthCheck();
  }

  Future<void> _loadQueueFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final rawList = prefs.getStringList(_prefKeyQueue) ?? [];
      _pendingQueue.clear();
      for (final str in rawList) {
        final Map<String, dynamic> decoded = jsonDecode(str);
        _pendingQueue.add(SyncAction.fromJson(decoded));
      }
      notifyListeners();
    } catch (e) {
      debugPrint('Load sync queue error: $e');
    }
  }

  Future<void> _saveQueueToStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final rawList = _pendingQueue.map((a) => jsonEncode(a.toJson())).toList();
      await prefs.setStringList(_prefKeyQueue, rawList);
    } catch (e) {
      debugPrint('Save sync queue error: $e');
    }
  }

  void _startPeriodicHealthCheck() {
    _periodicCheckTimer?.cancel();
    _periodicCheckTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      checkConnectivityAndSync();
    });
    checkConnectivityAndSync();
  }

  Future<void> checkConnectivityAndSync() async {
    try {
      final response = await ApiClient.get(ApiEndpoints.health);
      final wasOffline = !_isOnline;
      _isOnline = response.isSuccess;
      notifyListeners();

      if (_isOnline && (wasOffline || _pendingQueue.isNotEmpty)) {
        await syncPendingActions();
      }
    } catch (_) {
      _isOnline = false;
      notifyListeners();
    }
  }

  Future<void> queueAction({
    required String actionType,
    required Map<String, dynamic> payload,
  }) async {
    final action = SyncAction(
      id: '${DateTime.now().millisecondsSinceEpoch}_${actionType}_${_pendingQueue.length}',
      actionType: actionType,
      payload: payload,
      createdAt: DateTime.now(),
    );

    _pendingQueue.add(action);
    await _saveQueueToStorage();
    notifyListeners();

    if (_isOnline) {
      syncPendingActions();
    }
  }

  Future<void> syncPendingActions() async {
    if (_isSyncing || _pendingQueue.isEmpty || !_isOnline) return;

    _isSyncing = true;
    notifyListeners();

    try {
      final syncPayload = {
        'actions': _pendingQueue.map((a) => a.toJson()).toList(),
      };

      final response = await ApiClient.post(
        '${ApiEndpoints.baseUrl}/sync/batch',
        body: syncPayload,
      );

      if (response.isSuccess) {
        _pendingQueue.clear();
        await _saveQueueToStorage();
        _lastSyncedAt = DateTime.now();
      }
    } catch (e) {
      debugPrint('Sync batch failed: $e');
    } finally {
      _isSyncing = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _periodicCheckTimer?.cancel();
    super.dispose();
  }
}
