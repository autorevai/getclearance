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
  RefreshCw
} from 'lucide-react';

const suggestedQuestions = [
  { icon: FileText, text: "What documents do I need?", category: 'docs' },
  { icon: Camera, text: "How do I take a good selfie?", category: 'selfie' },
  { icon: Globe, text: "Is my country supported?", category: 'country' },
  { icon: HelpCircle, text: "Why was my document rejected?", category: 'rejection' },
];

const mockConversation = [
  {
    role: 'assistant',
    content: "Hi! I'm here to help you complete your identity verification. What would you like to know?",
    timestamp: new Date()
  }
];

const documentRequirements = {
  'United States': {
    accepted: ['Passport', 'Driver\'s License', 'State ID'],
    proofOfAddress: ['Utility bill', 'Bank statement', 'Government letter'],
    notes: 'Documents must be less than 3 months old'
  },
  'Mexico': {
    accepted: ['Passport', 'INE/IFE', 'Cédula Profesional'],
    proofOfAddress: ['CFE bill', 'Bank statement', 'PREDIAL'],
    notes: 'INE must show current address'
  }
};

export default function ApplicantAssistant({ workflowSteps = [], currentStep = 0, userCountry = 'United States' }) {
  const [messages, setMessages] = useState(mockConversation);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [language, setLanguage] = useState('en');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    const userMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    
    // Simulate AI response
    setTimeout(() => {
      const response = generateResponse(inputValue);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }]);
      setIsTyping(false);
    }, 1000);
  };

  const generateResponse = (question) => {
    const q = question.toLowerCase();
    
    if (q.includes('document') || q.includes('need') || q.includes('require')) {
      const docs = documentRequirements[userCountry];
      return `For verification in ${userCountry}, we accept:\n\n📄 **ID Documents:** ${docs.accepted.join(', ')}\n\n📍 **Proof of Address:** ${docs.proofOfAddress.join(', ')}\n\n⚠️ ${docs.notes}\n\nWould you like tips on how to photograph your documents?`;
    }
    
    if (q.includes('selfie') || q.includes('photo') || q.includes('face')) {
      return `Here are tips for a successful selfie verification:\n\n✅ **Good lighting** - Face a window or light source\n✅ **Neutral background** - Plain wall works best\n✅ **Remove accessories** - Take off glasses, hats, masks\n✅ **Look straight** - Keep your face centered in the frame\n✅ **Don't smile** - Keep a neutral expression\n\nThe camera will guide you through the process. Ready to try?`;
    }
    
    if (q.includes('reject') || q.includes('fail') || q.includes('denied')) {
      return `Common reasons for document rejection include:\n\n❌ **Blurry image** - Ensure good lighting and steady hands\n❌ **Glare or shadows** - Avoid flash and direct light on the document\n❌ **Cropped edges** - Make sure all four corners are visible\n❌ **Expired document** - Check the expiration date\n❌ **Wrong document type** - Use an accepted ID for your country\n\nWould you like me to check your specific rejection reason?`;
    }
    
    if (q.includes('country') || q.includes('support')) {
      return `We currently support identity verification in 190+ countries! Most government-issued IDs are accepted.\n\nFor ${userCountry}, we accept: ${documentRequirements[userCountry]?.accepted.join(', ') || 'Passport, National ID'}\n\nIs there a specific document you'd like to use?`;
    }
    
    if (q.includes('long') || q.includes('time') || q.includes('how long')) {
      return `The verification process typically takes:\n\n⏱️ **Document upload:** 2-3 minutes\n⏱️ **Selfie verification:** 1-2 minutes\n⏱️ **Review time:** Usually instant, up to 24 hours for manual review\n\nMost applications are processed within minutes!`;
    }
    
    if (q.includes('translate') || q.includes('spanish') || q.includes('language')) {
      return `I can help in multiple languages! 🌍\n\nJust let me know your preferred language, or I can automatically translate document requirements and instructions for you.\n\nCurrently available: English, Spanish, French, German, Portuguese, Chinese, Japanese, Korean, Arabic`;
    }
    
    return `I understand you're asking about "${question}". Let me help!\n\nTo complete your verification, you'll need to:\n1. Upload a valid ID document\n2. Complete a selfie verification\n3. Provide any additional information requested\n\nIs there a specific step you need help with?`;
  };

  const handleSuggestion = (suggestion) => {
    setInputValue(suggestion.text);
  };

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
        <button className="language-btn">
          <Languages size={14} />
          EN
        </button>
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
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? <Sparkles size={16} /> : <User size={16} />}
            </div>
            <div>
              <div 
                className="message-bubble"
                dangerouslySetInnerHTML={{ 
                  __html: msg.content
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br />') 
                }}
              />
              <div className="message-time">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
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
        <div className="input-wrapper">
          <div className="input-box">
            <input
              type="text"
              className="message-input"
              placeholder="Ask me anything about verification..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="attach-btn" title="Attach image">
              <Image size={18} />
            </button>
          </div>
          <button 
            className="send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim()}
          >
            <Send size={18} />
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
