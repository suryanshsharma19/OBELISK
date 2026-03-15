/**
 * Settings page container — groups ThemeToggle and NotificationSettings.
 */

import React from 'react';
import ThemeToggle from './ThemeToggle';
import NotificationSettings from './NotificationSettings';

export default function Settings() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Settings</h1>

      <div className="space-y-6 rounded-xl border border-gray-700 bg-gray-800 p-6">
        <ThemeToggle />
        <hr className="border-gray-700" />
        <NotificationSettings />
      </div>

      {/* About section */}
      <div className="rounded-xl border border-gray-700 bg-gray-800 p-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-300">About OBELISK</h3>
        <p className="text-xs text-gray-500">
          AI-Powered Supply Chain Attack Detection System. Built with
          FastAPI, React, Neo4j, PostgreSQL, and state-of-the-art ML models.
        </p>
        <p className="mt-2 text-xs text-gray-600">Version 1.0.0</p>
      </div>
    </div>
  );
}
