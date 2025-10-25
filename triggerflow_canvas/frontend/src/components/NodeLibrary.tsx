import type { NodeTemplate } from '../types';

interface NodeLibraryProps {
  templates: NodeTemplate[];
  onAddNode: (template: NodeTemplate) => void;
}

export default function NodeLibrary({ templates, onAddNode }: NodeLibraryProps) {
  return (
    <div className="node-library">
      <h2>节点库</h2>
      <p>拖拽或点击节点以加入画布。</p>
      <div className="node-list">
        {templates.map((template) => (
          <button key={template.type} type="button" onClick={() => onAddNode(template)}>
            <strong>{template.label}</strong>
            <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{template.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
