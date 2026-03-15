/**
 * 404 Not Found page.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <FileQuestion size={64} className="text-gray-600" />
      <h1 className="text-3xl font-bold text-white">404</h1>
      <p className="text-gray-400">The page you’re looking for doesn’t exist.</p>
      <Link
        to="/"
        className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
      >
        Go Home
      </Link>
    </div>
  );
}
