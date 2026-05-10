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
    <div className="max-w-5xl mx-auto h-[calc(100vh-10rem)] flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Server Console</h1>
      <div className="flex-1 bg-mc-panel border border-mc-border rounded-lg p-4 flex flex-col min-h-0">
        <ConsoleView />
      </div>
    </div>
  );
}
