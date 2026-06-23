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
  private model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

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

  async chatWithContext(question: string, graphData: any, chatHistory: any[] = []): Promise<string> {
    // Include relevant graph data for context
    const nodes = graphData?.nodes || [];
    const links = graphData?.links || [];
    
    // Get sample nodes (first 10) to provide context
    const sampleNodes = nodes.slice(0, 10).map((n: any) => ({
      name: n.name,
      type: n.type || 'concept'
    }));

    const prompt = `You are a helpful AI assistant with access to the user's memory database.

User's question: "${question}"

Memory database contains:
- ${nodes.length} nodes (concepts, people, places, events)
- ${links.length} connections between them
- Sample nodes: ${JSON.stringify(sampleNodes)}

Use this memory data to provide a helpful, contextual response. Reference relevant memories when appropriate:`;

    try {
      let text = await this.generateWithRetry(prompt);

      // Clean up markdown formatting
      text = text.replace(/\*\*(.*?)\*\*/g, '$1'); // Remove bold **text**
      text = text.replace(/\*(.*?)\*/g, '$1'); // Remove italic *text*
      text = text.replace(/^\* /gm, '• '); // Convert * to bullet points
      
      return text;
    } catch (error) {
      console.error('Error in chat:', error);
      const msg = error instanceof Error ? error.message : String(error);

      if (msg.includes('depleted') || msg.includes('billing') || msg.includes('prepayment')) {
        throw new Error('Gemini billing credits are depleted. Add credits in Google AI Studio to re-enable AI features.');
      }
      if (msg.includes('429')) {
        throw new Error('API quota exceeded. Please wait a moment and try again, or upgrade your plan for higher limits.');
      }
      if (msg.includes('503') || msg.includes('high demand') || msg.includes('overloaded')) {
        throw new Error('The AI model is temporarily overloaded. Please try again in a few seconds.');
      }

      throw new Error('Failed to process chat message');
    }
  }
}

export const geminiService = new GeminiService();
