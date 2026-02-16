import React, { useState, useEffect } from 'react';
import { api } from '../api';
import V8ContentViewer from './V8ContentViewer';

/**
 * MiddleArea - Pure V8 Content Display
 *
 * This component only supports V8 enhanced content.
 * All legacy content modes have been removed.
 */

function MiddleArea({
  viewMode,
  selectedTopic,
  selectedSubtopicId,
  subjectId
}) {
  const [loading, setLoading] = useState(false);
  const [v8Status, setV8Status] = useState(null);

  useEffect(() => {
    if (viewMode === 'content' && selectedSubtopicId) {
      checkV8Status();
    }
  }, [viewMode, selectedSubtopicId]);

  const checkV8Status = async () => {
    if (!selectedSubtopicId) return;

    setLoading(true);
    try {
      const res = await api.get(`/api/v8/subtopics/${selectedSubtopicId}/status`);
      setV8Status(res.data);
    } catch (err) {
      console.error('Error checking V8 status', err);
      setV8Status(null);
    } finally {
      setLoading(false);
    }
  };

  /* -------------------------------------------------------------------------
     CONTENT MODE - V8 Only
     ------------------------------------------------------------------------- */
  if (viewMode === 'content') {
    return (
      <div className="materials-main" style={{ padding: 0, background: '#f8fafc' }}>
        {loading ? (
          <div className="v8-loading">
            <div className="loading-spinner"></div>
            <div className="loading-text">Loading V8 Content...</div>
          </div>
        ) : selectedSubtopicId ? (
          <V8ContentViewer subtopicId={selectedSubtopicId} />
        ) : (
          <div className="v8-empty">
            <div className="empty-icon">📚</div>
            <div className="empty-text">Select a subtopic to view V8 enhanced content</div>
          </div>
        )}
      </div>
    );
  }

  /* -------------------------------------------------------------------------
     DEFAULT - Empty State
     ------------------------------------------------------------------------- */
  return (
    <div className="materials-main">
      <div className="content-header">
        <h1>AI Materials V8</h1>
        <p>Select a subtopic to begin learning with enhanced V8 content</p>
      </div>
      <div className="content-body">
        <div className="v8-empty">
          <div className="empty-icon">🎯</div>
          <div className="empty-text">
            V8 Enhanced Content
            <br />
            <small style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Interactive Learning: Concepts, Quiz, Flashcards
            </small>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MiddleArea;
