'use client';

import React, { useRef, useCallback, useMemo, useEffect, useState } from 'react';
import ForceGraph3D, { ForceGraphMethods } from 'react-force-graph-3d';
import * as THREE from 'three';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import SpriteText from 'three-spritetext';
import { useGraphStore } from '@/stores/graphStore';
import { GraphNode, GraphLink, NODE_COLORS, NodeType } from '@/types/graph';

interface Graph3DProps {
  width?: number;
  height?: number;
  backgroundColor?: string;
}

function checkWebGLSupport(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch (e) {
    return false;
  }
}

export default function Graph3D({
  width,
  height,
  backgroundColor = '#000011',
}: Graph3DProps) {
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [webGLSupported, setWebGLSupported] = useState(true);
  const [renderError, setRenderError] = useState(false);
  const [isClient, setIsClient] = useState(false);

  const {
    graphData,
    selectedNode,
    highlightedLinks,
    filterByType,
    searchQuery,
    setSelectedNode,
    setHoveredNode,
    getNeighbors,
  } = useGraphStore();

  useEffect(() => {
    setIsClient(true);
    const supported = checkWebGLSupport();
    setWebGLSupported(supported);

    const handleError = (e: ErrorEvent) => {
      if (e.message && (e.message.includes('WebGL') || e.message.includes('THREE'))) {
        console.error('WebGL Error caught:', e);
        setRenderError(true);
        setWebGLSupported(false);
        e.preventDefault();
      }
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  const filteredData = useMemo(() => {
    // Ensure graphData is properly initialized
    if (!graphData || !Array.isArray(graphData.nodes) || !Array.isArray(graphData.links)) {
      return { nodes: [], links: [] };
    }
    
    let nodes = graphData.nodes;
    let links = graphData.links;

    if (filterByType) {
      nodes = nodes.filter((node) => node.type === filterByType);
      const nodeIds = new Set(nodes.map((n) => n.id));
      links = links.filter((link) => {
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
        const targetId = typeof link.target === 'string' ? link.target : link.target.id;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
      });
    }

    if (searchQuery) {
      nodes = nodes.filter((node) =>
        node.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
      const nodeIds = new Set(nodes.map((n) => n.id));
      links = links.filter((link) => {
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
        const targetId = typeof link.target === 'string' ? link.target : link.target.id;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
      });
    }

    return { nodes, links };
  }, [graphData, filterByType, searchQuery]);

  const handleNodeClick = useCallback(
    (node: any) => {
      setSelectedNode(node);

      if (graphRef.current) {
        const distance = 150;
        const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

        graphRef.current.cameraPosition(
          {
            x: (node.x || 0) * distRatio,
            y: (node.y || 0) * distRatio,
            z: (node.z || 0) * distRatio,
          },
          node as any,
          1500
        );
      }
    },
    [setSelectedNode]
  );

  const handleNodeHover = useCallback(
    (node: any) => {
      setHoveredNode(node);
      document.body.style.cursor = node ? 'pointer' : 'default';

      let neighborNodes: Set<string> = new Set();
      let neighborLinks: Set<string> = new Set();
      if (node) {
        const neighbors = getNeighbors(node.id);
        neighborNodes = neighbors.nodes;
        neighborLinks = neighbors.links;
      }

      // Dim non-neighbours by mutating the existing sphere materials in place.
      // This keeps the highlight effect but avoids regenerating node geometry
      // on every pointer move (the previous cause of hover lag).
      const dimming = neighborNodes.size > 0;
      for (const n of filteredData.nodes as any[]) {
        const mat = n.__sphereMaterial;
        if (!mat) continue;
        mat.opacity = dimming ? (neighborNodes.has(n.id) ? 1 : 0.2) : 1.0;
      }

      // Edge highlighting stays in React state — it only re-evaluates cheap link
      // color/width accessors, not the node objects.
      useGraphStore.setState({
        highlightedNodes: neighborNodes,
        highlightedLinks: neighborLinks,
      });
    },
    [setHoveredNode, getNeighbors, filteredData]
  );

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  // Fact-highlight system: the AI overview (app/page.tsx) dispatches
  // 'highlightNodes' events with the node ids relevant to the current fact.
  // We dim everything else, light up links between relevant nodes, and fly
  // the camera to a focus node. An empty nodeIds list resets the view.
  useEffect(() => {
    const handleHighlight = (e: Event) => {
      const detail = (e as CustomEvent).detail || {};
      const nodeIds: string[] = Array.isArray(detail.nodeIds) ? detail.nodeIds : [];
      const idSet = new Set<string>(nodeIds);
      const dimming = idSet.size > 0;

      // Dim non-relevant nodes in place (same trick as hover highlighting).
      for (const n of graphData.nodes as any[]) {
        const mat = n.__sphereMaterial;
        if (!mat) continue;
        mat.opacity = dimming ? (idSet.has(n.id) ? 1 : 0.15) : 1.0;
      }

      // Highlight links that connect two relevant nodes.
      const linkIds = new Set<string>();
      if (dimming) {
        for (const link of graphData.links) {
          const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
          const targetId = typeof link.target === 'string' ? link.target : link.target.id;
          if (idSet.has(sourceId) && idSet.has(targetId)) {
            linkIds.add(`${sourceId}-${targetId}`);
          }
        }
      }
      useGraphStore.setState({ highlightedNodes: idSet, highlightedLinks: linkIds });

      // Fly the camera to the focus node (or the first relevant node).
      const focusId: string | undefined = detail.focusId ?? nodeIds[0];
      const focusNode = focusId
        ? (graphData.nodes as any[]).find((n) => n.id === focusId)
        : undefined;
      if (focusNode && graphRef.current) {
        const distance = 120;
        const distRatio =
          1 + distance / Math.hypot(focusNode.x || 0, focusNode.y || 0, focusNode.z || 0);
        graphRef.current.cameraPosition(
          {
            x: (focusNode.x || 0) * distRatio,
            y: (focusNode.y || 0) * distRatio,
            z: (focusNode.z || 0) * distRatio,
          },
          focusNode,
          1200
        );
        setSelectedNode(focusNode);
      } else if (!dimming) {
        setSelectedNode(null);
      }
    };

    window.addEventListener('highlightNodes', handleHighlight);
    return () => window.removeEventListener('highlightNodes', handleHighlight);
  }, [graphData, setSelectedNode]);

  const nodeThreeObject = useCallback((node: any) => {
    try {
      const nodeColor = node.color || NODE_COLORS[node.type as NodeType];
      const group = new THREE.Group();
      const nodeSize = (node.val || 6) * 2.5; // Make nodes 2.5x bigger (thick balls)
      // Note: intentionally NOT driven by hoveredNode/highlightedNodes — those
      // change on every pointer-move and would rebuild every node's meshes.
      // Hover feedback is handled cheaply via edge (linkColor) highlighting.
      const isSelected = selectedNode === node;

      // Create outer glow layers first (so they render behind the main sphere)
      if (isSelected) {
        // Outer glow
        const outerGlowGeometry = new THREE.SphereGeometry(nodeSize * 4, 16, 16);
        const outerGlowMaterial = new THREE.MeshBasicMaterial({
          color: nodeColor,
          transparent: true,
          opacity: 0.1,
          depthWrite: false,
        });
        const outerGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
        group.add(outerGlow);

        // Middle glow
        const middleGlowGeometry = new THREE.SphereGeometry(nodeSize * 2.5, 16, 16);
        const middleGlowMaterial = new THREE.MeshBasicMaterial({
          color: nodeColor,
          transparent: true,
          opacity: 0.2,
          depthWrite: false,
        });
        const middleGlow = new THREE.Mesh(middleGlowGeometry, middleGlowMaterial);
        group.add(middleGlow);
      }

      // Inner glow for all nodes
      const innerGlowGeometry = new THREE.SphereGeometry(nodeSize * 1.5, 16, 16);
      const innerGlowMaterial = new THREE.MeshBasicMaterial({
        color: nodeColor,
        transparent: true,
        opacity: isSelected ? 0.4 : 0.25,
        depthWrite: false,
      });
      const innerGlow = new THREE.Mesh(innerGlowGeometry, innerGlowMaterial);
      group.add(innerGlow);

      // Main sphere - make it more emissive for better bloom effect
      const geometry = new THREE.SphereGeometry(nodeSize, 16, 16);
      const material = new THREE.MeshPhongMaterial({
        color: nodeColor,
        emissive: nodeColor,
        emissiveIntensity: isSelected ? 2.0 : 1.5,
        shininess: 10,
        transparent: true,
        opacity: 1.0,
      });
      const sphere = new THREE.Mesh(geometry, material);
      // Keep a ref to the sphere material so hover highlighting can adjust opacity
      // in place (cheap) instead of rebuilding the whole node object every hover.
      node.__sphereMaterial = material;
      group.add(sphere);

      // Add text label
      const sprite = new SpriteText(node.name);
      sprite.material.depthWrite = false;
      sprite.color = '#ffffff';
      sprite.textHeight = 3;
      sprite.position.y = nodeSize + 8;
      sprite.backgroundColor = 'rgba(0,0,0,0.5)';
      sprite.padding = 2;
      sprite.borderRadius = 2;
      group.add(sprite);

      return group;
    } catch (error) {
      console.error('Error creating node object:', error);
      const geometry = new THREE.SphereGeometry(5);
      const material = new THREE.MeshBasicMaterial({ color: 0x3B82F6 });
      return new THREE.Mesh(geometry, material);
    }
  }, [selectedNode]);

  const linkColor = useCallback((link: any) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
    const targetId = typeof link.target === 'string' ? link.target : link.target.id;
    const linkId = `${sourceId}-${targetId}`;
    const isHighlighted = highlightedLinks.has(linkId);
    return isHighlighted ? '#ffffff' : '#4a5568';
  }, [highlightedLinks]);

  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force('link')?.distance((link: any) => 80);
      graphRef.current.d3Force('charge')?.strength(-500);
      graphRef.current.d3Force('center')?.strength(0.05);
    }
  }, []);

  useEffect(() => {
    if (graphRef.current && !renderError) {
      try {
        const scene = graphRef.current.scene();

        const ambientLight = new THREE.AmbientLight(0x404040, 1);
        scene.add(ambientLight);

        const light1 = new THREE.DirectionalLight(0xffffff, 0.6);
        light1.position.set(1, 1, 1);
        scene.add(light1);

        // Set up bloom effect exactly like the working example
        setTimeout(() => {
          try {
            if (graphRef.current) {
              const bloomPass = new UnrealBloomPass(
                new THREE.Vector2(256, 256), // resolution (can be any size, will be resized)
                2, // strength
                1, // radius
                0.3 // threshold
              );
              graphRef.current.postProcessingComposer().addPass(bloomPass);
              console.log('Bloom effect added successfully');
            }
          } catch (error) {
            console.log('Bloom setup error:', error);
          }
        }, 1000);
      } catch (error) {
        console.error('Error setting up scene:', error);
        setRenderError(true);
      }
    }
  }, [renderError]);

  if (!isClient || !webGLSupported || renderError) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-900 text-white p-8">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold mb-4">
            {!isClient ? 'Loading 3D Graph...' : '3D Visualization Not Available'}
          </h2>
          {isClient && (
            <>
              <p className="mb-4">
                Your browser or device doesn't support WebGL, which is required for 3D graphics.
              </p>
              <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <h3 className="font-semibold mb-2">Try these solutions:</h3>
                <ul className="text-left space-y-2 text-sm">
                  <li>• Use Chrome, Firefox, or Safari (latest versions)</li>
                  <li>• Enable hardware acceleration in browser settings</li>
                  <li>• Check if WebGL is enabled at chrome://gpu</li>
                  <li>• Try on a different device or browser</li>
                </ul>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold mb-2">Graph Data Summary:</h3>
                <p className="text-sm">Nodes: {filteredData.nodes.length}</p>
                <p className="text-sm">Links: {filteredData.links.length}</p>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

      return (
        <div className="relative w-full h-full">
          <ForceGraph3D
        ref={graphRef}
        width={width}
        height={height}
        graphData={filteredData}
        backgroundColor={backgroundColor}
        nodeLabel="name"
        nodeRelSize={1}
            nodeVal={(node: any) => (node.val || 6) * 2.5}
        nodeColor={(node: any) => node.color || NODE_COLORS[node.type as NodeType]}
        nodeOpacity={0.9}
        nodeResolution={8}
        nodeThreeObject={nodeThreeObject}
        nodeThreeObjectExtend={false}
        linkWidth={(link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
          const targetId = typeof link.target === 'string' ? link.target : link.target.id;
          const linkId = `${sourceId}-${targetId}`;
          return highlightedLinks.has(linkId) ? 2 : 1;
        }}
        linkOpacity={0.5}
        linkColor={linkColor}
        linkDirectionalParticles={(link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
          const targetId = typeof link.target === 'string' ? link.target : link.target.id;
          const linkId = `${sourceId}-${targetId}`;
          return highlightedLinks.has(linkId) ? 2 : 0;
        }}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleColor={() => '#ffffff'}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        onBackgroundClick={handleBackgroundClick}
        showNavInfo={false}
        enableNodeDrag={true}
        enableNavigationControls={true}
        enablePointerInteraction={true}
        controlType="orbit"
        rendererConfig={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          failIfMajorPerformanceCaveat: false,
        }}
      />
    </div>
  );
}