import type { WorkflowDefinition } from '../types';

interface WorkflowListProps {
  workflows: WorkflowDefinition[];
  selectedWorkflowId?: string;
  onSelect: (workflow: WorkflowDefinition) => void;
  onDelete: (workflowId: string) => void;
}

export default function WorkflowList({ workflows, selectedWorkflowId, onSelect, onDelete }: WorkflowListProps) {
  return (
    <div className="workflow-list">
      <h3>已保存流程</h3>
      {workflows.length === 0 && <p style={{ color: '#6b7280' }}>暂无保存的流程。</p>}
      {workflows.map((workflow) => (
        <div
          key={workflow.id}
          className="workflow-card"
          style={{
            borderColor: workflow.id === selectedWorkflowId ? '#2563eb' : '#e5e7eb',
            background: workflow.id === selectedWorkflowId ? '#eff6ff' : '#f9fafb'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>{workflow.name}</strong>
            <button
              type="button"
              onClick={() => onDelete(workflow.id)}
              style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }}
            >
              删除
            </button>
          </div>
          <div style={{ fontSize: '0.85rem', color: '#6b7280', margin: '4px 0 8px' }}>{workflow.description}</div>
          <button type="button" onClick={() => onSelect(workflow)} style={{ width: '100%', padding: '6px 0', borderRadius: '6px', border: '1px solid #2563eb', background: '#2563eb', color: 'white', cursor: 'pointer' }}>
            加载
          </button>
        </div>
      ))}
    </div>
  );
}
