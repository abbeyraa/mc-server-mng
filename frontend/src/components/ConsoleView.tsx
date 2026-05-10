"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function ConsoleView() {
  const [lines, setLines] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const onMessage = useCallback((msg: string) => {
    setLines((prev) => {
      const next = [...prev, msg];
      return next.length > 2000 ? next.slice(-2000) : next;
    });
  }, []);

  const { connected, send } = useWebSocket("/ws/console", onMessage);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  function sendCommand(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim()) {
      send(input.trim());
      setInput("");
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${connected ? "bg-mc-green" : "bg-red-500"}`} />
        <span className="text-xs text-gray-400">{connected ? "Connected" : "Reconnecting..."}</span>
      </div>
      <div className="flex-1 bg-black rounded p-3 overflow-y-auto font-mono text-xs text-green-400 min-h-0">
        {lines.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap break-all leading-5">
            {line}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={sendCommand} className="flex gap-2 mt-2">
        <span className="text-mc-green font-mono">&gt;</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-mc-panel border border-mc-border rounded px-3 py-1 text-sm font-mono text-white focus:outline-none focus:border-mc-green"
          placeholder="Enter command..."
          disabled={!connected}
        />
        <button
          type="submit"
          disabled={!connected}
          className="px-3 py-1 bg-mc-green text-white rounded text-sm disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
