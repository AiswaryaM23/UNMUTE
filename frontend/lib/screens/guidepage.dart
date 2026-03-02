import 'package:flutter/material.dart';

class GuidePage extends StatelessWidget {
  const GuidePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('User Guide'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const SizedBox(height: 10),

            const Text(
              "How to Use the App",
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 20),

            Image.asset(
              'guides/image/guide1.png',
              fit: BoxFit.contain,
            ),

            const SizedBox(height: 30),

            Image.asset(
              'guides/image/guide2.png',
              fit: BoxFit.contain,
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
