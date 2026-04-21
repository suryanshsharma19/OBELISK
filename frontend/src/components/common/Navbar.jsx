/**
 * Sidebar navigation with icon links.
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  LayoutDashboard,
  Search,
  Package,
  AlertTriangle,
  Bot,
  Settings,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'Analyze', icon: Search },
  { to: '/packages', label: 'Packages', icon: Package },
  { to: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { to: '/crawler', label: 'Crawler', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Navbar() {
  const sidebarOpen = useSelector((s) => s.ui.sidebarOpen);

  return (
    <nav
      className={`fixed left-0 top-20 z-20 flex h-[calc(100vh-5rem)] flex-col border-r-2 border-outline-variant bg-surface-container-lowest transition-none ${
        sidebarOpen ? 'w-52' : 'w-16'
      }`}
    >
      <ul className="mt-4 flex flex-1 flex-col gap-0">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-4 text-sm font-headline font-bold tracking-widest uppercase transition-none ${
                  isActive
                    ? 'border-l-2 border-primary-container text-primary-container bg-surface-container-highest'
                    : 'text-outline hover:text-on-surface hover:bg-surface-variant border-l-2 border-transparent'
                }`
              }
              title={label}
            >
              {({ isActive }) => (
                <>
                  <Icon size={20} className="shrink-0" strokeWidth={isActive ? 2.5 : 2} />
                  {sidebarOpen && <span className="pt-0.5">{label}</span>}
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
