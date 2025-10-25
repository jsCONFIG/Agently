import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import CanvasNode from './components/CanvasNode.jsx';
import NodeInspector from './components/NodeInspector.jsx';
import NodeLibrary from './components/NodeLibrary.jsx';
import { NODE_LIBRARY } from './registry.js';
import 'reactflow/dist/style.css';
import './App.css';

const nodeTypes = { canvas: CanvasNode };

function buildNodePayload(node) {
  return {
    id: node.id,
    name: node.data.name?.trim() || node.id,
    type: node.data.type,
    config: node.data.config ?? {},
    position: {
      x: Number(node.position.x.toFixed(2)),
      y: Number(node.position.y.toFixed(2)),
    },
  };
}

function buildEdgePayload(edge) {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
  };
}

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [metadata, setMetadata] = useState({ description: '' });
  const [userInput, setUserInput] = useState('TriggerFlow Canvas');
  const [status, setStatus] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const nodeLibraryEntries = useMemo(
    () =>
      Object.entries(NODE_LIBRARY).map(([key, value]) => ({
        key,
        label: value.label,
        description: value.description,
      })),
    [],
  );

  const hasStartNode = useMemo(
    () => nodes.some((node) => node.data.type === 'start'),
    [nodes],
  );

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  );

  const upsertNode = useCallback(
    (nextNode) => {
      setNodes((previous) => {
        const index = previous.findIndex((node) => node.id === nextNode.id);
        if (index === -1) {
          return [...previous, nextNode];
        }
        const updated = [...previous];
        updated[index] = nextNode;
        return updated;
      });
    },
    [setNodes],
  );

  useEffect(() => {
    async function loadFlow() {
      try {
        const response = await fetch('/api/flow');
        if (!response.ok) {
          throw new Error(`Failed to load flow: ${response.statusText}`);
        }
        const definition = await response.json();
        const flowNodes = (definition.nodes ?? []).map((node) => ({
          id: node.id,
          type: 'canvas',
          position: node.position ?? { x: 0, y: 0 },
          data: {
            name: node.name,
            type: node.type,
            config: node.config ?? {},
          },
        }));
        const flowEdges = (definition.edges ?? []).map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
        }));
        setNodes(flowNodes);
        setEdges(flowEdges);
        setMetadata(definition.metadata ?? { description: '' });
        setStatus(null);
      } catch (error) {
        console.error(error);
        setStatus({ type: 'error', message: error.message });
      } finally {
        setIsLoading(false);
      }
    }

    loadFlow();
  }, [setEdges, setNodes]);

  const addNode = useCallback(
    (type) => {
      if (type === 'start' && hasStartNode) {
        setStatus({ type: 'warning', message: 'Flows can only contain one start node.' });
        return;
      }
      const definition = NODE_LIBRARY[type];
      if (!definition) {
        setStatus({ type: 'error', message: `Unknown node type: ${type}` });
        return;
      }
      const id = `${type}-${Math.random().toString(36).slice(2, 8)}`;
      const position = {
        x: 100 + Math.random() * 200,
        y: 100 + Math.random() * 200,
      };
      const node = {
        id,
        type: 'canvas',
        position,
        data: {
          name: definition.label,
          type,
          config: { ...definition.defaultConfig },
        },
      };
      upsertNode(node);
      setSelectedNodeId(id);
    },
    [hasStartNode, upsertNode],
  );

  const updateSelectedNode = useCallback(
    (updates) => {
      if (!selectedNodeId) {
        return;
      }
      setNodes((current) =>
        current.map((node) => {
          if (node.id !== selectedNodeId) {
            return node;
          }
          const nextData = {
            ...node.data,
            ...('name' in updates ? { name: updates.name } : {}),
            ...('type' in updates ? { type: updates.type } : {}),
          };
          if (updates.config) {
            nextData.config = { ...updates.config };
          }
          return {
            ...node,
            data: nextData,
          };
        }),
      );
    },
    [selectedNodeId, setNodes],
  );

  const deleteSelectedNode = useCallback(() => {
    if (!selectedNodeId) {
      return;
    }
    setNodes((current) => current.filter((node) => node.id !== selectedNodeId));
    setEdges((current) => current.filter((edge) => edge.source !== selectedNodeId && edge.target !== selectedNodeId));
    setSelectedNodeId(null);
  }, [selectedNodeId, setEdges, setNodes]);

  const onConnect = useCallback(
    (connection) => {
      const id = connection.id ?? `${connection.source}-${connection.target}-${Math.random().toString(36).slice(2, 7)}`;
      setEdges((current) =>
        addEdge(
          {
            ...connection,
            id,
          },
          current,
        ),
      );
    },
    [setEdges],
  );

  const onSelectionChange = useCallback(({ nodes: selected }) => {
    setSelectedNodeId(selected?.[0]?.id ?? null);
  }, []);

  const serializedFlow = useMemo(
    () => ({
      nodes: nodes.map(buildNodePayload),
      edges: edges.map(buildEdgePayload),
      metadata,
    }),
    [nodes, edges, metadata],
  );

  const saveFlow = useCallback(async () => {
    setIsSaving(true);
    setStatus(null);
    try {
      const response = await fetch('/api/flow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(serializedFlow),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to save flow');
      }
      setStatus({ type: 'success', message: 'Flow saved successfully.' });
    } catch (error) {
      console.error(error);
      setStatus({ type: 'error', message: error.message });
    } finally {
      setIsSaving(false);
    }
  }, [serializedFlow]);

  const executeFlow = useCallback(async () => {
    setStatus(null);
    setExecutionResult(null);
    try {
      const response = await fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flow: serializedFlow, user_input: userInput }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Failed to execute flow');
      }
      setExecutionResult(payload);
      setStatus({ type: 'success', message: 'Flow executed successfully.' });
    } catch (error) {
      console.error(error);
      setStatus({ type: 'error', message: error.message });
    }
  }, [serializedFlow, userInput]);

  return (
    <div className="app-shell">
      <NodeLibrary
        entries={nodeLibraryEntries}
        onAddNode={addNode}
        disabledTypes={hasStartNode ? ['start'] : []}
      />
      <main className="canvas-container">
        <header className="canvas-toolbar">
          <div className="canvas-toolbar__group">
            <h1>TriggerFlow Canvas</h1>
            {metadata?.description !== undefined && (
              <input
                type="text"
                placeholder="Flow description"
                value={metadata.description ?? ''}
                onChange={(event) => setMetadata({ description: event.target.value })}
              />
            )}
          </div>
          <div className="canvas-toolbar__group">
            <input
              className="canvas-toolbar__user-input"
              type="text"
              value={userInput}
              onChange={(event) => setUserInput(event.target.value)}
              placeholder="User input for execution"
            />
            <button type="button" onClick={saveFlow} disabled={isSaving}>
              {isSaving ? 'Saving…' : 'Save Flow'}
            </button>
            <button type="button" className="primary" onClick={executeFlow}>
              Execute
            </button>
          </div>
        </header>
        <div className="canvas-body">
          {isLoading ? (
            <div className="canvas-loading">Loading canvas…</div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onSelectionChange={onSelectionChange}
              nodeTypes={nodeTypes}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={24} color="#e2e8f0" size={1} />
              <MiniMap pannable zoomable style={{ background: '#fff' }} />
              <Controls position="bottom-right" />
            </ReactFlow>
          )}
        </div>
        <footer className="canvas-footer">
          {status && <span className={`status status--${status.type}`}>{status.message}</span>}
          {executionResult && (
            <div className="execution-result">
              <strong>Result:</strong> {String(executionResult.result)}
              <strong>Runtime:</strong> {executionResult.runtime.toFixed(3)}s
            </div>
          )}
        </footer>
      </main>
      <NodeInspector
        selectedNode={selectedNode}
        onUpdate={updateSelectedNode}
        onDelete={deleteSelectedNode}
      />
    </div>
  );
}

export default App;
