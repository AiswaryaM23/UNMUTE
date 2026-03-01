import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

/// HTTP client — used only for health check and text-to-sign.
/// Real-time features (ASL detect, chatbot) use WebSocket via WsService.
class ApiService {
  static String get _base => AppConfig.baseUrl;
  static Map<String, String> get _headers => {'Content-Type': 'application/json'};

  // ── health ─────────────────────────────────────────────────────────────────
  static Future<bool> checkHealth() async {
    try {
      final res = await http
          .get(Uri.parse('$_base/health'))
          .timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ── auto-correct sentence via Gemini ────────────────────────────────────
  static Future<String> correctSentence(String text) async {
    final res = await http
        .post(
          Uri.parse('$_base/correct'),
          headers: _headers,
          body: jsonEncode({'text': text}),
        )
        .timeout(const Duration(seconds: 10));
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      return data['corrected'] as String? ?? text;
    }
    throw Exception('correct failed: ${res.statusCode}');
  }

  // ── text-to-sign (HTTP POST – one-shot, no stream needed) ─────────────────
  static Future<List<Map<String, dynamic>>> textToSign(String text) async {
    final res = await http
        .post(
          Uri.parse('$_base/text-to-sign'),
          headers: _headers,
          body: jsonEncode({'text': text}),
        )
        .timeout(const Duration(seconds: 15));

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      return List<Map<String, dynamic>>.from(data['signs'] as List);
    }
    throw Exception('text-to-sign failed: ${res.statusCode}');
  }
}
