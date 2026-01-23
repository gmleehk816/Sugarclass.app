
import { GoogleGenAI, GenerateContentResponse, Part } from "@google/genai";
import { Message, Role, FileData } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || "" });

export const getGeminiResponse = async (
  prompt: string,
  history: Message[],
  files: FileData[]
): Promise<string> => {
  const model = "gemini-3-flash-preview";

  // Construct RAG context from files
  let systemContext = "You are a highly capable RAG-enabled AI assistant. Use the provided context to answer questions accurately.\n";

  if (files.length > 0) {
    systemContext += "\nCONTEXT FROM UPLOADED DOCUMENTS:\n";
    files.forEach(f => {
      if (f.content) {
        systemContext += `--- Document: ${f.name} ---\n${f.content}\n`;
      }
    });
  }

  const parts: Part[] = [];

  // Add file parts for multimodal support (images)
  files.forEach(file => {
    if (file.type.startsWith('image/') && file.base64) {
      parts.push({
        inlineData: {
          mimeType: file.type,
          data: file.base64.split(',')[1]
        }
      });
    }
  });

  // Add the user prompt
  parts.push({ text: prompt });

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: model,
      contents: [
        { role: 'user', parts: parts }
      ],
      config: {
        systemInstruction: systemContext,
        temperature: 0.7,
      },
    });

    return response.text || "I'm sorry, I couldn't generate a response.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "An error occurred while processing your request. Please ensure your API key is valid and you have an active internet connection.";
  }
};
