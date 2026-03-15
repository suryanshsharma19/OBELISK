// WebSocket client with auto-reconnect

import { WS_BASE_URL } from '../utils/constants';
import { ensureAuthenticated, getAccessToken } from './session';

const MAX_RECONNECT_DELAY = 30_000;
const INITIAL_DELAY = 1_000;

class WebSocketClient {
  constructor(url = WS_BASE_URL) {
    this._url = url;
    this._ws = null;
    this._listeners = new Map(); // event -> Set<callback>
    this._reconnectDelay = INITIAL_DELAY;
    this._shouldReconnect = true;
  }


  connect() {
    if (this._ws?.readyState === WebSocket.OPEN) return;

    ensureAuthenticated()
      .then(() => {
        const token = getAccessToken();
        const url = token
          ? `${this._url}${this._url.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
          : this._url;

        this._ws = new WebSocket(url);
        this._ws.onopen = () => {
          this._reconnectDelay = INITIAL_DELAY;
          this._emit('open');
        };
        this._ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this._emit('message', data);
            if (data.type) this._emit(data.type, data);
          } catch {
            this._emit('message', event.data);
          }
        };
        this._ws.onerror = () => this._emit('error');
        this._ws.onclose = () => {
          this._emit('close');
          if (this._shouldReconnect) this._scheduleReconnect();
        };
      })
      .catch((err) => {
        console.warn('[WS] Authentication failed:', err.message);
        if (this._shouldReconnect) this._scheduleReconnect();
      });
  }

  disconnect() {
    this._shouldReconnect = false;
    this._ws?.close();
    this._ws = null;
  }

  send(data) {
    if (this._ws?.readyState !== WebSocket.OPEN) return;
    this._ws.send(JSON.stringify(data));
  }

  // returns unsubscribe function
  on(event, callback) {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set());
    }
    this._listeners.get(event).add(callback);
    return () => this._listeners.get(event)?.delete(callback);
  }


  _emit(event, data) {
    this._listeners.get(event)?.forEach((cb) => cb(data));
  }

  _scheduleReconnect() {
    setTimeout(() => this.connect(), this._reconnectDelay);
    this._reconnectDelay = Math.min(
      this._reconnectDelay * 2,
      MAX_RECONNECT_DELAY,
    );
  }
}

const wsClient = new WebSocketClient();
export default wsClient;
