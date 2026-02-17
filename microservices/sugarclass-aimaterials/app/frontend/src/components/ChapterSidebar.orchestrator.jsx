import React, { useState, useEffect } from 'react';
import { api } from '../api';

function ChapterSidebar({
  selectedChapter,
  onSelectChapter,
  viewMode,
  onModeChange,
  onSubjectChange,
  subtopics,
  selectedSubtopicId,
  onSelectSubtopic
}) {
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [loading, setLoading] = useState(true);
  const [sidebarTab, setSidebarTab] = useState('chapters');

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const res = await api.get('/api/db/subjects');
        const subjectsData = Array.isArray(res.data) ? res.data : [];
        setSubjects(subjectsData);

        if (subjectsData.length > 0) {
          const first = subjectsData[0];
          setSelectedSubject(first.id);
          if (onSubjectChange) onSubjectChange(first.id);
        }
      } catch (err) {
        console.error('Error loading subjects', err);
        setSubjects([]);
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

        {/* Chapters / Subtopics Tabs */}
        <div className="mode-tabs">
          <button
            className={`mode-tab ${sidebarTab === 'chapters' ? 'active' : ''}`}
            onClick={() => setSidebarTab('chapters')}
          >
            Chapters
          </button>
          <button
            className={`mode-tab ${sidebarTab === 'subtopics' ? 'active' : ''}`}
            onClick={() => setSidebarTab('subtopics')}
          >
            Subtopics
            {subtopics && subtopics.length > 0 && (
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 800,
                background: sidebarTab === 'subtopics' ? 'var(--accent)' : 'var(--accent-muted)',
                color: sidebarTab === 'subtopics' ? 'white' : 'var(--accent)',
                padding: '1px 6px',
                borderRadius: '6px',
                marginLeft: '6px'
              }}>
                {subtopics.length}
              </span>
            )}
          </button>
        </div>

        {/* Chapters List */}
        {sidebarTab === 'chapters' && (
          <>
            <label className="list-section-title">Chapters</label>
            {chapters.map((chapter) => (
              <button
                key={chapter.id}
                className={`sidebar-list-item has-content ${selectedChapter?.id === chapter.id ? 'active' : ''}`}
                onClick={() => handleChapterClick(chapter)}
              >
                <span className="sidebar-list-icon">
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
          </>
        )}

        {/* Subtopics List */}
        {sidebarTab === 'subtopics' && (
          <>
            <label className="list-section-title">
              {selectedChapter ? selectedChapter.title : 'Select a chapter first'}
            </label>
            {!subtopics || subtopics.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px', textAlign: 'center' }}>
                <div className="empty-state-icon">📄</div>
                <div className="empty-state-text">No subtopics available</div>
              </div>
            ) : (
              subtopics.map((subtopic) => (
                <button
                  key={subtopic.full_id}
                  className={`sidebar-list-item ${subtopic.has_v8_content ? 'has-content' : ''} ${selectedSubtopicId === subtopic.full_id ? 'active' : ''}`}
                  onClick={() => onSelectSubtopic && onSelectSubtopic(subtopic.full_id)}
                >
                  <span className="sidebar-list-icon" style={{
                    background: subtopic.has_v8_content ? 'rgba(61, 90, 69, 0.1)' : 'rgba(30, 41, 59, 0.05)',
                    color: subtopic.has_v8_content ? 'var(--success)' : 'var(--primary-light)'
                  }}>
                    {subtopic.has_v8_content ? '✓' : '•'}
                  </span>
                  <span style={{ flex: 1, textAlign: 'left', fontSize: '0.9rem' }}>
                    {subtopic.name}
                  </span>
                  {subtopic.v8_concepts_count > 0 && (
                    <span style={{
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      color: 'var(--accent)',
                      marginLeft: '4px'
                    }}>
                      {subtopic.v8_concepts_count}
                    </span>
                  )}
                </button>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ChapterSidebar;
