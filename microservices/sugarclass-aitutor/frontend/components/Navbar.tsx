import React, { useState, useEffect } from 'react';

interface NavbarProps {
  onNewChat: () => void;
  onToggleSidebar: () => void;
  systemStatus?: 'healthy' | 'error' | 'checking';
  selectedSubject?: string | null;
}

const Navbar: React.FC<NavbarProps> = ({ onNewChat, onToggleSidebar, systemStatus = 'checking', selectedSubject }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const getTitle = () => {
    const brand = 'Sugarclass AI Tutor';
    if (selectedSubject) {
      return `${brand} | ${selectedSubject}`;
    }
    return brand;
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex justify-center p-4 transition-all duration-500 ease-in-out pointer-events-none">
      <div
        className={`
          liquid-glass flex items-center justify-between px-4 md:px-6 py-2 transition-all duration-500 ease-in-out pointer-events-auto
          ${isScrolled
            ? 'w-[92%] md:w-[70%] lg:w-[50%] rounded-full shadow-lg h-14'
            : 'w-full md:w-[95%] rounded-3xl shadow-sm h-18'
          }
        `}
      >
        <div className="flex items-center gap-2 md:gap-4">
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-full hover:bg-black/5 transition-colors text-main"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-sm ${systemStatus === 'healthy' ? 'bg-green-500' : systemStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'}`}>
              {systemStatus === 'healthy' ? '✓' : systemStatus === 'error' ? '✕' : '…'}
            </div>
            <span className={`font-bold text-[#332F33] text-lg transition-opacity duration-300 ${isScrolled ? 'hidden lg:block' : 'block'}`}>
              {getTitle()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={onNewChat}
            className="hidden md:flex items-center gap-2 px-4 py-1.5 rounded-full primary-btn text-sm font-semibold transition-all hover:scale-105 active:scale-95 shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Session
          </button>

          <button className="p-2 rounded-full hover:bg-black/5 transition-colors text-main">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>

          <div className="w-9 h-9 rounded-full border-2 border-[#F43E01]/20 p-0.5">
            <img className="w-full h-full rounded-full object-cover" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
