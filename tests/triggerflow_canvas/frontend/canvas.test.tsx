import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import Canvas from '../../../triggerflow_canvas/frontend/src/components/Canvas';
import type { CanvasNode } from '../../../triggerflow_canvas/frontend/src/types';

document.body.innerHTML = '<div id="root"></div>';

const createNode = (overrides: Partial<CanvasNode> = {}): CanvasNode => ({
  id: 'node-1',
  type: 'action.chat_completion',
  label: '聊天',
  x: 120,
  y: 80,
  configuration: {},
  ports: [],
  ...overrides
});

it('renders empty state hint when there are no nodes', () => {
  const onSelect = vi.fn();
  const onUpdate = vi.fn();

  render(
    <Canvas nodes={[]} onSelectNode={onSelect} onUpdateNodePosition={onUpdate} />,
    { container: document.getElementById('root') as HTMLElement }
  );

  expect(screen.getByText('从左侧节点库中添加节点开始构建流程。')).toBeInTheDocument();
  expect(onSelect).not.toHaveBeenCalled();
  expect(onUpdate).not.toHaveBeenCalled();
});

it('highlights selected node and updates position when dragged', () => {
  const onSelect = vi.fn();
  const onUpdate = vi.fn();
  const node = createNode();

  const { container } = render(
    <Canvas
      nodes={[node]}
      selectedNodeId="node-1"
      onSelectNode={onSelect}
      onUpdateNodePosition={onUpdate}
    />,
    { container: document.getElementById('root') as HTMLElement }
  );

  const canvasNode = screen.getByRole('button', { name: /聊天/ });
  expect(canvasNode).toHaveClass('selected');

  Object.defineProperty(canvasNode, 'getBoundingClientRect', {
    value: () => ({
      x: node.x,
      y: node.y,
      top: node.y,
      left: node.x,
      right: node.x + 150,
      bottom: node.y + 40,
      width: 150,
      height: 40,
      toJSON: () => ''
    })
  });

  const canvas = container.querySelector('.canvas') as HTMLElement;
  Object.defineProperty(canvas, 'getBoundingClientRect', {
    value: () => ({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 1200,
      bottom: 900,
      width: 1200,
      height: 900,
      toJSON: () => ''
    })
  });

  fireEvent.pointerDown(canvasNode, { pointerId: 1, clientX: 140, clientY: 100 });
  fireEvent.pointerMove(canvas, { pointerId: 1, clientX: 260, clientY: 220 });
  fireEvent.pointerUp(canvas);

  expect(onSelect).toHaveBeenCalledWith('node-1');
  expect(onUpdate).toHaveBeenCalledWith('node-1', 120, 120);
});

it('selects node on click when not already selected', () => {
  const onSelect = vi.fn();
  const onUpdate = vi.fn();
  const node = createNode({ id: 'node-2', label: 'HTTP 触发器' });

  render(
    <Canvas
      nodes={[node]}
      selectedNodeId="node-1"
      onSelectNode={onSelect}
      onUpdateNodePosition={onUpdate}
    />,
    { container: document.getElementById('root') as HTMLElement }
  );

  const canvasNode = screen.getByRole('button', { name: /HTTP 触发器/ });
  fireEvent.click(canvasNode);

  expect(onSelect).toHaveBeenCalledWith('node-2');
  expect(onUpdate).not.toHaveBeenCalled();
});
