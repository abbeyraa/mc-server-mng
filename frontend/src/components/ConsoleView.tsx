"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

interface ConsoleViewProps {
  path?: string;
  title: string;
  inputEnabled?: boolean;
  placeholder?: string;
}

export default function ConsoleView({
  path = "/ws/console",
  title,
  inputEnabled = true,
  placeholder = "Enter command...",
}: ConsoleViewProps) {
  const [lines, setLines] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [inputMode, setInputMode] = useState<"command" | "chat">("command");
  const bottomRef = useRef<HTMLDivElement>(null);

  const onMessage = useCallback((msg: string) => {
    setLines((prev) => {
      const next = [...prev, msg];
      return next.length > 2000 ? next.slice(-2000) : next;
    });
  }, []);

  const { connected, send } = useWebSocket(path, onMessage);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  function sendCommand(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim()) {
      const message = input.trim();
      send(inputMode === "chat" ? `say ${message}` : message);
      setInput("");
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between gap-3 mb-2">
        <h2 className="text-sm font-semibold text-white">{title}</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-mc-green" : "bg-red-500"}`} />
          <span className="text-xs text-gray-400">{connected ? "Connected" : "Reconnecting..."}</span>
        </div>
      </div>
      <div className="flex-1 bg-black rounded p-3 overflow-y-auto font-mono text-xs text-green-400 min-h-0">
        {lines.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap break-all leading-5">
            {line}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      {inputEnabled && (
        <form onSubmit={sendCommand} className="flex gap-2 mt-2">
          <div className="flex overflow-hidden rounded border border-mc-border text-xs">
            <button
              type="button"
              onClick={() => setInputMode("command")}
              className={`px-2 py-1 ${inputMode === "command" ? "bg-mc-green text-white" : "bg-mc-panel text-gray-300"}`}
            >
              Command
            </button>
            <button
              type="button"
              onClick={() => setInputMode("chat")}
              className={`px-2 py-1 ${inputMode === "chat" ? "bg-mc-green text-white" : "bg-mc-panel text-gray-300"}`}
            >
              Chat
            </button>
          </div>
          <span className="text-mc-green font-mono">&gt;</span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-mc-panel border border-mc-border rounded px-3 py-1 text-sm font-mono text-white focus:outline-none focus:border-mc-green"
            placeholder={inputMode === "chat" ? "Message to server chat..." : placeholder}
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
      )}
    </div>
  );
}
