import httpx
import json
from typing import List, Dict, Any
from backend.core.config import settings

class GeminiService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL

    async def generate_questions(self, text: str, num_questions: int = 5, difficulty: str = "medium") -> List[Dict[str, Any]]:
        prompt = f"""
        Act as an expert educator. Based on the following study materials, generate {num_questions} multiple-choice questions.
        The difficulty level should be {difficulty}.
        
        For each question, provide:
        1. The question text.
        2. Four options (A, B, C, D).
        3. The correct answer.
        4. A detailed explanation of why that answer is correct.
        
        Respond ONLY with a JSON array in the following format:
        [
          {{
            "question": "text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": "optionX",
            "explanation": "text"
          }}
        ]
        
        Study Materials:
        {text}
        """
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert educator who generates high-quality assessments."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": { "type": "json_object" } if "gemini" not in self.model.lower() else None
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    print(f"LLM API Error: {response.status_code} - {response.text}")
                    return []

                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Clean up response text if it includes markdown blocks
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].strip()
                    
                return json.loads(content)
            except Exception as e:
                print(f"Error calling LLM API or parsing response: {e}")
                return []

    async def extract_text_from_image(self, image_path: str) -> str:
        import base64
        
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Detect mime type from extension
            ext = image_path.split('.')[-1].lower()
            mime_type = f"image/{ext}" if ext in ['png', 'jpg', 'jpeg'] else "image/jpeg"
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all readable text from this study material. Preserve the structure and context. If it's a diagram, describe it briefly."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_string}"}}
                        ]
                    }
                ],
                "max_tokens": 4096
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    print(f"Vision API Error: {response.status_code} - {response.text}")
                    return "Error extracting text from image."

                result = response.json()
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error in extract_text_from_image: {e}")
            return f"Failed to process image: {str(e)}"

gemini_service = GeminiService()
