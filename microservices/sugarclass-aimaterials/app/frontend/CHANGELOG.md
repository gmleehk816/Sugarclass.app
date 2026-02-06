# Frontend Changelog

## 2025-12-29

### ChapterSidebar Component

#### Fixed

- **Chapter Number Display:** Fixed issue where chapter numbers showed full topic IDs instead of simple numbers
  - Added regex extraction: `/ch(\d+)$/i`
  - Example: `engineering_gcse_8852_ch1` now displays as `1. Engineering materials`

#### Changed

- **Chapter List Format:** Simplified display
  - Removed `Ch{n}` badge box
  - Removed subtitle showing subtopic count
  - Now shows only: `{number}. {title}`
  
- **Header Subject Display:** Shows current subject name instead of "Chapter Navigation"

### Files Modified

- `src/components/ChapterSidebar.jsx`
  - Line 43: Added chapter number extraction regex
  - Line 176: Updated primary text to use extracted number
  - Line 81: Added `currentSubjectName` variable

### Build Notes

```bash
npm run build
Copy-Item -Path "dist/*" -Destination "../static/frontend/" -Recurse -Force
```
