import React, { useState, useEffect } from 'react';
import { api } from './api';

// Orchestrator-styled components
import ChapterSidebar from './components/ChapterSidebar.orchestrator';
import MainSidebar from './components/MainSidebar.orchestrator';
import SubtopicSidebar from './components/SubtopicSidebar.orchestrator';
import MiddleArea from './components/MiddleArea.orchestrator';

function App() {
  /* -------------------------------------------------------------------------
     GLOBAL STATE
  ------------------------------------------------------------------------- */
  const [topics, setTopics] = useState([]);               // Topic list (topic-navigation mode)
  const [subtopics, setSubtopics] = useState([]);         // Sub-topic list (content mode)
  const [exercises, setExercises] = useState([]);         // Exercise list (exercise mode)
  const [questions, setQuestions] = useState([]);         // Past-paper questions (QA mode)

  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null); // currently selected topic (topic nav)
  const [selectedChapter, setSelectedChapter] = useState(null); // currently selected chapter (chapter nav)
  const [selectedSubtopicId, setSelectedSubtopicId] = useState(null);

  // UI / mode state
  const [viewMode, setViewMode] = useState('content');   // content | exercise | qa
  const [contentMode, setContentMode] = useState('rewrite');   // rewrite (default) | raw
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Loading & navigation mode
  const [loading, setLoading] = useState(true);
  const useChapterNavigation = true; // << default TRUE as requested

  /* -------------------------------------------------------------------------
     HELPERS
  ------------------------------------------------------------------------- */
  /** Load topics when a subject changes (topic-navigation branch) */
  const loadTopicsForSubject = async (subjectId) => {
    if (!subjectId) return;
    try {
      const res = await api.get(`/api/db/subjects/${subjectId}/topics`);
      const list = res.data.map(t => ({
        id: String(t.id),               // displayed id as string
        full_id: t.id,                  // original id
        name: t.name,
        type: t.type,
        subject_id: t.subject_id,
        order_num: t.order_num,
        subtopic_count: t.subtopic_count,
        processed_count: t.processed_count,
      }));
      setTopics(list);

      // auto-select first topic with content
      if (list.length > 0) {
        const withContent = list.find(t => t.processed_count > 0);
        handleTopicSelect(withContent || list[0]);
      }
    } catch (err) {
      console.error('Error loading topics', err);
    }
  };

  /** Load subtopics (and exercises / questions) for a topic */
  const handleTopicSelect = async (topic) => {
    setSelectedTopic(topic);
    setSelectedSubtopicId(null);
    setCurrentExerciseIndex(0);
    setCurrentQuestionIndex(0);
    setExercises([]);
    setQuestions([]);

    try {
      const topicId = String(topic.full_id || topic.id);
      const isMath = selectedSubject === 'mathematics_0607' || topicId.startsWith('mathematics_0607_');
      const processedOnly = isMath && contentMode === 'processed' && (topic.processed_count > 0);
      const url = `/api/db/topics/${topicId}/subtopics${processedOnly ? '?processed_only=true' : ''}`;
      const subRes = await api.get(url);

      const allSubtopics = subRes.data.map(s => ({
        id: String(s.id),
        full_id: s.id,
        name: s.name,
        topic_id: topic.id,
        has_content: (s.raw_chars || 0) > 0 || (s.processed_chars || 0) > 0,
        is_processed: s.processed_id !== null && (s.processed_chars || 0) > 0,
        raw_chars: s.raw_chars,
        processed_chars: s.processed_chars,
      }));

      // Split into content and exercise subtopics
      const questionRE = /^(What|Which|Why|How|Name|State|Describe|Explain|Give|In what|Chloroplasts)/i;
      const contentSubs = allSubtopics.filter(s => s.has_content || !questionRE.test(s.name));
      const exerciseSubs = allSubtopics.filter(s => !s.has_content && questionRE.test(s.name));

      setSubtopics(contentSubs);
      setExercises(exerciseSubs);

      // auto-select first subtopic with processed content
      const firstProcessed = contentSubs.find(s => s.is_processed) || contentSubs.find(s => s.has_content);
      if (firstProcessed) setSelectedSubtopicId(firstProcessed.full_id);
      else if (contentSubs.length > 0) setSelectedSubtopicId(contentSubs[0].full_id);
    } catch (err) {
      console.error('Error fetching subtopics', err);
    }

    // fetch exercises (generated) and questions (past papers)
    try {
      const ex = await api.get(`/api/topics/${topic.id}/exercises`);
      if (Array.isArray(ex.data) && ex.data.length) setExercises(ex.data);
    } catch (err) {
      /* ignore */
    }

    try {
      const q = await api.get(`/api/topics/${topic.id}/questions`);
      setQuestions(q.data);
    } catch (err) {
      /* ignore */
    }
  };

  /** Subject has changed – reset state and decide navigation mode */
  const handleSubjectChange = (subjectId) => {
    setSelectedSubject(subjectId);

    // Reset all downstream selections
    setSelectedTopic(null);
    setSelectedChapter(null);
    setSubtopics([]);
    setSelectedSubtopicId(null);
    setExercises([]);
    setQuestions([]);

    // *** Keep chapter navigation ON – do NOT turn it off ***
    // setUseChapterNavigation(false);  // ← removed as requested

    // Only load full topic list when we are *not* in chapter navigation mode
    if (!useChapterNavigation) {
      loadTopicsForSubject(subjectId);
    }
  };

  /** Chapter clicked in ChapterSidebar */
  const handleChapterSelect = async (chapter) => {
    setSelectedChapter(chapter);
    setSelectedSubtopicId(null);
    setSubtopics([]);
    setExercises([]);
    setQuestions([]);

    try {
      const topicId = String(chapter.id);
      const res = await api.get(`/api/db/topics/${topicId}/subtopics`);

      const subtopicsList = res.data.map(s => ({
        id: String(s.id),
        full_id: s.id,
        name: s.name,
        topic_id: chapter.id,
        has_content: (s.raw_chars || 0) > 0 || (s.processed_chars || 0) > 0,
        is_processed: s.processed_id !== null && (s.processed_chars || 0) > 0,
        order_num: s.order_num,
      }));

      setSubtopics(subtopicsList);

      // Auto-select first subtopic with content
      const firstWithContent = subtopicsList.find(s => s.has_content) || subtopicsList[0];
      if (firstWithContent) setSelectedSubtopicId(firstWithContent.full_id);

      // Set selectedTopic for MiddleArea
      setSelectedTopic({
        id: chapter.id,
        name: chapter.title,
        full_id: chapter.id,
        subject_id: selectedSubject,
        type: 'Topic'
      });

    } catch (err) {
      console.error('Error loading subtopics for chapter', err);
    }

    // fetch exercises (generated) and questions (past papers) for chapter
    try {
      const ex = await api.get(`/api/topics/${chapter.id}/exercises`);
      if (Array.isArray(ex.data) && ex.data.length) setExercises(ex.data);
    } catch (err) {
      console.error('Error fetching exercises for chapter', err);
    }

    try {
      const q = await api.get(`/api/topics/${chapter.id}/questions`);
      if (Array.isArray(q.data)) setQuestions(q.data);
    } catch (err) {
      console.error('Error fetching questions for chapter', err);
    }
  };

  /** Subtopic clicked inside right sidebar (when in chapter nav mode) */
  const handleSubtopicClick = (subId) => {
    setSelectedSubtopicId(subId);

    // also derive selectedTopic (needed by MiddleArea header)
    const sub = subtopics.find(s => String(s.full_id) === String(subId));
    if (sub) {
      setSelectedTopic({ id: sub.topic_id, name: sub.name, full_id: sub.topic_id, subject_id: selectedSubject, type: 'Topic' });
    }
  };

  /* -------------------------------------------------------------------------
     INITIAL LOAD
  ------------------------------------------------------------------------- */
  useEffect(() => { setLoading(false); }, []);

  /* -------------------------------------------------------------------------
     RENDER
  ------------------------------------------------------------------------- */
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Loading AI Materials...</div>
      </div>
    );
  }

  return (
    <div className="materials-root">
      {/* LEFT SIDEBAR */}
      <div className="materials-sidebar materials-sidebar-left">
        {useChapterNavigation ? (
          <ChapterSidebar
            selectedChapter={selectedChapter}
            onSelectChapter={handleChapterSelect}
            viewMode={viewMode}
            onModeChange={setViewMode}
            onSubjectChange={handleSubjectChange}
          />
        ) : (
          <MainSidebar
            topics={topics}
            selectedTopic={selectedTopic}
            onSelectTopic={handleTopicSelect}
            viewMode={viewMode}
            onModeChange={setViewMode}
            onSubjectChange={handleSubjectChange}
          />
        )}
      </div>

      {/* MIDDLE CONTENT */}
      <div className="materials-main">
        <MiddleArea
          viewMode={viewMode}
          selectedTopic={selectedTopic}

          /* content props */
          selectedSubtopicId={selectedSubtopicId}
          subjectId={selectedSubject}
          contentMode={contentMode}
          onContentModeChange={setContentMode}

          /* exercise props */
          exercises={exercises}
          currentExerciseIndex={currentExerciseIndex}
          onExerciseIndexChange={setCurrentExerciseIndex}

          /* QA props */
          questions={questions}
          currentQuestionIndex={currentQuestionIndex}
          onQuestionIndexChange={setCurrentQuestionIndex}
        />
      </div>

      {/* RIGHT SIDEBAR */}
      <div className="materials-sidebar materials-sidebar-right">
        <SubtopicSidebar
          viewMode={viewMode}
          selectedTopic={selectedTopic}
          subtopics={subtopics}
          selectedSubtopicId={selectedSubtopicId}
          onSelectSubtopic={handleSubtopicClick}

          exercises={exercises}
          currentExerciseIndex={currentExerciseIndex}
          onSelectExercise={setCurrentExerciseIndex}

          questions={questions}
          currentQuestionIndex={currentQuestionIndex}
          onSelectQuestion={setCurrentQuestionIndex}
        />
      </div>
    </div>
  );
}

export default App;
