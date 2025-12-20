import React, { useState, useEffect, useRef } from 'react';
import './RAGChatWidget.css';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

const RAGChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Capture selected text on mouseup
  useEffect(() => {
    const handleMouseUp = () => {
      const selected = window.getSelection()?.toString().trim();
      if (selected && selected.length > 10) { // Only capture meaningful selections
        setSelectedText(selected);
        if (isOpen && inputRef.current) {
          inputRef.current.focus();
        }
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isOpen]);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Call the backend API
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputValue,
          selected_text: selectedText, // Pass the selected text as priority context
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.answer,
        role: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setSelectedText(''); // Clear selected text after use
    } catch (error) {
      console.error('Error fetching response:', error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSelectedText('');
  };

  return (
    <>
      {/* Floating chat button */}
      {!isOpen && (
        <button
          className="rag-chat-toggle"
          onClick={toggleChat}
          aria-label="Open chat"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H17.69L19.81 21.01C19.92 21.21 19.89 21.46 19.73 21.63C19.57 21.8 19.34 21.85 19.14 21.75L16.46 20.28C16.1 20.66 15.64 20.92 15.14 21.03C14.64 21.14 14.12 21.09 13.65 20.88L12.08 21.76C12.06 21.77 12.04 21.77 12.02 21.78C12 21.79 11.98 21.79 11.96 21.79C11.94 21.79 11.92 21.79 11.9 21.78C11.88 21.77 11.86 21.77 11.84 21.76L10.27 20.88C9.8 21.09 9.28 21.14 8.78 21.03C8.28 20.92 7.82 20.66 7.46 20.28L4.78 21.75C4.58 21.85 4.35 21.8 4.19 21.63C4.03 21.46 4 21.21 4.11 21.01L6.31 17H5C4.46957 17 3.96086 16.7893 3.58579 16.4142C3.21071 16.0391 3 15.5304 3 15V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      )}

      {/* Chat widget */}
      {isOpen && (
        <div className="rag-chat-widget">
          <div className="rag-chat-header">
            <div className="rag-chat-title">Book Assistant</div>
            <div className="rag-chat-actions">
              <button
                className="rag-chat-clear-btn"
                onClick={clearChat}
                title="Clear chat"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M2 4H3.33333H14"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M12.6667 4V13.3333C12.6667 13.5101 12.5966 13.6797 12.4716 13.8047C12.3466 13.9297 12.177 14 12 14H4C3.82304 14 3.65339 13.9297 3.5284 13.8047C3.4034 13.6797 3.33333 13.5101 3.33333 13.3333V4M5 4V2.66667C5 2.48971 5.07007 2.32006 5.20003 2.19506C5.33 2.07006 5.49965 2 5.66667 2H10.3333C10.5003 2 10.67 2.07006 10.8 2.19506C10.93 2.32006 11 2.48971 11 2.66667V4"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M6.66667 7V11.3333"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M9.33333 7V11.3333"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
              <button
                className="rag-chat-close-btn"
                onClick={toggleChat}
                title="Close chat"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 4L4 12"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M4 4L12 12"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
          </div>

          <div className="rag-chat-messages">
            {messages.length === 0 ? (
              <div className="rag-chat-welcome">
                <p>Hello! I'm your book assistant.</p>
                <p>Select text on the page and ask me questions about it, or ask general questions about the book.</p>
                {selectedText && (
                  <div className="rag-chat-selected-text-preview">
                    <p><strong>Selected text:</strong> "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"</p>
                  </div>
                )}
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`rag-chat-message rag-chat-message--${message.role}`}
                >
                  <div className="rag-chat-message-content">
                    {message.content}
                  </div>
                  <div className="rag-chat-message-timestamp">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              ))
            )}
            {isTyping && (
              <div className="rag-chat-message rag-chat-message--assistant">
                <div className="rag-chat-message-content">
                  <div className="rag-chat-typing-indicator">
                    <div className="rag-chat-typing-dot"></div>
                    <div className="rag-chat-typing-dot"></div>
                    <div className="rag-chat-typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {selectedText && (
            <div className="rag-chat-selected-text">
              <span className="rag-chat-selected-text-label">Selected:</span> "{selectedText.substring(0, 80)}{selectedText.length > 80 ? '...' : ''}"
            </div>
          )}

          <form className="rag-chat-input-form" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={selectedText ? "Ask about selected text..." : "Ask a question about the book..."}
              disabled={isLoading}
              className="rag-chat-input"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="rag-chat-send-btn"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default RAGChatWidget;