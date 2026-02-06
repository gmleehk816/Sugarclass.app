import React, { useState, useEffect } from 'react';
import { api } from '../api';

function ChapterSidebar({ selectedChapter, onSelectChapter, viewMode, onModeChange, onSubjectChange }) {
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const res = await api.get('/api/db/subjects');
        // Debug logging
        console.log('Raw res.data:', res.data);
        console.log('Type of res.data:', typeof res.data);
        console.log('Is Array?', Array.isArray(res.data));

        // Ensure res.data is an array before setting
        const subjectsData = Array.isArray(res.data) ? res.data : [];
        console.log('ChapterSidebar: Fetched subjects:', subjectsData);
        setSubjects(subjectsData);

        if (subjectsData.length > 0) {
          const first = subjectsData[0];
          setSelectedSubject(first.id);
          if (onSubjectChange) onSubjectChange(first.id);
        }
      } catch (err) {
        console.error('Error loading subjects', err);
        setSubjects([]); // Ensure subjects is always an array
      } finally {
        setLoading(false);
      }
    };
    fetchSubjects();
  }, []);

  useEffect(() => {
    const fetchChapters = async (subjectId) => {
      if (!subjectId) return;
      try {
        const res = await api.get(`/api/db/subjects/${subjectId}/topics`);
        const topicList = res.data || [];

        const chapters = topicList.map((t, index) => ({
          id: t.id,
          chapter_num: t.order_num !== undefined ? t.order_num : index + 1,
          title: t.name,
          type: t.type,
          subtopic_count: t.subtopic_count || 0,
          processed_count: t.processed_count || 0,
        })).sort((a, b) => (a.chapter_num || 0) - (b.chapter_num || 0));

        setChapters(chapters);

        if (!selectedChapter && chapters.length > 0) {
          handleChapterClick(chapters[0]);
        }
      } catch (err) {
        console.error('Error loading chapters', err);
      }
    };
    fetchChapters(selectedSubject);
  }, [selectedSubject, selectedChapter]);

  const handleSubjectChange = (e) => {
    const id = e.target.value;
    setSelectedSubject(id);
    if (onSubjectChange) onSubjectChange(id);
  };

  const handleChapterClick = (chapter) => {
    if (onSelectChapter) {
      onSelectChapter(chapter);
    }
  };

  const handleMode = (newMode) => {
    if (onModeChange) onModeChange(newMode);
  };

  const currentSubjectName = subjects.find(s => s.id === selectedSubject)?.name || 'Select Subject';

  if (loading) {
    return (
      <div className="materials-sidebar materials-sidebar-left">
        <div className="loading-container">
          <div className="loading-spinner" style={{ width: 32, height: 32 }}></div>
        </div>
      </div>
    );
  }

  return (
    <div className="materials-sidebar materials-sidebar-left">
      {/* Header */}
      <div className="sidebar-header">
        <h2>AI Materials</h2>
        <p style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '4px' }}>{currentSubjectName}</p>
      </div>

      {/* Subject Selector */}
      <div className="sidebar-content">
        <label className="list-section-title">Subject</label>
        <select
          className="subject-select"
          value={selectedSubject}
          onChange={handleSubjectChange}
        >
          {subjects.map(subject => (
            <option key={subject.id} value={subject.id}>{subject.name}</option>
          ))}
        </select>

        {/* Mode Tabs */}
        <div className="mode-tabs">
          <button
            className={`mode-tab ${viewMode === 'content' ? 'active' : ''}`}
            onClick={() => handleMode('content')}
          >
            Content
          </button>
          <button
            className={`mode-tab ${viewMode === 'exercise' ? 'active' : ''}`}
            onClick={() => handleMode('exercise')}
          >
            Exercises
          </button>
          <button
            className={`mode-tab ${viewMode === 'qa' ? 'active' : ''}`}
            onClick={() => handleMode('qa')}
          >
            Q&A
          </button>
        </div>

        {/* Chapters List */}
        <label className="list-section-title">Chapters</label>
        {chapters.map((chapter) => (
          <button
            key={chapter.id}
            className={`list-item has-content ${selectedChapter?.id === chapter.id ? 'active' : ''}`}
            onClick={() => handleChapterClick(chapter)}
          >
            <span className="list-item-icon">
              {String(chapter.chapter_num || '').replace(/\D/g, '').slice(0, 2) || '•'}
            </span>
            <span style={{ flex: 1, textAlign: 'left' }}>{chapter.title}</span>
            {chapter.processed_count > 0 && (
              <span style={{ fontSize: '0.7rem', color: 'var(--accent)', marginLeft: '8px' }}>
                ✓
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export default ChapterSidebar;
