---
name: handle-file-io-correctly
description: Use this skill when reading from or writing to files to avoid missing file errors and ensure correct output structure.
---
1. Verify the target directory exists; create it with `os.makedirs(path, exist_ok=True)` if necessary.  
2. Open files with the correct mode (`'r'`, `'w'`, `'a'`) and encoding (`'utf-8'`).  
3. When writing JSON, use `json.dump(..., ensure_ascii=False, indent=2)` to preserve readability.  
4. For CSV output, use the `csv` module with `quoting=csv.QUOTE_MINIMAL` and `escapechar='\\'` to handle special characters.  
5. After writing, close the file or use a context manager (`with` statement).  
6. Validate the output format against the specification before finalizing the file.  
7. Handle exceptions gracefully: log errors and exit with a clear message if a required file cannot be created or read.  
8. In tests, mock file paths or use temporary directories to avoid side effects.
