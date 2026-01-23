import React from 'react';

interface ScrollToBottomProps {
    visible: boolean;
    onClick: () => void;
}

const ScrollToBottom: React.FC<ScrollToBottomProps> = ({ visible, onClick }) => {
    if (!visible) return null;

    return (
        <button
            onClick={onClick}
            className="fixed bottom-32 right-8 w-12 h-12 bg-[#F43E01] text-white rounded-full shadow-lg flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-40"
            title="Scroll to bottom"
        >
            <svg className="w-6 h-6 transform rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
        </button>
    );
};

export default ScrollToBottom;
