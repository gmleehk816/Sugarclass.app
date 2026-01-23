import React from 'react';

interface Chat {
    id: number;
    title: string;
    lastMessage: string;
    createdAt: string;
    updatedAt: string;
    messages?: Array<{ question: string; answer: string }>;
}

interface RecentChatsProps {
    chats: Chat[];
    onLoadChat: (chatId: number) => void;
    onClearHistory: () => void;
}

const RecentChats: React.FC<RecentChatsProps> = ({ chats, onLoadChat, onClearHistory }) => {
    const formatTime = (dateString: string): string => {
        const date = new Date(dateString);
        const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="border-t border-black/10 pt-4">
            <div className="flex items-center justify-between mb-3">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">
                    Recent Chats
                </p>
                {chats.length > 0 && (
                    <button
                        onClick={onClearHistory}
                        className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                        title="Clear all chats"
                    >
                        Clear All
                    </button>
                )}
            </div>
            
            {chats.length === 0 ? (
                <p className="text-sm text-gray-400 italic px-1">No recent chats</p>
            ) : (
                <div className="space-y-2 max-h-40 overflow-y-auto">
                    {chats.map((chat) => (
                        <button
                            key={chat.id}
                            onClick={() => onLoadChat(chat.id)}
                            className="w-full text-left p-3 rounded-xl bg-[#F0F0E9] hover:bg-white border border-black/5 hover:border-[#F43E01] transition-all group"
                        >
                            <div className="text-sm font-semibold text-[#332F33] truncate group-hover:text-[#F43E01]">
                                {chat.title}
                            </div>
                            <div className="text-xs text-gray-500 truncate mt-1">
                                {chat.lastMessage}
                            </div>
                            <div className="text-[10px] text-gray-400 mt-1">
                                {formatTime(chat.updatedAt)}
                            </div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default RecentChats;
