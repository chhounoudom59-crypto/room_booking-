import 'package:flutter/material.dart';
import 'app_drawer.dart';

class AppPageShell extends StatelessWidget {
  final String title;
  final Widget child;

  const AppPageShell({
    super.key,
    required this.title,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
      ),
      drawer: const AppDrawer(),
      body: SafeArea(child: child),
    );
  }
}