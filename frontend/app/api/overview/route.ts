import { NextRequest, NextResponse } from 'next/server';
import { geminiService } from '@/lib/gemini';

// Generates the "Play" experience: a narrated overview of the journal plus a
// few facts about the person, each tied to the graph nodes it came from. Runs
// Gemini server-side with the full graph payload (the backend chat route only
// sees a 10-node sample, which is too thin for this).
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  try {
    const { graphData } = await request.json();

    const overview = await geminiService.generateBrainOverview(graphData);

    return NextResponse.json({ success: true, ...overview });
  } catch (error) {
    console.error('Error generating brain overview:', error);
    const message = error instanceof Error ? error.message : 'Failed to generate overview';
    const status = message.includes('empty') ? 400 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
