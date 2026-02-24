import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API = 'http://localhost:5000/api';

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [notes, setNotes] = useState([]);
  const [stats, setStats] = useState({});
  const [newTask, setNewTask] = useState('');
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [tasksRes, notesRes, statsRes] = await Promise.all([
        axios.get(`${API}/tasks`),
        axios.get(`${API}/notes`),
        axios.get(`${API}/stats`)
      ]);
      setTasks(tasksRes.data);
      setNotes(notesRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
    }
  };

  const addTask = async () => {
    if (!newTask.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${API}/tasks`, { task: newTask });
      setNewTask('');
      fetchData();
    } catch (err) {
      console.error('Error adding task:', err);
    }
    setLoading(false);
  };

  const deleteTask = async (index) => {
    try {
      await axios.delete(`${API}/tasks/${index}`);
      fetchData();
    } catch (err) {
      console.error('Error deleting task:', err);
    }
  };

  const completeTask = async (index) => {
    try {
      await axios.put(`${API}/tasks/${index}`, { done: !tasks[index].done });
      fetchData();
    } catch (err) {
      console.error('Error updating task:', err);
    }
  };

  const addNote = async () => {
    if (!newNote.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${API}/notes`, { note: newNote });
      setNewNote('');
      fetchData();
    } catch (err) {
      console.error('Error adding note:', err);
    }
    setLoading(false);
  };

  const deleteNote = async (index) => {
    try {
      await axios.delete(`${API}/notes/${index}`);
      fetchData();
    } catch (err) {
      console.error('Error deleting note:', err);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>🎤 Voice Agent Dashboard</h1>
        <p>Manage your tasks and notes</p>
      </header>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-number">{stats.totalTasks || 0}</div>
          <div className="stat-label">Total Tasks</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.pendingTasks || 0}</div>
          <div className="stat-label">Pending</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.completedTasks || 0}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.totalNotes || 0}</div>
          <div className="stat-label">Notes</div>
        </div>
      </div>

      <div className="main-content">
        <div className="section">
          <h2>📋 Tasks</h2>
          
          <div className="input-group">
            <input
              type="text"
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTask()}
              placeholder="Add a new task..."
              className="input"
            />
            <button onClick={addTask} disabled={loading} className="btn btn-primary">
              {loading ? '...' : 'Add'}
            </button>
          </div>

          <div className="task-list">
            {tasks.length === 0 ? (
              <p className="empty">No tasks yet</p>
            ) : (
              tasks.map((task, idx) => (
                <div key={idx} className={`task-item ${task.done ? 'completed' : ''}`}>
                  <input
                    type="checkbox"
                    checked={task.done}
                    onChange={() => completeTask(idx)}
                    className="checkbox"
                  />
                  <span className="task-text">{task.task}</span>
                  <button
                    onClick={() => deleteTask(idx)}
                    className="btn btn-danger btn-small"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="section">
          <h2>📌 Notes</h2>
          
          <div className="input-group">
            <input
              type="text"
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addNote()}
              placeholder="Add a new note..."
              className="input"
            />
            <button onClick={addNote} disabled={loading} className="btn btn-primary">
              {loading ? '...' : 'Add'}
            </button>
          </div>

          <div className="notes-grid">
            {notes.length === 0 ? (
              <p className="empty">No notes yet</p>
            ) : (
              notes.map((note, idx) => (
                <div key={idx} className="note-card">
                  <p>{note.note}</p>
                  <button
                    onClick={() => deleteNote(idx)}
                    className="btn btn-danger btn-small"
                  >
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
