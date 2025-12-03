import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  FileText,
  Camera,
  Upload,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Globe,
  Languages,
  ChevronRight,
  Paperclip,
  Image,
  X,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { useAskAssistant } from '../hooks/useAI';

const suggestedQuestions = [
  { icon: FileText, text: "What documents do I need?", category: 'docs' },
  { icon: Camera, text: "How do I take a good selfie?", category: 'selfie' },
  { icon: Globe, text: "Is my country supported?", category: 'country' },
  { icon: HelpCircle, text: "Why was my document rejected?", category: 'rejection' },
];

const initialMessage = {
  id: 'welcome',
  role: 'assistant',
  content: "Hi! I'm here to help you complete your identity verification. What would you like to know?",
  timestamp: new Date()
};

export default function ApplicantAssistant({ workflowSteps = [], currentStep = 0, userCountry = 'United States', applicantId = null }) {
  const [messages, setMessages] = useState([initialMessage]);
  const [inputValue, setInputValue] = useState('');
  const [language, setLanguage] = useState('en');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Use real AI hook
  const askAssistantMutation = useAskAssistant();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || askAssistantMutation.isPending) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const query = inputValue;
    setInputValue('');

    try {
      // Call real AI API
      const response = await askAssistantMutation.mutateAsync({
        query,
        applicantId,
        context: {
          country: userCountry,
          language,
          currentStep,
          workflowSteps
        }
      });

      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.generated_at || Date.now()),
        sources: response.sources
      }]);
    } catch (error) {
      console.error('AI Assistant error:', error);
      // Add error message to chat
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your request. Please try again in a moment.",
        timestamp: new Date(),
        isError: true
      }]);
    }
  };

  const handleSuggestion = (suggestion) => {
    // Auto-send the suggestion instead of just filling input
    if (askAssistantMutation.isPending) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: suggestion.text,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);

    askAssistantMutation.mutateAsync({
      query: suggestion.text,
      applicantId,
      context: {
        country: userCountry,
        language,
        currentStep,
        workflowSteps
      }
    }).then(response => {
      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.generated_at || Date.now()),
        sources: response.sources
      }]);
    }).catch(error => {
      console.error('AI Assistant error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your request. Please try again in a moment.",
        timestamp: new Date(),
        isError: true
      }]);
    });
  };

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    setShowLanguageMenu(false);
  };

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset file input
    e.target.value = '';

    // Add file message to chat
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: `[Attached: ${file.name}]`,
      timestamp: new Date(),
      file: { name: file.name, type: file.type, size: file.size }
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Send with file context
      const response = await askAssistantMutation.mutateAsync({
        query: `I've attached a document: ${file.name}. Can you help me understand if this is the right type of document for verification?`,
        applicantId,
        context: {
          country: userCountry,
          language,
          currentStep,
          workflowSteps,
          attachedFile: {
            name: file.name,
            type: file.type,
            size: file.size
          }
        }
      });

      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.generated_at || Date.now()),
        sources: response.sources
      }]);
    } catch (error) {
      console.error('AI Assistant error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I'm sorry, I couldn't process your document. Please try again in a moment.",
        timestamp: new Date(),
        isError: true
      }]);
    }
  };

  const [showLanguageMenu, setShowLanguageMenu] = useState(false);

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'es', label: 'Español' },
    { code: 'fr', label: 'Français' },
    { code: 'de', label: 'Deutsch' },
    { code: 'pt', label: 'Português' },
    { code: 'zh', label: '中文' },
    { code: 'ja', label: '日本語' },
    { code: 'ko', label: '한국어' },
    { code: 'ar', label: 'العربية' }
  ];

  // Calculate progress from props
  const totalSteps = workflowSteps.length || 3;
  const progressPercent = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 33;

  return (
    <div className="applicant-assistant">
      <style>{`
        .applicant-assistant {
          display: flex;
          flex-direction: column;
          height: 100%;
          max-width: 480px;
          margin: 0 auto;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          overflow: hidden;
        }
        
        /* Header */
        .assistant-header {
          padding: 16px 20px;
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          color: white;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .assistant-avatar {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .assistant-info {
          flex: 1;
        }
        
        .assistant-name {
          font-weight: 600;
          font-size: 15px;
        }
        
        .assistant-status {
          font-size: 12px;
          opacity: 0.9;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        
        .status-dot {
          width: 8px;
          height: 8px;
          background: #10b981;
          border-radius: 50%;
        }
        
        .language-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: rgba(255, 255, 255, 0.2);
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.15s;
        }

        .language-btn:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        .language-menu {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 8px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 6px;
          min-width: 140px;
          z-index: 100;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        .language-option {
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 13px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
        }

        .language-option:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .language-option.active {
          background: var(--accent-glow);
          color: var(--accent-primary);
        }
        
        /* Progress Bar */
        .progress-section {
          padding: 16px 20px;
          background: var(--bg-tertiary);
          border-bottom: 1px solid var(--border-color);
        }
        
        .progress-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .progress-label {
          font-size: 13px;
          font-weight: 500;
        }
        
        .progress-value {
          font-size: 12px;
          color: var(--text-muted);
        }
        
        .progress-bar {
          height: 6px;
          background: var(--border-color);
          border-radius: 3px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--accent-primary), #a855f7);
          border-radius: 3px;
          transition: width 0.3s ease;
        }
        
        .progress-steps {
          display: flex;
          gap: 8px;
          margin-top: 12px;
        }
        
        .progress-step {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: var(--text-muted);
        }
        
        .progress-step.complete {
          color: var(--success);
        }
        
        .progress-step.current {
          color: var(--accent-primary);
          font-weight: 500;
        }
        
        .step-indicator {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 2px solid currentColor;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 9px;
        }
        
        .step-indicator.complete {
          background: var(--success);
          border-color: var(--success);
          color: white;
        }
        
        /* Messages */
        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .message {
          display: flex;
          gap: 12px;
          max-width: 85%;
        }
        
        .message.user {
          flex-direction: row-reverse;
          margin-left: auto;
        }
        
        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .message.assistant .message-avatar {
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          color: white;
        }
        
        .message.user .message-avatar {
          background: var(--bg-tertiary);
          color: var(--text-secondary);
        }
        
        .message-bubble {
          padding: 12px 16px;
          border-radius: 16px;
          font-size: 14px;
          line-height: 1.5;
        }
        
        .message.assistant .message-bubble {
          background: var(--bg-tertiary);
          border-bottom-left-radius: 4px;
        }
        
        .message.user .message-bubble {
          background: var(--accent-primary);
          color: white;
          border-bottom-right-radius: 4px;
        }
        
        .message-bubble strong {
          font-weight: 600;
        }
        
        .message-time {
          font-size: 10px;
          color: var(--text-muted);
          margin-top: 4px;
        }
        
        .message.user .message-time {
          text-align: right;
        }
        
        /* Typing Indicator */
        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 12px 16px;
          background: var(--bg-tertiary);
          border-radius: 16px;
          border-bottom-left-radius: 4px;
          width: fit-content;
        }
        
        .typing-dot {
          width: 8px;
          height: 8px;
          background: var(--text-muted);
          border-radius: 50%;
          animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) {
          animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
          animation-delay: 0.4s;
        }
        
        @keyframes typing {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-4px); opacity: 1; }
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        .message-bubble.error {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid var(--danger);
        }
        
        /* Suggestions */
        .suggestions {
          padding: 0 20px 16px;
        }
        
        .suggestions-label {
          font-size: 11px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 8px;
        }
        
        .suggestions-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        
        .suggestion-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          font-size: 12px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
          text-align: left;
        }
        
        .suggestion-btn:hover {
          background: var(--bg-hover);
          border-color: var(--accent-primary);
          color: var(--text-primary);
        }
        
        .suggestion-icon {
          color: var(--accent-primary);
        }
        
        /* Input */
        .input-section {
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
          background: var(--bg-secondary);
        }
        
        .input-wrapper {
          display: flex;
          gap: 8px;
          align-items: flex-end;
        }
        
        .input-box {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 8px 12px;
          transition: border-color 0.15s;
        }
        
        .input-box:focus-within {
          border-color: var(--accent-primary);
        }
        
        .message-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          font-size: 14px;
          color: var(--text-primary);
          resize: none;
          max-height: 80px;
          font-family: inherit;
        }
        
        .message-input::placeholder {
          color: var(--text-muted);
        }
        
        .attach-btn {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s;
        }
        
        .attach-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        .send-btn {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          border: none;
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: opacity 0.15s;
        }
        
        .send-btn:hover {
          opacity: 0.9;
        }
        
        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        /* Disclaimer */
        .disclaimer {
          padding: 8px 20px 12px;
          font-size: 10px;
          color: var(--text-muted);
          text-align: center;
        }
      `}</style>
      
      <div className="assistant-header">
        <div className="assistant-avatar">
          <Sparkles size={20} />
        </div>
        <div className="assistant-info">
          <div className="assistant-name">Verification Assistant</div>
          <div className="assistant-status">
            <span className="status-dot" />
            Online • Ready to help
          </div>
        </div>
        <div style={{ position: 'relative' }}>
          <button
            className="language-btn"
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
          >
            <Languages size={14} />
            {languages.find(l => l.code === language)?.label.slice(0, 2).toUpperCase() || 'EN'}
          </button>
          {showLanguageMenu && (
            <div className="language-menu">
              {languages.map((lang) => (
                <div
                  key={lang.code}
                  className={`language-option ${language === lang.code ? 'active' : ''}`}
                  onClick={() => handleLanguageChange(lang.code)}
                >
                  {lang.label}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div className="progress-section">
        <div className="progress-header">
          <span className="progress-label">Verification Progress</span>
          <span className="progress-value">1 of 3 steps</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: '33%' }} />
        </div>
        <div className="progress-steps">
          <div className="progress-step complete">
            <div className="step-indicator complete">
              <CheckCircle2 size={10} />
            </div>
            ID Upload
          </div>
          <div className="progress-step current">
            <div className="step-indicator">2</div>
            Selfie
          </div>
          <div className="progress-step">
            <div className="step-indicator">3</div>
            Review
          </div>
        </div>
      </div>
      
      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id || msg.timestamp} className={`message ${msg.role === 'user' ? 'user' : 'assistant'}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? <User size={16} /> : (
                msg.isError ? <AlertCircle size={16} /> : <Sparkles size={16} />
              )}
            </div>
            <div>
              <div
                className={`message-bubble ${msg.isError ? 'error' : ''}`}
                dangerouslySetInnerHTML={{
                  __html: msg.content
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br />')
                }}
              />
              <div className="message-time">
                {(msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp))
                  .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        
        {askAssistantMutation.isPending && (
          <div className="message assistant">
            <div className="message-avatar">
              <Sparkles size={16} />
            </div>
            <div className="typing-indicator">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {messages.length <= 1 && (
        <div className="suggestions">
          <div className="suggestions-label">Quick Questions</div>
          <div className="suggestions-grid">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                className="suggestion-btn"
                onClick={() => handleSuggestion(q)}
              >
                <q.icon size={14} className="suggestion-icon" />
                {q.text}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <div className="input-section">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*,.pdf"
          style={{ display: 'none' }}
        />
        <div className="input-wrapper">
          <div className="input-box">
            <input
              type="text"
              className="message-input"
              placeholder={askAssistantMutation.isPending ? "Thinking..." : "Ask me anything about verification..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              disabled={askAssistantMutation.isPending}
            />
            <button
              className="attach-btn"
              title="Attach document"
              onClick={handleAttachClick}
              disabled={askAssistantMutation.isPending}
            >
              <Paperclip size={18} />
            </button>
          </div>
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim() || askAssistantMutation.isPending}
          >
            {askAssistantMutation.isPending ? (
              <Loader2 size={18} className="spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </div>
      
      <div className="disclaimer">
        AI assistant helps with verification questions. It cannot approve or reject applications.
      </div>
    </div>
  );
}

// Add missing User import for the icon
const User = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);
