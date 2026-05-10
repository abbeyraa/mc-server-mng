"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/console", label: "Console" },
  { href: "/profiles", label: "Profiles" },
  { href: "/worlds", label: "Worlds" },
  { href: "/mods", label: "Mods" },
  { href: "/backup", label: "Backups" },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <nav className="bg-mc-panel border-b border-mc-border px-6 py-3 flex items-center gap-6">
      <span className="text-mc-green font-bold text-lg tracking-wide">⛏ MC Manager</span>
      <div className="flex gap-4 flex-1">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`text-sm ${pathname === l.href ? "text-mc-green font-semibold" : "text-gray-400 hover:text-white"}`}
          >
            {l.label}
          </Link>
        ))}
      </div>
      <button onClick={logout} className="text-sm text-gray-400 hover:text-red-400">
        Logout
      </button>
    </nav>
  );
}
