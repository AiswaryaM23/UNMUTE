import 'package:flutter/material.dart';
import 'dart:math' as math;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Unmute',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.purple,
      ),
      home: const UnmuteLandingPage(),
    );
  }
}

class UnmuteLandingPage extends StatefulWidget {
  const UnmuteLandingPage({super.key});

  @override
  State<UnmuteLandingPage> createState() => _UnmuteLandingPageState();
}

class _UnmuteLandingPageState extends State<UnmuteLandingPage>
    with TickerProviderStateMixin {
  late AnimationController _glowController;
  late AnimationController _gradientController;
  late Animation<double> _glowAnimation;
  final List<Particle> _particles = [];

  @override
  void initState() {
    super.initState();

    // Glow animation controller
    _glowController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    )..repeat(reverse: true);

    _glowAnimation = Tween<double>(begin: 20.0, end: 40.0).animate(
      CurvedAnimation(parent: _glowController, curve: Curves.easeInOut),
    );

    // Gradient shift animation controller
    _gradientController = AnimationController(
      duration: const Duration(seconds: 15),
      vsync: this,
    )..repeat();

    // Create particles periodically
    Future.doWhile(() async {
      await Future.delayed(const Duration(milliseconds: 300));
      if (mounted) {
        setState(() {
          _particles.add(Particle());
        });
        // Remove old particles
        _particles.removeWhere((p) => p.age > 10);
      }
      return mounted;
    });
  }

  @override
  void dispose() {
    _glowController.dispose();
    _gradientController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Animated gradient background
          AnimatedBuilder(
            animation: _gradientController,
            builder: (context, child) {
              return CustomPaint(
                painter: GradientBackgroundPainter(
                  animation: _gradientController.value,
                ),
                size: Size.infinite,
              );
            },
          ),

          // Grid pattern overlay
          CustomPaint(
            painter: GridPainter(),
            size: Size.infinite,
          ),

          // Particles
          ...(_particles.map((particle) => ParticleWidget(particle: particle))),

          // Main content
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Animated gradient text with glow
                AnimatedBuilder(
                  animation: _glowAnimation,
                  builder: (context, child) {
                    return ShaderMask(
                      shaderCallback: (bounds) {
                        return const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            Colors.white,
                            Color(0xFFa78bfa),
                            Color(0xFFec4899),
                          ],
                          stops: [0.0, 0.5, 1.0],
                        ).createShader(bounds);
                      },
                      child: Container(
                        decoration: BoxDecoration(
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFFa78bfa)
                                  .withOpacity(0.4),
                              blurRadius: _glowAnimation.value,
                              spreadRadius: _glowAnimation.value / 2,
                            ),
                          ],
                        ),
                        child: Text(
                          'UNMUTE',
                          style: TextStyle(
                            fontSize: MediaQuery.of(context).size.width > 768
                                ? 128
                                : 64,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 6.4,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    );
                  },
                ),

                const SizedBox(height: 32),

                // Tagline with fade-in effect
                TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0.0, end: 1.0),
                  duration: const Duration(seconds: 2),
                  builder: (context, value, child) {
                    return Opacity(
                      opacity: value,
                      child: Transform.translate(
                        offset: Offset(0, 20 * (1 - value)),
                        child: child,
                      ),
                    );
                  },
                  child: Text(
                    'Your Voice Matters',
                    style: TextStyle(
                      fontSize: MediaQuery.of(context).size.width > 768
                          ? 24
                          : 16,
                      fontWeight: FontWeight.w300,
                      letterSpacing: 4.8,
                      color: Colors.white.withOpacity(0.6),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// Gradient background painter
class GradientBackgroundPainter extends CustomPainter {
  final double animation;

  GradientBackgroundPainter({required this.animation});

  @override
  void paint(Canvas canvas, Size size) {
    final angle = animation * 2 * math.pi;
    final offset = Offset(-50 * math.sin(angle), -50 * math.cos(angle));

    final paint1 = Paint()
      ..shader = RadialGradient(
        center: Alignment(0.2 + offset.dx / size.width, 0.5 + offset.dy / size.height),
        radius: 0.5,
        colors: [
          const Color(0xFF7828c8).withOpacity(0.15),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    final paint2 = Paint()
      ..shader = RadialGradient(
        center: Alignment(0.8 + offset.dx / size.width, 0.8 + offset.dy / size.height),
        radius: 0.5,
        colors: [
          const Color(0xFFc82878).withOpacity(0.15),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    final paint3 = Paint()
      ..shader = RadialGradient(
        center: Alignment(0.4 + offset.dx / size.width, 0.2 + offset.dy / size.height),
        radius: 0.5,
        colors: [
          const Color(0xFF2878c8).withOpacity(0.15),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint1);
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint2);
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint3);
  }

  @override
  bool shouldRepaint(GradientBackgroundPainter oldDelegate) => true;
}

// Grid pattern painter
class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.02)
      ..strokeWidth = 1;

    const gridSize = 50.0;

    // Draw vertical lines
    for (double x = 0; x < size.width; x += gridSize) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }

    // Draw horizontal lines
    for (double y = 0; y < size.height; y += gridSize) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}

// Particle class
class Particle {
  final double x;
  final double duration;
  final double delay;
  double age = 0;

  Particle()
      : x = math.Random().nextDouble(),
        duration = math.Random().nextDouble() * 4 + 6,
        delay = math.Random().nextDouble() * 8;
}

// Particle widget
class ParticleWidget extends StatefulWidget {
  final Particle particle;

  const ParticleWidget({super.key, required this.particle});

  @override
  State<ParticleWidget> createState() => _ParticleWidgetState();
}

class _ParticleWidgetState extends State<ParticleWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: (widget.particle.duration * 1000).toInt()),
      vsync: this,
    );

    Future.delayed(Duration(milliseconds: (widget.particle.delay * 1000).toInt()), () {
      if (mounted) {
        _controller.forward();
      }
    });

    widget.particle.age = 0;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final screenHeight = MediaQuery.of(context).size.height;
        final progress = _controller.value;
        
        double opacity;
        if (progress < 0.1) {
          opacity = progress / 0.1;
        } else if (progress > 0.9) {
          opacity = (1 - progress) / 0.1;
        } else {
          opacity = 1.0;
        }

        return Positioned(
          left: MediaQuery.of(context).size.width * widget.particle.x,
          bottom: screenHeight * progress - 20,
          child: Opacity(
            opacity: opacity,
            child: Container(
              width: 4,
              height: 4,
              decoration: BoxDecoration(
                color: const Color(0xFFa78bfa).withOpacity(0.6),
                shape: BoxShape.circle,
              ),
            ),
          ),
        );
      },
    );
  }
}