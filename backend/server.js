const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Path to agent memory (shared with Python agent)
const MEMORY_FILE = path.join(__dirname, '../agent_memory.json');

// Helper function to read memory
function readMemory() {
  try {
    if (fs.existsSync(MEMORY_FILE)) {
      const data = fs.readFileSync(MEMORY_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error reading memory:', error);
  }
  return { tasks: [], notes: [] };
}

// Helper function to write memory
function writeMemory(data) {
  try {
    fs.writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2));
    return true;
  } catch (error) {
    console.error('Error writing memory:', error);
    return false;
  }
}

// ============================================================
// TASKS ENDPOINTS
// ============================================================

// GET all tasks
app.get('/api/tasks', (req, res) => {
  const memory = readMemory();
  const tasks = memory.tasks || [];
  res.json(tasks);
});

// GET pending tasks only
app.get('/api/tasks/pending', (req, res) => {
  const memory = readMemory();
  const tasks = (memory.tasks || []).filter(t => !t.done);
  res.json(tasks);
});

// POST - Add new task
app.post('/api/tasks', (req, res) => {
  const { task } = req.body;
  
  if (!task) {
    return res.status(400).json({ error: 'Task text required' });
  }

  const memory = readMemory();
  const newTask = {
    task: task,
    done: false,
    added: new Date().toISOString()
  };

  memory.tasks = (memory.tasks || []);
  memory.tasks.push(newTask);

  if (writeMemory(memory)) {
    res.status(201).json(newTask);
  } else {
    res.status(500).json({ error: 'Failed to save task' });
  }
});

// PUT - Complete/update task
app.put('/api/tasks/:index', (req, res) => {
  const { index } = req.params;
  const { done } = req.body;

  const memory = readMemory();
  const tasks = memory.tasks || [];

  if (index < 0 || index >= tasks.length) {
    return res.status(404).json({ error: 'Task not found' });
  }

  tasks[index].done = done;
  memory.tasks = tasks;

  if (writeMemory(memory)) {
    res.json(tasks[index]);
  } else {
    res.status(500).json({ error: 'Failed to update task' });
  }
});

// DELETE - Remove task
app.delete('/api/tasks/:index', (req, res) => {
  const { index } = req.params;

  const memory = readMemory();
  const tasks = memory.tasks || [];

  if (index < 0 || index >= tasks.length) {
    return res.status(404).json({ error: 'Task not found' });
  }

  const deleted = tasks.splice(index, 1);
  memory.tasks = tasks;

  if (writeMemory(memory)) {
    res.json({ deleted: deleted[0] });
  } else {
    res.status(500).json({ error: 'Failed to delete task' });
  }
});

// ============================================================
// NOTES ENDPOINTS
// ============================================================

// GET all notes
app.get('/api/notes', (req, res) => {
  const memory = readMemory();
  const notes = memory.notes || [];
  res.json(notes);
});

// POST - Add new note
app.post('/api/notes', (req, res) => {
  const { note } = req.body;

  if (!note) {
    return res.status(400).json({ error: 'Note text required' });
  }

  const memory = readMemory();
  const newNote = {
    note: note,
    time: new Date().toISOString()
  };

  memory.notes = (memory.notes || []);
  memory.notes.push(newNote);

  if (writeMemory(memory)) {
    res.status(201).json(newNote);
  } else {
    res.status(500).json({ error: 'Failed to save note' });
  }
});

// DELETE - Remove note
app.delete('/api/notes/:index', (req, res) => {
  const { index } = req.params;

  const memory = readMemory();
  const notes = memory.notes || [];

  if (index < 0 || index >= notes.length) {
    return res.status(404).json({ error: 'Note not found' });
  }

  const deleted = notes.splice(index, 1);
  memory.notes = notes;

  if (writeMemory(memory)) {
    res.json({ deleted: deleted[0] });
  } else {
    res.status(500).json({ error: 'Failed to delete note' });
  }
});

// ============================================================
// STATS ENDPOINT
// ============================================================

// GET statistics
app.get('/api/stats', (req, res) => {
  const memory = readMemory();
  const tasks = memory.tasks || [];
  const notes = memory.notes || [];
  
  const stats = {
    totalTasks: tasks.length,
    completedTasks: tasks.filter(t => t.done).length,
    pendingTasks: tasks.filter(t => !t.done).length,
    totalNotes: notes.length
  };

  res.json(stats);
});

// ============================================================
// HEALTH CHECK
// ============================================================

app.get('/api/health', (req, res) => {
  res.json({ status: 'Server running', port: PORT });
});

// ============================================================
// START SERVER
// ============================================================

app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════╗
║  Voice Agent API Server Running        ║
║  http://localhost:${PORT}              ║
║  Press Ctrl+C to stop                  ║
╚════════════════════════════════════════╝
  `);
  console.log('Endpoints:');
  console.log('  GET  /api/tasks');
  console.log('  POST /api/tasks');
  console.log('  PUT  /api/tasks/:index');
  console.log('  DELETE /api/tasks/:index');
  console.log('  GET  /api/notes');
  console.log('  POST /api/notes');
  console.log('  DELETE /api/notes/:index');
  console.log('  GET  /api/stats');
  console.log('  GET  /api/health');
});
