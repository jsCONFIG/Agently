import type { WorkflowDefinition } from '../types';

const API_BASE = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Request failed');
  }

  return (await response.json()) as T;
}

export async function listWorkflows(): Promise<WorkflowDefinition[]> {
  const response = await fetch(`${API_BASE}/workflows`);
  return handleResponse<WorkflowDefinition[]>(response);
}

export async function saveWorkflow(workflow: WorkflowDefinition): Promise<WorkflowDefinition> {
  const method = workflow.id ? 'PUT' : 'POST';
  const endpoint = workflow.id ? `${API_BASE}/workflows/${workflow.id}` : `${API_BASE}/workflows`;
  const response = await fetch(endpoint, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow)
  });
  return handleResponse<WorkflowDefinition>(response);
}

export async function deleteWorkflow(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/workflows/${id}`, { method: 'DELETE' });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Failed to delete workflow');
  }
}

export async function executeWorkflow(id: string): Promise<{ runId: string }> {
  const response = await fetch(`${API_BASE}/workflows/${id}/execute`, { method: 'POST' });
  return handleResponse<{ runId: string }>(response);
}

export function createLogStream(runId: string, signal?: AbortSignal): EventSource {
  const url = `${API_BASE}/runs/${runId}/logs`;
  const eventSource = new EventSource(url);
  if (signal) {
    signal.addEventListener('abort', () => eventSource.close());
  }
  return eventSource;
}
