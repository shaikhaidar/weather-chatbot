import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, BarChart } from 'lucide-react';
import Plot from 'react-plotly.js';
import { createSession, sendMessage, getMessages } from '../api';

const ChatWindow = ({ sessionIdProp, systemMode }: { sessionIdProp: string | null, systemMode: string }) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionIdProp) {
      loadExistingSession(sessionIdProp);
    } else {
      initSession();
    }
  }, [sessionIdProp]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadExistingSession = async (id: string) => {
    setSessionId(id);
    try {
      const hist = await getMessages(id);
      setMessages(hist);
    } catch (err) {
      console.error(err);
    }
  };

  const initSession = async () => {
    try {
      const session = await createSession('New Chat');
      setSessionId(session.id);
      setMessages([]); // clear old messages for new chat
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !sessionId) return;

    const userText = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setLoading(true);

    try {
      const isOnline = navigator.onLine;
      const response = await sendMessage(sessionId, userText, isOnline, systemMode);
      setMessages(prev => [...prev, { role: 'assistant', content: response.content, graphs: response.graphs, mode: response.mode }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to weatherBOT brain.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto w-full bg-white rounded-xl shadow-sm border overflow-hidden">
      
      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
             <Bot className="w-16 h-16 opacity-20" />
             <p className="text-lg">weatherBOT initialized. Ask me about the weather or analyze a dataset.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
              )}

              <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'}`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
                
                {/* Render Plotly Graphs inline if they exist */}
                {msg.graphs && (
                  <div className="mt-4 p-2 bg-white rounded-xl border overflow-hidden">
                    <Plot
                      data={msg.graphs.data}
                      layout={{ ...msg.graphs.layout, autosize: true, margin: { t: 40, r: 10, b: 30, l: 40 } }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '300px' }}
                    />
                  </div>
                )}
                
                {msg.mode && (
                  <span className="inline-block mt-2 text-[10px] uppercase tracking-wider font-semibold opacity-50">
                    Mode: {msg.mode}
                  </span>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-gray-600" />
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-4 justify-start">
             <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
               <Bot className="w-5 h-5 text-blue-600 animate-pulse" />
             </div>
             <div className="bg-gray-100 rounded-2xl rounded-bl-none p-4 flex gap-1 items-center">
               <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
               <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s'}}></div>
               <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s'}}></div>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t">
        <div className="relative flex items-center max-w-4xl mx-auto">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask weatherBOT..." 
            className="w-full border border-gray-300 rounded-full pl-6 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 shadow-inner" 
            disabled={loading}
          />
          <button 
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="absolute right-2 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
