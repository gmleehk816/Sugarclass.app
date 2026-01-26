import fitz  # PyMuPDF


class PDFService:
    @staticmethod
    async def extract_text(file_path: str) -> str:
        import fitz
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Fallback to OCR if text is minimal (likely a scanned PDF)
            if len(text.strip()) < 50:
                print(f"Minimal text found in {file_path}, falling back to Vision OCR...")
                return await PDFService.extract_text_vision(file_path)
                
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return await PDFService.extract_text_vision(file_path)
            
        return text

    @staticmethod
    async def extract_text_vision(file_path: str) -> str:
        import fitz
        import os
        from backend.services.gemini_service import gemini_service
        
        full_text = ""
        try:
            doc = fitz.open(file_path)
            # Process first 5 pages max to avoid excessive API usage
            num_pages = min(len(doc), 5)
            
            for i in range(num_pages):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # High res
                temp_img = f"{file_path}_p{i}.png"
                pix.save(temp_img)
                
                page_text = await gemini_service.extract_text_from_image(temp_img)
                full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
                
                # Cleanup temp image
                if os.path.exists(temp_img):
                    os.remove(temp_img)
            
            doc.close()
        except Exception as e:
            print(f"Error in Vision OCR for PDF: {e}")
            
        return full_text

pdf_service = PDFService()
