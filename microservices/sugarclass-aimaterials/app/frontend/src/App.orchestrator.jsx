import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Orchestrator-styled components
import ChapterSidebar from './components/ChapterSidebar.orchestrator';
import MainSidebar from './components/MainSidebar.orchestrator';
import SubtopicSidebar from './components/SubtopicSidebar.orchestrator';
import MiddleArea from './components/MiddleArea.orchestrator';

function App() {
  /* -------------------------------------------------------------------------
     GLOBAL STATE
     ------------------------------------------------------------------------- */
  const [topics, setTopics] = useState([]);
  const [subtopics, setSubtopics] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [questions, setQuestions] = useState([]);

  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [selectedSubtopicId, setSelectedSubtopicId] = useState(null);

  const [viewMode, setViewMode] = useState('content');
  const [contentMode, setContentMode] = useState('rewrite');
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const [loading, setLoading] = useState(true);
  const useChapterNavigation = true;

  /* -------------------------------------------------------------------------
     HELPERS
     ------------------------------------------------------------------------- */
  const loadTopicsForSubject = async (subjectId) => {
    if (!subjectId) return;
    try {
      const res = await axios.get(`/api/db/subjects/${subjectId}/topics`);
      const list = res.data.map(t => ({
        id: String(t.id),
        full_id: t.id,
        name: t.name,
        type: t.type,
        subject_id: t.subject_id,
        order_num: t.order_num,
        subtopic_count: t.subtopic_count,
        processed_count: t.processed_count,
      }));
      setTopics(list);

      if (list.length > 0) {
        const withContent = list.find(t => t.processed_count > 0);
        handleTopicSelect(withContent || list[0]);
      }
    } catch (err) {
      console.error('Error loading topics', err);
    }
  };

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
      const subRes = await axios.get(url);

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

      const questionRE = /^(What|Which|Why|How|Name|State|Describe|Explain|Give|In what|Chloroplasts)/i;
      const contentSubs = allSubtopics.filter(s => s.has_content || !questionRE.test(s.name));
      const exerciseSubs = allSubtopics.filter(s => !s.has_content && questionRE.test(s.name));

      setSubtopics(contentSubs);
      setExercises(exerciseSubs);

      const firstProcessed = contentSubs.find(s => s.is_processed) || contentSubs.find(s => s.has_content);
      if (firstProcessed) setSelectedSubtopicId(firstProcessed.full_id);
      else if (contentSubs.length > 0) setSelectedSubtopicId(contentSubs[0].full_id);
    } catch (err) {
      console.error('Error fetching subtopics', err);
    }

    try {
      const ex = await axios.get(`/api/topics/${topic.id}/exercises`);
      if (Array.isArray(ex.data) && ex.data.length) setExercises(ex.data);
    } catch (err) {
      /* ignore */
    }

    try {
      const q = await axios.get(`/api/topics/${topic.id}/questions`);
      setQuestions(q.data);
    } catch (err) {
      /* ignore */
    }
  };

  const handleSubjectChange = (subjectId) => {
    setSelectedSubject(subjectId);
    setSelectedTopic(null);
    setSelectedChapter(null);
    setSubtopics([]);
    setSelectedSubtopicId(null);
    setExercises([]);
    setQuestions([]);

    if (!useChapterNavigation) {
      loadTopicsForSubject(subjectId);
    }
  };

  const handleChapterSelect = async (chapter) => {
    setSelectedChapter(chapter);
    setSelectedSubtopicId(null);
    setSubtopics([]);
    setExercises([]);
    setQuestions([]);

    try {
      const topicId = String(chapter.id);
      const res = await axios.get(`/api/db/topics/${topicId}/subtopics`);

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

      const firstWithContent = subtopicsList.find(s => s.has_content) || subtopicsList[0];
      if (firstWithContent) setSelectedSubtopicId(firstWithContent.full_id);

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

    try {
      const ex = await axios.get(`/api/topics/${chapter.id}/exercises`);
      if (Array.isArray(ex.data) && ex.data.length) setExercises(ex.data);
    } catch (err) {
      console.error('Error fetching exercises for chapter', err);
    }

    try {
      const q = await axios.get(`/api/topics/${chapter.id}/questions`);
      if (Array.isArray(q.data)) setQuestions(q.data);
    } catch (err) {
      console.error('Error fetching questions for chapter', err);
    }
  };

  const handleSubtopicClick = (subId) => {
    setSelectedSubtopicId(subId);
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
     RENDER (Orchestrator Design System)
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
          selectedSubtopicId={selectedSubtopicId}
          subjectId={selectedSubject}
          contentMode={contentMode}
          onContentModeChange={setContentMode}
          exercises={exercises}
          currentExerciseIndex={currentExerciseIndex}
          onExerciseIndexChange={setCurrentExerciseIndex}
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
