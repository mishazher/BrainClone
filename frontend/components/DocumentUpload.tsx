'use client';

import { useCallback, useRef, useState } from 'react';
import { FileText, Upload, X, CheckCircle2, Loader2 } from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';
import { GraphNode, GraphLink, NODE_COLORS, NodeType } from '@/types/graph';

interface DocumentUploadProps {
  onClose: () => void;
}

interface UploadResult {
  documentId: string;
  filename: string;
  entitiesExtracted: number;
  entities: Array<{ name?: string; category?: string; description?: string }>;
}

function categoryToType(category?: string): NodeType {
  switch ((category || '').toLowerCase()) {
    case 'person': return 'person';
    case 'location': return 'location';
    default: return 'event';
  }
}

export default function DocumentUpload({ onClose }: DocumentUploadProps) {
  const { graphData, setGraphData } = useGraphStore();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [addedToGraph, setAddedToGraph] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelected = useCallback((selected: File | null) => {
    setError(null);
    setResult(null);
    setAddedToGraph(false);
    setFile(selected);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) handleFileSelected(dropped);
  }, [handleFileSelected]);

  const handleUpload = async () => {
    if (!file || isUploading) return;

    setIsUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata', JSON.stringify({ source: 'upload', uploaded_at: new Date().toISOString() }));
      formData.append('extract_entities', 'true');

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.error || `Upload failed (${response.status})`);
      }

      setResult({
        documentId: data.document_id,
        filename: data.filename || file.name,
        entitiesExtracted: data.entities_extracted ?? 0,
        entities: Array.isArray(data.entities) ? data.entities : [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  // Merge the uploaded document + its extracted entities into the 3D graph.
  const handleAddToGraph = () => {
    if (!result || addedToGraph) return;

    const existingNames = new Set(
      (graphData?.nodes ?? []).map((n) => n.name.toLowerCase())
    );

    const docId = `document_${Date.now()}`;
    const docNode: GraphNode = {
      id: docId,
      name: result.filename,
      type: 'journal',
      val: 1,
      color: NODE_COLORS.journal,
      metadata: {
        source: 'document',
        document_id: result.documentId,
        timestamp: new Date().toISOString(),
      },
    };

    const entityNodes: GraphNode[] = result.entities
      .filter((e) => e.name && !existingNames.has(e.name.toLowerCase()))
      .map((e, i) => {
        const type = categoryToType(e.category);
        return {
          id: `${docId}_entity_${i}`,
          name: e.name as string,
          type,
          val: 1,
          color: NODE_COLORS[type],
          metadata: { source: 'document', description: e.description, category: e.category },
        };
      });

    // Link the document to its entities; link entities already in the graph too.
    const links: GraphLink[] = entityNodes.map((n) => ({
      source: docId,
      target: n.id,
      relationship: 'mentions',
      strength: 0.8,
      color: NODE_COLORS.journal,
    }));
    for (const e of result.entities) {
      if (!e.name) continue;
      const existing = (graphData?.nodes ?? []).find(
        (n) => n.name.toLowerCase() === e.name!.toLowerCase()
      );
      if (existing) {
        links.push({
          source: docId,
          target: existing.id,
          relationship: 'mentions',
          strength: 0.8,
          color: NODE_COLORS.journal,
        });
      }
    }

    setGraphData({
      nodes: [...(graphData?.nodes ?? []), docNode, ...entityNodes],
      links: [...(graphData?.links ?? []), ...links],
    });
    setAddedToGraph(true);
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-lg mx-4 bg-gray-800/95 rounded-xl p-6 shadow-2xl border border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            Upload Document to Your Brain
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-gray-400 mb-4">
          Documents are chunked and embedded for retrieval (RAG), and entities are
          extracted into your knowledge graph.
        </p>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragging ? 'border-cyan-400 bg-cyan-400/10' : 'border-gray-600 hover:border-gray-500'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".txt,.md,.pdf,.docx,.html,.json,.csv"
            onChange={(e) => handleFileSelected(e.target.files?.[0] ?? null)}
          />
          <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          {file ? (
            <p className="text-white text-sm font-medium">{file.name} <span className="text-gray-400">({(file.size / 1024).toFixed(1)} KB)</span></p>
          ) : (
            <p className="text-gray-400 text-sm">
              Drag &amp; drop a file here, or click to browse<br />
              <span className="text-xs text-gray-500">.txt, .md, .pdf, .docx, .html, .json, .csv</span>
            </p>
          )}
        </div>

        {error && (
          <div className="mt-3 px-3 py-2 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-3 px-3 py-3 bg-green-900/30 border border-green-700 rounded-lg text-sm">
            <div className="flex items-center gap-2 text-green-300 font-medium mb-1">
              <CheckCircle2 className="w-4 h-4" />
              Ingested “{result.filename}”
            </div>
            <p className="text-gray-300">
              {result.entitiesExtracted} entit{result.entitiesExtracted === 1 ? 'y' : 'ies'} extracted.
            </p>
            {result.entities.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {result.entities.map((e, i) => (
                  <span key={i} className="px-2 py-0.5 bg-gray-700 text-gray-200 rounded-full text-xs">
                    {e.name}
                  </span>
                ))}
              </div>
            )}
            {result.entities.length > 0 && (
              <button
                onClick={handleAddToGraph}
                disabled={addedToGraph}
                className="mt-3 w-full px-3 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-lg hover:from-cyan-700 hover:to-blue-700 transition-all disabled:opacity-50 text-sm"
              >
                {addedToGraph ? 'Added to graph ✓' : 'Add entities to graph'}
              </button>
            )}
          </div>
        )}

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-lg hover:from-cyan-700 hover:to-blue-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Ingesting…</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload</span>
              </>
            )}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
