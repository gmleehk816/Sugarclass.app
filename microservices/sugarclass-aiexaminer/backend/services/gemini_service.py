import httpx
import json
from typing import List, Dict, Any
from backend.core.config import settings

class GeminiService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL

    async def generate_questions(self, text: str, num_questions: int = 5, difficulty: str = "medium", exclude_questions: List[str] = None) -> List[Dict[str, Any]]:
        exclude_section = f"\n        DO NOT generate any of the following questions as they already exist: {', '.join(exclude_questions)}" if exclude_questions else ""
        prompt = f"""
        Act as an expert educator. Based on the following study materials, generate {num_questions} multiple-choice questions.
        The difficulty level should be {difficulty}.{exclude_section}
        
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

    async def generate_short_questions(self, text: str, num_questions: int = 5, difficulty: str = "medium", exclude_questions: List[str] = None) -> List[Dict[str, Any]]:
        """Generate short answer questions from study materials"""
        exclude_section = f"\n        DO NOT generate any of the following questions as they already exist: {', '.join(exclude_questions)}" if exclude_questions else ""
        prompt = f"""
        Act as an expert educator. Based on the following study materials, generate {num_questions} short answer questions.
        The difficulty level should be {difficulty}.{exclude_section}
        
        For each question, provide:
        1. The question text (should require a paragraph-length response).
        2. The expected/model answer.
        3. Key points that should be included in a correct answer (3-5 bullet points).
        4. The difficulty level.
        
        Respond ONLY with a JSON array in the following format:
        [
          {{
            "question": "text",
            "expected_answer": "A comprehensive answer...",
            "key_points": ["point1", "point2", "point3"],
            "difficulty": "{difficulty}"
          }}
        ]
        
        Study Materials:
        {text}
        """
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert educator who creates thoughtful short-answer questions that test deep understanding."},
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
                print(f"Error generating short questions: {e}")
                return []

    async def validate_short_answer(
        self, 
        question: str, 
        expected_answer: str, 
        key_points: List[str], 
        user_answer: str
    ) -> Dict[str, Any]:
        """Validate a user's short answer response using AI"""
        
        prompt = f"""
        You are an expert educator evaluating a student's answer. Be fair but thorough in your assessment.
        
        Question: {question}
        
        Model Answer: {expected_answer}
        
        Key Points to Cover:
        {chr(10).join(f"- {point}" for point in key_points)}
        
        Student's Answer: {user_answer}
        
        Evaluate the student's answer and provide:
        1. is_correct: true if the answer covers most key points adequately (>60% accuracy)
        2. score: A score from 0-100 based on accuracy and completeness
        3. feedback: A helpful, constructive feedback message (2-3 sentences)
        4. correct_points: List of key points the student correctly addressed
        5. missing_points: List of key points the student missed or got wrong
        
        Respond ONLY with a JSON object in this format:
        {{
            "is_correct": true/false,
            "score": 0-100,
            "feedback": "Your detailed feedback...",
            "correct_points": ["point1", "point2"],
            "missing_points": ["point3"]
        }}
        """
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a fair and encouraging educator who provides constructive feedback. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
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
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"Validation API Error: {response.status_code} - {response.text}")
                    return {
                        "is_correct": False,
                        "score": 0,
                        "feedback": "Unable to validate answer at this time. Please try again.",
                        "correct_points": [],
                        "missing_points": key_points
                    }

                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Clean up response text if it includes markdown blocks
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].strip()
                    
                return json.loads(content)
            except Exception as e:
                print(f"Error validating short answer: {e}")
                return {
                    "is_correct": False,
                    "score": 0,
                    "feedback": f"Validation failed: {str(e)}",
                    "correct_points": [],
                    "missing_points": key_points
                }

    async def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from an image using Vision AI. Handles blurry/problematic images gracefully."""
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
                            {
                                "type": "text", 
                                "text": """You are an OCR specialist. Analyze this image and extract all readable text.

INSTRUCTIONS:
1. Extract ALL visible text from the image exactly as written
2. Preserve the structure (headings, paragraphs, bullet points)
3. If there are diagrams or charts, describe their key information
4. If handwritten, do your best to transcribe accurately

QUALITY CHECK:
- If the image is too blurry to read, start your response with "[QUALITY_ISSUE]" followed by a brief description
- If no meaningful text is found, start with "[NO_TEXT]"
- If partially readable, extract what you can and note unclear parts with [unclear]

Extract the text now:"""
                            },
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
                    timeout=90.0  # Increased timeout for large images
                )
                
                if response.status_code != 200:
                    print(f"Vision API Error: {response.status_code} - {response.text}")
                    return "[EXTRACTION_ERROR] Could not process this image. Please try uploading a clearer version."

                result = response.json()
                extracted_text = result['choices'][0]['message']['content'].strip()
                
                # Handle quality issues gracefully
                if extracted_text.startswith("[QUALITY_ISSUE]"):
                    return extracted_text  # Pass through the quality issue message
                elif extracted_text.startswith("[NO_TEXT]"):
                    return "[NO_TEXT] This image doesn't contain readable text. It may be a diagram, photo, or the text is not visible."
                
                # Basic validation: if extraction is too short, it might be problematic
                if len(extracted_text) < 50:
                    return f"[LIMITED_TEXT] Only partial text was extracted: {extracted_text}"
                
                return extracted_text
                
        except Exception as e:
            print(f"Error in extract_text_from_image: {e}")
            return f"[EXTRACTION_ERROR] Failed to process image: {str(e)}"

gemini_service = GeminiService()

