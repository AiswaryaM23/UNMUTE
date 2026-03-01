import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config.dart';
import 'screens/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Restore saved backend URL (if any)
  final prefs = await SharedPreferences.getInstance();
  final savedUrl = prefs.getString('backend_url');
  if (savedUrl != null && savedUrl.isNotEmpty) {
    AppConfig.baseUrl = savedUrl;
  }

  runApp(const AslApp());
}

class AslApp extends StatelessWidget {
  const AslApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ASL Sign Language',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF1565C0),
          secondary: Color(0xFF42A5F5),
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
