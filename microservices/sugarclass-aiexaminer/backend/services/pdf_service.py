import fitz  # PyMuPDF
from typing import List, Optional, Tuple


# Maximum number of pages that can be processed
MAX_PAGES_LIMIT = 20


class PDFService:
    @staticmethod
    async def get_page_count(file_path: str) -> int:
        """Get the total number of pages in a PDF file."""
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            print(f"Error getting page count: {e}")
            return 0
    
    @staticmethod
    async def extract_text(file_path: str, selected_pages: Optional[List[int]] = None) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            selected_pages: Optional list of 1-indexed page numbers to extract. 
                           If None, extracts from all pages (limited to MAX_PAGES_LIMIT).
        """
        import fitz
        text = ""
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            # Determine which pages to process
            if selected_pages:
                # Use selected pages (1-indexed, convert to 0-indexed)
                pages_to_process = [p - 1 for p in selected_pages if 1 <= p <= total_pages]
                # Limit to MAX_PAGES_LIMIT
                pages_to_process = pages_to_process[:MAX_PAGES_LIMIT]
            else:
                # Process all pages, limited to MAX_PAGES_LIMIT
                pages_to_process = list(range(min(total_pages, MAX_PAGES_LIMIT)))
            
            for page_idx in pages_to_process:
                page = doc.load_page(page_idx)
                page_text = page.get_text()
                text += f"\n--- Page {page_idx + 1} ---\n{page_text}\n"
            
            doc.close()
            
            # Fallback to OCR if text is minimal (likely a scanned PDF)
            if len(text.strip()) < 50:
                print(f"Minimal text found in {file_path}, falling back to Vision OCR...")
                return await PDFService.extract_text_vision(file_path, selected_pages)
                
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return await PDFService.extract_text_vision(file_path, selected_pages)
            
        return text

    @staticmethod
    async def extract_text_vision(file_path: str, selected_pages: Optional[List[int]] = None) -> str:
        """Extract text from PDF using Vision OCR for scanned documents."""
        import fitz
        import os
        from backend.services.gemini_service import gemini_service
        
        full_text = ""
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            # Determine which pages to process
            if selected_pages:
                # Use selected pages (1-indexed, convert to 0-indexed)
                pages_to_process = [p - 1 for p in selected_pages if 1 <= p <= total_pages]
                # For OCR, limit to 10 pages to avoid excessive API usage
                pages_to_process = pages_to_process[:min(10, MAX_PAGES_LIMIT)]
            else:
                # Process first 5 pages max by default
                pages_to_process = list(range(min(total_pages, 5)))
            
            for page_idx in pages_to_process:
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High res
                temp_img = f"{file_path}_p{page_idx}.png"
                pix.save(temp_img)
                
                page_text = await gemini_service.extract_text_from_image(temp_img)
                full_text += f"\n--- Page {page_idx + 1} ---\n{page_text}\n"
                
                # Cleanup temp image
                if os.path.exists(temp_img):
                    os.remove(temp_img)
            
            doc.close()
        except Exception as e:
            print(f"Error in Vision OCR for PDF: {e}")
            
        return full_text

    @staticmethod
    async def extract_text_with_metadata(file_path: str, selected_pages: Optional[List[int]] = None) -> Tuple[str, int, List[int]]:
        """
        Extract text from PDF and return metadata.
        
        Returns:
            Tuple of (extracted_text, total_pages, processed_pages)
        """
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
        except:
            total_pages = 0
        
        text = await PDFService.extract_text(file_path, selected_pages)
        
        if selected_pages:
            processed_pages = [p for p in selected_pages if 1 <= p <= total_pages][:MAX_PAGES_LIMIT]
        else:
            processed_pages = list(range(1, min(total_pages, MAX_PAGES_LIMIT) + 1))
        
        return text, total_pages, processed_pages

    @staticmethod
    async def get_page_previews(file_path: str) -> List[dict]:
        """
        Get preview text for each page in the PDF.
        
        Returns:
            List of dicts with page number, preview text (first ~100 chars), and any headers found.
        """
        previews = []
        try:
            doc = fitz.open(file_path)
            for page_idx in range(len(doc)):
                try:
                    page = doc.load_page(page_idx)
                    text = page.get_text().strip()
                    
                    # Get first meaningful line (skip empty lines)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    first_line = lines[0] if lines else ""
                    
                    # Get preview (first 100 chars of content)
                    preview_text = text[:150].replace('\n', ' ').strip()
                    if len(text) > 150:
                        preview_text += "..."
                    
                    # Try to detect if it's a title/header page
                    is_title_page = (
                        len(text) < 200 and 
                        page_idx == 0
                    ) or (
                        first_line and 
                        len(first_line) < 80 and 
                        first_line.isupper()
                    )
                    
                    previews.append({
                        "page": page_idx + 1,
                        "title": first_line[:60] + ("..." if len(first_line) > 60 else "") if first_line else f"Page {page_idx + 1}",
                        "preview": preview_text if preview_text else "(No text content)",
                        "char_count": len(text),
                        "is_title_page": is_title_page
                    })
                except Exception as page_err:
                    print(f"Error getting preview for page {page_idx + 1}: {page_err}")
                    previews.append({
                        "page": page_idx + 1,
                        "title": f"Page {page_idx + 1}",
                        "preview": "(Error loading page content)",
                        "char_count": 0,
                        "is_title_page": False
                    })
            
            doc.close()
        except Exception as e:
            print(f"Error getting page previews: {e}")
        
        return previews


pdf_service = PDFService()

