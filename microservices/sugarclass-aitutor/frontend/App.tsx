import React, { useState, useRef, useEffect } from 'react';
import Navbar from './components/Navbar';
import SourceCard from './components/SourceCard';
import DiagramDisplay from './components/DiagramDisplay';
import ScrollToBottom from './components/ScrollToBottom';
import RecentChats from './components/RecentChats';
import SettingsModal, { UserSettings } from './components/SettingsModal';
import { Message, Role, Source } from './types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  streamQuery,
  getHealth,
  getSubjects,
  startTutorSession,
  streamChatWithTutor,
  endTutorSession,
  Subject
} from './services/apiService';

interface ChatHistory {
  id: number;
  title: string;
  lastMessage: string;
  createdAt: string;
  updatedAt: string;
  messages: Array<{ question: string; answer: string; time: string }>;
}

const DEFAULT_SETTINGS: UserSettings = {
  displayName: '',
  curriculum: 'CIE_IGCSE',
  gradeLevel: 'Year_11',
};

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: Role.MODEL,
      text: "Hello! I'm your AITutor. Select a subject to start learning, or ask me anything about your materials.",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'error' | 'checking'>('checking');
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectSearchTerm, setSubjectSearchTerm] = useState('');
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<string | null>(null);
  const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number>(Date.now());
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [userScrolledUp, setUserScrolledUp] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [userSettings, setUserSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageContainerRef = useRef<HTMLDivElement>(null);

  const filteredSubjects = subjects.filter(subject =>
    subject.name.toLowerCase().includes(subjectSearchTerm.toLowerCase()) ||
    subject.syllabus.toLowerCase().includes(subjectSearchTerm.toLowerCase())
  );

  useEffect(() => {
    // Initialize user ID
    let userId = localStorage.getItem('tutor_user_id');
    if (!userId) {
      userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('tutor_user_id', userId);
    }
    setUserId(userId);

    // Load subjects
    loadSubjects();

    // Check system health
    checkHealth();

    // Set up polling intervals
    const healthInterval = setInterval(checkHealth, 30000); // 30 seconds
    const subjectsInterval = setInterval(loadSubjects, 21600000); // 6 hours

    // Restore selected subject and chapter from localStorage
    const savedSubject = localStorage.getItem('tutor_subject');
    const savedChapter = localStorage.getItem('tutor_chapter');
    if (savedSubject) {
      setSelectedSubject(savedSubject);
      setSelectedChapter(savedChapter);
      setExpandedSubjects(new Set([savedSubject]));
      updateWelcomeMessage(savedSubject, savedChapter);
    }

    return () => {
      clearInterval(healthInterval);
      clearInterval(subjectsInterval);
    };
  }, []);


  // Load chat history from localStorage
  useEffect(() => {
    const savedChats = localStorage.getItem('ai_tutor_chats');
    if (savedChats) {
      try {
        setChatHistory(JSON.parse(savedChats));
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
  }, []);

  // Load user settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('ai_tutor_settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setUserSettings({ ...DEFAULT_SETTINGS, ...parsed });
      } catch (error) {
        console.error('Failed to load user settings:', error);
      }
    }
  }, []);

  const handleSaveSettings = (newSettings: UserSettings) => {
    setUserSettings(newSettings);
    localStorage.setItem('ai_tutor_settings', JSON.stringify(newSettings));

    // Update curriculum and grade in localStorage for session start
    localStorage.setItem('tutor_curriculum', newSettings.curriculum);
    localStorage.setItem('tutor_grade', newSettings.gradeLevel);
  };

  // Auto-scroll detection
  useEffect(() => {
    const container = messageContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
      setUserScrolledUp(!isAtBottom);
      setShowScrollButton(!isAtBottom);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  const checkHealth = async () => {
    try {
      await getHealth();
      setSystemStatus('healthy');
    } catch (err) {
      console.error('Failed to connect to backend:', err);
      setSystemStatus('error');
    }
  };

  const loadSubjects = async () => {
    try {
      const data = await getSubjects();
      setSubjects(data.subjects);

      // Auto-expand the currently selected subject if any
      const savedSubject = localStorage.getItem('tutor_subject');
      if (savedSubject) {
        setExpandedSubjects(prev => new Set([...Array.from(prev), savedSubject]));
      }
    } catch (error) {
      console.error('Failed to load subjects:', error);
    }
  };

  const selectSubject = async (subjectName: string, chapterName: string | null = null) => {
    setSelectedSubject(subjectName);
    setSelectedChapter(chapterName);
    localStorage.setItem('tutor_subject', subjectName);
    if (chapterName) {
      localStorage.setItem('tutor_chapter', chapterName);
    } else {
      localStorage.removeItem('tutor_chapter');
    }

    // Clear chat and update welcome message
    setMessages([
      {
        id: Date.now().toString(),
        role: Role.MODEL,
        text: chapterName
          ? `Welcome! Let's study **${subjectName}**: *${chapterName}*. What would you like to know about this chapter?`
          : getSubjectWelcomeMessage(subjectName),
        timestamp: new Date()
      }
    ]);

    // Start new tutor session
    try {
      if (userId) {
        const sessionResponse = await startTutorSession({
          user_id: userId,
          subject: subjectName,
          chapter: chapterName || undefined,
          curriculum: localStorage.getItem('tutor_curriculum') || 'CIE_IGCSE',
          grade_level: localStorage.getItem('tutor_grade') || 'GCSE'
        });
        setSessionId(sessionResponse.session_id);
        console.log('Session started:', sessionResponse.session_id, 'chapter:', chapterName);
      }
    } catch (error) {
      console.error('Failed to start tutor session:', error);
    }

    // Close sidebar on mobile
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
  };

  const getSubjectWelcomeMessage = (subject: string): string => {
    const subjectLower = subject.toLowerCase();

    if (subjectLower.includes('engineering')) {
      return `Ready to explore ${subject}! From materials and mechanics to electronics and systems - what would you like to learn today?`;
    } else if (subjectLower.includes('math') || subjectLower.includes('mathematics')) {
      return `Ready to explore ${subject}! I can help with algebra, calculus, geometry, and more. What topic shall we start with?`;
    } else if (subjectLower.includes('physics')) {
      return `Let's dive into ${subject}! From mechanics to waves and electricity - what would you like to learn today?`;
    } else if (subjectLower.includes('chemistry')) {
      return `Welcome to ${subject}! Organic, inorganic, physical chemistry - pick a topic and let's explore together!`;
    } else if (subjectLower.includes('biology')) {
      return `${subject} time! Cells, genetics, ecology - there's so much to discover. What interests you most?`;
    } else if (subjectLower.includes('music')) {
      return `Let's study ${subject}! From theory to composition and history - what would you like to learn about?`;
    } else if (subjectLower.includes('ict') || subjectLower.includes('computer') || subjectLower.includes('cs')) {
      return `Let's study ${subject}! From hardware and software to programming and networking - what topic would you like to explore?`;
    } else if (subjectLower.includes('english')) {
      return `${subject} time! Literature, language, writing - what would you like to work on today?`;
    } else if (subjectLower.includes('history')) {
      return `Ready to explore ${subject}! From ancient to modern times - what era or topic interests you?`;
    } else if (subjectLower.includes('geography')) {
      return `${subject} exploration time! Physical and human geography - what would you like to learn?`;
    }

    return `Let's study ${subject}! What would you like to learn today?`;
  };

  const updateWelcomeMessage = (subject: string | null, chapter: string | null = null) => {
    if (!subject) {
      setMessages([
        {
          id: Date.now().toString(),
          role: Role.MODEL,
          text: "Hello! I'm your Sugarclass AI Tutor. Select a subject to start learning, or ask me anything about your materials.",
          timestamp: new Date()
        }
      ]);
    } else {
      setMessages([
        {
          id: Date.now().toString(),
          role: Role.MODEL,
          text: chapter
            ? `Welcome back! We're studying **${subject}**: *${chapter}*. What would you like to learn next?`
            : getSubjectWelcomeMessage(subject),
          timestamp: new Date()
        }
      ]);
    }
  };

  const suggestedPrompts = [
    selectedSubject ? `Explain the basics of ${selectedSubject}` : "Show me the subjects",
    "What are the key concepts?",
    "Give me some practice questions",
    "Explain with examples",
    "How does this work?",
    "Compare and contrast"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const saveChatToHistory = (question: string, answer: string) => {
    setChatHistory(prev => {
      const chatIndex = prev.findIndex(c => c.id === currentChatId);
      let newHistory = [...prev];

      if (chatIndex !== -1) {
        const updatedChat = {
          ...prev[chatIndex],
          messages: [...prev[chatIndex].messages, { question, answer, time: new Date().toISOString() }],
          lastMessage: question,
          updatedAt: new Date().toISOString()
        };
        newHistory[chatIndex] = updatedChat;
      } else {
        const newChat: ChatHistory = {
          id: currentChatId,
          title: question.substring(0, 50),
          lastMessage: question,
          messages: [{ question, answer, time: new Date().toISOString() }],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        newHistory = [newChat, ...newHistory];
      }

      // Keep only last 20 chats
      const trimmedHistory = newHistory.slice(0, 20);
      localStorage.setItem('ai_tutor_chats', JSON.stringify(trimmedHistory));
      return trimmedHistory;
    });
  };

  const loadChatFromHistory = (chatId: number) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;

    setCurrentChatId(chatId);
    const restoredMessages: Message[] = [
      {
        id: '1',
        role: Role.MODEL,
        text: selectedSubject ? getSubjectWelcomeMessage(selectedSubject) : "Hello! I'm your AI Tutor. Select a subject to start learning, or ask me anything about your materials.",
        timestamp: new Date()
      }
    ];

    chat.messages.forEach((msg, idx) => {
      restoredMessages.push({
        id: (idx + 2).toString(),
        role: Role.USER,
        text: msg.question,
        timestamp: new Date()
      });
      restoredMessages.push({
        id: (idx + 3).toString(),
        role: Role.MODEL,
        text: msg.answer,
        timestamp: new Date()
      });
    });

    setMessages(restoredMessages);
    setSidebarOpen(false);
  };

  const clearChatHistory = () => {
    setChatHistory([]);
    localStorage.removeItem('ai_tutor_chats');
  };

  const handleSend = async (overrideInput?: string) => {
    const textToSend = overrideInput || input;
    if (!textToSend.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: Role.USER,
      text: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    const botMessageId = (Date.now() + 1).toString();
    let fullText = '';

    try {
      // Create initial empty bot message
      const initialBotMessage: Message = {
        id: botMessageId,
        role: Role.MODEL,
        text: '',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, initialBotMessage]);

      const onChunk = (chunk: string) => {
        fullText += chunk;
        setMessages(prev => prev.map(msg =>
          msg.id === botMessageId ? { ...msg, text: fullText } : msg
        ));
      };

      // Check if user has selected a subject
      if (!selectedSubject) {
        // No subject selected - show prompt to select subject
        const noSubjectMessage = "Please select a subject from the sidebar to start learning.";
        setMessages(prev => prev.map(msg =>
          msg.id === botMessageId ? { ...msg, text: noSubjectMessage } : msg
        ));
        setIsTyping(false);
        return;
      }

      // Start a session if one doesn't exist
      let currentSessionId = sessionId;
      if (!currentSessionId && userId) {
        try {
          const sessionResponse = await startTutorSession({
            user_id: userId,
            subject: selectedSubject,
            chapter: selectedChapter || undefined,
            curriculum: localStorage.getItem('tutor_curriculum') || 'CIE_IGCSE',
            grade_level: localStorage.getItem('tutor_grade') || 'GCSE'
          });
          currentSessionId = sessionResponse.session_id;
          setSessionId(currentSessionId);
        } catch (error) {
          console.error('Failed to start session:', error);
          setMessages(prev => prev.map(msg =>
            msg.id === botMessageId ? { ...msg, text: 'Failed to start session. Please try selecting a subject again.' } : msg
          ));
          setIsTyping(false);
          return;
        }
      }

      // Use tutor chat streaming
      if (currentSessionId) {
        await streamChatWithTutor(
          { session_id: currentSessionId, message: textToSend },
          onChunk,
          (error) => { throw new Error(error); },
          (metadata) => {
            // Update final message with metadata
            setMessages(prev => prev.map(msg =>
              msg.id === botMessageId ? {
                ...msg,
                sources: metadata.sources,
                text: metadata.quiz_active ? fullText + '\n\n📝 Quiz mode active - answer the question above' : fullText
              } : msg
            ));
            saveChatToHistory(textToSend, fullText);
          }
        );
      } else {
        // Should not reach here, but fallback
        throw new Error('No active session. Please select a subject.');
      }
    } catch (error: any) {
      console.error('Error in handleSend:', error);
      let errorMsg = error.message || 'Failed to get response from backend';

      // Enhanced error messages
      if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
        errorMsg = '❌ Cannot connect to RAG service. Please ensure:\n1. Docker containers are running\n2. RAG service is accessible\n3. Try restarting services';
      } else if (errorMsg.includes('503')) {
        errorMsg = '⚠️ RAG service is starting up. Please wait a moment and try again.';
      } else if (errorMsg.includes('408') || errorMsg.includes('timeout')) {
        errorMsg = '⏱️ Query timed out. This may happen on first query while loading models. Please try again.';
      }

      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.id === botMessageId && lastMsg.text === '') {
          // Replace empty bot message with error
          return prev.map(msg => msg.id === botMessageId ? { ...msg, text: errorMsg } : msg);
        } else {
          // Add new error message
          return [...prev, {
            id: (Date.now() + 2).toString(),
            role: Role.MODEL,
            text: errorMsg,
            timestamp: new Date()
          }];
        }
      });
    } finally {
      setIsTyping(false);
    }
  };

  const clearChat = async () => {
    // Clear session
    if (sessionId) {
      try {
        await endTutorSession(sessionId);
      } catch (error) {
        console.error("Failed to end session:", error);
      }
      setSessionId(null);
    }

    // Reset to initial state (keep current subject selection)
    updateWelcomeMessage(selectedSubject);
  };

  const deselectSubject = async () => {
    // Clear session
    if (sessionId) {
      try {
        await endTutorSession(sessionId);
      } catch (error) {
        console.error("Failed to end session:", error);
      }
      setSessionId(null);
    }

    // Clear subject and chapter selection
    setSelectedSubject(null);
    setSelectedChapter(null);
    localStorage.removeItem('tutor_subject');
    localStorage.removeItem('tutor_chapter');

    // Reset to initial state
    updateWelcomeMessage(null);
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <Navbar
        onNewChat={clearChat}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onOpenSettings={() => setSettingsOpen(true)}
        systemStatus={systemStatus}
        selectedSubject={selectedSubject}
      />

      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[60] animate-in fade-in duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Drawer */}
      <aside className={`
        fixed left-0 top-0 bottom-0 w-80 bg-white z-[70] shadow-2xl transition-transform duration-500 ease-in-out p-6 flex flex-col gap-6
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-main">📚 Subjects</h2>
          <button onClick={() => setSidebarOpen(false)} className="p-1 hover:bg-black/5 rounded-full">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Subjects List */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {/* Show selected subject info with deselect button */}
          {selectedSubject && (
            <div className="bg-[#F43E01]/5 border border-[#F43E01]/20 rounded-xl p-3 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-bold text-[#F43E01] uppercase tracking-widest">Selected</p>
                <p className="font-semibold text-sm truncate text-main">{selectedSubject}</p>
                {selectedChapter && (
                  <p className="text-xs text-gray-500 truncate mt-0.5">→ {selectedChapter}</p>
                )}
              </div>
              <button
                onClick={deselectSubject}
                className="p-2 rounded-lg hover:bg-[#F43E01]/10 text-[#F43E01] transition-colors"
                title="Deselect subject"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          <div className="space-y-2">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Available Subjects</p>

            {/* Subject Search Bar */}
            <div className="relative group px-1">
              <input
                type="text"
                placeholder="Find a subject..."
                value={subjectSearchTerm}
                onChange={(e) => setSubjectSearchTerm(e.target.value)}
                className="w-full bg-white/50 border border-black/5 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#F43E01]/20 focus:border-[#F43E01] transition-all placeholder:text-gray-400"
              />
              <svg className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <div className="space-y-1">
            {subjects.length === 0 ? (
              <div className="p-4 text-center">
                <div className="flex justify-center gap-1 mb-2">
                  <div className="w-1.5 h-1.5 bg-[#F43E01] rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-[#F43E01] rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-1.5 h-1.5 bg-[#F43E01] rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Loading Subjects...</p>
              </div>
            ) : filteredSubjects.length === 0 ? (
              <p className="text-sm text-gray-400 italic px-1">No subjects found matching "{subjectSearchTerm}"</p>
            ) : (
              filteredSubjects.map((subject) => {
                const isExpanded = expandedSubjects.has(subject.name);
                const hasChapters = subject.chapters && subject.chapters.length > 0;

                return (
                  <div key={subject.id} className="space-y-1">
                    <div className="group relative">
                      <button
                        onClick={() => {
                          const next = new Set(expandedSubjects);
                          if (isExpanded) {
                            next.delete(subject.name);
                          } else {
                            next.add(subject.name);
                          }
                          setExpandedSubjects(next);

                          // Also select the subject if it wasn't selected
                          if (selectedSubject !== subject.name) {
                            selectSubject(subject.name);
                          }
                        }}
                        className={`w-full text-left p-3 rounded-xl transition-all border flex items-center justify-between group/btn ${selectedSubject === subject.name
                          ? 'bg-[#F43E01] text-white border-[#F43E01] shadow-md ring-2 ring-[#F43E01]/10'
                          : 'bg-white text-main border-black/5 hover:border-[#F43E01]'
                          }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-sm truncate">{subject.name}</div>
                          <div className={`text-[10px] opacity-70 truncate ${selectedSubject === subject.name && !selectedChapter ? 'text-white' : ''}`}>
                            {subject.syllabus}
                          </div>
                        </div>
                        {hasChapters && (
                          <svg
                            className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                          </svg>
                        )}
                      </button>
                    </div>

                    {/* Chapters Tree */}
                    {isExpanded && hasChapters && (
                      <div className="ml-4 pl-4 border-l-2 border-[#F43E01]/10 space-y-1 py-1 animate-in slide-in-from-top-2 duration-300">
                        {subject.chapters?.map((chapter, idx) => (
                          <button
                            key={`${subject.id}-ch-${idx}`}
                            onClick={() => selectSubject(subject.name, chapter.name)}
                            className={`w-full text-left p-2 rounded-lg text-xs transition-all border ${selectedSubject === subject.name && selectedChapter === chapter.name
                              ? 'bg-[#F43E01]/10 text-[#F43E01] border-[#F43E01]/20 font-bold'
                              : 'text-gray-600 border-transparent hover:bg-black/5'
                              }`}
                          >
                            <div className="truncate flex items-center gap-2">
                              <span className="opacity-40">•</span>
                              {chapter.name}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>


        {/* Recent Chats */}
        <RecentChats
          chats={chatHistory}
          onLoadChat={loadChatFromHistory}
          onClearHistory={clearChatHistory}
        />

        <button
          onClick={clearChat}
          className="w-full py-3 rounded-2xl border-2 border-red-100 text-red-500 font-bold hover:bg-red-50 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear Chat
        </button>
      </aside>

      {/* Main Content Area */}
      <main ref={messageContainerRef} className="flex-1 max-w-4xl w-full mx-auto px-4 md:px-8 pt-28 pb-40 space-y-8 overflow-y-auto">
        {messages.map((msg, index) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === Role.USER ? 'items-end' : 'items-start'} animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className={`
              max-w-[88%] md:max-w-[75%] p-5 md:p-6 rounded-[2rem] shadow-sm relative group
              ${msg.role === Role.USER
                ? 'bg-[#F43E01] text-white rounded-tr-none'
                : 'bg-white text-[#332F33] rounded-tl-none border border-black/5'
              }
            `}>
              <div className="leading-relaxed text-[15px] md:text-[17px] tracking-wide font-medium markdown-content">
                {msg.text ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  msg.role === Role.MODEL && (
                    <div className="flex gap-1.5 py-2 items-center">
                      <div className="w-2.5 h-2.5 bg-[#F43E01]/30 rounded-full animate-bounce"></div>
                      <div className="w-2.5 h-2.5 bg-[#F43E01]/50 rounded-full animate-bounce [animation-delay:-.3s]"></div>
                      <div className="w-2.5 h-2.5 bg-[#F43E01] rounded-full animate-bounce [animation-delay:-.5s]"></div>
                    </div>
                  )
                )}
              </div>

              {/* Diagram and Images Display */}
              {(msg.diagram || (msg.documentImages && msg.documentImages.length > 0)) && (
                <DiagramDisplay
                  diagram={msg.diagram}
                  documentImages={msg.documentImages}
                />
              )}

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-6 pt-6 border-t border-black/5">
                  <button
                    onClick={() => {
                      const el = document.getElementById(`sources-${msg.id}`);
                      if (el) el.classList.toggle('hidden');
                      const arrow = document.getElementById(`arrow-${msg.id}`);
                      if (arrow) arrow.classList.toggle('rotate-180');
                    }}
                    className="flex items-center justify-between w-full group hover:opacity-80 transition-opacity"
                  >
                    <div className="flex items-center gap-2">
                      <svg id={`arrow-${msg.id}`} className="w-4 h-4 text-gray-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Supporting Evidence</p>
                    </div>
                    <span className="text-[10px] font-bold text-[#F43E01] bg-[#F43E01]/5 px-2 py-0.5 rounded-full">
                      {msg.sources.length} Sources
                    </span>
                  </button>
                  <div id={`sources-${msg.id}`} className="hidden mt-4 space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pb-2">
                      {msg.sources.slice(0, 4).map((source, i) => (
                        <SourceCard key={i} source={source} />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className={`text-[11px] mt-3 font-semibold opacity-40 uppercase tracking-widest ${msg.role === Role.USER ? 'text-white' : 'text-[#332F33]'}`}>
                {msg.timestamp instanceof Date ? msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
              </div>
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </main>

      {/* Suggestion Bar & Input */}
      <div className="fixed bottom-0 left-0 right-0 z-40 p-4 bg-gradient-to-t from-[#F0F0E9] via-[#F0F0E9]/95 to-transparent">
        <div className="max-w-4xl mx-auto w-full space-y-4">

          {/* Suggested Prompts */}
          {messages.length < 3 && !isTyping && (
            <div className="flex gap-2 overflow-x-auto pb-2 px-1 no-scrollbar">
              {suggestedPrompts.map((p, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(p)}
                  className="shrink-0 px-4 py-2 rounded-full bg-white border border-black/5 text-sm font-bold text-main hover:border-[#F43E01] hover:text-[#F43E01] transition-all shadow-sm"
                >
                  {p}
                </button>
              ))}
            </div>
          )}


          {/* Enhanced Input Box */}
          <div className="bg-white rounded-[2.5rem] shadow-2xl border border-black/5 p-3 flex items-end gap-3 transition-all focus-within:ring-4 focus-within:ring-[#F43E01]/10">

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Message your AI Tutor..."
              className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-3 text-[16px] text-[#332F33] max-h-40 min-h-[48px] font-medium placeholder:text-gray-400"
              rows={1}
            />

            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              className={`
                w-12 h-12 rounded-full transition-all duration-300 flex items-center justify-center shrink-0
                ${!input.trim() || isTyping
                  ? 'bg-gray-100 text-gray-300'
                  : 'primary-btn shadow-lg hover:scale-105 active:scale-95'
                }
              `}
            >
              <svg className="w-6 h-6 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>

          <div className="flex justify-between items-center px-4">
            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-[0.2em] hidden md:block">
              {systemStatus === 'healthy' ? '✓ Connected' : '⚠ Offline'}
            </span>
            <div className="flex items-center gap-6">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-[0.2em]">Sugarclass AI Tutor</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll to Bottom Button */}
      <ScrollToBottom
        visible={showScrollButton}
        onClick={scrollToBottom}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={userSettings}
        onSave={handleSaveSettings}
      />
    </div>
  );
};

export default App;
