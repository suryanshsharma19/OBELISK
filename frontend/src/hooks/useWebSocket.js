/**
 * React hook that wraps the WebSocket singleton.
 *
 * Connects on mount, disconnects on unmount, and provides
 * a `lastMessage` state for easy consumption.
 *
 * Usage:
 *   const { lastMessage, connected } = useWebSocket();
 */

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
