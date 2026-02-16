import React, { useState, useEffect } from 'react';
import { api } from './api';

// V8 Components
import ChapterSidebar from './components/ChapterSidebar.orchestrator';
import SubtopicSidebar from './components/SubtopicSidebar.orchestrator';
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

  // Default to chapter navigation
  const useChapterNavigation = true;

  /* -------------------------------------------------------------------------
     HELPERS
  ------------------------------------------------------------------------- */

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

      const subtopicsData = Array.isArray(res.data) ? res.data : [];
      const allSubtopics = subtopicsData.map(s => ({
        id: String(s.id),
        full_id: s.id,
        name: s.name,
        topic_id: topic.id,
        has_v8_content: s.v8_concepts_count > 0 || s.processed_at !== null,
        v8_concepts_count: s.v8_concepts_count || 0,
      }));

      setSubtopics(allSubtopics);

      // Auto-select first subtopic
      if (allSubtopics.length > 0) {
        setSelectedSubtopicId(allSubtopics[0].full_id);
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

      const subtopicsData = Array.isArray(res.data) ? res.data : [];
      const subtopicsList = subtopicsData.map(s => ({
        id: String(s.id),
        full_id: s.id,
        name: s.name,
        topic_id: chapter.id,
        has_v8_content: s.v8_concepts_count > 0 || s.processed_at !== null,
        v8_concepts_count: s.v8_concepts_count || 0,
        order_num: s.order_num,
      }));

      setSubtopics(subtopicsList);

      if (subtopicsList.length > 0) {
        setSelectedSubtopicId(subtopicsList[0].full_id);
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
    <div className="materials-root">
      {/* MOBILE OVERLAY */}
      {mobileSidebarOpen && (
        <div
          className="materials-mobile-overlay"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* LEFT SIDEBAR */}
      <div className={`materials-sidebar materials-sidebar-left ${mobileSidebarOpen ? 'mobile-open' : ''}`}>
        <ChapterSidebar
          selectedChapter={selectedChapter}
          onSelectChapter={(chapter) => {
            handleChapterSelect(chapter);
            setMobileSidebarOpen(false);
          }}
          viewMode={viewMode}
          onModeChange={setViewMode}
          onSubjectChange={handleSubjectChange}
        />
      </div>

      {/* MIDDLE CONTENT */}
      <MiddleArea
        viewMode={viewMode}
        selectedTopic={selectedTopic}
        selectedSubtopicId={selectedSubtopicId}
        subjectId={selectedSubject}
      />

      {/* RIGHT SIDEBAR */}
      <div className="materials-sidebar materials-sidebar-right">
        <SubtopicSidebar
          viewMode={viewMode}
          selectedTopic={selectedTopic}
          subtopics={subtopics}
          selectedSubtopicId={selectedSubtopicId}
          onSelectSubtopic={handleSubtopicClick}
        />
      </div>
    </div>
  );
}

export default App;
