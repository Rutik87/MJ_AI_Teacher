import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:frontend/core/constants/subjects.dart';

class SubjectBadge extends StatelessWidget {
  final String subjectName;
  final bool isSelected;
  final VoidCallback? onTap;

  const SubjectBadge({
    super.key,
    required this.subjectName,
    this.isSelected = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final subj = MPSCSubjects.getSubject(subjectName);
    final theme = Theme.of(context);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected
              ? subj.color
              : subj.color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? subj.color : subj.color.withOpacity(0.3),
            width: 1.2,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              subj.icon,
              size: 16,
              color: isSelected ? Colors.white : subj.color,
            ),
            const SizedBox(width: 6),
            Text(
              subjectName,
              style: GoogleFonts.notoSansDevanagari(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                color: isSelected ? Colors.white : theme.textTheme.bodyMedium?.color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
