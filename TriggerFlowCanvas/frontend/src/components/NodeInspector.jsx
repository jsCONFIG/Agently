import { useMemo } from 'react';
import { NODE_LIBRARY } from '../registry.js';
import './NodeInspector.css';

function NodeInspector({ selectedNode, onUpdate, onDelete }) {
  const definition = useMemo(() => {
    if (!selectedNode) {
      return null;
    }
    return NODE_LIBRARY[selectedNode.data.type] ?? null;
  }, [selectedNode]);

  if (!selectedNode) {
    return (
      <div className="node-inspector">
        <h2>Inspector</h2>
        <p>Select a node to edit its name and configuration.</p>
      </div>
    );
  }

  const config = selectedNode.data.config ?? {};

  return (
    <div className="node-inspector">
      <h2>Inspector</h2>
      <div className="node-inspector__section">
        <label htmlFor="node-name">Display name</label>
        <input
          id="node-name"
          type="text"
          value={selectedNode.data.name}
          onChange={(event) => onUpdate({ name: event.target.value })}
        />
      </div>
      <div className="node-inspector__section">
        <span className="node-inspector__type">{selectedNode.data.type}</span>
        <p className="node-inspector__hint">{definition?.description}</p>
      </div>
      {definition?.configSchema?.map((field) => (
        <div key={field.key} className="node-inspector__section">
          <label htmlFor={`cfg-${field.key}`}>{field.label}</label>
          {field.type === 'textarea' ? (
            <textarea
              id={`cfg-${field.key}`}
              rows={3}
              value={config[field.key] ?? ''}
              placeholder={field.placeholder}
              onChange={(event) =>
                onUpdate({
                  config: {
                    ...config,
                    [field.key]: event.target.value,
                  },
                })
              }
            />
          ) : (
            <input
              id={`cfg-${field.key}`}
              type="text"
              value={config[field.key] ?? ''}
              placeholder={field.placeholder}
              onChange={(event) =>
                onUpdate({
                  config: {
                    ...config,
                    [field.key]: event.target.value,
                  },
                })
              }
            />
          )}
        </div>
      ))}
      <button type="button" className="node-inspector__delete" onClick={onDelete}>
        Delete node
      </button>
    </div>
  );
}

export default NodeInspector;
