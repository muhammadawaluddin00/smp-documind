'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  MessageSquareText,
  FileText,
  Activity,
  Settings,
} from 'lucide-react';

const links = [
  { href: '/',           label: 'Dashboard',     icon: LayoutDashboard },
  { href: '/chat',       label: 'Ask DocuMind',  icon: MessageSquareText },
  { href: '/documents',  label: 'Knowledge Base',icon: FileText },
  { href: '/evaluation', label: 'Evaluation',    icon: Activity },
  { href: '/settings',   label: 'Settings',      icon: Settings },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-64 shrink-0 border-r border-ink-100 bg-white px-4 py-6 flex flex-col gap-1">
      <Link href="/" className="flex items-center gap-2 px-2 mb-8">
        <div className="size-9 rounded-xl bg-gradient-to-br from-ink-900 to-signal-600 grid place-items-center text-white font-display font-extrabold">
          S
        </div>
        <div>
          <div className="font-display font-bold text-ink-900 leading-tight">
            DocuMind
          </div>
          <div className="text-[10px] uppercase tracking-widest text-ink-700/60">
            SMP Technology
          </div>
        </div>
      </Link>

      <nav className="flex flex-col gap-0.5">
        {links.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? path === '/' : path?.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={[
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
                active
                  ? 'bg-ink-900 text-white shadow-soft'
                  : 'text-ink-700 hover:bg-ink-50',
              ].join(' ')}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-xl border border-ink-100 bg-ink-50 p-3 text-xs text-ink-700">
        <div className="font-semibold text-ink-900 mb-1">SLO status</div>
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-ok-500 animate-pulse" />
          All targets met
        </div>
      </div>
    </aside>
  );
}
