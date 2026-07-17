import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, ChevronDown, ChevronUp, Zap, MessageSquare, PlusCircle } from 'lucide-react';
import Plot from 'react-plotly.js';
import { createSession, sendMessage, getMessages, getSessionXAI } from '../api';

interface XAIExplanation {
  rank: number;
  feature: string;
  importance: number;
  direction: 'positive' | 'negative';
  pct_contribution: number;
}

interface Message {
  role: string;
  content: string;
  graphs?: any;
  mode?: string;
  recommendations?: string[];
  intent?: string;
  latency?: number;
  xai?: { explanations: XAIExplanation[]; attention_map: any };
}

const ChatWindow = ({ sessionIdProp, systemMode, onSessionInit }: { sessionIdProp: string | null; systemMode: string; onSessionInit?: (id: string) => void }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [xaiOpen, setXaiOpen] = useState<number | null>(null);
  const [xaiData, setXaiData] = useState<Record<number, any>>({});
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
      if (onSessionInit) {
        onSessionInit(session.id);
      }
      setMessages([]);
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
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: response.content,
          graphs: response.graphs,
          mode: response.mode,
          recommendations: response.recommendations || [],
          intent: response.intent,
          latency: response.latency,
        },
      ]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to weatherBOT brain.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecommendationClick = (rec: string) => {
    setInput(rec);
  };

  const toggleXAI = async (msgIdx: number) => {
    if (xaiOpen === msgIdx) {
      setXaiOpen(null);
      return;
    }
    setXaiOpen(msgIdx);
    if (!xaiData[msgIdx] && sessionId) {
      try {
        const data = await getSessionXAI(sessionId);
        setXaiData(prev => ({ ...prev, [msgIdx]: data }));
      } catch (e) {
        console.error('XAI fetch error', e);
      }
    }
  };

  const isPredictionIntent = (intent?: string) =>
    intent === 'PREDICTION_REQUEST' || intent === 'DATA_QUERY' || intent === 'XAI_REQUEST';

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
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
              )}

              <div className="flex flex-col gap-2 max-w-[80%]">
                {/* Message bubble */}
                <div className={`rounded-2xl p-4 ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'}`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Plotly Graphs */}
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

                  <div className="flex items-center gap-3 mt-2">
                    {msg.mode && (
                      <span className="text-[10px] uppercase tracking-wider font-semibold opacity-50">
                        Mode: {msg.mode}
                      </span>
                    )}
                    {msg.latency !== undefined && (
                      <span className="text-[10px] uppercase tracking-wider font-semibold opacity-60 flex items-center gap-1">
                        ⚡ {msg.latency}s
                      </span>
                    )}
                  </div>
                </div>

                {/* XAI Panel — only for assistant messages with prediction intent */}
                {msg.role === 'assistant' && isPredictionIntent(msg.intent) && (
                  <div className="ml-0">
                    <button
                      id={`xai-toggle-${idx}`}
                      onClick={() => toggleXAI(idx)}
                      className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium px-3 py-1 rounded-full bg-indigo-50 hover:bg-indigo-100 transition-colors"
                    >
                      <Zap className="w-3 h-3" />
                      Why this prediction?
                      {xaiOpen === idx ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>

                    {xaiOpen === idx && xaiData[idx] && (
                      <div className="mt-2 bg-indigo-50 border border-indigo-100 rounded-xl p-4 space-y-3">
                        <h4 className="text-xs font-bold text-indigo-700 uppercase tracking-wider">XAI Feature Explanations</h4>
                        {xaiData[idx]?.explanations?.explanations?.slice(0, 5).map((exp: XAIExplanation, i: number) => (
                          <div key={i} className="flex items-center gap-3">
                            <span className="w-5 h-5 rounded-full bg-indigo-200 text-indigo-700 text-[10px] flex items-center justify-center font-bold flex-shrink-0">{exp.rank}</span>
                            <div className="flex-1">
                              <div className="flex justify-between text-xs">
                                <span className="font-semibold text-gray-700">{exp.feature}</span>
                                <span className={`font-medium ${exp.direction === 'positive' ? 'text-emerald-600' : 'text-red-500'}`}>
                                  {exp.direction === 'positive' ? '▲' : '▼'} {exp.pct_contribution}%
                                </span>
                              </div>
                              <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${exp.direction === 'positive' ? 'bg-emerald-400' : 'bg-red-400'}`}
                                  style={{ width: `${Math.min(100, exp.pct_contribution * 3)}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                        {xaiData[idx]?.attention_map?.data && (
                          <div className="mt-2 bg-white rounded-lg border overflow-hidden">
                            <Plot
                              data={xaiData[idx].attention_map.data}
                              layout={{ ...xaiData[idx].attention_map.layout, autosize: true, height: 250, margin: { l: 120, r: 10, t: 30, b: 20 } }}
                              useResizeHandler={true}
                              style={{ width: '100%', height: '250px' }}
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Recommendation chips */}
                {msg.role === 'assistant' && msg.recommendations && msg.recommendations.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-1">
                    {msg.recommendations.map((rec, rIdx) => (
                      <button
                        key={rIdx}
                        id={`rec-chip-${idx}-${rIdx}`}
                        onClick={() => handleRecommendationClick(rec)}
                        className="flex items-center gap-1 text-xs text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-full px-3 py-1 transition-colors"
                      >
                        <MessageSquare className="w-3 h-3" />
                        {rec}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-5 h-5 text-gray-600" />
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading dots */}
        {loading && (
          <div className="flex gap-4 justify-start">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <Bot className="w-5 h-5 text-blue-600 animate-pulse" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-none p-4 flex gap-1 items-center">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t flex flex-col gap-3">
        <div className="flex justify-between items-center px-4">
          <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Active Session
          </span>
          <button 
            onClick={initSession}
            className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-semibold px-3 py-1.5 rounded-full bg-blue-50 hover:bg-blue-100 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            New Chat
          </button>
        </div>
        <div className="relative flex items-center w-full">
          <input
            id="chat-input"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask weatherBOT..."
            className="w-full border border-gray-300 rounded-full pl-6 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 shadow-inner"
            disabled={loading}
          />
          <button
            id="chat-send-btn"
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
