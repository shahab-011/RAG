import React, { useState, useEffect, useRef } from 'react';
import {
  BookOpen,
  Send,
  Upload,
  FileText,
  Sparkles,
  Bot,
  User,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Trash2,
  Cpu,
  Layers,
  Zap,
  Loader2
} from 'lucide-react';
import './App.css';

const API_BASE = 'http://127.0.0.1:8765/api';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [expandedSources, setExpandedSources] = useState({});

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    fetchHealth();
    fetchDocuments();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      }
    } catch (err) {
      console.error('API connection failed:', err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus(`Uploading & Indexing ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadStatus(`Indexed ${data.chunks} chunks across ${data.pages} pages!`);
        fetchDocuments();
        setTimeout(() => setUploadStatus(''), 4000);
      } else {
        const errData = await res.json();
        setUploadStatus(`Error: ${errData.detail || 'Upload failed'}`);
      }
    } catch (err) {
      setUploadStatus(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async (questionText = input) => {
    const query = questionText.trim();
    if (!query || loading) return;

    const userMessage = { id: Date.now(), sender: 'user', text: query };
    setMessages((prev) => [...prev, userMessage]);
    if (questionText === input) setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, k: 4 }),
      });

      if (res.ok) {
        const data = await res.json();
        const aiMessage = {
          id: Date.now() + 1,
          sender: 'ai',
          text: data.answer,
          sources: data.sources || [],
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        const errData = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            sender: 'ai',
            text: `Error: ${errData.detail || 'Failed to generate answer'}`,
            sources: [],
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'ai',
          text: 'Network error connecting to RAG backend server.',
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const handleSuggestionClick = (promptText) => {
    handleSend(promptText);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header glass-panel">
        <div className="header-left">
          <div className="logo-icon">
            <BookOpen size={22} />
          </div>
          <div>
            <h1 className="app-title gradient-text">Student RAG Studio</h1>
          </div>
        </div>

        <div className="header-right">
          <span className="badge badge-model">
            <Cpu size={12} /> Local HF: all-MiniLM-L6-v2
          </span>
          <span className="badge badge-free">
            <Zap size={12} /> 0 API Costs
          </span>
          <span className="badge badge-vector">
            <Layers size={12} /> ChromaDB Vectorstore
          </span>
          <div className="pulsing-dot" title="Local Engine Active"></div>
        </div>
      </header>

      {/* Main Main Grid */}
      <main className="app-main">
        {/* Sidebar: Documents & Upload */}
        <aside className="sidebar glass-panel">
          <div className="sidebar-title">
            <BookOpen size={18} /> My Textbook Library
          </div>

          {/* Upload Dropzone */}
          <label className="upload-dropzone">
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              style={{ display: 'none' }}
            />
            {uploading ? (
              <Loader2 size={24} className="spinner upload-icon" />
            ) : (
              <Upload size={24} className="upload-icon" />
            )}
            <div className="upload-text">
              {uploading ? 'Processing File...' : 'Upload Book / Document'}
            </div>
            <div className="upload-subtext">Supports PDF & TXT files</div>
          </label>

          {uploadStatus && (
            <div
              style={{
                fontSize: '0.78rem',
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                color: '#a5b4fc',
              }}
            >
              {uploadStatus}
            </div>
          )}

          {/* Document List */}
          <div className="doc-list">
            {documents.length === 0 ? (
              <div
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  textAlign: 'center',
                  padding: '16px 0',
                }}
              >
                No documents uploaded yet.
              </div>
            ) : (
              documents.map((doc, idx) => (
                <div className="doc-card" key={idx}>
                  <div className="doc-icon">
                    <FileText size={18} />
                  </div>
                  <div className="doc-info">
                    <div className="doc-name">{doc.filename}</div>
                    <div className="doc-meta">
                      <span>{doc.pages > 0 ? `${doc.pages} Pages` : 'Text File'}</span>
                      <span>•</span>
                      <span>{doc.size_mb} MB</span>
                    </div>
                  </div>
                  <CheckCircle2 size={16} style={{ color: '#10b981' }} />
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Chat Interface */}
        <section className="chat-container glass-panel">
          <div className="chat-header">
            <div className="chat-header-title">
              <Sparkles size={18} style={{ color: '#818cf8' }} /> Study Assistant Chat
            </div>
            {messages.length > 0 && (
              <button className="btn-secondary" onClick={clearChat} title="Clear conversation">
                <Trash2 size={14} /> Clear Chat
              </button>
            )}
          </div>

          <div className="messages-area">
            {messages.length === 0 ? (
              <div className="welcome-card glass-panel">
                <div className="welcome-icon">
                  <Bot size={32} />
                </div>
                <h2 className="welcome-title">Ask Anything About Your Textbooks</h2>
                <p className="welcome-subtitle">
                  Upload your study books or documents on the left. The AI will read your documents using local Hugging Face embeddings and provide answers directly with page citations.
                </p>

                <div className="suggestions-grid">
                  <button
                    className="suggestion-pill"
                    onClick={() => handleSuggestionClick('What is deep learning?')}
                  >
                    💡 What is deep learning?
                  </button>
                  <button
                    className="suggestion-pill"
                    onClick={() => handleSuggestionClick('Explain gradient descent in simple terms')}
                  >
                    📐 Explain gradient descent in simple terms
                  </button>
                  <button
                    className="suggestion-pill"
                    onClick={() => handleSuggestionClick('What are artificial neural networks?')}
                  >
                    🧠 What are artificial neural networks?
                  </button>
                  <button
                    className="suggestion-pill"
                    onClick={() => handleSuggestionClick('Summarize the main concepts in the document')}
                  >
                    📑 Summarize the main concepts in the book
                  </button>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div className={`message-wrapper ${msg.sender}`} key={msg.id}>
                  <div className={`message-avatar ${msg.sender}`}>
                    {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </div>
                  <div className="message-bubble">
                    <div style={{ whitespace: 'pre-wrap' }}>{msg.text}</div>

                    {/* Book Citations */}
                    {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                      <div className="citation-box">
                        <button
                          className="citation-toggle"
                          onClick={() => toggleSources(msg.id)}
                        >
                          <BookOpen size={14} />
                          {msg.sources.length} Book Source Citations
                          {expandedSources[msg.id] ? (
                            <ChevronUp size={14} />
                          ) : (
                            <ChevronDown size={14} />
                          )}
                        </button>

                        {expandedSources[msg.id] && (
                          <div className="citation-list">
                            {msg.sources.map((src, sIdx) => (
                              <div className="citation-item" key={sIdx}>
                                <div className="citation-header">
                                  <span>📖 {src.source}</span>
                                  <span>Page {src.page}</span>
                                </div>
                                <div className="citation-content">"{src.content}"</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {loading && (
              <div className="message-wrapper ai">
                <div className="message-avatar ai">
                  <Bot size={18} />
                </div>
                <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Loader2 size={16} className="spinner" />
                  <span>Searching textbooks with Hugging Face vectors...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="chat-input-area">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask a question about your books (e.g. What is deep learning?)..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={loading}
            />
            <button
              className="btn-primary"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              <Send size={16} /> Ask AI
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
