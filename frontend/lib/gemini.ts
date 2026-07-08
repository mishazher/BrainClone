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

  /**
   * Prepare a narrated overview of the user's journal/memory graph: a short
   * summary plus a handful of facts about the person, each tied to the graph
   * nodes it came from (so the UI can highlight them).
   */
  async generateBrainOverview(graphData?: {
    nodes?: Array<{ name: string; type?: string; metadata?: Record<string, any> }>;
    links?: Array<any>;
    linkCount?: number;
  }): Promise<BrainOverview> {
    const nodes = Array.isArray(graphData?.nodes) ? graphData!.nodes! : [];
    const links = Array.isArray(graphData?.links) ? graphData!.links! : [];
    const linkCount = typeof graphData?.linkCount === 'number' ? graphData.linkCount : links.length;

    if (nodes.length === 0) {
      throw new Error('The knowledge graph is empty — add some memories first.');
    }

    // Journal nodes carry the richest signal (entry text/summaries); include
    // them in more detail than plain entity nodes.
    const journalNodes = nodes.filter((n) => n.type === 'journal').slice(0, 15);
    const entityNodes = nodes.filter((n) => n.type !== 'journal').slice(0, 80);

    const journalContext = journalNodes.map((n) => ({
      name: n.name,
      summary: String(n.metadata?.summary || n.metadata?.description || '').slice(0, 400),
    }));
    const entityContext = entityNodes.map((n) => ({
      name: n.name,
      type: n.type,
      description: n.metadata?.description
        ? String(n.metadata.description).slice(0, 150)
        : undefined,
    }));

    const prompt = `You are the narrator of a person's "brain" — a knowledge graph built from their journal entries.

Journal entries (${journalNodes.length} shown):
${JSON.stringify(journalContext)}

Entities in their memory graph (${entityNodes.length} of ${nodes.length} shown; ${linkCount} connections total):
${JSON.stringify(entityContext)}

Prepare a spoken-style overview of this person's journal, plus 3 to 5 interesting facts about the person (their relationships, places they frequent, notable events, patterns you notice).

Rules:
- Each fact MUST list the node names it is based on in "nodeNames", copied EXACTLY as they appear above.
- Keep the overview to 2-4 sentences, warm and personal, second person ("Your memories show...").
- Each fact is one sentence.

Return ONLY this JSON, nothing else:
{"overview": "...", "facts": [{"fact": "...", "nodeNames": ["...", "..."]}]}`;

    const text = await this.generateWithRetry(prompt);

    let jsonText = text.trim();
    if (jsonText.startsWith('```json')) {
      jsonText = jsonText.replace(/^```json\s*/, '').replace(/\s*```$/, '');
    } else if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/^```\s*/, '').replace(/\s*```$/, '');
    }

    try {
      const parsed = JSON.parse(jsonText) as BrainOverview;
      return {
        overview: String(parsed.overview || ''),
        facts: Array.isArray(parsed.facts)
          ? parsed.facts
              .filter((f) => f && typeof f.fact === 'string')
              .map((f) => ({
                fact: f.fact,
                nodeNames: Array.isArray(f.nodeNames) ? f.nodeNames.filter((n) => typeof n === 'string') : [],
              }))
          : [],
      };
    } catch {
      // Model ignored the JSON contract — degrade gracefully to a plain overview.
      return { overview: text.trim(), facts: [] };
    }
  }
}

export interface BrainOverview {
  overview: string;
  facts: Array<{ fact: string; nodeNames: string[] }>;
}

export const geminiService = new GeminiService();
