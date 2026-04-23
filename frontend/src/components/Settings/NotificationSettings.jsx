/**
 * Notification preferences panel.
 */

import React from 'react';
import useLocalStorage from '../../hooks/useLocalStorage';
import { STORAGE_KEYS } from '../../utils/constants';
import { useDispatch, useSelector } from 'react-redux';
import { addToast } from '../../store/slices/uiSlice';

const DEFAULT_PREFS = {
  browser: true,
  email: false,
  criticalOnly: false,
};

export default function NotificationSettings() {
  const dispatch = useDispatch();
  const theme = useSelector((s) => s.ui.theme);
  const [prefs, setPrefs] = useLocalStorage(
    STORAGE_KEYS.NOTIFICATIONS,
    DEFAULT_PREFS,
  );

  const toggle = (key) => async () => {
    if (key === 'browser' && !prefs.browser && 'Notification' in window) {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        dispatch(
          addToast({
            type: 'warning',
            message: 'Browser notification permission was not granted.',
          }),
        );
        return;
      }
    }

    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-4">
      <h3 className={`text-sm font-semibold ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Notifications</h3>

      {[
        { key: 'browser', label: 'Browser Notifications', desc: 'Show desktop notifications for new alerts' },
        { key: 'email', label: 'Email Notifications', desc: 'Receive email for critical detections' },
        { key: 'criticalOnly', label: 'Critical Only', desc: 'Only notify for critical threat levels' },
      ].map(({ key, label, desc }) => (
        <div key={key} className="flex items-center justify-between">
          <div>
            <p className={`text-sm ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{label}</p>
            <p className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-600'}`}>{desc}</p>
          </div>
          <button
            onClick={toggle(key)}
            type="button"
            className={`relative h-6 w-11 transition-colors ${
              prefs[key]
                ? 'bg-neon-600'
                : theme === 'dark'
                  ? 'bg-gray-600'
                  : 'bg-gray-300'
            }`}
            role="switch"
            aria-checked={prefs[key]}
            aria-label={`Toggle ${label}`}
          >
            <span
              className={`absolute left-0.5 top-0.5 h-5 w-5 bg-white transition-transform ${
                prefs[key] ? 'translate-x-5' : ''
              }`}
            />
          </button>
        </div>
      ))}
    </div>
  );
}
