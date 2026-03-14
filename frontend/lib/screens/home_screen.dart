import 'package:flutter/material.dart';
import 'asl_detector_screen.dart';
import 'text_to_sign_screen.dart';
import 'chatbot_screen.dart';
import 'settings_screen.dart';
import 'guidepage.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text(
          'ASL DETECTOR',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white70),
            tooltip: 'Settings',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 12),
            const Text(
              'Choose a feature',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 24),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                children: [
                  _FeatureCard(
                    icon: Icons.sign_language,
                    label: 'Sign Language Detection',
                    subtitle: 'Real-time letters & words detection',
                    gradient: const [Color(0xFF1565C0), Color(0xFF42A5F5)],
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const AslDetectorScreen()),
                    ),
                  ),
                  _FeatureCard(
                    icon: Icons.translate,
                    label: 'Text → Sign',
                    subtitle: 'Convert text to sign images',
                    gradient: const [Color(0xFF2E7D32), Color(0xFF66BB6A)],
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const TextToSignScreen()),
                    ),
                  ),
                  _FeatureCard(
                    icon: Icons.chat_bubble_outline,
                    label: 'AI Chatbot',
                    subtitle: 'Chat with Gemini',
                    gradient: const [Color(0xFF6A1B9A), Color(0xFFAB47BC)],
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const ChatbotScreen()),
                    ),
                  ),
                  _FeatureCard(
                    icon: Icons.menu_book,
                    label: 'Guide',
                    subtitle: 'Learn basics',
                    gradient: const [Color(0xFFEF6C00), Color(0xFFFFA726)],
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const GuidePage()),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final List<Color> gradient;
  final VoidCallback onTap;

  const _FeatureCard({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.gradient,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradient,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: gradient.last.withOpacity(0.4),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: Colors.white, size: 36),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(subtitle,
                      style: const TextStyle(
                          color: Colors.white70, fontSize: 11)),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }
}