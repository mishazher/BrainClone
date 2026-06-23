import axios from 'axios';
import { z } from 'zod';
import { GraphData, GraphNode, GraphLink } from '@/types/graph';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  // Keep frontend snappy on prod if backend is unreachable
  timeout: 6000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const GraphNodeSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['person', 'event', 'location']),
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

  async getNode(nodeId: string): Promise<GraphNode> {
    try {
      const response = await api.get(`/graph/nodes/${nodeId}`);
      return GraphNodeSchema.parse(response.data);
    } catch (error) {
      // Return demo node if backend not available
      const demoNode = DEMO_GRAPH_DATA.nodes.find(n => n.id === nodeId);
      if (demoNode) return demoNode;
      throw new Error('Node not found');
    }
  },

  async createNode(node: Omit<GraphNode, 'id'>): Promise<GraphNode> {
    try {
      const response = await api.post('/graph/nodes', node);
      return GraphNodeSchema.parse(response.data);
    } catch (error) {
      // In demo mode, just return the node with a generated ID
      return { ...node, id: `demo_${Date.now()}` };
    }
  },

  async updateNode(nodeId: string, updates: Partial<GraphNode>): Promise<GraphNode> {
    try {
      const response = await api.patch(`/graph/nodes/${nodeId}`, updates);
      return GraphNodeSchema.parse(response.data);
    } catch (error) {
      // In demo mode, return updated node
      const demoNode = DEMO_GRAPH_DATA.nodes.find(n => n.id === nodeId);
      if (demoNode) return { ...demoNode, ...updates };
      throw new Error('Node not found');
    }
  },

  async deleteNode(nodeId: string): Promise<void> {
    try {
      await api.delete(`/graph/nodes/${nodeId}`);
    } catch (error) {
      // In demo mode, just log the action
      console.log('Demo mode: Would delete node', nodeId);
    }
  },

  async createLink(link: Omit<GraphLink, 'color'>): Promise<GraphLink> {
    try {
      const response = await api.post('/graph/links', link);
      return GraphLinkSchema.parse(response.data);
    } catch (error) {
      // In demo mode, just return the link
      return { ...link, color: '#666' };
    }
  },

  async deleteLink(sourceId: string, targetId: string): Promise<void> {
    try {
      await api.delete(`/graph/links/${sourceId}/${targetId}`);
    } catch (error) {
      // In demo mode, just log the action
      console.log('Demo mode: Would delete link', sourceId, targetId);
    }
  },

  async searchNodes(query: string): Promise<GraphNode[]> {
    try {
      const response = await api.get('/graph/search', { params: { q: query } });
      return z.array(GraphNodeSchema).parse(response.data);
    } catch (error) {
      // In demo mode, filter demo nodes
      return DEMO_GRAPH_DATA.nodes.filter(node =>
        node.name.toLowerCase().includes(query.toLowerCase()) ||
        node.metadata?.description?.toLowerCase().includes(query.toLowerCase())
      );
    }
  },

  async getNeighbors(nodeId: string, depth: number = 1): Promise<GraphData> {
    try {
      const response = await api.get(`/graph/nodes/${nodeId}/neighbors`, {
        params: { depth },
      });
      return GraphDataSchema.parse(response.data);
    } catch (error) {
      // In demo mode, find neighbors from demo data
      const neighbors = DEMO_GRAPH_DATA.links
        .filter(link => link.source === nodeId || link.target === nodeId)
        .map(link => link.source === nodeId ? link.target : link.source);

      const neighborNodes = DEMO_GRAPH_DATA.nodes.filter(node =>
        neighbors.includes(node.id) || node.id === nodeId
      );

      const neighborLinks = DEMO_GRAPH_DATA.links.filter(link =>
        neighborNodes.some(node => node.id === link.source || node.id === link.target)
      );

      return { nodes: neighborNodes, links: neighborLinks };
    }
  },
};

export const r2rApi = {
  async uploadDocument(file: File, metadata?: Record<string, any>): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await api.post('/r2r/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.document_id;
  },

  async query(query: string, documentId?: string): Promise<any> {
    const response = await api.post('/r2r/query', {
      query,
      document_id: documentId,
      search_settings: {
        use_hybrid_search: true,
        limit: 10,
      },
    });
    return response.data;
  },

  async extractEntities(documentId: string): Promise<GraphData> {
    const response = await api.post(`/r2r/documents/${documentId}/extract`);
    return GraphDataSchema.parse(response.data);
  },
};

export const authApi = {
  async login(email: string, password: string): Promise<{ token: string; user: any }> {
    const response = await api.post('/auth/login', { email, password });
    localStorage.setItem('auth_token', response.data.token);
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout');
    localStorage.removeItem('auth_token');
  },

  async register(email: string, password: string, name: string): Promise<any> {
    const response = await api.post('/auth/register', { email, password, name });
    return response.data;
  },

  async getCurrentUser(): Promise<any> {
    const response = await api.get('/auth/me');
    return response.data;
  },
};