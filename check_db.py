import sys
sys.path.insert(0, '/app/app')
from pdf_converter import extract_toc
from pathlib import Path
import json

# Find PDFs in uploads
uploads = Path('/app/uploads')
pdfs = list(uploads.rglob('*.pdf'))
print(f"Found {len(pdfs)} PDFs:")
for p in pdfs:
    print(f"  {p}")

if pdfs:
    pdf = pdfs[0]
    print(f"\nExtracting TOC from: {pdf.name}")
    toc = extract_toc(pdf)
    print(f"TOC entries: {len(toc)}")
    for entry in toc[:30]:
        indent = "  " * (entry['level'] - 1)
        print(f"  {indent}L{entry['level']} p{entry['page']}: {entry['title']}")
    if len(toc) > 30:
        print(f"  ... and {len(toc) - 30} more entries")
else:
    # Try to find PDFs elsewhere
    print("\nNo PDFs in /app/uploads, searching /app...")
    import subprocess
    result = subprocess.run(['find', '/app', '-name', '*.pdf', '-type', 'f'], capture_output=True, text=True)
    print(result.stdout[:2000] if result.stdout else "No PDFs found")
