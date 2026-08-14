const API_URL = 'http://localhost:8000/api';

export const generatePlan = async (userInput) => {
  const res = await fetch(`${API_URL}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput }),
  });
  return res.json();
};

export const buildApp = async (userInput, plan) => {
  const res = await fetch(`${API_URL}/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput, plan }),
  });
  return res.json();
};

export const fetchFiles = async () => {
  const res = await fetch(`${API_URL}/files`);
  return res.json();
};

export const fetchFileContent = async (path) => {
  const res = await fetch(`${API_URL}/file?path=${encodeURIComponent(path)}`);
  if (!res.ok) throw new Error('File not found');
  return res.json();
};

export const saveFile = async (fileName, content) => {
  const res = await fetch(`${API_URL}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_name: fileName, content }),
  });
  return res.json();
};

export const runCommand = async (cmd) => {
  const res = await fetch(`${API_URL}/terminal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cmd }),
  });
  return res.json();
};

export const editFile = async (fileName, instruction) => {
  const res = await fetch(`${API_URL}/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_name: fileName, instruction }),
  });
  return res.json();
};

export const startDevServer = async () => {
  const res = await fetch(`${API_URL}/devserver`, {
    method: 'POST'
  });
  return res.json();
};

export const updateApp = async (userInput) => {
  const res = await fetch(`${API_URL}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput }),
  });
  return res.json();
};
