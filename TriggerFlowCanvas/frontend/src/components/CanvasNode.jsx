import { memo } from 'react';
import './CanvasNode.css';

const typeColors = {
  start: '#10b981',
  echo: '#6366f1',
  uppercase: '#f59e0b',
  llm: '#8b5cf6',
  output: '#0ea5e9',
};

function CanvasNode({ data, selected }) {
  const color = typeColors[data.type] ?? '#94a3b8';
  return (
    <div
      className="canvas-node"
      style={{
        borderColor: color,
        boxShadow: selected ? `0 0 0 3px ${color}33` : 'none',
      }}
    >
      <div className="canvas-node__name">{data.name}</div>
      <div className="canvas-node__type" style={{ color }}>
        {data.type}
      </div>
    </div>
  );
}

export default memo(CanvasNode);
