/**
 * Settings page container — groups ThemeToggle and NotificationSettings.
 */

import React from 'react';
import ThemeToggle from './ThemeToggle';
import NotificationSettings from './NotificationSettings';
import { useSelector } from 'react-redux';

export default function Settings() {
  const theme = useSelector((s) => s.ui.theme);
  const isDark = theme === 'dark';

  return (
    <div className="space-y-6">
      <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Settings</h1>

      <div
        className={`space-y-6 rounded-xl p-6 ${
          isDark ? 'border border-gray-700 bg-gray-800' : 'border border-gray-200 bg-white'
        }`}
      >
        <ThemeToggle />
        <hr className={isDark ? 'border-gray-700' : 'border-gray-200'} />
        <NotificationSettings />
      </div>

      {/* About section */}
      <div
        className={`rounded-xl p-6 ${
          isDark ? 'border border-gray-700 bg-gray-800' : 'border border-gray-200 bg-white'
        }`}
      >
        <h3 className={`mb-2 text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>About OBELISK</h3>
        <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-600'}`}>
          AI-Powered Supply Chain Attack Detection System. Built with
          FastAPI, React, Neo4j, PostgreSQL, and state-of-the-art ML models.
        </p>
        <p className={`mt-2 text-xs ${isDark ? 'text-gray-600' : 'text-gray-500'}`}>Version 1.0.0</p>
      </div>
    </div>
  );
}
