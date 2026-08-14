import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/constants/subjects.dart';
import 'package:frontend/providers/books_provider.dart';

class BookUploadDialog extends StatefulWidget {
  const BookUploadDialog({super.key});

  @override
  State<BookUploadDialog> createState() => _BookUploadDialogState();
}

class _BookUploadDialogState extends State<BookUploadDialog> {
  final TextEditingController _titleController = TextEditingController();
  String _selectedSubject = 'इतिहास';
  PlatformFile? _selectedFile;
  bool _isUploading = false;
  String? _error;

  Future<void> _pickFile() async {
    try {
      FilePickerResult? result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        withData: kIsWeb,
      );

      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _selectedFile = result.files.first;
          if (_titleController.text.isEmpty) {
            _titleController.text = _selectedFile!.name.replaceAll('.pdf', '');
          }
          _error = null;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'फाईल निवडताना त्रुटी: $e';
      });
    }
  }

  Future<void> _submitUpload() async {
    if (_selectedFile == null) {
      setState(() => _error = 'कृपया PDF फाईल निवडा.');
      return;
    }

    setState(() {
      _isUploading = true;
      _error = null;
    });

    final booksProv = context.read<BooksProvider>();
    final success = await booksProv.uploadBook(
      filePath: _selectedFile!.path ?? '',
      fileBytes: _selectedFile!.bytes,
      filename: _selectedFile!.name,
      title: _titleController.text.trim(),
      subjectName: _selectedSubject,
    );

    if (mounted) {
      setState(() => _isUploading = false);
      if (success) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('पुस्तक अपलोड झाले! इंडेक्सिंग सुरू आहे...')),
        );
      } else {
        setState(() {
          _error = booksProv.errorMessage ?? 'अपलोड अयशस्वी.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'नवीन पुस्तक जोडा 📚',
                    style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              // File Picker Button
              InkWell(
                onTap: _pickFile,
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.white24, style: BorderStyle.solid),
                    borderRadius: BorderRadius.circular(12),
                    color: Colors.white.withOpacity(0.04),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.picture_as_pdf, color: Colors.redAccent, size: 32),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _selectedFile != null ? _selectedFile!.name : 'PDF फाईल निवडा',
                              style: GoogleFonts.poppins(
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            Text(
                              _selectedFile != null
                                  ? '${(_selectedFile!.size / 1024 / 1024).toStringAsFixed(2)} MB'
                                  : 'फक्त .pdf फाईल्स अनुमत',
                              style: GoogleFonts.notoSansDevanagari(fontSize: 11, color: Colors.white54),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.folder_open, color: Colors.white70),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              // Title textfield
              TextField(
                controller: _titleController,
                decoration: InputDecoration(
                  labelText: 'पुस्तकाचे नाव (Title)',
                  labelStyle: GoogleFonts.notoSansDevanagari(fontSize: 13),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: GoogleFonts.notoSansDevanagari(fontSize: 14),
              ),
              const SizedBox(height: 16),
              // Subject Dropdown
              DropdownButtonFormField<String>(
                value: _selectedSubject,
                decoration: InputDecoration(
                  labelText: 'विषय (Subject)',
                  labelStyle: GoogleFonts.notoSansDevanagari(fontSize: 13),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                items: MPSCSubjects.list.map((s) {
                  return DropdownMenuItem<String>(
                    value: s.nameMr,
                    child: Text(s.nameMr, style: GoogleFonts.notoSansDevanagari(fontSize: 13)),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) setState(() => _selectedSubject = val);
                },
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(
                  _error!,
                  style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                ),
              ],
              const SizedBox(height: 20),
              // Submit button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isUploading ? null : _submitUpload,
                  child: _isUploading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : Text('अपलोड करा व इंडेक्स करा', style: GoogleFonts.notoSansDevanagari(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
