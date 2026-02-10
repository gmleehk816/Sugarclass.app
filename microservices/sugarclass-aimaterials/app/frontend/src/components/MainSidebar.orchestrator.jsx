import React, { useState, useEffect } from 'react';
import axios from 'axios';

function MainSidebar({ topics, selectedTopic, onSelectTopic, viewMode, onModeChange, onSubjectChange }) {
  const handleMode = (newMode) => {
    if (onModeChange) onModeChange(newMode);
  };

  const handleTopicClick = (topic) => {
    if (onSelectTopic) {
      onSelectTopic(topic);
    }
  };

  return (
    <div className="materials-sidebar materials-sidebar-left">
      {/* Header */}
      <div className="sidebar-header">
        <h2>AI Materials</h2>
        <p style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '4px' }}>Browse by topic</p>
      </div>

      {/* Mode Tabs */}
      <div className="sidebar-content">
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

        {/* Topics List */}
        <label className="list-section-title">Topics</label>
        {topics.length === 0 ? (
          <div className="empty-state" style={{ padding: '20px' }}>
            <div className="empty-state-text" style={{ fontSize: '0.85rem' }}>No topics available</div>
          </div>
        ) : (
          topics.map((topic) => (
            <button
              key={topic.id}
              className={`sidebar-list-item has-content ${selectedTopic?.id === topic.id ? 'active' : ''}`}
              onClick={() => handleTopicClick(topic)}
            >
              <span className="sidebar-list-icon" style={{
                background: topic.processed_count > 0 ? 'rgba(61, 90, 69, 0.1)' : 'rgba(30, 41, 59, 0.05)',
                color: topic.processed_count > 0 ? 'var(--success)' : 'var(--primary-light)'
              }}>
                {topic.processed_count > 0 ? '✓' : '•'}
              </span>
              <span style={{ flex: 1, textAlign: 'left', fontSize: '0.9rem' }}>
                {topic.name}
              </span>
              {topic.subtopic_count > 0 && (
                <span style={{ fontSize: '0.7rem', color: 'var(--primary-light)', marginLeft: '8px' }}>
                  {topic.subtopic_count}
                </span>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
}

export default MainSidebar;
