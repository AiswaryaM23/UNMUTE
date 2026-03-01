import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../services/ws_service.dart';

class _Message {
  final String text;
  final bool isUser;
  _Message(this.text, {required this.isUser});
}

/// Gemini AI chatbot screen.
class ChatbotScreen extends StatefulWidget {
  const ChatbotScreen({super.key});

  @override
  State<ChatbotScreen> createState() => _ChatbotScreenState();
}

class _ChatbotScreenState extends State<ChatbotScreen> {
  final TextEditingController _ctrl = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final List<_Message> _messages = [];
  bool _loading = false;

  late final WsService _ws;
  StreamSubscription<String>? _wsSub;
  bool _wsConnected = false;

  @override
  void initState() {
    super.initState();
    _ws = WsService('ws/chat');
    _ws.connect();
    _wsConnected = true;
    _wsSub = _ws.stream.listen(_onWsMessage, onError: (_) {
      if (mounted) setState(() => _wsConnected = false);
    });
  }

  void _onWsMessage(String raw) {
    final data = WsService.parseJson(raw);
    final response = data['response'] as String?;
    final error = data['error'] as String?;
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (error != null) {
        _messages.add(_Message('Error: $error', isUser: false));
      } else if (response != null && response != 'Chat cleared.') {
        _messages.add(_Message(response, isUser: false));
      }
    });
    _scrollToBottom();
  }

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _loading) return;
    _ctrl.clear();
    setState(() {
      _messages.add(_Message(text, isUser: true));
      _loading = true;
    });
    _scrollToBottom();
    _ws.send(text);
  }

  void _clearChat() {
    _ws.send('CLEAR');
    setState(() => _messages.clear());
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _ws.dispose();
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('AI Chatbot', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.white70),
            tooltip: 'Clear chat',
            onPressed: _clearChat,
          ),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Icon(
              _wsConnected ? Icons.wifi : Icons.wifi_off,
              color: _wsConnected ? Colors.greenAccent : Colors.redAccent,
              size: 20,
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Message list ────────────────────────────────────────────────
          Expanded(
            child: _messages.isEmpty
                ? const _EmptyChat()
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.symmetric(
                        vertical: 12, horizontal: 10),
                    itemCount: _messages.length,
                    itemBuilder: (ctx, i) => _ChatBubble(msg: _messages[i]),
                  ),
          ),

          // ── Typing indicator ────────────────────────────────────────────
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 6),
              child: Text('Gemini is thinking…',
                  style: TextStyle(color: Colors.white38, fontSize: 13)),
            ),

          // ── Input bar ───────────────────────────────────────────────────
          _InputBar(ctrl: _ctrl, onSend: _send, loading: _loading),
        ],
      ),
    );
  }
}

// ── Sub-widgets ───────────────────────────────────────────────────────────────

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.chat_bubble_outline, color: Colors.white24, size: 64),
          SizedBox(height: 16),
          Text('Start a conversation with Gemini AI',
              style: TextStyle(color: Colors.white38, fontSize: 15)),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final _Message msg;
  const _ChatBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isUser = msg.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.78),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF1565C0) : const Color(0xFF1E1E2E),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(14),
            topRight: const Radius.circular(14),
            bottomLeft: Radius.circular(isUser ? 14 : 2),
            bottomRight: Radius.circular(isUser ? 2 : 14),
          ),
        ),
        child: isUser
            ? Text(msg.text,
                style:
                    const TextStyle(color: Colors.white, fontSize: 15))
            : MarkdownBody(
                data: msg.text,
                styleSheet: MarkdownStyleSheet(
                  p: const TextStyle(color: Colors.white70, fontSize: 15),
                  code: const TextStyle(
                      color: Colors.greenAccent,
                      backgroundColor: Colors.transparent,
                      fontFamily: 'monospace'),
                ),
              ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController ctrl;
  final VoidCallback onSend;
  final bool loading;

  const _InputBar(
      {required this.ctrl, required this.onSend, required this.loading});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF161B22),
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: ctrl,
              style: const TextStyle(color: Colors.white),
              maxLines: null,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
              decoration: InputDecoration(
                hintText: 'Ask something…',
                hintStyle: const TextStyle(color: Colors.white38),
                filled: true,
                fillColor: const Color(0xFF0D1117),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                    horizontal: 18, vertical: 12),
              ),
            ),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            backgroundColor:
                loading ? Colors.white12 : const Color(0xFF6A1B9A),
            child: IconButton(
              icon: Icon(loading ? Icons.hourglass_empty : Icons.send,
                  color: Colors.white, size: 20),
              onPressed: loading ? null : onSend,
            ),
          ),
        ],
      ),
    );
  }
}
