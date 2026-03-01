/// Global configuration for the ASL Sign Language App.
///
/// Before running on a real Android device:
///   Change [baseUrl] to your PC's local IP address, e.g. "http://192.168.1.5:8000"
///
/// For the Android emulator, the special alias 10.0.2.2 maps to the host machine's
/// localhost, so you can keep the default value.
class AppConfig {
  /// Base URL of the running FastAPI backend.
  static String baseUrl = 'http://10.0.2.2:8000';
}
