import { useEffect, useRef, useState, useCallback } from "react";

export default function useWebSocket(url) {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log(`[WS] Connected to ${url}`);
    };

    ws.onmessage = (e) => {
      setLastMessage(e.data);
    };

    ws.onerror = (e) => {
      console.error("[WS] Error:", e);
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[WS] Disconnected");
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  }, []);

  return { connected, lastMessage, sendMessage };
}
