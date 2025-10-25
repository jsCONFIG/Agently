import { useCallback, useRef } from 'react';
import type { CanvasNode } from '../types';

interface CanvasProps {
  nodes: CanvasNode[];
  selectedNodeId?: string;
  onSelectNode: (nodeId: string) => void;
  onUpdateNodePosition: (nodeId: string, x: number, y: number) => void;
}

type DragContext = {
  nodeId: string;
  offsetX: number;
  offsetY: number;
};

export default function Canvas({ nodes, selectedNodeId, onSelectNode, onUpdateNodePosition }: CanvasProps) {
  const dragContext = useRef<DragContext | null>(null);

  const handlePointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>, node: CanvasNode) => {
      const boundingRect = event.currentTarget.getBoundingClientRect();
      dragContext.current = {
        nodeId: node.id,
        offsetX: event.clientX - boundingRect.left,
        offsetY: event.clientY - boundingRect.top
      };
      onSelectNode(node.id);
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [onSelectNode]
  );

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!dragContext.current) return;
      const canvas = event.currentTarget.closest('.canvas');
      if (!(canvas instanceof HTMLElement)) return;
      const { left, top } = canvas.getBoundingClientRect();
      const x = event.clientX - left - dragContext.current.offsetX;
      const y = event.clientY - top - dragContext.current.offsetY;
      onUpdateNodePosition(dragContext.current.nodeId, Math.max(0, x), Math.max(0, y));
    },
    [onUpdateNodePosition]
  );

  const handlePointerUp = useCallback(() => {
    dragContext.current = null;
  }, []);

  return (
    <div className="canvas" onPointerMove={handlePointerMove} onPointerUp={handlePointerUp}>
      {nodes.map((node) => (
        <div
          key={node.id}
          role="button"
          tabIndex={0}
          className={`canvas-node ${node.id === selectedNodeId ? 'selected' : ''}`}
          style={{ left: node.x, top: node.y }}
          onPointerDown={(event) => handlePointerDown(event, node)}
          onClick={() => onSelectNode(node.id)}
        >
          <div style={{ fontWeight: 600 }}>{node.label}</div>
          <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{node.type}</div>
        </div>
      ))}
      {nodes.length === 0 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            color: '#6b7280'
          }}
        >
          从左侧节点库中添加节点开始构建流程。
        </div>
      )}
    </div>
  );
}
