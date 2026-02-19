import React, { useState, useEffect } from 'react';
import { Menu, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from './api';

// V8 Components
import ChapterSidebar from './components/ChapterSidebar.orchestrator';
import MiddleArea from './components/MiddleArea.orchestrator';

/**
 * AI Materials V8 Application
 *
 * Pure V8 implementation with 7 interactive view modes:
 * - Learn: Concepts with SVGs and bullet points
 * - Quiz: Interactive MCQ quiz
 * - Cards: Flashcard flip cards
 * - Real Life: Real-life application images
 * - Original: Source markdown content
 */

function App() {
  /* -------------------------------------------------------------------------
     GLOBAL STATE
  ------------------------------------------------------------------------- */
  const [topics, setTopics] = useState([]);
  const [subtopics, setSubtopics] = useState([]);

  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [selectedSubtopicId, setSelectedSubtopicId] = useState(null);

  // UI state
  const [viewMode, setViewMode] = useState('content');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);

  // Default to chapter navigation
  const useChapterNavigation = true;

  /* -------------------------------------------------------------------------
     HELPERS
  ------------------------------------------------------------------------- */

  const mapDbSubtopics = (rows = [], fallbackTopicId = null) => {
    const list = Array.isArray(rows) ? rows : [];
    return list.map(s => ({
      id: String(s.id),
      full_id: s.id,
      name: s.name,
      topic_id: s.topic_id ?? fallbackTopicId,
      topic_name: s.topic_name,
      has_v8_content: (s.v8_concepts_count || 0) > 0 || s.processed_at !== null,
      v8_concepts_count: s.v8_concepts_count || 0,
      order_num: s.order_num,
    }));
  };

  /** Load topics for a subject */
  const loadTopicsForSubject = async (subjectId) => {
    if (!subjectId) return;
    try {
      const res = await api.get(`/api/db/subjects/${subjectId}/topics`);
      const topicsData = Array.isArray(res.data) ? res.data : [];
      const list = topicsData.map(t => ({
        id: String(t.id),
        full_id: t.id,
        name: t.name,
        subject_id: t.subject_id,
        order_num: t.order_num,
        subtopic_count: t.subtopic_count,
      }));
      setTopics(list);

      if (list.length > 0) {
        handleTopicSelect(list[0]);
      }
    } catch (err) {
      console.error('Error loading topics', err);
      setTopics([]);
    }
  };

  /** Load subtopics for a topic */
  const handleTopicSelect = async (topic) => {
    setSelectedTopic(topic);
    setSelectedSubtopicId(null);
    setSubtopics([]);

    try {
      const topicId = String(topic.full_id || topic.id);
      const res = await api.get(`/api/db/topics/${topicId}/subtopics`);

      const topicSubtopics = mapDbSubtopics(res.data, topic.id);
      setSubtopics(topicSubtopics);

      // Auto-select first subtopic
      if (topicSubtopics.length > 0) {
        setSelectedSubtopicId(topicSubtopics[0].full_id);
      }
    } catch (err) {
      console.error('Error fetching subtopics', err);
      setSubtopics([]);
    }
  };

  /** Subject changed */
  const handleSubjectChange = (subjectId) => {
    setSelectedSubject(subjectId);
    setSelectedTopic(null);
    setSelectedChapter(null);
    setSubtopics([]);
    setSelectedSubtopicId(null);

    if (!useChapterNavigation) {
      loadTopicsForSubject(subjectId);
    }
  };

  /** Chapter selected */
  const handleChapterSelect = async (chapter) => {
    setSelectedChapter(chapter);
    setSelectedSubtopicId(null);
    setSubtopics([]);

    try {
      const topicId = String(chapter.id);
      const res = await api.get(`/api/db/topics/${topicId}/subtopics`);

      const chapterSubtopics = mapDbSubtopics(res.data, chapter.id);
      setSubtopics(chapterSubtopics);

      if (chapterSubtopics.length > 0) {
        setSelectedSubtopicId(chapterSubtopics[0].full_id);
      }

      setSelectedTopic({
        id: chapter.id,
        name: chapter.title,
        full_id: chapter.id,
        subject_id: selectedSubject,
      });

    } catch (err) {
      console.error('Error loading subtopics for chapter', err);
      setSubtopics([]);
    }
  };

  /** Subtopic clicked */
  const handleSubtopicClick = (subId) => {
    setSelectedSubtopicId(subId);

    const sub = subtopics.find(s => String(s.full_id) === String(subId));
    if (sub) {
      setSelectedTopic({
        id: sub.topic_id,
        name: sub.name,
        full_id: sub.topic_id,
        subject_id: selectedSubject,
      });
    }
  };

  /* -------------------------------------------------------------------------
     INITIAL LOAD
  ------------------------------------------------------------------------- */
  useEffect(() => {
    setLoading(false);
    const handleToggle = () => setMobileSidebarOpen(true);
    window.addEventListener('toggle-sidebar', handleToggle);
    return () => window.removeEventListener('toggle-sidebar', handleToggle);
  }, []);

  /* -------------------------------------------------------------------------
     RENDER
  ------------------------------------------------------------------------- */
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Loading AI Materials V8...</div>
      </div>
    );
  }

  return (
    <div className="materials-root materials-root-two-col">
      {/* MOBILE OVERLAY */}
      {mobileSidebarOpen && (
        <div
          className="materials-mobile-overlay"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* LEFT SIDEBAR (Collapsible) */}
      <div
        className={`materials-sidebar materials-sidebar-left ${mobileSidebarOpen ? 'mobile-open' : ''}`}
        style={{
          width: isSidebarVisible ? '280px' : '0',
          minWidth: isSidebarVisible ? '220px' : '0',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          opacity: isSidebarVisible ? 1 : 0,
          pointerEvents: isSidebarVisible ? 'auto' : 'none',
          position: 'relative'
        }}
      >
        <ChapterSidebar
          selectedChapter={selectedChapter}
          onSelectChapter={(chapter) => {
            handleChapterSelect(chapter);
            setMobileSidebarOpen(false);
          }}
          viewMode={viewMode}
          onModeChange={setViewMode}
          onSubjectChange={handleSubjectChange}
          subtopics={subtopics}
          selectedSubtopicId={selectedSubtopicId}
          onSelectSubtopic={handleSubtopicClick}
        />
      </div>

      {/* SIDEBAR TOGGLE BUTTON (Floating) */}
      <button
        onClick={() => setIsSidebarVisible(!isSidebarVisible)}
        className="sidebar-toggle-btn"
        style={{
          position: 'absolute',
          left: isSidebarVisible ? '265px' : '15px',
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 100,
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: 'white',
          border: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          color: '#64748b'
        }}
        title={isSidebarVisible ? "Hide Sidebar" : "Show Sidebar"}
      >
        {isSidebarVisible ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <MiddleArea
          selectedTopic={selectedTopic}
          selectedSubtopicId={selectedSubtopicId}
          subjectId={selectedSubject}
          isParentSidebarVisible={isSidebarVisible}
          onToggleParentSidebar={() => setIsSidebarVisible(!isSidebarVisible)}
        />
      </div>
    </div>
  );
}

export default App;
