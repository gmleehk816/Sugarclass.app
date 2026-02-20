import pymupdf4llm
import re

pdf_path = "/tmp/test.pdf"

# Convert pages 1-100 to see patterns across more content
md = pymupdf4llm.to_markdown(pdf_path, pages=list(range(100)))

lines = md.split('\n')

# Show ALL non-empty lines from pages ~5-15 (likely TOC + first chapter area)
print("=== RAW LINES 200-500 ===")
for i in range(200, min(500, len(lines))):
    stripped = lines[i].strip()
    if stripped:
        print(f"  L{i:4d}: {stripped[:140]}")

# Also look for page break patterns
print("\n=== PAGE BREAKS ===")
for i, line in enumerate(lines):
    if re.match(r'^-{3,}', line.strip()):
        # Show context around page breaks
        if i < len(lines) - 3:
            ctx = ' | '.join(l.strip()[:60] for l in lines[i+1:i+4] if l.strip())
            print(f"  L{i:4d}: --- BREAK --- next: {ctx}")
