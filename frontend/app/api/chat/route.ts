import { NextRequest, NextResponse } from 'next/server';

// The Gemini chat call now lives on the FastAPI backend. This route is a thin
// server-side proxy so the browser never needs the backend URL or any API key.
// Note: no trailing slash, must include the /api/v1 prefix.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, graphData, chatHistory } = body;

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, graphData, chatHistory }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      // Surface the backend's user-facing message (quota/billing/overload, etc.)
      const detail = data?.detail || 'Failed to process chat message';
      return NextResponse.json({ error: detail }, { status: response.status });
    }

    // Backend already returns { success, response, timestamp }.
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying chat message to backend:', error);
    return NextResponse.json(
      {
        error: 'Failed to process chat message',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
