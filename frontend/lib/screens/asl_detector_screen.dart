import 'dart:async';
import 'dart:convert';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import '../services/ws_service.dart';
import '../services/api_service.dart';

class AslDetectorScreen extends StatefulWidget {
  const AslDetectorScreen({super.key});

  @override
  State<AslDetectorScreen> createState() => _AslDetectorScreenState();
}

class _AslDetectorScreenState extends State<AslDetectorScreen> {
  CameraController? _camCtrl;
  bool _camReady = false;
  String? _camError;

  late final WsService _ws;
  StreamSubscription<String>? _wsSub;

  String? _letter;
  String _currentWord = '';
  String _sentence = '';
  bool _handDetected = false;
  bool _correcting = false;

  String? _lastChar;
  int _stableCount = 0;
  static const int _stableThreshold = 3;

  DateTime _lastHandTime = DateTime.now();
  DateTime _lastAppendTime = DateTime(2000);
  static const Duration _spaceTimeout = Duration(milliseconds: 1500);
  static const Duration _sentenceTimeout = Duration(seconds: 4);
  static const Duration _letterCooldown = Duration(milliseconds: 900);

  Timer? _captureTimer;
  bool _capturing = false;

  @override
  void initState() {
    super.initState();
    _ws = WsService('ws/detect');
    _ws.connect();
    _wsSub = _ws.stream.listen(_onWsMessage);
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      final cam = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _camCtrl =
          CameraController(cam, ResolutionPreset.low, enableAudio: false);
      await _camCtrl!.initialize();

      if (!mounted) return;
      setState(() => _camReady = true);
      _startCapture();
    } catch (e) {
      if (mounted) {
        setState(() => _camError = 'Camera error: $e');
      }
    }
  }

  void _startCapture() {
    _captureTimer =
        Timer.periodic(const Duration(milliseconds: 300), (_) async {
      if (_capturing ||
          _camCtrl == null ||
          !_camCtrl!.value.isInitialized) return;

      _capturing = true;
      try {
        final xFile = await _camCtrl!.takePicture();
        final bytes = await xFile.readAsBytes();
        _ws.send(base64Encode(bytes));
      } catch (_) {} finally {
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

        if (letter == _lastChar) {
          _stableCount++;
        } else {
          _stableCount = 0;
        }

        if (_stableCount >= _stableThreshold) {
          final cooldownPassed =
              now.difference(_lastAppendTime) > _letterCooldown;

          if (cooldownPassed) {
            _currentWord += letter.toLowerCase();
            _lastAppendTime = now;
          }

          _stableCount = 0;
          _lastChar = null;
        } else {
          _lastChar = letter;
        }
      } else {
        final elapsed = now.difference(_lastHandTime);

        if (elapsed > _spaceTimeout && _currentWord.isNotEmpty) {
          _sentence += '$_currentWord ';
          _currentWord = '';
          _lastHandTime = now;
        }

        if (elapsed > _sentenceTimeout && _sentence.isNotEmpty) {
          _sentence = _addPunctuation(_sentence);
          _lastHandTime = now;
        }
      }
    });
  }

  String _addPunctuation(String s) {
    s = s.trim();
    if (s.isEmpty) return '$s ';
    if (s.endsWith('.') || s.endsWith('?') || s.endsWith('!')) return '$s ';
    return '$s. ';
  }

  void _backspace() => setState(() {
        if (_currentWord.isNotEmpty) {
          _currentWord =
              _currentWord.substring(0, _currentWord.length - 1);
        } else if (_sentence.isNotEmpty) {
          final t = _sentence.trimRight();
          _sentence =
              t.isEmpty ? '' : '${t.substring(0, t.length - 1)} ';
        }
      });

  void _addSpace() => setState(() {
        if (_currentWord.isNotEmpty) {
          _sentence += '$_currentWord ';
          _currentWord = '';
        }
      });

  void _clearAll() => setState(() {
        _sentence = '';
        _currentWord = '';
        _letter = null;
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
    } finally {
      if (mounted) setState(() => _correcting = false);
    }
  }

  void _sendToChatbot() {
    final fullSentence = (_sentence + _currentWord).trim();
    if (fullSentence.isEmpty) return;
    Navigator.pop(context, fullSentence);
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
        title: const Text('ASL Detector',
            style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Column(
        children: [
          Expanded(flex: 5, child: _buildCamera()),
          _LetterBadge(letter: _letter, handDetected: _handDetected),
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
              onSendToChatbot: _sendToChatbot,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCamera() {
    if (_camError != null) {
      return Center(
          child: Text(_camError!,
              style: const TextStyle(color: Colors.redAccent)));
    }
    if (!_camReady || _camCtrl == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return CameraPreview(_camCtrl!);
  }
}

class _LetterBadge extends StatelessWidget {
  final String? letter;
  final bool handDetected;

  const _LetterBadge({this.letter, required this.handDetected});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 80,
      alignment: Alignment.center,
      child: handDetected
          ? Text(
              letter ?? '',
              style: const TextStyle(
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                  color: Colors.greenAccent),
            )
          : const Text(
              'No Hand Detected',
              style: TextStyle(color: Colors.redAccent),
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
  final VoidCallback onSendToChatbot;

  const _SentencePanel({
    required this.sentence,
    required this.currentWord,
    required this.correcting,
    required this.onBackspace,
    required this.onSpace,
    required this.onClear,
    required this.onAutoCorrect,
    required this.onSendToChatbot,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      color: const Color(0xFF161B22),
      child: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              child: Text(
                sentence + currentWord,
                style: const TextStyle(color: Colors.white, fontSize: 18),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              _ActionBtn(label: "⌫", onTap: onBackspace),
              _ActionBtn(label: "Space", onTap: onSpace),
              _ActionBtn(label: "Clear", onTap: onClear),
              _ActionBtn(
                  label: correcting ? "Correcting..." : "Auto Correct",
                  onTap: onAutoCorrect),
              _ActionBtn(label: "To Chatbot", onTap: onSendToChatbot),
            ],
          )
        ],
      ),
    );
  }
}

class _ActionBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _ActionBtn({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onTap,
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color.fromARGB(255, 12, 223, 57),
      ),
      child: Text(label),
    );
  }
}