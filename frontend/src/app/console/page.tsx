"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import ConsoleView from "@/components/ConsoleView";

export default function ConsolePage() {
  const router = useRouter();
  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
  }, [router]);

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-10rem)] flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Console</h1>
      <div className="grid flex-1 min-h-0 gap-4 lg:grid-cols-2">
        <div className="bg-mc-panel border border-mc-border rounded-lg p-4 flex flex-col min-h-0">
          <ConsoleView title="Minecraft Server" placeholder="time set day" />
        </div>
        <div className="bg-mc-panel border border-mc-border rounded-lg p-4 flex flex-col min-h-0">
          <ConsoleView path="/ws/playit-console" title="Playit.gg" inputEnabled={false} />
        </div>
      </div>
    </div>
  );
}
