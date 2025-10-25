export const NODE_LIBRARY = {
  start: {
    label: 'Start',
    description: 'Entry point of the flow. Exactly one start node is required.',
    defaultConfig: {},
  },
  echo: {
    label: 'Echo',
    description: 'Render a template that can reference {value} or {name}.',
    defaultConfig: { template: '{value}' },
    configSchema: [
      {
        key: 'template',
        label: 'Template',
        placeholder: 'Hello {value}',
        type: 'textarea',
      },
    ],
  },
  uppercase: {
    label: 'Uppercase',
    description: 'Convert the input text to uppercase.',
    defaultConfig: {},
    configSchema: [],
  },
  llm: {
    label: 'LLM Prompt',
    description: 'Simulate an LLM call with a prompt template.',
    defaultConfig: {
      prompt: 'Respond to: {value}',
      suffix: ' (simulated)',
    },
    configSchema: [
      {
        key: 'prompt',
        label: 'Prompt',
        placeholder: 'Summarize {value}',
        type: 'textarea',
      },
      {
        key: 'suffix',
        label: 'Suffix',
        placeholder: ' (simulated)',
        type: 'text',
      },
    ],
  },
  output: {
    label: 'Output',
    description: 'Expose the value as a named output in the execution result.',
    defaultConfig: { label: 'result' },
    configSchema: [
      {
        key: 'label',
        label: 'Output label',
        placeholder: 'result',
        type: 'text',
      },
    ],
  },
};

export const NODE_TYPES = Object.keys(NODE_LIBRARY);
