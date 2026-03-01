import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';
import '../config.dart';

/// Manages a single persistent WebSocket connection to one backend endpoint.
///
/// Usage:
///   final ws = WsService('ws/detect');
///   ws.connect();
///   ws.send('base64data...');
///   ws.stream.listen((msg) { ... });
///   ws.dispose();
class WsService {
  final String _path;

  WebSocketChannel? _channel;
  final _controller = StreamController<String>.broadcast();
  bool _disposed = false;

  WsService(this._path);

  /// ws:// URL derived from the HTTP base URL in AppConfig.
  String get _wsUrl {
    final base = AppConfig.baseUrl
        .replaceFirst('https://', 'wss://')
        .replaceFirst('http://', 'ws://');
    return '$base/$_path';
  }

  /// Broadcast stream of raw text messages from the server.
  Stream<String> get stream => _controller.stream;

  bool get isConnected => _channel != null;

  /// Open the WebSocket connection.
  void connect() {
    if (_disposed) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(_wsUrl));
      _channel!.stream.listen(
        (data) {
          if (!_controller.isClosed) _controller.add(data.toString());
        },
        onError: (e) {
          if (!_controller.isClosed) _controller.addError(e);
          _channel = null;
        },
        onDone: () {
          _channel = null;
        },
      );
    } catch (e) {
      _controller.addError(e);
    }
  }

  /// Send a text message to the server.
  void send(String data) {
    if (_channel == null) connect();
    _channel?.sink.add(data);
  }

  /// Parse the next JSON reply into a Map.
  static Map<String, dynamic> parseJson(String raw) {
    return jsonDecode(raw) as Map<String, dynamic>;
  }

  void dispose() {
    _disposed = true;
    _channel?.sink.close();
    _controller.close();
  }
}
