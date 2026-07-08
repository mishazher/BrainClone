import { GraphData } from '@/types/graph';

// Payload sent to the AI context routes (/api/overview, /api/chat, /api/journal).
export interface SlimGraphData {
  nodes: Array<{
    name: string;
    type: string;
    metadata?: { summary?: string; description?: string };
  }>;
  links: never[];
  linkCount: number;
}

/**
 * Strip the live graph down to what the AI prompts actually use.
 *
 * The store's node objects get mutated in place by the force-graph engine
 * (x/y/z, velocities, attached THREE.js objects), so serializing them raw
 * produces multi-megabyte — or circular — JSON. Vercel rejects bodies over
 * ~4.5 MB with FUNCTION_PAYLOAD_TOO_LARGE, so always send this slim shape.
 */
export function slimGraphForContext(graphData?: GraphData | null): SlimGraphData {
  const nodes = Array.isArray(graphData?.nodes) ? graphData!.nodes : [];
  const links = Array.isArray(graphData?.links) ? graphData!.links : [];

  return {
    nodes: nodes.map((n) => {
      const summary = typeof n.metadata?.summary === 'string' ? n.metadata.summary.slice(0, 400) : undefined;
      const description = typeof n.metadata?.description === 'string' ? n.metadata.description.slice(0, 400) : undefined;
      return {
        name: n.name,
        type: n.type,
        ...(summary || description ? { metadata: { summary, description } } : {}),
      };
    }),
    links: [],
    linkCount: links.length,
  };
}
