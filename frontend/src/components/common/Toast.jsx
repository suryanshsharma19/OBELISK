// Toast notification component

import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { removeToast } from '../../store/slices/uiSlice';
import { X, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';

const ICONS = {
  success: <CheckCircle size={18} className="text-neon-400" />,
  error: <XCircle size={18} className="text-red-400" />,
  warning: <AlertTriangle size={18} className="text-amber-400" />,
  info: <Info size={18} className="text-blue-400" />,
};

function ToastItem({ toast }) {
  const dispatch = useDispatch();

  useEffect(() => {
    const timer = setTimeout(
      () => dispatch(removeToast(toast.id)),
      toast.duration || 5000,
    );
    return () => clearTimeout(timer);
  }, [dispatch, toast.id, toast.duration]);

  return (
    <div className="flex items-start gap-2 rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 shadow-lg">
      {ICONS[toast.type] || ICONS.info}
      <span className="flex-1 text-sm text-gray-200">{toast.message}</span>
      <button
        onClick={() => dispatch(removeToast(toast.id))}
        className="text-gray-500 hover:text-white"
        aria-label="Dismiss"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export default function Toast() {
  const toasts = useSelector((s) => s.ui.toasts);

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
