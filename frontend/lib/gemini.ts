import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.NEXT_PUBLIC_GEMINI_API_KEY || '');

export interface JournalAnalysis {
  title: string;
  summary: string;
  entities: {
    people: string[];
    places: string[];
    events: string[];
    emotions: string[];
    topics: string[];
  };
  connections: {
    type: 'person' | 'event' | 'location' | 'topic';
    name: string;
    relationship: string;
    confidence: number;
  }[];
  insights: string[];
}

export class GeminiService {
  private model = genAI.getGenerativeModel({ model: 'gemini-2.5-pro' });

  /**
   * Call the model, retrying on transient overload (503) / rate-limit (429)
   * errors with exponential backoff. Free-tier keys hit these intermittently.
   */
  private async generateWithRetry(prompt: string, maxRetries = 4): Promise<string> {
    let lastError: unknown;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await this.model.generateContent(prompt);
        return (await result.response).text();
      } catch (error) {
        lastError = error;
        const msg = error instanceof Error ? error.message : String(error);
        // Billing depletion / disabled is a hard wall — retrying just wastes time.
        const hardLimit = msg.includes('depleted') || msg.includes('billing') ||
          msg.includes('prepayment') || msg.includes('SERVICE_DISABLED');
        const transient = !hardLimit && (msg.includes('503') || msg.includes('429') ||
          msg.includes('high demand') || msg.includes('overloaded'));
        if (!transient || attempt === maxRetries) break;
        // 0.5s, 1s, 2s, 4s
        const delay = 500 * 2 ** attempt;
        console.warn(`Gemini transient error (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms`);
        await new Promise((r) => setTimeout(r, delay));
      }
    }
    throw lastError;
  }

  async analyzeJournalEntry(text: string, existingGraph?: any): Promise<JournalAnalysis> {
    const prompt = `Analyze: "${text}"

Return JSON: {title, summary, entities: {people:[], places:[], events:[], emotions:[], topics:[]}, connections: [{type, name, relationship, confidence}], insights: []}

JSON only:`;

    try {
      const text = await this.generateWithRetry(prompt);

      // Parse the JSON response (remove markdown code blocks if present)
      let jsonText = text.trim();
      if (jsonText.startsWith('```json')) {
        jsonText = jsonText.replace(/^```json\s*/, '').replace(/\s*```$/, '');
      } else if (jsonText.startsWith('```')) {
        jsonText = jsonText.replace(/^```\s*/, '').replace(/\s*```$/, '');
      }
      const analysis = JSON.parse(jsonText) as JournalAnalysis;
      return analysis;
    } catch (error) {
      console.error('Error analyzing journal entry:', error);
      console.error('Error details:', error instanceof Error ? error.message : error);
      console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace');
      
      const msg = error instanceof Error ? error.message : String(error);
      if (msg.includes('depleted') || msg.includes('billing') || msg.includes('prepayment')) {
        throw new Error('Gemini billing credits are depleted. Add credits in Google AI Studio to re-enable AI features.');
      }
      if (msg.includes('429')) {
        throw new Error('API quota exceeded. Please wait a moment and try again, or upgrade your plan for higher limits.');
      }

      throw new Error('Failed to analyze journal entry');
    }
  }

  // NOTE: chat moved to the FastAPI backend (`POST /api/v1/chat`). The Next.js
  // `/api/chat` route now proxies there, so the chatbot Gemini call no longer
  // runs in the frontend. Journaling (`analyzeJournalEntry`) still runs here.
}

export const geminiService = new GeminiService();
