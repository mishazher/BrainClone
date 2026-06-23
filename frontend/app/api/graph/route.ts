
import { NextRequest, NextResponse } from 'next/server';
import { GraphData, GraphNode, NODE_COLORS, NodeType } from '@/types/graph';

// Note: no trailing slash, and must include the /api/v1 prefix.
const API_Base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function categoryToType(category?: string): NodeType {
  switch (category) {
    case 'Person': return 'person';
    case 'Location': return 'location';
    case 'Event':
    case 'Date':
    default: return 'event';
  }
}

// Transform the backend's raw cypher result ({ results: [{ n, r, m }] }) into the
// { nodes, links } shape the frontend store expects. Done here (server-side) so the
// browser never calls the backend directly — avoids CORS and the build-time URL bake.
function resultsToGraphData(results: any[]): GraphData {
  const nodes = new Map<string, GraphNode>();
  const links: GraphData['links'] = [];
  const linkSet = new Set<string>();

  const addNode = (raw: any) => {
    if (!raw || !raw.name || nodes.has(raw.name)) return;
    const type = categoryToType(raw.category);
    nodes.set(raw.name, {
      id: raw.name,
      name: raw.name,
      type,
      val: 1,
      color: NODE_COLORS[type],
      metadata: { description: raw.description, category: raw.category },
    });
  };

  for (const record of results || []) {
    addNode(record.n);
    addNode(record.m);
    if (record.r && record.n && record.m) {
      const a = `${record.n.name}-${record.m.name}`;
      const b = `${record.m.name}-${record.n.name}`;
      if (!linkSet.has(a) && !linkSet.has(b)) {
        links.push({
          source: record.n.name,
          target: record.m.name,
          relationship: record.r.type || 'RELATED_TO',
          strength: 1,
        });
        linkSet.add(a);
      }
    }
  }

  return { nodes: Array.from(nodes.values()), links };
}

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
    const graphData = resultsToGraphData(data.results);

    // Shape matches what app/page.tsx expects: { success, data: { nodes, links } }
    return NextResponse.json({ success: true, data: graphData });

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
