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

        # Handle empty or very short answers
        if not user_answer or len(user_answer.strip()) < 5:
            return {
                "is_correct": False,
                "score": 0,
                "feedback": "Your answer is too short. Please provide a more detailed response that addresses the key points.",
                "correct_points": [],
                "missing_points": key_points
            }

        prompt = f"""You are an expert educator evaluating a student's answer. Be fair, thorough, and encouraging.

QUESTION:
{question}

MODEL ANSWER (for reference):
{expected_answer}

KEY POINTS TO EVALUATE (student should cover these):
{chr(10).join(f"- {point}" for point in key_points)}

STUDENT'S ANSWER:
{user_answer}

EVALUATION INSTRUCTIONS:
1. Compare the student's answer against each key point
2. A key point is "covered" if the student demonstrates understanding of that concept, even if worded differently
3. Be generous with partial credit - focus on understanding, not exact wording
4. Consider synonyms and alternative explanations as valid

SCORING GUIDE:
- 90-100: Excellent - covers all or nearly all key points with good understanding
- 70-89: Good - covers most key points adequately
- 50-69: Partial - covers some key points but missing important ones
- 25-49: Weak - shows some understanding but misses most key points
- 0-24: Insufficient - does not demonstrate understanding of the topic

Respond with a JSON object (no markdown, no code blocks):
{{
    "is_correct": true/false (true if score >= 60),
    "score": <number 0-100>,
    "feedback": "<2-3 sentences of constructive feedback>",
    "correct_points": ["<key points the student addressed>"],
    "missing_points": ["<key points the student missed>"]
}}"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a fair and encouraging educator. Evaluate student answers objectively. Always respond with valid JSON only, no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
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
                    timeout=45.0  # Increased timeout for complex evaluations
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
                    # Handle case where ``` appears multiple times
                    parts = content.split("```")
                    if len(parts) >= 2:
                        content = parts[1].strip()
                        # Remove 'json' if it's at the start
                        if content.lower().startswith("json"):
                            content = content[4:].strip()

                # Parse JSON response
                parsed = json.loads(content)

                # Validate and normalize the response
                return {
                    "is_correct": bool(parsed.get("is_correct", False)),
                    "score": max(0, min(100, int(parsed.get("score", 0)))),  # Clamp to 0-100
                    "feedback": str(parsed.get("feedback", "No feedback provided.")),
                    "correct_points": list(parsed.get("correct_points", [])),
                    "missing_points": list(parsed.get("missing_points", []))
                }

            except json.JSONDecodeError as e:
                print(f"JSON parsing error in validate_short_answer: {e}")
                print(f"Raw content: {content if 'content' in dir() else 'N/A'}")
                return {
                    "is_correct": False,
                    "score": 0,
                    "feedback": "Failed to parse AI response. Please try again.",
                    "correct_points": [],
                    "missing_points": key_points
                }
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

