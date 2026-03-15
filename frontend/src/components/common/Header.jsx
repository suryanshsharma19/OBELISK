/**
 * Top header bar with logo, search, notification bell, and theme toggle.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Bell, Shield, Sun, Moon, Menu } from 'lucide-react';
import { toggleTheme, toggleSidebar } from '../../store/slices/uiSlice';

export default function Header() {
  const dispatch = useDispatch();
  const theme = useSelector((s) => s.ui.theme);
  const unreadCount = useSelector((s) => s.alerts.unreadCount);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-gray-700 bg-gray-900 px-4">
      {/* Left: hamburger + logo */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white"
          aria-label="Toggle sidebar"
        >
          <Menu size={20} />
        </button>

        <Link to="/" className="flex items-center gap-2 text-white">
          <Shield size={24} className="text-emerald-400" />
          <span className="text-lg font-bold tracking-wide">OBELISK</span>
        </Link>
      </div>

      {/* Right: notifications + theme */}
      <div className="flex items-center gap-3">
        <Link
          to="/alerts"
          className="relative rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white"
          aria-label="Alerts"
        >
          <Bell size={20} />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>

        <button
          onClick={() => dispatch(toggleTheme())}
          className="rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>
    </header>
  );
}
