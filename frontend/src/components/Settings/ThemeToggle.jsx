/**
 * Dark / light theme toggle switch.
 */

import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { toggleTheme } from '../../store/slices/uiSlice';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle() {
  const dispatch = useDispatch();
  const theme = useSelector((s) => s.ui.theme);

  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-white">Theme</p>
        <p className="text-xs text-gray-500">
          Currently using {theme} mode
        </p>
      </div>
      <button
        onClick={() => dispatch(toggleTheme())}
        className="flex items-center gap-2 rounded-lg bg-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-600"
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        Switch to {theme === 'dark' ? 'light' : 'dark'}
      </button>
    </div>
  );
}
