import 'package:flutter/material.dart';

class SubjectItem {
  final String nameMr;
  final String nameEn;
  final IconData icon;
  final Color color;

  const SubjectItem({
    required this.nameMr,
    required this.nameEn,
    required this.icon,
    required this.color,
  });
}

class MPSCSubjects {
  static const List<SubjectItem> list = [
    SubjectItem(nameMr: 'इतिहास', nameEn: 'History', icon: Icons.history_edu, color: Color(0xFFE65100)),
    SubjectItem(nameMr: 'भूगोल', nameEn: 'Geography', icon: Icons.public, color: Color(0xFF2E7D32)),
    SubjectItem(nameMr: 'राज्यशास्त्र', nameEn: 'Polity', icon: Icons.account_balance, color: Color(0xFF1565C0)),
    SubjectItem(nameMr: 'अर्थशास्त्र', nameEn: 'Economics', icon: Icons.trending_up, color: Color(0xFFC2185B)),
    SubjectItem(nameMr: 'महाराष्ट्राचा इतिहास', nameEn: 'Maharashtra History', icon: Icons.fort, color: Color(0xFFD84315)),
    SubjectItem(nameMr: 'महाराष्ट्राचा भूगोल', nameEn: 'Maharashtra Geography', icon: Icons.terrain, color: Color(0xFF388E3C)),
    SubjectItem(nameMr: 'महाराष्ट्र विशेष', nameEn: 'Maharashtra Special', icon: Icons.star, color: Color(0xFFF57C00)),
    SubjectItem(nameMr: 'सामान्य विज्ञान', nameEn: 'General Science', icon: Icons.science, color: Color(0xFF00838F)),
    SubjectItem(nameMr: 'पर्यावरण', nameEn: 'Environment', icon: Icons.park, color: Color(0xFF558B2F)),
    SubjectItem(nameMr: 'चालू घडामोडी', nameEn: 'Current Affairs', icon: Icons.newspaper, color: Color(0xFF6A1B9A)),
    SubjectItem(nameMr: 'सामान्य ज्ञान', nameEn: 'General Knowledge', icon: Icons.lightbulb, color: Color(0xFFAD1457)),
    SubjectItem(nameMr: 'गणित', nameEn: 'Mathematics', icon: Icons.calculate, color: Color(0xFF0277BD)),
    SubjectItem(nameMr: 'बुद्धिमत्ता', nameEn: 'Reasoning', icon: Icons.psychology, color: Color(0xFF00695C)),
    SubjectItem(nameMr: 'PYQ', nameEn: 'Previous Year Questions', icon: Icons.quiz, color: Color(0xFF4527A0)),
    SubjectItem(nameMr: 'Notes', nameEn: 'Study Notes', icon: Icons.note_alt, color: Color(0xFF4E342E)),
    SubjectItem(nameMr: 'Other', nameEn: 'Other', icon: Icons.folder, color: Color(0xFF37474F)),
  ];

  static SubjectItem getSubject(String nameMr) {
    return list.firstWhere(
      (s) => s.nameMr == nameMr,
      orElse: () => const SubjectItem(
        nameMr: 'General',
        nameEn: 'General',
        icon: Icons.menu_book,
        color: Color(0xFFFF6B35),
      ),
    );
  }
}
