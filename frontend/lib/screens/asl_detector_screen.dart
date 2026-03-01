import 'dart:async';
import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../services/ws_service.dart';
import '../services/api_service.dart';

/// Screen that opens the device camera, sends frames to the backend for ASL
/// letter prediction, and builds up a sentence using the same stability / timeout
/// logic as sentence_inference.py.
class AslDetectorScreen extends StatefulWidget {
  const AslDetectorScreen({super.key});

  @override
  State<AslDetectorScreen> createState() => _AslDetectorScreenState();
}

class _AslDetectorScreenState extends State<AslDetectorScreen> {
  // ── camera ─────────────────────────────────────────────────────────────────
  CameraController? _camCtrl;
  bool _camReady = false;
  String? _camError;

  // ── WebSocket ──────────────────────────────────────────────────────────────
  late final WsService _ws;
  StreamSubscription<String>? _wsSub;
  bool _wsConnected = false;

  // ── prediction state ───────────────────────────────────────────────────────
  String? _letter;
  String _currentWord = '';
  String _sentence = '';
  bool _handDetected = false;
  bool _correcting = false;

  String? _lastChar;
  int _stableCount = 0;
  static const int _stableThreshold = 3;  // 3 frames × 300ms = ~1 second hold

  DateTime _lastHandTime = DateTime.now();
  DateTime _lastAppendTime = DateTime(2000);
  static const Duration _spaceTimeout = Duration(milliseconds: 1500);
  static const Duration _sentenceTimeout = Duration(seconds: 4);
  static const Duration _letterCooldown = Duration(milliseconds: 900);

  // ── periodic capture ───────────────────────────────────────────────────────
  Timer? _captureTimer;
  bool _capturing = false;

  @override
  void initState() {
    super.initState();
    _ws = WsService('ws/detect');
    _ws.connect();
    _wsConnected = true;
    _wsSub = _ws.stream.listen(_onWsMessage, onError: (_) {
      if (mounted) setState(() => _wsConnected = false);
    });
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        if (mounted) setState(() => _camError = 'No cameras found on this device.');
        return;
      }
      final cam = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );
      _camCtrl = CameraController(cam, ResolutionPreset.low, enableAudio: false);
      await _camCtrl!.initialize();
      if (!mounted) return;
      setState(() => _camReady = true);
      _startCapture();
    } catch (e) {
      if (mounted) setState(() => _camError = 'Camera error: $e');
    }
  }

  void _startCapture() {
    _captureTimer = Timer.periodic(const Duration(milliseconds: 300), (_) async {
      if (_capturing || _camCtrl == null || !_camCtrl!.value.isInitialized) return;
      _capturing = true;
      try {
        final xFile = await _camCtrl!.takePicture();
        final bytes = await xFile.readAsBytes();
        _ws.send(base64Encode(bytes));
      } catch (_) {
        // ignore individual frame errors
      } finally {
        _capturing = false;
      }
    });
  }

  void _onWsMessage(String raw) {
    final data = WsService.parseJson(raw);
    final detected = data['hand_detected'] == true;
    final letter = data['letter'] as String?;
    final now = DateTime.now();
    if (!mounted) return;
    setState(() {
      _handDetected = detected;
      _letter = letter;
      if (detected && letter != null) {
        _lastHandTime = now;
        if (letter == _lastChar) { _stableCount++; } else { _stableCount = 0; }
        if (_stableCount >= _stableThreshold) {
          final lower = letter.toLowerCase();
          final cooldownPassed = now.difference(_lastAppendTime) > _letterCooldown;
          if (cooldownPassed) {
            _currentWord += lower;
            _lastAppendTime = now;
          }
          _stableCount = 0;
          _lastChar = null;  // reset so same letter can be signed again
        } else {
          _lastChar = letter;
        }
      } else {
        final elapsed = now.difference(_lastHandTime);
        if (elapsed > _spaceTimeout && _currentWord.isNotEmpty) {
          _sentence += '$_currentWord '; _currentWord = ''; _lastHandTime = now;
        }
        if (elapsed > _sentenceTimeout && _sentence.isNotEmpty) {
          _sentence = _addPunctuation(_sentence); _lastHandTime = now;
        }
      }
    });
  }

  String _addPunctuation(String s) {
    s = s.trim();
    if (s.isEmpty) return '$s ';
    if (s.endsWith('.') || s.endsWith('?') || s.endsWith('!')) return '$s ';
    const q = ['what','why','how','when','where','who','is','are','do','does','can'];
    if (q.contains(s.split(' ').first.toLowerCase())) return '$s? ';
    return '$s. ';
  }

  void _backspace() => setState(() {
    if (_currentWord.isNotEmpty) {
      _currentWord = _currentWord.substring(0, _currentWord.length - 1);
    } else if (_sentence.isNotEmpty) {
      final t = _sentence.trimRight();
      _sentence = t.isEmpty ? '' : '${t.substring(0, t.length - 1)} ';
    }
  });

  void _addSpace() => setState(() {
    if (_currentWord.isNotEmpty) { _sentence += '$_currentWord '; _currentWord = ''; }
  });

  void _clearAll() => setState(() {
    _sentence = ''; _currentWord = ''; _letter = null; _stableCount = 0;
  });

  Future<void> _autoCorrect() async {
    final full = (_sentence + _currentWord).trim();
    if (full.isEmpty) return;
    setState(() => _correcting = true);
    try {
      final corrected = await ApiService.correctSentence(full);
      setState(() {
        _sentence = '$corrected ';
        _currentWord = '';
      });
    } catch (_) {
      // silently ignore – keep original text
    } finally {
      if (mounted) setState(() => _correcting = false);
    }
  }

  @override
  void dispose() {
    _captureTimer?.cancel();
    _camCtrl?.dispose();
    _wsSub?.cancel();
    _ws.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('ASL Detector', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [Padding(
          padding: const EdgeInsets.only(right: 12),
          child: Icon(
            _wsConnected ? Icons.wifi : Icons.wifi_off,
            color: _wsConnected ? Colors.greenAccent : Colors.redAccent,
            size: 20,
          ),
        )],
      ),
      body: Column(
        children: [
          // ── Camera preview ───────────────────────────────────────────────
          Expanded(
            flex: 5,
            child: _buildCamera(),
          ),

          // ── Detected letter badge ────────────────────────────────────────
          _LetterBadge(letter: _letter, handDetected: _handDetected),

          // ── Sentence output ──────────────────────────────────────────────
          Expanded(
            flex: 3,
            child: _SentencePanel(
              sentence: _sentence,
              currentWord: _currentWord,
              correcting: _correcting,
              onBackspace: _backspace,
              onSpace: _addSpace,
              onClear: _clearAll,
              onAutoCorrect: _autoCorrect,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCamera() {
    if (_camError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(_camError!,
              style: const TextStyle(color: Colors.redAccent),
              textAlign: TextAlign.center),
        ),
      );
    }
    if (!_camReady || _camCtrl == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return ClipRRect(
      child: CameraPreview(_camCtrl!),
    );
  }
}

// ── Sub-widgets ──────────────────────────────────────────────────────────────

class _LetterBadge extends StatelessWidget {
  final String? letter;
  final bool handDetected;

  const _LetterBadge({this.letter, required this.handDetected});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF161B22),
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 20),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: handDetected ? const Color(0xFF1A237E) : Colors.white12,
              borderRadius: BorderRadius.circular(12),
            ),
            alignment: Alignment.center,
            child: Text(
              letter ?? '?',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: handDetected ? Colors.lightBlueAccent : Colors.white38,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Text(
            handDetected
                ? 'Hand detected – detecting letter'
                : 'No hand detected',
            style: TextStyle(
              color: handDetected ? Colors.white70 : Colors.white38,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

class _SentencePanel extends StatelessWidget {
  final String sentence;
  final String currentWord;
  final bool correcting;
  final VoidCallback onBackspace;
  final VoidCallback onSpace;
  final VoidCallback onClear;
  final VoidCallback onAutoCorrect;

  const _SentencePanel({
    required this.sentence,
    required this.currentWord,
    required this.correcting,
    required this.onBackspace,
    required this.onSpace,
    required this.onClear,
    required this.onAutoCorrect,
  });

  @override
  Widget build(BuildContext context) {
    final display = sentence + currentWord;
    return Container(
      color: const Color(0xFF0D1117),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Sentence Output',
              style: TextStyle(
                  color: Colors.white54,
                  fontSize: 12,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                display.isEmpty ? 'Start signing...' : display,
                style: TextStyle(
                  color: display.isEmpty ? Colors.white24 : Colors.white,
                  fontSize: 18,
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _ActionBtn(label: '⌫', onTap: onBackspace),
              const SizedBox(width: 8),
              _ActionBtn(label: 'SPACE', onTap: onSpace),
              const SizedBox(width: 8),
              _ActionBtn(label: 'CLEAR', color: Colors.redAccent, onTap: onClear),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: correcting ? null : onAutoCorrect,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1B5E20),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              icon: correcting
                  ? const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.auto_fix_high, size: 18),
              label: Text(correcting ? 'Correcting...' : 'Auto-Correct Sentence'),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final Color? color;

  const _ActionBtn({required this.label, required this.onTap, this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: color ?? const Color(0xFF1E3A5F),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 12),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        child: Text(label, style: const TextStyle(fontSize: 13)),
      ),
    );
  }
}
