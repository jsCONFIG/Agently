import { useCallback, useEffect, useMemo, useState } from 'react';
import Canvas from './components/Canvas';
import NodeLibrary from './components/NodeLibrary';
import PropertiesPanel from './components/PropertiesPanel';
import WorkflowList from './components/WorkflowList';
import {
  createLogStream,
  deleteWorkflow,
  executeWorkflow,
  listWorkflows,
  saveWorkflow
} from './services/api';
import type { CanvasNode, NodeTemplate, WorkflowDefinition } from './types';

function generateId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

const DEFAULT_WORKFLOW: WorkflowDefinition = {
  id: '',
  name: '未命名流程',
  description: '新的 TriggerFlow 流程',
  nodes: [],
  edges: []
};

function createEmptyWorkflow(): WorkflowDefinition {
  return {
    ...DEFAULT_WORKFLOW,
    id: '',
    nodes: [],
    edges: []
  };
}

export default function App() {
  const templates = useMemo<NodeTemplate[]>(
    () => [
      {
        type: 'trigger.http',
        label: 'HTTP 触发器',
        description: '监听 HTTP 请求并触发工作流。',
        defaultConfiguration: {
          method: 'POST',
          path: '/webhook'
        },
        ports: [
          { id: 'out', label: '输出', direction: 'output' }
        ]
      },
      {
        type: 'action.chat_completion',
        label: '对话生成',
        description: '调用 TriggerFlow 核心进行大模型对话。',
        defaultConfiguration: {
          prompt: '你好 TriggerFlow',
          model: 'gpt-4o-mini'
        },
        ports: [
          { id: 'in', label: '输入', direction: 'input' },
          { id: 'out', label: '输出', direction: 'output' }
        ]
      },
      {
        type: 'action.http_request',
        label: 'HTTP 请求',
        description: '向外部 API 发送请求并返回响应。',
        defaultConfiguration: {
          url: 'https://example.com/api',
          method: 'GET'
        },
        ports: [
          { id: 'in', label: '输入', direction: 'input' },
          { id: 'out', label: '输出', direction: 'output' }
        ]
      }
    ],
    []
  );

  const [workflow, setWorkflow] = useState<WorkflowDefinition>(createEmptyWorkflow());
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string>();
  const [logs, setLogs] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    listWorkflows()
      .then(setWorkflows)
      .catch((error) => console.error('Failed to load workflows', error));
  }, []);

  const selectedNode = useMemo(() => nodes.find((node) => node.id === selectedNodeId), [nodes, selectedNodeId]);
  const selectedTemplate = useMemo(
    () => templates.find((template) => template.type === selectedNode?.type),
    [templates, selectedNode?.type]
  );

  const handleAddNode = useCallback(
    (template: NodeTemplate) => {
      const node: CanvasNode = {
        id: generateId('node'),
        type: template.type,
        label: template.label,
        x: 80 + nodes.length * 40,
        y: 120 + nodes.length * 40,
        configuration: { ...template.defaultConfiguration },
        ports: template.ports
      };
      setNodes((prev) => [...prev, node]);
      setSelectedNodeId(node.id);
    },
    [nodes.length]
  );

  const handleUpdateNodePosition = useCallback((nodeId: string, x: number, y: number) => {
    setNodes((prev) => prev.map((node) => (node.id === nodeId ? { ...node, x, y } : node)));
  }, []);

  const handleUpdateConfiguration = useCallback(
    (configuration: Record<string, unknown>) => {
      if (!selectedNodeId) return;
      setNodes((prev) => prev.map((node) => (node.id === selectedNodeId ? { ...node, configuration } : node)));
    },
    [selectedNodeId]
  );

  const handleDeleteNode = useCallback(() => {
    if (!selectedNodeId) return;
    setNodes((prev) => prev.filter((node) => node.id !== selectedNodeId));
    setSelectedNodeId(undefined);
  }, [selectedNodeId]);

  const handleWorkflowMetaChange = useCallback((key: 'name' | 'description', value: string) => {
    setWorkflow((prev) => ({ ...prev, [key]: value }));
  }, []);

  const refreshWorkflows = useCallback(() => {
    listWorkflows()
      .then(setWorkflows)
      .catch((error) => console.error('Failed to refresh workflows', error));
  }, []);

  const handleSaveWorkflow = useCallback(async () => {
    setIsSaving(true);
    try {
      const payload: WorkflowDefinition = {
        ...workflow,
        nodes,
        edges: workflow.edges
      };
      const saved = await saveWorkflow(payload);
      setWorkflow(saved);
      refreshWorkflows();
      return saved;
    } catch (error) {
      console.error('Failed to save workflow', error);
      return undefined;
    } finally {
      setIsSaving(false);
    }
  }, [nodes, refreshWorkflows, workflow]);

  const handleLoadWorkflow = useCallback((loaded: WorkflowDefinition) => {
    const normalized = loaded.id
      ? { ...loaded, nodes: loaded.nodes ?? [], edges: loaded.edges ?? [] }
      : createEmptyWorkflow();
    setWorkflow(normalized);
    setNodes(normalized.nodes.map((node) => ({ ...node, configuration: { ...node.configuration } })));
    setSelectedNodeId(undefined);
  }, []);

  const handleDeleteWorkflow = useCallback(
    async (workflowId: string) => {
      await deleteWorkflow(workflowId);
      if (workflow.id === workflowId) {
        setWorkflow(createEmptyWorkflow());
        setNodes([]);
        setSelectedNodeId(undefined);
      }
      refreshWorkflows();
    },
    [refreshWorkflows, workflow.id]
  );

  const handleExecuteWorkflow = useCallback(async () => {
    let activeWorkflow = workflow;
    if (!activeWorkflow.id) {
      const saved = await handleSaveWorkflow();
      if (!saved) return;
      activeWorkflow = saved;
    }
    setIsExecuting(true);
    setLogs([]);
    try {
      const { runId } = await executeWorkflow(activeWorkflow.id);
      const eventSource = createLogStream(runId);
      eventSource.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { message: string };
        setLogs((prev) => [...prev, payload.message]);
      };
      eventSource.onerror = () => {
        eventSource.close();
        setIsExecuting(false);
      };
    } catch (error) {
      console.error('Workflow execution failed', error);
      setIsExecuting(false);
    }
  }, [handleSaveWorkflow, workflow.id, workflow.name]);

  return (
    <div className="app-shell">
      <header className="toolbar">
        <strong>TriggerFlow Canvas</strong>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '0.75rem', color: '#d1d5db' }}>名称</span>
          <input
            type="text"
            value={workflow.name}
            onChange={(event) => handleWorkflowMetaChange('name', event.target.value)}
            style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid #374151', minWidth: '220px' }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '0.75rem', color: '#d1d5db' }}>描述</span>
          <input
            type="text"
            value={workflow.description ?? ''}
            onChange={(event) => handleWorkflowMetaChange('description', event.target.value)}
            style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid #374151', minWidth: '280px' }}
          />
        </label>
        <button
          type="button"
          onClick={handleSaveWorkflow}
          disabled={isSaving}
          style={{ padding: '8px 14px', borderRadius: '6px', border: 'none', background: '#2563eb', color: 'white', cursor: 'pointer' }}
        >
          {isSaving ? '保存中…' : '保存流程'}
        </button>
        <button
          type="button"
          onClick={handleExecuteWorkflow}
          disabled={isExecuting}
          style={{ padding: '8px 14px', borderRadius: '6px', border: 'none', background: '#10b981', color: 'white', cursor: 'pointer' }}
        >
          {isExecuting ? '执行中…' : '执行流程'}
        </button>
      </header>
      <NodeLibrary templates={templates} onAddNode={handleAddNode} />
      <div style={{ gridArea: 'canvas', position: 'relative' }}>
        <Canvas
          nodes={nodes}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
          onUpdateNodePosition={handleUpdateNodePosition}
        />
        <div className="canvas-controls">
          <button type="button" onClick={() => handleLoadWorkflow(DEFAULT_WORKFLOW)}>清空画布</button>
        </div>
      </div>
      <div style={{ gridArea: 'properties', display: 'flex', flexDirection: 'column' }}>
        <PropertiesPanel
          node={selectedNode}
          template={selectedTemplate}
          onChange={handleUpdateConfiguration}
          onDeleteNode={handleDeleteNode}
        />
        <WorkflowList
          workflows={workflows}
          selectedWorkflowId={workflow.id}
          onSelect={handleLoadWorkflow}
          onDelete={handleDeleteWorkflow}
        />
        <div style={{ marginTop: 'auto' }}>
          <h3>运行日志</h3>
          <div style={{
            height: '160px',
            overflowY: 'auto',
            background: '#111827',
            color: '#f3f4f6',
            padding: '8px',
            borderRadius: '6px',
            fontFamily: 'ui-monospace, SFMono-Regular'
          }}>
            {logs.length === 0 && <div style={{ color: '#9ca3af' }}>等待执行日志…</div>}
            {logs.map((line, index) => (
              <div key={`${line}-${index}`}>{line}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
