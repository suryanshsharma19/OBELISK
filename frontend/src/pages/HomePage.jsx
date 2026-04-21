/**
 * Landing page — brutalist hero section with quick-start CTA.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Terminal } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex flex-col flex-1 relative grid-bg overflow-hidden text-on-background">
      <section className="relative z-10 container mx-auto px-6 py-16 md:py-32 flex flex-col lg:flex-row items-center gap-16 flex-grow w-full max-w-7xl">
        {/* Left: Typography & Actions */}
        <div className="flex-1 space-y-10">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 border-2 border-outline-variant bg-surface-container-low px-3 py-1 font-mono text-xs text-primary-container uppercase tracking-widest">
              <span className="w-2 h-2 bg-primary-container"></span>
              SYSTEM: ONLINE & SECURE
            </div>
            <h1 className="font-headline text-5xl md:text-7xl font-bold uppercase tracking-tighter leading-[0.9] text-on-surface break-words">
              OBELISK:<br/>
              <span className="text-primary-container">AI-POWERED</span><br/>
              SUPPLY CHAIN<br/>
              SECURITY.
            </h1>
          </div>
          <p className="font-body text-on-surface-variant max-w-xl text-lg leading-relaxed border-l-2 border-outline-variant pl-4">
            Identify, isolate, and neutralize malicious dependencies before they breach your CI/CD pipeline. Continuous analysis of npm, PyPI, and RubyGems.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 pt-4">
            <Link to="/analyze" className="bg-primary-container text-on-primary-container font-headline font-bold uppercase tracking-widest px-8 py-4 border-2 border-primary-fixed-dim hover:bg-background hover:text-primary-container hover:border-primary-container transition-none flex items-center justify-center gap-2">
              SCAN YOUR DEPENDENCIES 
              <ArrowRight size={20} />
            </Link>
            <Link to="/alerts" className="bg-transparent text-primary-container font-headline font-bold uppercase tracking-widest px-8 py-4 border-2 border-primary-container hover:bg-primary-container hover:text-on-primary-container transition-none flex items-center justify-center gap-2">
              VIEW THREAT INTEL
            </Link>
          </div>
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6 pt-8 border-t-2 border-outline-variant">
            <div className="space-y-1">
              <div className="font-mono text-xs text-on-surface-variant uppercase tracking-wider">Accuracy Rate</div>
              <div className="font-headline text-3xl font-bold text-primary-container">84.7%</div>
            </div>
            <div className="space-y-1">
              <div className="font-mono text-xs text-on-surface-variant uppercase tracking-wider">Training Datapoints</div>
              <div className="font-headline text-3xl font-bold text-on-surface">27K+</div>
            </div>
            <div className="space-y-1 hidden md:block">
              <div className="font-mono text-xs text-on-surface-variant uppercase tracking-wider">Malicious Samples</div>
              <div className="font-headline text-3xl font-bold text-error">1.5K+</div>
            </div>
          </div>
        </div>
        
        {/* Right: Terminal Window */}
        <div className="flex-1 w-full max-w-2xl relative">
          <div className="absolute -inset-2 border-2 border-outline-variant opacity-50 hidden md:block"></div>
          <div className="absolute -inset-4 border-2 border-outline-variant opacity-20 hidden md:block"></div>
          <div className="bg-surface-container-lowest border-2 border-outline-variant relative flex flex-col shadow-2xl overflow-hidden h-[500px]">
            {/* Terminal Header */}
            <div className="bg-surface-container border-b-2 border-outline-variant px-4 py-3 flex justify-between items-center scanline-bg">
              <div className="flex items-center gap-3">
                <Terminal size={16} className="text-primary-container" />
                <span className="font-mono text-xs text-on-surface tracking-widest">OBELISK_SCANNER_v2.4.1</span>
              </div>
              <div className="flex gap-2">
                <div className="w-3 h-3 border border-outline-variant bg-surface-container-highest"></div>
                <div className="w-3 h-3 border border-outline-variant bg-surface-container-highest"></div>
                <div className="w-3 h-3 border border-error bg-error opacity-50"></div>
              </div>
            </div>
            
            {/* Terminal Body */}
            <div className="p-6 font-mono text-sm space-y-3 overflow-y-auto flex-grow text-on-surface-variant bg-surface-container-lowest relative">
              <div className="absolute top-0 left-0 right-0 h-1 bg-primary-container opacity-30 shadow-[0_0_10px_#00ff88]"></div>
              
              <div className="flex gap-4">
                <span className="text-outline">10:42:01</span>
                <span className="text-on-surface">Initializing dependency tree analysis...</span>
              </div>
              <div className="flex gap-4">
                <span className="text-outline">10:42:02</span>
                <span className="text-on-surface">Fetching node_modules metadata... <span className="text-primary-container">[OK]</span></span>
              </div>
              <div className="flex gap-4">
                <span className="text-outline">10:42:05</span>
                <span className="text-on-surface">Scanning <span className="text-primary-container">lodash@4.17.21</span>... <span className="text-secondary-container bg-on-secondary-container px-1">CLEAN</span></span>
              </div>
              <div className="flex gap-4">
                <span className="text-outline">10:42:06</span>
                <span className="text-on-surface">Scanning <span className="text-primary-container">react@18.2.0</span>... <span className="text-secondary-container bg-on-secondary-container px-1">CLEAN</span></span>
              </div>
              
              <div className="flex gap-4 mt-4 border-l-2 border-error pl-4 bg-error-container/20 py-2">
                <span className="text-error">10:42:08</span>
                <div className="flex flex-col">
                  <span className="text-error font-bold uppercase">ALERT: Malicious payload detected</span>
                  <span>Target: <span className="text-on-surface bg-surface-variant px-1">colors-js-fake@1.0.3</span></span>
                  <span>Signature: <span className="text-on-error-container">CWE-506: Embedded Malicious Code</span></span>
                  <span>Action: <span className="text-on-surface uppercase underline">Quarantined</span></span>
                </div>
              </div>
              
              <div className="flex gap-4">
                <span className="text-outline">10:42:10</span>
                <span className="text-on-surface">Scanning <span className="text-primary-container">express@4.18.2</span>... <span className="text-secondary-container bg-on-secondary-container px-1">CLEAN</span></span>
              </div>
              <div className="flex gap-4">
                <span className="text-outline">10:42:11</span>
                <span className="text-on-surface animate-pulse">Awaiting next block...<span className="text-primary-container">_</span></span>
              </div>
            </div>
            
            {/* Terminal Footer */}
            <div className="bg-surface-container border-t-2 border-outline-variant px-4 py-2 flex justify-between items-center font-mono text-[10px] text-outline">
              <span>CPU: 14% | MEM: 1.2GB</span>
              <span>NODE: AMS-04</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
