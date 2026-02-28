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
      className={`fixed left-0 top-16 z-20 flex h-[calc(100vh-4rem)] flex-col border-r border-gray-700 bg-gray-900 transition-all duration-200 ${
        sidebarOpen ? 'w-52' : 'w-16'
      }`}
    >
      <ul className="mt-4 flex flex-1 flex-col gap-1 px-2">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-600/20 text-emerald-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
              title={label}
            >
              <Icon size={20} className="shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
