import React, { useState, useEffect } from 'react';
import { api } from '../api';

function MiddleArea({
  viewMode,
  selectedTopic,
  selectedSubtopicId,
  subjectId,
  contentMode,
  onContentModeChange,
  exercises,
  currentExerciseIndex,
  onExerciseIndexChange,
  questions,
  currentQuestionIndex,
  onQuestionIndexChange
}) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [showAnswer, setShowAnswer] = useState(false);

  useEffect(() => {
    if (viewMode === 'content' && selectedSubtopicId) {
      loadContent();
    }
  }, [viewMode, selectedSubtopicId, contentMode]);

  const loadContent = async () => {
    if (!selectedSubtopicId) return;

    setLoading(true);
    try {
      const mode = contentMode === 'raw' ? 'raw' : 'processed';
      const res = await api.get(`/api/db/content/${selectedSubtopicId}?mode=${mode}`);
      setContent(res.data);
    } catch (err) {
      console.error('Error loading content', err);
      setContent(null);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionClick = (optionIndex) => {
    setSelectedOption(optionIndex);
  };

  const currentExercise = exercises[currentExerciseIndex];
  const currentQuestion = questions[currentQuestionIndex];

  /* -------------------------------------------------------------------------
     CONTENT MODE
     ------------------------------------------------------------------------- */
  if (viewMode === 'content') {
    return (
      <div className="materials-main">
        {/* Mobile Header Toggle */}
        <div className="materials-mobile-header" style={{ display: 'flex' }}>
          <button
            className="materials-menu-btn"
            onClick={() => window.dispatchEvent(new CustomEvent('toggle-sidebar'))}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
            <span>Menu</span>
          </button>
        </div>

        {/* Header */}
        <div className="content-header">
          <h1>{selectedTopic?.name || 'AI Materials'}</h1>
          <p>{content?.subtopic_name || content?.summary || 'Select a subtopic to view content'}</p>

          {/* Content Mode Toggle */}
          {content && (
            <div className="mode-toggle">
              <button
                className={`mode-toggle-btn ${contentMode === 'rewrite' ? 'active' : ''}`}
                onClick={() => onContentModeChange && onContentModeChange('rewrite')}
              >
                AI Enhanced
              </button>
              <button
                className={`mode-toggle-btn ${contentMode === 'raw' ? 'active' : ''}`}
                onClick={() => onContentModeChange && onContentModeChange('raw')}
              >
                Original
              </button>
            </div>
          )}
        </div>

        {/* Content Body */}
        <div className="content-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <div className="loading-text">Loading content...</div>
            </div>
          ) : content?.html_content ? (
            <div className="content-card animate-fade-in">
              <div
                className="content-html"
                dangerouslySetInnerHTML={{ __html: content.html_content }}
              />
            </div>
          ) : content?.markdown_content ? (
            <div className="content-card animate-fade-in">
              <div
                className="content-html"
                dangerouslySetInnerHTML={{ __html: content.markdown_content }}
              />
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📚</div>
              <div className="empty-state-text">
                {selectedSubtopicId ? 'No content available for this subtopic' : 'Select a subtopic to begin'}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------------------------
     EXERCISE MODE
     ------------------------------------------------------------------------- */
  if (viewMode === 'exercise') {
    const mobileHeader = (
      <div className="materials-mobile-header" style={{ display: 'flex' }}>
        <button
          className="materials-menu-btn"
          onClick={() => window.dispatchEvent(new CustomEvent('toggle-sidebar'))}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
          <span>Menu</span>
        </button>
      </div>
    );

    if (!currentExercise) {
      return (
        <div className="materials-main">
          {mobileHeader}
          <div className="content-header">
            <h1>Exercises</h1>
          </div>
          <div className="content-body">
            <div className="empty-state">
              <div className="empty-state-icon">📝</div>
              <div className="empty-state-text">No exercises available</div>
            </div>
          </div>
        </div>
      );
    }

    // Ensure options is always an array
    const options = Array.isArray(currentExercise.options) ? currentExercise.options : [];
    const correctIndex = options.findIndex(opt => opt.is_correct);

    return (
      <div className="materials-main">
        {mobileHeader}
        <div className="content-header">
          <h1>Exercise {currentExerciseIndex + 1}</h1>
          <p>Question {currentExerciseIndex + 1} of {exercises.length}</p>
        </div>

        <div className="content-body">
          <div className="exercise-card animate-fade-in">
            <div className="exercise-number">Q{currentExerciseIndex + 1}</div>
            <div className="exercise-question">
              {currentExercise.question_text || currentExercise.question || currentExercise.text || currentExercise.name}
            </div>

            {options.length > 0 && (
              <div className="option-list">
                {options.map((option, index) => {
                  const letter = String.fromCharCode(65 + index);
                  const isSelected = selectedOption === index;
                  const isCorrect = index === correctIndex;

                  let itemClass = 'option-item';
                  if (isSelected && showAnswer) {
                    itemClass += isCorrect ? ' correct' : ' incorrect';
                  } else if (isSelected) {
                    itemClass += ' selected';
                  }

                  return (
                    <div
                      key={index}
                      className={itemClass}
                      onClick={() => !showAnswer && handleOptionClick(index)}
                      style={{ cursor: showAnswer ? 'default' : 'pointer' }}
                    >
                      <span className="option-letter">{letter}</span>
                      <span>{option.text || option.option}</span>
                      {showAnswer && isCorrect && <span style={{ marginLeft: 'auto', color: 'var(--success)' }}>✓</span>}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Answer and Navigation */}
            <div style={{ marginTop: '24px' }}>
              {selectedOption !== null && !showAnswer && (
                <button className="btn-primary" onClick={() => setShowAnswer(true)}>
                  Show Answer
                </button>
              )}

              {showAnswer && (
                <div style={{ marginTop: '16px', padding: '16px', background: 'rgba(61, 90, 69, 0.1)', borderRadius: 'var(--radius-md)' }}>
                  <p style={{ color: 'var(--success)', fontWeight: 600, marginBottom: '8px' }}>
                    {selectedOption === correctIndex ? '✓ Correct!' : '✗ Incorrect'}
                  </p>
                  {currentExercise.explanation && (
                    <p style={{ fontSize: '0.9rem', color: 'var(--primary-light)' }}>
                      {currentExercise.explanation}
                    </p>
                  )}
                </div>
              )}

              <div className="nav-buttons">
                <button
                  className="btn-secondary"
                  onClick={() => onExerciseIndexChange && onExerciseIndexChange(Math.max(0, currentExerciseIndex - 1))}
                  disabled={currentExerciseIndex === 0}
                >
                  Previous
                </button>
                <button
                  className="btn-primary"
                  onClick={() => {
                    setSelectedOption(null);
                    setShowAnswer(false);
                    onExerciseIndexChange && onExerciseIndexChange(Math.min(exercises.length - 1, currentExerciseIndex + 1));
                  }}
                  disabled={currentExerciseIndex >= exercises.length - 1}
                >
                  {currentExerciseIndex >= exercises.length - 1 ? 'Finish' : 'Next'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* -------------------------------------------------------------------------
     QA MODE
     ------------------------------------------------------------------------- */
  if (viewMode === 'qa') {
    const mobileHeader = (
      <div className="materials-mobile-header" style={{ display: 'flex' }}>
        <button
          className="materials-menu-btn"
          onClick={() => window.dispatchEvent(new CustomEvent('toggle-sidebar'))}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
          <span>Menu</span>
        </button>
      </div>
    );

    if (!currentQuestion) {
      return (
        <div className="materials-main">
          {mobileHeader}
          <div className="content-header">
            <h1>Past Questions</h1>
          </div>
          <div className="content-body">
            <div className="empty-state">
              <div className="empty-state-icon">❓</div>
              <div className="empty-state-text">No questions available</div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="materials-main">
        {mobileHeader}
        <div className="content-header">
          <h1>Past Question {currentQuestionIndex + 1}</h1>
          <p>Question {currentQuestionIndex + 1} of {questions.length}</p>
        </div>

        <div className="content-body">
          <div className="question-card animate-fade-in">
            <div className="question-number">Q{currentQuestionIndex + 1}</div>
            <div className="question-text">
              {currentQuestion.question || currentQuestion.text}
            </div>

            {currentQuestion.answer && (
              <div style={{ marginTop: '20px', padding: '16px', background: 'var(--accent-muted)', borderRadius: 'var(--radius-md)' }}>
                <label className="list-section-title" style={{ marginBottom: '8px' }}>Answer:</label>
                <p style={{ fontSize: '0.95rem', lineHeight: '1.6' }}>{currentQuestion.answer}</p>
              </div>
            )}

            {currentQuestion.marks && (
              <p style={{ marginTop: '16px', fontSize: '0.85rem', color: 'var(--primary-light)' }}>
                Marks: {currentQuestion.marks}
              </p>
            )}

            <div className="nav-buttons">
              <button
                className="btn-secondary"
                onClick={() => onQuestionIndexChange && onQuestionIndexChange(Math.max(0, currentQuestionIndex - 1))}
                disabled={currentQuestionIndex === 0}
              >
                Previous
              </button>
              <button
                className="btn-primary"
                onClick={() => onQuestionIndexChange && onQuestionIndexChange(Math.min(questions.length - 1, currentQuestionIndex + 1))}
                disabled={currentQuestionIndex >= questions.length - 1}
              >
                {currentQuestionIndex >= questions.length - 1 ? 'Finish' : 'Next'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default MiddleArea;
