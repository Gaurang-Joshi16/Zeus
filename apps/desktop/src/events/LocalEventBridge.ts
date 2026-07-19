import type { EventBridge } from './EventBridge';

export class WebSocketEventBridge implements EventBridge {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Array<(payload?: unknown) => void>> = new Map();
  private pendingRequests: Map<string, { resolve: (val: unknown) => void; reject: (err: Error) => void }> = new Map();
  private _connected = false;
  private _reconnectAttempts = 0;
  private _reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.connect();
  }

  get connected(): boolean {
    return this._connected;
  }

  private connect() {
    // Clean up any previous connection
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onclose = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      try { this.ws.close(); } catch { /* ignore */ }
      this.ws = null;
    }

    try {
      this.ws = new WebSocket('ws://localhost:8000/ws');
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._connected = true;
      this._reconnectAttempts = 0;
      console.log('[Zeus] Connected to backend');
      this.publishLocal('WS_CONNECTED', {});
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event) {
          console.log(`[Zeus] Event: ${data.event}`, data.payload);
          this.publishLocal(data.event, data.payload);
        } else if (data.request_id) {
          const req = this.pendingRequests.get(data.request_id);
          if (req) {
            if (data.error) req.reject(new Error(data.error));
            else req.resolve(data.result);
            this.pendingRequests.delete(data.request_id);
          }
        }
      } catch (e) {
        console.error('[Zeus] Error parsing message', e);
      }
    };

    this.ws.onerror = () => {
      // Suppress noisy error logging — onclose will handle reconnect
    };

    this.ws.onclose = () => {
      const wasConnected = this._connected;
      this._connected = false;
      if (wasConnected) {
        console.log('[Zeus] Disconnected from backend');
      }
      this.publishLocal('WS_DISCONNECTED', {});
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (this._reconnectTimer) return;
    // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
    const delay = Math.min(1000 * Math.pow(2, this._reconnectAttempts), 10000);
    this._reconnectAttempts++;
    // Only log every 5th attempt to reduce console spam
    if (this._reconnectAttempts <= 1 || this._reconnectAttempts % 5 === 0) {
      console.log(`[Zeus] Reconnecting in ${delay / 1000}s... (attempt ${this._reconnectAttempts})`);
    }
    this._reconnectTimer = setTimeout(() => {
      this._reconnectTimer = null;
      this.connect();
    }, delay);
  }

  async invoke(type: string, payload: unknown = {}): Promise<unknown> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      const err = new Error(`WebSocket not connected — cannot invoke '${type}'`);
      console.error(`[Zeus] ${err.message}`);
      throw err;
    }
    return new Promise((resolve, reject) => {
      const requestId = Math.random().toString(36).substring(7);

      const timeout = setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          const err = new Error(`IPC timeout waiting for '${type}'`);
          console.error(`[Zeus] ${err.message}`);
          reject(err);
        }
      }, 5000);

      this.pendingRequests.set(requestId, {
        resolve: (val) => { clearTimeout(timeout); resolve(val); },
        reject: (err) => { clearTimeout(timeout); reject(err); }
      });

      this.ws!.send(JSON.stringify({ type, payload, request_id: requestId }));
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  publish(_event: string, _payload?: unknown): void {
    // Placeholder for future backend-directed publish
  }

  private publishLocal(event: string, payload?: unknown): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(payload));
    }
  }

  subscribe(event: string, handler: (payload?: unknown) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(handler);
    return () => this.unsubscribe(event, handler);
  }

  unsubscribe(event: string, handler: (payload?: unknown) => void): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      this.listeners.set(
        event,
        handlers.filter((h) => h !== handler)
      );
    }
  }
}

export const eventBridge = new WebSocketEventBridge();
