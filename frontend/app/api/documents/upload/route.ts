import { NextRequest, NextResponse } from 'next/server';

// Server-side proxy for document ingestion. Forwards the multipart form to the
// backend's POST /documents/upload, which sends it to the external R2R server
// (chunk + embed + optional Gemini KG extraction). Proxying keeps the backend
// URL off the client and avoids CORS.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Ingestion + graph extraction can take a while.
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  try {
    const incoming = await request.formData();
    const file = incoming.get('file');

    if (!(file instanceof File)) {
      return NextResponse.json({ error: 'A file is required' }, { status: 400 });
    }

    const formData = new FormData();
    formData.append('file', file);

    const metadata = incoming.get('metadata');
    if (typeof metadata === 'string' && metadata) {
      formData.append('metadata', metadata);
    }

    const extractEntities = incoming.get('extract_entities');
    if (typeof extractEntities === 'string') {
      formData.append('extract_entities', extractEntities);
    }

    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(55_000),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      let detail: string = data?.detail || data?.error || 'Failed to upload document';
      // The backend proxies to an R2R server; when that server is down the
      // raw httpx error leaks through — translate it for the UI.
      if (detail.includes('All connection attempts failed')) {
        detail = 'The document ingestion service (R2R) is currently offline. Uploads will work again once it is back up.';
      }
      return NextResponse.json({ error: detail }, { status: response.status });
    }

    // Backend returns { status, document_id, filename, entities_extracted, entities }.
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying document upload to backend:', error);
    const timedOut = error instanceof Error && error.name === 'TimeoutError';
    return NextResponse.json(
      {
        error: timedOut
          ? 'Document ingestion timed out — it may still complete in the background'
          : 'Backend unavailable — could not upload document',
      },
      { status: timedOut ? 504 : 502 }
    );
  }
}
