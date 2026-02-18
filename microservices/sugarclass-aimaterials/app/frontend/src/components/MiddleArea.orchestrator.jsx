import React, { useState, useEffect } from 'react';
import { api } from '../api';
import V8ContentViewer from './V8ContentViewer';

/**
 * MiddleArea - Pure V8 Content Display
 *
 * This component only supports V8 enhanced content.
 */

function MiddleArea({
  selectedTopic,
  selectedSubtopicId,
  subjectId,
  isParentSidebarVisible,
  onToggleParentSidebar
}) {
  const [loading, setLoading] = useState(false);
  const [v8Status, setV8Status] = useState(null);

  useEffect(() => {
    if (selectedSubtopicId) {
      checkV8Status();
    }
  }, [selectedSubtopicId]);

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

  return (
    <div className="materials-main" style={{ padding: 0, background: '#f8fafc' }}>
      {loading ? (
        <div className="v8-loading">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading V8 Content...</div>
        </div>
      ) : selectedSubtopicId ? (
        <V8ContentViewer
          subtopicId={selectedSubtopicId}
          isParentSidebarVisible={isParentSidebarVisible}
          onToggleParentSidebar={onToggleParentSidebar}
        />
      ) : (
        <div className="v8-empty">
          <div className="empty-icon">📚</div>
          <div className="empty-text">Select a subtopic to view V8 enhanced content</div>
        </div>
      )}
    </div>
  );
}

export default MiddleArea;
