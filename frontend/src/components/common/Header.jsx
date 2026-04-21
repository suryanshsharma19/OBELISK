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
    <header className="sticky top-0 z-50 flex h-20 items-center justify-between border-b-2 border-outline-variant bg-neutral-950 px-4 sm:px-6 lg:px-8 w-full flat no-shadows">
      {/* Left: hamburger + logo */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="rounded-none p-2 text-outline hover:bg-primary-container hover:text-neutral-950 transition-none lg:hidden border-2 border-transparent"
          aria-label="Toggle sidebar"
        >
          <Menu size={24} />
        </button>

        <Link to="/" className="flex items-center gap-3">
          <img src="/logo.svg" alt="OBELISK Logo" className="h-8 w-8 object-contain drop-shadow-[0_0_8px_#00ff88]" />
          {/* Neon Aegis Logo Extracted */}
          <span className="text-3xl font-black tracking-tighter text-primary-container font-headline uppercase leading-none hidden sm:inline-block">
            OBELISK
          </span>
        </Link>
      </div>

      {/* Center: Hidden Links for larger screens (from extracted style) */}
      <nav className="hidden md:flex items-center gap-8 font-headline uppercase tracking-[0.2em] font-bold text-sm">
        <Link to="/analyze" className="text-outline hover:bg-primary-container hover:text-neutral-950 transition-none p-2 -m-2">Analyze</Link>
        <Link to="/dashboard" className="text-outline hover:bg-primary-container hover:text-neutral-950 transition-none p-2 -m-2">Dashboard</Link>
      </nav>

      {/* Right: notifications + action button */}
      <div className="flex items-center gap-5 font-headline uppercase tracking-[0.2em] font-bold text-xs">
        <Link
          to="/alerts"
          className="relative text-outline hover:bg-primary-container hover:text-neutral-950 transition-none p-2 -m-2"
          aria-label="Alerts"
        >
          <Bell size={20} />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-[16px] w-[16px] items-center justify-center bg-primary-container text-[10px] font-black text-on-primary-container">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>
        
        <Link
          to="/analyze"
          className="hidden sm:inline-block bg-primary-container text-on-primary-container border-2 border-primary-fixed-dim py-2 px-4 hover:bg-neutral-950 hover:text-primary-container transition-none rounded-none"
        >
          GET ACCESS
        </Link>
      </div>
    </header>
  );
}
