import type { CanvasNode, NodeTemplate } from '../types';

interface PropertiesPanelProps {
  node?: CanvasNode;
  template?: NodeTemplate;
  onChange: (configuration: Record<string, unknown>) => void;
  onDeleteNode: () => void;
}

function renderField(
  key: string,
  value: unknown,
  onChange: (key: string, value: unknown) => void
): JSX.Element {
  const typedValue = typeof value === 'string' || typeof value === 'number' ? value : '';
  return (
    <div key={key} className="property-field">
      <label htmlFor={`prop-${key}`}>{key}</label>
      <input
        id={`prop-${key}`}
        type="text"
        value={typedValue}
        onChange={(event) => onChange(key, event.target.value)}
      />
    </div>
  );
}

export default function PropertiesPanel({ node, template, onChange, onDeleteNode }: PropertiesPanelProps) {
  if (!node || !template) {
    return (
      <div className="properties-panel">
        <h2>属性</h2>
        <p>选择画布中的节点以编辑其属性。</p>
      </div>
    );
  }

  const handleChange = (key: string, value: unknown) => {
    onChange({ ...node.configuration, [key]: value });
  };

  return (
    <div className="properties-panel">
      <h2>{node.label}</h2>
      <p style={{ color: '#6b7280' }}>{template.description}</p>
      {Object.entries(node.configuration).map(([key, value]) => renderField(key, value, handleChange))}
      <button type="button" onClick={onDeleteNode} style={{ marginTop: '12px', background: '#ef4444', color: 'white', padding: '8px 12px', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
        删除节点
      </button>
    </div>
  );
}
