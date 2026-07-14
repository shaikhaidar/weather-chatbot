import React, { useState, useEffect } from 'react';
import { getSessions } from '../api';
import { MessageSquare, Clock } from 'lucide-react';

const History = ({ onSelectSession }: { onSelectSession: (id: string) => void }) => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Loading history...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-4xl mx-auto">
      <div className="bg-white rounded-xl border shadow-sm">
        <div className="p-6 border-b flex justify-between items-center">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-500" />
            Conversation History
          </h3>
          <span className="text-sm text-gray-500">{sessions.length} Sessions</span>
        </div>
        
        <div className="divide-y">
          {sessions.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              No conversations found. Start a new chat!
            </div>
          ) : (
            sessions.map((session) => (
              <div 
                key={session.id} 
                className="p-4 hover:bg-gray-50 cursor-pointer transition-colors flex items-center gap-4 group"
                onClick={() => onSelectSession(session.id)}
              >
                <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-500 group-hover:bg-blue-100 transition-colors">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{session.title}</h4>
                  <p className="text-sm text-gray-500">{new Date(session.created_at).toLocaleString()}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default History;
