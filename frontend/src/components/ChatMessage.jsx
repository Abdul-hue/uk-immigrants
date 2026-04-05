import React from 'react';

const ChatMessage = ({ message, sender, hint, isTyping }) => {
  const isUser = sender === 'user';

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      <div className="chat-bubble">
        {isTyping ? (
          <div className="typing-indicator">
            <div className="typing-dot" style={{ animationDelay: '0s' }}></div>
            <div className="typing-dot" style={{ animationDelay: '0.16s' }}></div>
            <div className="typing-dot" style={{ animationDelay: '0.32s' }}></div>
          </div>
        ) : (
          <>
            <div className="message-content">{message}</div>
            {hint && (
              <span className="chat-hint">
                💡 {hint}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
