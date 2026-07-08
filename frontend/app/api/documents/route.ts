import { NextRequest, NextResponse } from 'next/server';

// Server-side proxy to the backend's document routes (R2R document-RAG).
// Note: no trailing slash, must include the /api/v1 prefix.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function GET(request: NextRequest) {
  try {
    const limit = request.nextUrl.searchParams.get('limit') || '50';
    const offset = request.nextUrl.searchParams.get('offset') || '0';

    const response = await fetch(`${API_BASE}/documents?limit=${limit}&offset=${offset}`, {
      cache: 'no-store',
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data?.detail || 'Failed to list documents';
      return NextResponse.json({ error: detail }, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error listing documents from backend:', error);
    return NextResponse.json(
      { error: 'Backend unavailable — could not list documents' },
      { status: 502 }
    );
  }
}
