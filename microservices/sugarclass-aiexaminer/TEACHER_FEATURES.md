# AI Examiner Teacher Customization Features

## Summary of Changes

I've added comprehensive features to transform AI Examiner into a teacher-friendly platform for creating and managing student exercises. Here's what's new:

## ✅ Features Implemented

### 1. **Material Management & Folder Organization** 
- **Edit Material Names**: Teachers can rename uploaded materials
  - Click the Edit icon (appears on hover) on any material card
  - Inline editing with instant save
  - Backend endpoint: `PATCH /v1/upload/{material_id}`

- **Folder/Session Management**:
  - Each upload session automatically creates a folder
  - **Rename Folders**: Click edit icon on any session/folder to rename all materials together
  - **View Folder Contents**: Click folder icon to see all files in a session
  - **Add Files to Folders**: Add more materials to existing sessions/folders
  - **Delete Individual Files**: Remove specific files from folders
  - **Delete Entire Folders**: Remove all files in a session at once
  
- **Auto-Naming from Materials**: Exercise titles automatically derive from material filenames
  - Removes file extension
  - Used as default quiz title
  - Editable during review and after creation

### 2. **Question Editing**
- **Full Quiz Editor** (`/quiz/{quiz_id}/edit`):
  - Edit quiz title
  - Edit question text
  - Modify MCQ options and correct answers
  - Edit short answer expected responses
  - Update explanations
  - Add new questions (MCQ or Short Answer)
  - Delete questions
  - Visual indicators for question types

- **Access Method**:
  - "Edit Questions" button on each exercise card
  - Comprehensive editing interface
  - Save changes instantly to database

### 3. **Backend API Enhancements**

#### Existing Endpoints Enhanced:
```python
# Material editing
PATCH /v1/upload/{material_id}
Body: { "filename": "new_name.pdf" }

# Quiz editing (full update)
PATCH /v1/quiz/{quiz_id}
Body: { 
  "title": "New Title",  # optional
  "questions": [...]      # optional
}

# Upload with session/folder support
POST /v1/upload/
FormData: {
  "file": file,
  "session_id": "optional_session_id"  # Groups files into folders
}
```

#### New Collections Backend (for future expansion):
```python
# Note: Collections system built but UI integrated into Materials page
# Each session_id acts as a folder automatically
```

## 📁 Files Modified/Created

### Backend:
1. **`backend/api/endpoints/upload.py`**
   - Added `MaterialUpdateRequest` model
   - Added `PATCH /{material_id}` endpoint
   - Added `collection_id` parameter to upload endpoint

2. **`backend/api/endpoints/quiz.py`**
   - Added `QuizUpdateRequest` model
   - Updated `PATCH /{quiz_id}` to support full quiz editing

3. **`backend/models/quiz.py`**
   - Added `Collection` model for folder support
   - Added `collection_id` field to `Material` model

4. **`backend/api/endpoints/collections.py`** *(NEW - for future expansion)*
   - Full CRUD API for collections/folders
   - Currently sessions act as folders automatically

5. **`backend/main.py`**
   - Registered collections router

### Frontend:
1. **`frontend/src/app/materials/page.tsx`**
   - Added material editing state and UI
   - Added session/folder renaming functionality
   - Added folder detail modal to view/manage files
   - Added "Add Files to Folder" capability
   - Integrated complete folder CRUD operations

2. **`frontend/src/app/page.tsx`**
   - Added "Edit Questions" button to exercise cards
   - Auto-naming from material filenames (already implemented)

3. **`frontend/src/app/quiz/[quiz_id]/edit/page.tsx`** *(NEW)*
   - Full quiz editor page
   - Edit all quiz properties
   - Add/remove questions
   - Change question types and content

## 🎯 Teacher Workflow

### Creating & Organizing Materials:
1. **Upload Materials** → Materials page
   - Upload PDFs or images
   - Multiple files in one session create a folder automatically
   - Rename individual materials or entire folders
   - Materials organized by upload session (folder)

2. **Manage Folders**:
   - **Rename Folder**: Click edit icon → Enter new name
   - **View Files**: Click folder icon → See all files in folder
   - **Add Files**: Click "Add Files" → Upload more to existing folder
   - **Delete Files**: In folder view → Delete individual files
   - **Delete Folder**: Click trash icon → Remove entire folder

3. **Generate Questions** → Click "Configure & Start Quiz"
   - Upload PDFs or images
   - Rename materials as needed
   - Materials organized by name

2. **Generate Questions** → Click "Configure & Start Quiz"
   - Select pages (for large PDFs)
   - Choose question type (MCQ/Short Answer/Mixed)
   - Set number of questions
   - Review and customize questions before saving

3. **Edit Anytime** → "Edit Questions" button
   - Modify questions
   - Add/remove questions
   - Update correct answers
   - Add explanations

### Managing Exercises:
- **Rename**: Click edit icon on quiz title
- **Edit Questions**: Click "Edit Questions" button
- **Delete**: Click trash icon
- **View Performance**: Check accuracy and attempts

## 🚀 Usage Examples

### Edit Material Name:
```
1. Go to Materials page
2. Hover over material card
3. Click Edit icon (appears on hover)
4. Type new name
5. Press Enter or click checkmark
```

### Edit Exercise Questions:
```
1. Go to Exercises page (homepage)
2. Find the exercise
3. Click "Edit Questions"
4. Modify any field
5. Click "Save Changes"
```

### Add New Question:
```
1. In quiz editor
2. Scroll to bottom
3. Click "Add Multiple Choice" or "Add Short Answer"
4. Fill in details
5. Save changes
```

## 🎨 UI/UX Features

- **Inline Editing**: Quick edits without page navigation
- **Visual Feedback**: Icons and colors indicate editability
- **Auto-Save**: Changes persist immediately
- **Hover States**: Edit buttons appear on hover
- **Validation**: Prevents empty titles/questions

## 🔒 Safety Features

- **Confirmation Dialogs**: For destructive actions (delete)
- **Validation**: Ensures data integrity
- **Error Handling**: User-friendly error messages
- **Cancel Options**: Can cancel edits anytime

## 📊 Technical Details

### State Management:
- React hooks for editing state
- Optimistic updates for better UX
- Proper cleanup on cancel

### API Design:
- RESTful endpoints
- Optional fields for partial updates
- Consistent error responses

### Database:
- JSON column for flexible question storage
- Supports all question types
- Easy to extend

## 🎓 Perfect for Teachers

This setup allows teachers to:
- ✅ Create exercises from their materials
- ✅ Customize questions to match curriculum
- ✅ Rename and organize materials
- ✅ Add explanations for students
- ✅ Maintain a library of reusable exercises
- ✅ Track student performance
- ✅ Iterate and improve questions over time

All changes are instantly saved and available for student use!
