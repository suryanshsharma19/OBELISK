import React, { useState } from 'react';
import { BlastRadius } from '../components/NetworkGraph/BlastRadius';
import { Search } from 'lucide-react';

export default function BlastRadiusPage() {
  const [pkgName, setPkgName] = useState('');
  const [activePackage, setActivePackage] = useState('lodash');

  const handleSearch = (e) => {
    e.preventDefault();
    if (pkgName.trim()) setActivePackage(pkgName.trim());
  };

  return (
    <div className="flex h-full flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Vulnerability Blast Radius</h1>
        <p className="text-gray-500">Visualize dependency cascades and infection propagation.</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1 max-w-md">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search size={18} className="text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full rounded-md border-0 py-2.5 pl-10 pr-4 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 dark:bg-gray-800 dark:text-gray-100 dark:ring-gray-700"
            placeholder="Search package (e.g. lodash)"
            value={pkgName}
            onChange={(e) => setPkgName(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          Simulate Cascade
        </button>
      </form>

      <div className="flex-1 min-h-[600px]">
        {activePackage && <BlastRadius pkgName={activePackage} />}
      </div>
    </div>
  );
}
