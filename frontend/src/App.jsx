// Root application component

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

import Header from './components/common/Header';
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import Toast from './components/common/Toast';
import ErrorBoundary from './components/common/ErrorBoundary';

import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import AnalyzePage from './pages/AnalyzePage';
import PackagesPage from './pages/PackagesPage';
import AlertsPage from './pages/AlertsPage';
import SettingsPage from './pages/SettingsPage';
import PackageDetailPage from './pages/PackageDetailPage';
import NotFoundPage from './pages/NotFoundPage';

// Lazy-load the crawler page to keep initial bundle small
const CrawlerPage = React.lazy(() =>
  import('./components/Crawler/CrawlerMonitor'),
);

export default function App() {
  const sidebarOpen = useSelector((s) => s.ui.sidebarOpen);
  const theme = useSelector((s) => s.ui.theme);

  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return (
    <div
      className={`flex min-h-screen flex-col ${
        theme === 'dark' ? 'bg-gray-950 text-gray-100' : 'bg-gray-100 text-gray-900'
      }`}
    >
      <Header />
      <Navbar />

      {/* Main content area — offset by the sidebar width */}
      <main
        className={`flex-1 transition-all duration-200 pt-4 pb-8 px-6 ${
          sidebarOpen ? 'ml-52' : 'ml-16'
        }`}
      >
        <ErrorBoundary>
          <React.Suspense fallback={<div className="py-12 text-center text-gray-500">Loading…</div>}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/analyze" element={<AnalyzePage />} />
              <Route path="/packages" element={<PackagesPage />} />
              <Route path="/packages/:id" element={<PackageDetailPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/crawler" element={<CrawlerPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/404" element={<NotFoundPage />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </React.Suspense>
        </ErrorBoundary>
      </main>

      <Footer />
      <Toast />
    </div>
  );
}
