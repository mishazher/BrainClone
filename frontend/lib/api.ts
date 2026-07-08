import axios from 'axios';
import { z } from 'zod';
import { GraphData, GraphNode, GraphLink, NODE_COLORS, NodeType } from '@/types/graph';

// Direct-to-backend base URL. Note: browser calls to the backend require CORS;
// prefer the same-origin /api/* Next.js proxy routes where one exists.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  // Keep frontend snappy on prod if backend is unreachable
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const GraphNodeSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['person', 'event', 'location', 'journal']),
  val: z.number(),
  color: z.string(),
  metadata: z.record(z.string(), z.any()).optional(),
});

const GraphLinkSchema = z.object({
  source: z.string(),
  target: z.string(),
  relationship: z.string(),
  strength: z.number().optional(),
});

const GraphDataSchema = z.object({
  nodes: z.array(GraphNodeSchema),
  links: z.array(GraphLinkSchema),
});

// Demo data for when backend is not available
const DEMO_GRAPH_DATA: GraphData = {
  nodes: [],
  links: []
};

function categoryToType(category?: string): NodeType {
  switch ((category || '').toLowerCase()) {
    case 'person': return 'person';
    case 'location': return 'location';
    case 'journal': return 'journal';
    default: return 'event';
  }
}

// Map a raw backend entity ({ id?, name, type/category, description, ... })
// into the GraphNode shape the store expects.
function entityToNode(raw: any): GraphNode {
  const type = categoryToType(raw?.category || raw?.type);
  return {
    id: String(raw?.id ?? raw?.name ?? `entity_${Date.now()}`),
    name: String(raw?.name ?? raw?.id ?? 'Unknown'),
    type,
    val: 1,
    color: NODE_COLORS[type],
    metadata: { description: raw?.description, category: raw?.category ?? raw?.type },
  };
}

export const graphApi = {
  async getGraph(): Promise<GraphData> {
    try {
      // Fetch through the same-origin /api/graph route. That route proxies the
      // backend server-side (no CORS) and already transforms the cypher results
      // into { success, data: { nodes, links } } — single source of truth.
      const response = await fetch('/api/graph');
      if (!response.ok) {
        throw new Error(`/api/graph responded with ${response.status}`);
      }

      const result = await response.json();
      if (result.success && result.data) {
        return result.data as GraphData;
      }

      return DEMO_GRAPH_DATA;
    } catch (error) {
      console.warn('Failed to load graph, using demo data:', error);
      // Return demo data when the graph can't be loaded (e.g., backend down)
      return DEMO_GRAPH_DATA;
    }
  },

  // Backend route: GET /graph/entities/{entity_id} -> { entity: {...} }
  async getNode(nodeId: string): Promise<GraphNode> {
    try {
      const response = await api.get(`/graph/entities/${encodeURIComponent(nodeId)}`);
      return entityToNode(response.data?.entity ?? response.data);
    } catch (error) {
      const demoNode = DEMO_GRAPH_DATA.nodes.find(n => n.id === nodeId);
      if (demoNode) return demoNode;
      throw new Error('Node not found');
    }
  },

  // Backend route: POST /graph/entities -> { status, entity_id, entity_type }
  async createNode(node: Omit<GraphNode, 'id'>): Promise<GraphNode> {
    try {
      const response = await api.post('/graph/entities', {
        name: node.name,
        type: node.type,
        description: node.metadata?.description,
      });
      return { ...node, id: response.data?.entity_id ?? `entity_${Date.now()}` };
    } catch (error) {
      // In demo mode, just return the node with a generated ID
      return { ...node, id: `demo_${Date.now()}` };
    }
  },

  // Backend route: PUT /graph/entities/{entity_id} (no PATCH on the backend)
  async updateNode(nodeId: string, updates: Partial<GraphNode>): Promise<GraphNode> {
    try {
      await api.put(`/graph/entities/${encodeURIComponent(nodeId)}`, updates);
      const demoNode = DEMO_GRAPH_DATA.nodes.find(n => n.id === nodeId);
      return { ...(demoNode ?? { id: nodeId, name: nodeId, type: 'event' as const, val: 1, color: NODE_COLORS.event }), ...updates };
    } catch (error) {
      const demoNode = DEMO_GRAPH_DATA.nodes.find(n => n.id === nodeId);
      if (demoNode) return { ...demoNode, ...updates };
      throw new Error('Node not found');
    }
  },

  // Backend route: DELETE /graph/entities/{entity_id}
  async deleteNode(nodeId: string): Promise<void> {
    try {
      await api.delete(`/graph/entities/${encodeURIComponent(nodeId)}`);
    } catch (error) {
      console.log('Demo mode: Would delete node', nodeId);
    }
  },

  // Backend route: POST /graph/relationships
  async createLink(link: Omit<GraphLink, 'color'>): Promise<GraphLink> {
    try {
      await api.post('/graph/relationships', {
        source_id: typeof link.source === 'string' ? link.source : link.source.id,
        target_id: typeof link.target === 'string' ? link.target : link.target.id,
        type: link.relationship,
        weight: link.strength,
      });
      return { ...link, color: '#666' };
    } catch (error) {
      // In demo mode, just return the link
      return { ...link, color: '#666' };
    }
  },

  // The backend has no DELETE-relationship route; go through POST /graph/cypher.
  async deleteLink(sourceId: string, targetId: string): Promise<void> {
    try {
      const query =
        'MATCH (a {name: $source})-[r]-(b {name: $target}) DELETE r';
      await api.post(
        `/graph/cypher?query=${encodeURIComponent(query)}`,
        { parameters: { source: sourceId, target: targetId } }
      );
    } catch (error) {
      console.log('Demo mode: Would delete link', sourceId, targetId);
    }
  },

  // Backend route: GET /search/suggestions?partial_query=...&limit=...
  async searchNodes(query: string): Promise<GraphNode[]> {
    try {
      const response = await api.get('/search/suggestions', {
        params: { partial_query: query, limit: 20 },
      });
      const suggestions: any[] = response.data?.suggestions ?? [];
      return suggestions.map(s =>
        entityToNode({ id: s.entity_id, name: s.text, type: s.type })
      );
    } catch (error) {
      // In demo mode, filter demo nodes
      return DEMO_GRAPH_DATA.nodes.filter(node =>
        node.name.toLowerCase().includes(query.toLowerCase()) ||
        node.metadata?.description?.toLowerCase().includes(query.toLowerCase())
      );
    }
  },

  // Backend route: POST /graph/traverse -> { status, nodes, edges/relationships }
  async getNeighbors(nodeId: string, depth: number = 1): Promise<GraphData> {
    try {
      const response = await api.post('/graph/traverse', {
        start_entity_id: nodeId,
        max_depth: depth,
        limit: 50,
      });
      const rawNodes: any[] = response.data?.nodes ?? [];
      const rawEdges: any[] = response.data?.edges ?? response.data?.relationships ?? [];
      return {
        nodes: rawNodes.map(entityToNode),
        links: rawEdges
          .filter(e => e?.source && e?.target)
          .map(e => ({
            source: typeof e.source === 'object' ? e.source.id : e.source,
            target: typeof e.target === 'object' ? e.target.id : e.target,
            relationship: e.type || 'RELATED_TO',
            strength: e.weight ?? 1,
          })),
      };
    } catch (error) {
      return { nodes: [], links: [] };
    }
  },
};

// Document-RAG API (R2R behind the backend's /documents and /search routes).
// Prefer the same-origin /api/documents proxy routes from browser code.
export const documentsApi = {
  // Backend route: POST /documents/upload (multipart)
  async uploadDocument(file: File, metadata?: Record<string, any>): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.document_id;
  },

  // Backend route: GET /documents
  async listDocuments(limit = 100, offset = 0): Promise<any[]> {
    const response = await api.get('/documents', { params: { limit, offset } });
    return response.data?.documents ?? [];
  },

  // Backend route: POST /search/hybrid?query=...&limit=... (query params)
  async query(query: string, limit = 10): Promise<any> {
    const response = await api.post('/search/hybrid', null, {
      params: { query, limit },
    });
    return response.data;
  },

  // Backend route: POST /documents/{id}/extract -> { status, entities_extracted, ... }
  async extractEntities(documentId: string): Promise<any> {
    const response = await api.post(`/documents/${encodeURIComponent(documentId)}/extract`);
    return response.data;
  },

  // Backend route: GET /documents/{id}/entities
  async getDocumentEntities(documentId: string): Promise<GraphNode[]> {
    const response = await api.get(`/documents/${encodeURIComponent(documentId)}/entities`);
    const entities: any[] = response.data?.entities ?? [];
    return entities.map(entityToNode);
  },

  // Backend route: DELETE /documents/{id}
  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${encodeURIComponent(documentId)}`);
  },
};

// Kept for backwards compatibility with older imports.
export const r2rApi = documentsApi;
