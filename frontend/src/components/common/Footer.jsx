/**
 * Minimal footer bar displayed at the bottom of the main content area.
 */

import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-neutral-950 w-full border-t-2 border-outline-variant flex flex-col md:flex-row justify-between items-center px-8 py-6 gap-4 z-50">
      <div className="text-lg font-bold text-primary-container font-headline uppercase">OBELISK</div>
      
      <div className="flex flex-wrap justify-center gap-6 font-mono text-xs tracking-tight">
        <a 
          href="https://github.com/suryanshsharma19/OBELISK" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-outline hover:text-primary-container uppercase transition-none"
        >
          GITHUB_REPO
        </a>
        <a 
          href="https://github.com/suryanshsharma19" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-outline hover:text-primary-container uppercase transition-none"
        >
          DEVELOPER_PROFILE
        </a>
      </div>
      
      <div className="font-mono text-xs tracking-tight text-outline uppercase text-center md:text-right">
        DEVELOPED BY SURYANSH SHARMA.
      </div>
    </footer>
  );
}
