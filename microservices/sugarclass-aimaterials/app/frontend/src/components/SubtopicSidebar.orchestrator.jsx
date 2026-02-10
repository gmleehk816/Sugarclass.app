import React from 'react';

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
                <span style={{ flex: 1, textAlign: 'left', fontSize: '0.9rem' }}>
                  {subtopic.name}
                </span>
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
