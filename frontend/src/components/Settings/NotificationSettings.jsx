/**
 * Notification preferences panel.
 */

import React from 'react';
import useLocalStorage from '../../hooks/useLocalStorage';
import { STORAGE_KEYS } from '../../utils/constants';

const DEFAULT_PREFS = {
  browser: true,
  email: false,
  criticalOnly: false,
};

export default function NotificationSettings() {
  const [prefs, setPrefs] = useLocalStorage(
    STORAGE_KEYS.NOTIFICATIONS,
    DEFAULT_PREFS,
  );

  const toggle = (key) => () => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-300">Notifications</h3>

      {[
        { key: 'browser', label: 'Browser Notifications', desc: 'Show desktop notifications for new alerts' },
        { key: 'email', label: 'Email Notifications', desc: 'Receive email for critical detections' },
        { key: 'criticalOnly', label: 'Critical Only', desc: 'Only notify for critical threat levels' },
      ].map(({ key, label, desc }) => (
        <div key={key} className="flex items-center justify-between">
          <div>
            <p className="text-sm text-white">{label}</p>
            <p className="text-xs text-gray-500">{desc}</p>
          </div>
          <button
            onClick={toggle(key)}
            className={`relative h-6 w-11 rounded-full transition-colors ${
              prefs[key] ? 'bg-neon-600' : 'bg-gray-600'
            }`}
            role="switch"
            aria-checked={prefs[key]}
          >
            <span
              className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                prefs[key] ? 'translate-x-5' : ''
              }`}
            />
          </button>
        </div>
      ))}
    </div>
  );
}
