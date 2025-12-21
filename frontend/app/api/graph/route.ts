
import { NextRequest, NextResponse } from 'next/server';

const API_Base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function GET(request: NextRequest) {
  try {
    // Proxy query params
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('query');

    // Construct real backend URL
    // The backend endpoint is POST /graph/cypher
    const backendUrl = `${API_Base}/graph/cypher`;

    const defaultQuery = 'MATCH (n) OPTIONAL MATCH (n)-[r]-(m) RETURN DISTINCT n, r, m LIMIT 500';
    const cypherQuery = query || defaultQuery;

    const response = await fetch(backendUrl + `?query=${encodeURIComponent(cypherQuery)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json(data);

  } catch (error) {
    console.error('Error fetching graph data from backend:', error);
    return NextResponse.json(
      { error: 'Failed to fetch graph data' },
      { status: 500 }
    );
  }
}

// Ensure POST also proxies if needed, or disable it if we only want read access
export async function POST(request: NextRequest) {
  // For now, let's just proxy POST as well to /graph/nodes or similar if that's what's intended?
  // Actually the previous in-memory store handled POST /api/graph to "save" the graph.
  // The real backend doesn't seem to have a "save entire graph" endpoint, it has specific /nodes /relationships
  // So we should probably remove this bulk save capability or forward it intelligently.
  // Given the GraphApi in lib/api.ts sends individual node creates/updates, 
  // we might not ever hit this bulk POST in a real scenario unless "Save Graph" button does it.

  return NextResponse.json({ message: "Bulk save not supported in live mode" }, { status: 501 });
}
