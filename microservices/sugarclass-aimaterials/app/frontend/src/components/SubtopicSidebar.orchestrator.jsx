import React from 'react';
import { api } from '../api';

function SubtopicSidebar({
  viewMode,
  selectedTopic,
  subtopics,
  selectedSubtopicId,
  onSelectSubtopic,
  exercises,
  currentExerciseIndex,
  onSelectExercise,
  questions,
  currentQuestionIndex,
  onSelectQuestion
}) {
  const handleDeleteSubtopic = async (id, name) => {
    if (window.confirm(`Are you sure you want to delete subtopic "${name}"? This will delete all generated content.`)) {
      try {
        await api.delete(`/api/admin/v8/subtopics/${id}`);
        window.location.reload(); // Quickest way to refresh for now
      } catch (err) {
        console.error('Error deleting subtopic:', err);
        alert('Failed to delete subtopic');
      }
    }
  };

  const handleRenameSubtopic = async (id, currentName) => {
    const newName = prompt('Enter new subtopic name:', currentName);
    if (newName && newName !== currentName) {
      try {
        await api.patch(`/api/admin/v8/subtopics/${id}`, { name: newName });
        window.location.reload(); // Quickest way to refresh for now
      } catch (err) {
        console.error('Error renaming subtopic:', err);
        alert('Failed to rename subtopic');
      }
    }
  };

  const handleSubtopicClick = (subId) => {
    if (onSelectSubtopic) onSelectSubtopic(subId);
  };

  if (viewMode === 'content') {
    return (
      <div className="materials-sidebar materials-sidebar-right">
        {/* Header */}
        <div className="sidebar-header">
          <h2>Subtopics</h2>
          <p style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '4px' }}>
            {selectedTopic?.name || 'Select a topic'}
          </p>
        </div>

        {/* Subtopics List */}
        <div className="sidebar-content">
          {subtopics.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <div className="empty-state-text">No subtopics available</div>
            </div>
          ) : (
            subtopics.map((subtopic) => (
              <button
                key={subtopic.full_id}
                className={`sidebar-list-item ${subtopic.is_processed ? 'has-content' : ''} ${selectedSubtopicId === subtopic.full_id ? 'active' : ''}`}
                onClick={() => handleSubtopicClick(subtopic.full_id)}
              >
                <span className="sidebar-list-icon" style={{
                  background: subtopic.is_processed ? 'rgba(61, 90, 69, 0.1)' : 'rgba(30, 41, 59, 0.05)',
                  color: subtopic.is_processed ? 'var(--success)' : 'var(--primary-light)'
                }}>
                  {subtopic.is_processed ? '✓' : '•'}
                </span>
                <span style={{ flex: 1, textAlign: 'left', fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {subtopic.name}
                </span>
                <div className="subtopic-actions" style={{ display: 'flex', gap: '4px', marginLeft: '4px' }}>
                  <button
                    className="action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRenameSubtopic(subtopic.full_id, subtopic.name);
                    }}
                    title="Rename"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.8rem', padding: '2px', opacity: 0.6 }}
                  >
                    ✏️
                  </button>
                  <button
                    className="action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSubtopic(subtopic.full_id, subtopic.name);
                    }}
                    title="Delete"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.8rem', padding: '2px', opacity: 0.6 }}
                  >
                    🗑️
                  </button>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    );
  }

  if (viewMode === 'exercise') {
    return (
      <div className="materials-sidebar materials-sidebar-right">
        <div className="sidebar-header">
          <h2>Exercises</h2>
          <p style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '4px' }}>
            {exercises.length} questions
          </p>
        </div>

        <div className="sidebar-content">
          {exercises.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📝</div>
              <div className="empty-state-text">No exercises available</div>
            </div>
          ) : (
            exercises.map((exercise, index) => (
              <button
                key={exercise.id || index}
                className={`sidebar-list-item ${currentExerciseIndex === index ? 'active' : ''}`}
                onClick={() => onSelectExercise && onSelectExercise(index)}
              >
                <span className="sidebar-list-icon">{index + 1}</span>
                <span style={{ flex: 1, textAlign: 'left', fontSize: '0.9rem' }}>
                  {exercise.question || exercise.name || `Question ${index + 1}`}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    );
  }

  if (viewMode === 'qa') {
    return (
      <div className="materials-sidebar materials-sidebar-right">
        <div className="sidebar-header">
          <h2>Past Questions</h2>
          <p style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '4px' }}>
            {questions.length} questions
          </p>
        </div>

        <div className="sidebar-content">
          {questions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">❓</div>
              <div className="empty-state-text">No questions available</div>
            </div>
          ) : (
            questions.map((question, index) => (
              <button
                key={question.id || index}
                className={`sidebar-list-item ${currentQuestionIndex === index ? 'active' : ''}`}
                onClick={() => onSelectQuestion && onSelectQuestion(index)}
              >
                <span className="sidebar-list-icon">{index + 1}</span>
                <span style={{ flex: 1, textAlign: 'left', fontSize: '0.9rem' }}>
                  {question.question || question.text || `Question ${index + 1}`}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    );
  }

  return null;
}

export default SubtopicSidebar;
