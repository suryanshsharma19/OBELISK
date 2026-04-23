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
  const isDark = theme === 'dark';

  return (
    <div className="flex items-center justify-between">
      <div>
        <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>Theme</p>
        <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-600'}`}>
          Currently using {theme} mode
        </p>
      </div>
      <button
        onClick={() => dispatch(toggleTheme())}
        type="button"
        className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm ${
          isDark
            ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
        }`}
      >
        {isDark ? <Sun size={16} /> : <Moon size={16} />}
        Switch to {isDark ? 'light' : 'dark'}
      </button>
    </div>
  );
}
