import React, { useState, useEffect } from 'react';

export interface UserSettings {
  displayName: string;
  curriculum: string;
  gradeLevel: string;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: UserSettings;
  onSave: (settings: UserSettings) => void;
}

const CURRICULA = [
  { value: 'CIE_IGCSE', label: 'Cambridge IGCSE' },
  { value: 'CIE_AS', label: 'Cambridge AS Level' },
  { value: 'CIE_A2', label: 'Cambridge A2 Level' },
  { value: 'EDEXCEL_IGCSE', label: 'Edexcel IGCSE' },
  { value: 'EDEXCEL_AS', label: 'Edexcel AS Level' },
  { value: 'EDEXCEL_A2', label: 'Edexcel A2 Level' },
  { value: 'IB_MYP', label: 'IB MYP' },
  { value: 'IB_DP', label: 'IB Diploma' },
];

const GRADE_LEVELS = [
  { value: 'Year_9', label: 'Year 9' },
  { value: 'Year_10', label: 'Year 10' },
  { value: 'Year_11', label: 'Year 11 (GCSE)' },
  { value: 'Year_12', label: 'Year 12 (AS Level)' },
  { value: 'Year_13', label: 'Year 13 (A2 Level)' },
];

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, settings, onSave }) => {
  const [localSettings, setLocalSettings] = useState<UserSettings>(settings);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings, isOpen]);

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  const handleReset = () => {
    setLocalSettings(settings);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[80] animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
        <div
          className="bg-white rounded-3xl shadow-2xl w-full max-w-md max-h-[85vh] overflow-hidden animate-in zoom-in-95 fade-in duration-300"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-black/5">
            <h2 className="text-xl font-bold text-[#332F33]">Settings</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-black/5 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-5">
            {/* Display Name */}
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={localSettings.displayName}
                onChange={(e) => setLocalSettings({ ...localSettings, displayName: e.target.value })}
                placeholder="Enter your name"
                className="w-full px-4 py-3 rounded-xl border border-black/10 focus:outline-none focus:ring-2 focus:ring-[#F43E01]/20 focus:border-[#F43E01] transition-all"
              />
            </div>

            {/* Curriculum */}
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                Curriculum
              </label>
              <select
                value={localSettings.curriculum}
                onChange={(e) => setLocalSettings({ ...localSettings, curriculum: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-black/10 focus:outline-none focus:ring-2 focus:ring-[#F43E01]/20 focus:border-[#F43E01] transition-all bg-white"
              >
                {CURRICULA.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-2">Select your exam board curriculum</p>
            </div>

            {/* Grade Level */}
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                Grade Level
              </label>
              <select
                value={localSettings.gradeLevel}
                onChange={(e) => setLocalSettings({ ...localSettings, gradeLevel: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-black/10 focus:outline-none focus:ring-2 focus:ring-[#F43E01]/20 focus:border-[#F43E01] transition-all bg-white"
              >
                {GRADE_LEVELS.map((g) => (
                  <option key={g.value} value={g.value}>{g.label}</option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-2">This helps tailor explanations to your level</p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-black/5 bg-black/[0.02]">
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-semibold text-gray-500 hover:text-gray-700 transition-colors"
            >
              Reset
            </button>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-5 py-2.5 rounded-xl text-sm font-semibold text-gray-600 hover:bg-black/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-[#F43E01] hover:bg-[#d63501] transition-colors shadow-sm"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default SettingsModal;
