/**
 * Live feed of crawler events streamed over WebSocket.
 * Shows the latest 50 messages in reverse-chronological order.
 */

import React, { useState, useEffect } from 'react';
import useWebSocket from '../../hooks/useWebSocket';
import { timeAgo } from '../../utils/formatters';

const MAX_MESSAGES = 50;

export default function LiveFeed() {
  const { lastMessage, connected } = useWebSocket();
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    if (!lastMessage) return;
    setMessages((prev) => [lastMessage, ...prev].slice(0, MAX_MESSAGES));
  }, [lastMessage]);

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Live Feed</h3>
        <span className={`text-xs ${connected ? 'text-neon-400' : 'text-gray-500'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      {messages.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500">
          Waiting for events…
        </p>
      ) : (
        <div className="max-h-72 space-y-2 overflow-y-auto">
          {messages.map((msg, i) => (
            <div
              key={`${msg.timestamp || ''}-${i}`}
              className="flex items-start gap-2 rounded-lg bg-gray-900 px-3 py-2"
            >
              <span className="shrink-0 text-xs text-gray-600">
                {msg.timestamp ? timeAgo(msg.timestamp) : '#'}
              </span>
              <span className="text-xs text-gray-300">
                {msg.message || JSON.stringify(msg)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
