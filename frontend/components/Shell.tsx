"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const nav = [
  ["Home", "/"],
  ["Projects", "/projects"],
  ["Compare", "/compare"],
  ["Observability", "/observability"],
  ["Failures", "/failures"],
  ["Review", "/review"],
  ["Reports", "/reports"],
  ["Settings", "/settings"]
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-line bg-white px-5 py-6 lg:block">
        <div className="mb-8">
          <div className="text-lg font-semibold tracking-normal">AgentOps Studio</div>
          <div className="mt-1 text-sm text-slate-500">Local evaluation and observability</div>
        </div>
        <nav className="space-y-1">
          {nav.map(([label, href]) => (
            <Link key={href} href={href} className={`block rounded-md px-3 py-2 text-sm font-medium ${pathname === href ? "bg-ink text-white" : "text-slate-700 hover:bg-panel"}`}>
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="lg:pl-72">
        <div className="mx-auto max-w-7xl px-5 py-6">{children}</div>
      </main>
    </div>
  );
}
