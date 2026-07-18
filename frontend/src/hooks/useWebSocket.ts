"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { getToken } from "@/lib/auth";

const WS_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/^http/, "ws");

export function useWebSocket(path: string, onMessage: (msg: string) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const generationRef = useRef(0);

  const connect = useCallback(() => {
    const token = getToken();
    if (!token) return;
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const generation = generationRef.current;
    const ws = new WebSocket(`${WS_BASE}${path}?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      if (generation === generationRef.current) {
        reconnectTimer.current = setTimeout(connect, 3000);
      }
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (e) => {
      if (e.data) onMessage(e.data as string);
    };
  }, [path, onMessage]);

  useEffect(() => {
    generationRef.current += 1;
    connect();
    return () => {
      generationRef.current += 1;
      clearTimeout(reconnectTimer.current);
      const ws = wsRef.current;
      wsRef.current = null;
      ws?.close();
    };
  }, [connect]);

  const send = useCallback((msg: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  }, []);

  return { connected, send };
}
