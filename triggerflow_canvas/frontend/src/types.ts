export type NodePortDirection = 'input' | 'output';

export interface NodePort {
  id: string;
  label: string;
  direction: NodePortDirection;
}

export interface CanvasNode {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
  configuration: Record<string, unknown>;
  ports: NodePort[];
}

export interface NodeTemplate {
  type: string;
  label: string;
  description: string;
  defaultConfiguration: Record<string, unknown>;
  ports: NodePort[];
}

export interface WorkflowEdge {
  id: string;
  from: { nodeId: string; portId: string };
  to: { nodeId: string; portId: string };
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  nodes: CanvasNode[];
  edges: WorkflowEdge[];
  createdAt?: string;
  updatedAt?: string;
}
