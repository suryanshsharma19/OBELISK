// Hook wrapper around the WebSocket singleton

import { useState, useEffect, useRef } from 'react';
import wsClient from '../services/websocket';

export default function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const unsubs = useRef([]);

  useEffect(() => {
    // Register listeners
    unsubs.current.push(
      wsClient.on('open', () => setConnected(true)),
      wsClient.on('close', () => setConnected(false)),
      wsClient.on('message', (data) => setLastMessage(data)),
    );

    wsClient.connect();

    return () => {
      unsubs.current.forEach((unsub) => unsub());
      unsubs.current = [];
    };
  }, []);

  return { connected, lastMessage, send: wsClient.send.bind(wsClient) };
}
