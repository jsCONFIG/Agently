import './NodeLibrary.css';

function NodeLibrary({ entries, onAddNode, disabledTypes = [] }) {
  return (
    <div className="node-library">
      <h2>Node Library</h2>
      <p>Select a block and drop it onto the canvas.</p>
      <div className="node-library__items">
        {entries.map(({ key, label, description }) => {
          const disabled = disabledTypes.includes(key);
          return (
            <button
              key={key}
              type="button"
              className="node-library__item"
              onClick={() => onAddNode(key)}
              disabled={disabled}
              title={description}
            >
              <span className="node-library__item-label">{label}</span>
              <span className="node-library__item-type">{key}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default NodeLibrary;
