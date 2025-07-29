import React, { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './AIChat.css';

const AIChat = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  // اسکرول به پایین
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // بارگذاری لیست سشن‌ها
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await api.get('/chat/sessions/', { withCredentials: true });
      setSessions(response.data.data || []);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError('خطا در بارگذاری لیست چت‌ها');
    }
  };

  // بارگذاری پیام‌های یک سشن
  const fetchSessionMessages = async (sessionId) => {
    try {
      const response = await api.get(`/chat/sessions/${sessionId}/messages/`, {
        withCredentials: true,
      });
      if (response.data.success && Array.isArray(response.data.data)) {
        setMessages(response.data.data);
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
      setError('خطا در بارگذاری پیام‌ها');
      setMessages([]);
    }
  };

  // انتخاب یک سشن
  const handleSessionSelect = async (session) => {
    setCurrentSession(session);
    await fetchSessionMessages(session.id);
    setSidebarOpen(false);
  };

  // چت جدید (فقط حالت تمیز، بدون ایجاد سشن)
  const handleNewChat = () => {
    setCurrentSession(null);
    setMessages([]);
    setInputMessage('');
    setSidebarOpen(false);
  };

  // حذف یک سشن
  const deleteSession = async (sessionId) => {
    if (!window.confirm('آیا از حذف این چت اطمینان دارید؟')) return;

    try {
      await api.delete(`/chat/sessions/${sessionId}/`, { withCredentials: true });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Error deleting session:', err);
      alert('حذف چت با خطا مواجه شد.');
    }
  };

  // ارسال پیام
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      content: inputMessage,
      role: 'user',
      created_at: new Date().toISOString(),
    };

    let sessionId = currentSession?.id;

    // اگر سشن نداشتیم، با اولین پیام ایجاد می‌شه
    if (!sessionId) {
      const title = inputMessage.length > 50
        ? inputMessage.substring(0, 50) + '...'
        : inputMessage;

      try {
        const response = await api.post(
          '/chat/sessions/',
          { title },
          { withCredentials: true }
        );
        const newSession = response.data.data;
        setSessions((prev) => [newSession, ...prev.filter(s => s.id !== newSession.id)]);
        setCurrentSession(newSession);
        sessionId = newSession.id;
      } catch (err) {
        setError('خطا در ایجاد چت جدید');
        return;
      }
    }

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError('');

    try {
      const response = await api.post(
        '/chat/chat/',
        { message: inputMessage, session_id: sessionId },
        { withCredentials: true, timeout: 300000 }
      );

      const botMessage = {
        content: response.data.data.ai_message.content,
        role: 'assistant',
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMsg = err.response?.data?.message || 'ارسال پیام ناموفق بود';
      setError(errorMsg);

      setMessages((prev) => [
        ...prev,
        {
          content: 'متاسفانه مشکلی در ارسال پیام پیش آمد. لطفاً دوباره تلاش کنید.',
          role: 'system',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // رندر مارک‌داون
  const MarkdownRenderer = ({ content }) => (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );

  return (
    <div className="ai-chat-container">
      {/* اوورلی موبایل */}
      <div
        className={`overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* سایدبار */}
      <div className={`sessions-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sessions-header">
          <button onClick={handleNewChat} className="new-chat-button">
            + چت جدید
          </button>
        </div>

        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="empty-sessions">هنوز چتی ندارید</div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
                onClick={() => handleSessionSelect(session)}
              >
                <div className="session-content">
                  <div className="session-title">{session.title}</div>
                  <div className="session-date">
                    {new Date(session.updated_at).toLocaleDateString('fa-IR')}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation(); // جلوگیری از trigger شدن select
                    deleteSession(session.id);
                  }}
                  className="delete-session-btn"
                  title="حذف چت"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ناحیه اصلی چت */}
      <div className="chat-main">
        <div className="chat-header">
          <div>
            <h3>{currentSession?.title || 'چت با هوش مصنوعی'}</h3>
            <p>سوالات خود را بپرسید</p>
          </div>
          <button
            className="menu-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
        </div>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <div className="empty-chat-content">
                <div className="empty-chat-icon">🤖</div>
                <p>به چت هوش مصنوعی خوش آمدید</p>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message-wrapper ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
                >
                  <div className={`message-bubble ${msg.role}`}>
                    <div className="message-content">
                      <MarkdownRenderer content={msg.content} />
                    </div>
                    <div className="message-time">
                      {new Date(msg.created_at).toLocaleTimeString('fa-IR', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message-wrapper assistant-message">
                  <div className="message-bubble typing-indicator">در حال تایپ...</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={sendMessage} className="message-form">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="پیام خود را بنویسید..."
            disabled={loading}
            className="message-input"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="send-button"
          >
            ارسال
          </button>
        </form>
      </div>
    </div>
  );
};

export default AIChat;