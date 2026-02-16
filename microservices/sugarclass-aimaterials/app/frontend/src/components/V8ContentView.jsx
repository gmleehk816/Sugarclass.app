import React, { useState, useEffect } from 'react';
import { api } from '../api';

/**
 * V8ContentView - Display V8 enhanced content with 7 view modes
 *
 * View Modes:
 * - learn: Concepts with SVGs and bullet points
 * - quiz: Interactive MCQ quiz
 * - flashcards: Flip cards for learning
 * - reallife: Real-life application images
 * - original: Source markdown content
 */

function V8ContentView({ subtopicId }) {
  const [v8Data, setV8Data] = useState(null);
  const [activeTab, setActiveTab] = useState('learn');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quiz state
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    loadV8Data();
  }, [subtopicId]);

  const loadV8Data = async () => {
    try {
      setLoading(true);
      setError(null);

      // Use the V8 public endpoint to get full data
      const res = await api.get(`/api/v8/subtopics/${subtopicId}`);
      setV8Data(res.data);
    } catch (err) {
      console.error('Error loading V8 data:', err);
      setError(err.response?.data?.detail || 'Failed to load V8 content');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="v8-loading">
        <div className="loading-spinner"></div>
        <div className="loading-text">Loading V8 Content...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="v8-error">
        <div className="error-icon">⚠️</div>
        <div className="error-text">{error}</div>
      </div>
    );
  }

  if (!v8Data) {
    return (
      <div className="v8-empty">
        <div className="empty-icon">📚</div>
        <div className="empty-text">No V8 content available</div>
      </div>
    );
  }

  return (
    <div className="v8-content-view">
      {/* V8 Tab Navigation */}
      <div className="v8-tab-bar">
        <button
          className={`v8-tab ${activeTab === 'learn' ? 'active' : ''}`}
          onClick={() => setActiveTab('learn')}
        >
          <span className="tab-icon">📖</span>
          <span className="tab-label">Learn</span>
        </button>
        <button
          className={`v8-tab ${activeTab === 'quiz' ? 'active' : ''}`}
          onClick={() => setActiveTab('quiz')}
          disabled={!v8Data.quiz || v8Data.quiz.length === 0}
        >
          <span className="tab-icon">❓</span>
          <span className="tab-label">Quiz</span>
          {v8Data.quiz && v8Data.quiz.length > 0 && (
            <span className="tab-badge">{v8Data.quiz.length}</span>
          )}
        </button>
        <button
          className={`v8-tab ${activeTab === 'flashcards' ? 'active' : ''}`}
          onClick={() => setActiveTab('flashcards')}
          disabled={!v8Data.flashcards || v8Data.flashcards.length === 0}
        >
          <span className="tab-icon">⚡</span>
          <span className="tab-label">Cards</span>
          {v8Data.flashcards && v8Data.flashcards.length > 0 && (
            <span className="tab-badge">{v8Data.flashcards.length}</span>
          )}
        </button>
        <button
          className={`v8-tab ${activeTab === 'reallife' ? 'active' : ''}`}
          onClick={() => setActiveTab('reallife')}
          disabled={!v8Data.reallife_images || v8Data.reallife_images.length === 0}
        >
          <span className="tab-icon">🌍</span>
          <span className="tab-label">Real Life</span>
        </button>
        <button
          className={`v8-tab ${activeTab === 'original' ? 'active' : ''}`}
          onClick={() => setActiveTab('original')}
        >
          <span className="tab-icon">📄</span>
          <span className="tab-label">Original</span>
        </button>
      </div>

      {/* V8 Tab Content */}
      <div className="v8-tab-content">
        {activeTab === 'learn' && (
          <V8LearnView
            concepts={v8Data.concepts || []}
            learningObjectives={v8Data.learning_objectives || []}
            keyTerms={v8Data.key_terms || []}
            formulas={v8Data.formulas || []}
          />
        )}
        {activeTab === 'quiz' && (
          <V8QuizView
            quiz={v8Data.quiz || []}
            selectedAnswers={selectedAnswers}
            onAnswerSelect={setSelectedAnswers}
            showResults={showResults}
            onShowResults={setShowResults}
          />
        )}
        {activeTab === 'flashcards' && (
          <V8FlashcardsView flashcards={v8Data.flashcards || []} />
        )}
        {activeTab === 'reallife' && (
          <V8RealLifeView images={v8Data.reallife_images || []} />
        )}
        {activeTab === 'original' && (
          <V8OriginalView subtopic={v8Data} />
        )}
      </div>
    </div>
  );
}

/* ==========================================================================
   V8 LEARN VIEW (Concepts with SVGs)
   ========================================================================== */

function V8LearnView({ concepts, learningObjectives, keyTerms, formulas }) {
  return (
    <div className="v8-learn-view animate-fade-in">
      {/* Learning Objectives */}
      {learningObjectives && learningObjectives.length > 0 && (
        <div className="v8-section">
          <h2 className="v8-section-title">🎯 Learning Objectives</h2>
          <div className="v8-card">
            <ul className="v8-objectives-list">
              {learningObjectives.map((obj, index) => (
                <li key={index} className="v8-objective-item">
                  <span className="objective-bullet">•</span>
                  <span className="objective-text">{obj.objective_text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Concepts with SVGs */}
      {concepts && concepts.length > 0 && concepts.map((concept, index) => (
        <div key={concept.id || index} className="v8-section">
          <h2 className="v8-concept-title">
            <span className="concept-icon">{concept.icon || '📚'}</span>
            <span className="concept-text">{concept.title}</span>
          </h2>

          <div className="v8-two-column">
            {/* Left: Bullet Points */}
            <div className="v8-concept-content">
              <div className="v8-card">
                {concept.generated && concept.generated.bullets ? (
                  <ul
                    className="v8-bullet-list"
                    dangerouslySetInnerHTML={{ __html: concept.generated.bullets }}
                  />
                ) : (
                  <div className="v8-placeholder">
                    <div className="placeholder-text">Content not available</div>
                  </div>
                )}
              </div>
            </div>

            {/* Right: SVG */}
            <div className="v8-concept-visual">
              <div className="v8-card v8-visual-card">
                {concept.generated && concept.generated.svg ? (
                  <div
                    className="v8-svg-container"
                    dangerouslySetInnerHTML={{ __html: concept.generated.svg }}
                  />
                ) : (
                  <div className="v8-visual-placeholder">
                    <div className="placeholder-icon">📊</div>
                    <div className="placeholder-text">Diagram not available</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}

      {/* Key Terms */}
      {keyTerms && keyTerms.length > 0 && (
        <div className="v8-section">
          <h2 className="v8-section-title">🔑 Key Terms</h2>
          <div className="v8-card">
            <div className="v8-terms-grid">
              {keyTerms.map((term, index) => (
                <div key={index} className="v8-term-item">
                  <span className="term-name">{term.term}:</span>
                  <span className="term-definition">{term.definition}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Formulas */}
      {formulas && formulas.length > 0 && (
        <div className="v8-section">
          <h2 className="v8-section-title">📐 Formulas</h2>
          <div className="v8-formulas-grid">
            {formulas.map((formula, index) => (
              <div key={index} className="v8-formula-box">
                <div className="formula-expression">{formula.formula}</div>
                {formula.description && (
                  <div className="formula-description">{formula.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ==========================================================================
   V8 QUIZ VIEW
   ========================================================================== */

function V8QuizView({ quiz, selectedAnswers, onAnswerSelect, showResults, onShowResults }) {
  const handleOptionClick = (questionIndex, optionLetter) => {
    if (!showResults) {
      onAnswerSelect({
        ...selectedAnswers,
        [questionIndex]: optionLetter
      });
    }
  };

  const handleCheckAnswers = () => {
    onShowResults(true);
  };

  const handleReset = () => {
    onShowResults(false);
    onAnswerSelect({});
  };

  if (!quiz || quiz.length === 0) {
    return (
      <div className="v8-empty-state">
        <div className="empty-icon">📝</div>
        <div className="empty-text">No quiz questions available</div>
      </div>
    );
  }

  // Calculate score
  const correctCount = Object.entries(selectedAnswers).filter(
    ([idx, answer]) => quiz[idx]?.correct_answer === answer
  ).length;
  const score = Math.round((correctCount / quiz.length) * 100);

  return (
    <div className="v8-quiz-view animate-fade-in">
      {showResults && (
        <div className="v8-quiz-summary">
          <div className="score-circle">
            <div className="score-value">{score}%</div>
            <div className="score-label">
              {correctCount} of {quiz.length} correct
            </div>
          </div>
          <button className="btn-secondary" onClick={handleReset}>
            Try Again
          </button>
        </div>
      )}

      {quiz.map((q, questionIndex) => {
        const options = typeof q.options === 'string' ? JSON.parse(q.options) : q.options;
        const selectedAnswer = selectedAnswers[questionIndex];
        const isCorrect = selectedAnswer === q.correct_answer;

        return (
          <div key={q.id || questionIndex} className="v8-quiz-question">
            <div className="v8-q-header">
              <span className="v8-q-number">Question {questionIndex + 1}</span>
              {q.difficulty && (
                <span className={`v8-q-badge v8-q-badge-${q.difficulty}`}>
                  {q.difficulty}
                </span>
              )}
            </div>

            <div className="v8-q-text">{q.question_text}</div>

            <div className="v8-q-options">
              {Object.entries(options).map(([letter, text]) => {
                const isSelected = selectedAnswer === letter;
                const isCorrectOption = letter === q.correct_answer;

                let optionClass = 'v8-q-option';
                if (showResults) {
                  if (isCorrectOption) optionClass += ' correct';
                  else if (isSelected) optionClass += ' incorrect';
                } else if (isSelected) {
                  optionClass += ' selected';
                }

                return (
                  <div
                    key={letter}
                    className={optionClass}
                    onClick={() => handleOptionClick(questionIndex, letter)}
                  >
                    <span className="option-letter">{letter}</span>
                    <span className="option-text">{text}</span>
                    {showResults && isCorrectOption && (
                      <span className="option-check">✓</span>
                    )}
                  </div>
                );
              })}
            </div>

            {showResults && q.explanation && (
              <div className={`v8-q-explanation ${isCorrect ? 'correct' : 'incorrect'}`}>
                <strong>Explanation:</strong> {q.explanation}
              </div>
            )}
          </div>
        );
      })}

      {!showResults && Object.keys(selectedAnswers).length === quiz.length && (
        <div className="v8-quiz-actions">
          <button className="btn-primary" onClick={handleCheckAnswers}>
            Check Answers
          </button>
        </div>
      )}
    </div>
  );
}

/* ==========================================================================
   V8 FLASHCARDS VIEW
   ========================================================================== */

function V8FlashcardsView({ flashcards }) {
  if (!flashcards || flashcards.length === 0) {
    return (
      <div className="v8-empty-state">
        <div className="empty-icon">⚡</div>
        <div className="empty-text">No flashcards available</div>
      </div>
    );
  }

  return (
    <div className="v8-flashcards-view animate-fade-in">
      <div className="v8-flashcards-grid">
        {flashcards.map((card, index) => (
          <div
            key={card.id || index}
            className="v8-flashcard"
            onClick={(e) => {
              e.currentTarget.classList.toggle('flipped');
            }}
          >
            <div className="v8-flashcard-inner">
              <div className="v8-flashcard-front">
                <div className="flashcard-content">
                  <h3 className="flashcard-front-text">{card.front}</h3>
                </div>
                <div className="flashcard-hint">Tap to flip</div>
              </div>
              <div className="v8-flashcard-back">
                <div className="flashcard-content">
                  <p className="flashcard-back-text">{card.back}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ==========================================================================
   V8 REAL LIFE VIEW
   ========================================================================== */

function V8RealLifeView({ images }) {
  if (!images || images.length === 0) {
    return (
      <div className="v8-empty-state">
        <div className="empty-icon">🌍</div>
        <div className="empty-text">No real-life images available</div>
      </div>
    );
  }

  const imageConfig = {
    everyday: {
      icon: '🚗',
      defaultTitle: 'Everyday Applications',
      gradient: 'linear-gradient(135deg, #0369a1, #0ea5e9)'
    },
    sports: {
      icon: '🏃',
      defaultTitle: 'Sports Applications',
      gradient: 'linear-gradient(135deg, #059669, #10b981)'
    },
    transport: {
      icon: '🚀',
      defaultTitle: 'Transportation Technology',
      gradient: 'linear-gradient(135deg, #d97706, #f59e0b)'
    }
  };

  return (
    <div className="v8-reallife-view animate-fade-in">
      <div className="v8-reallife-grid">
        {images.map((img, index) => {
          const config = imageConfig[img.image_type] || imageConfig.everyday;

          return (
            <div key={img.id || index} className="v8-reallife-card">
              <div className="v8-reallife-layout">
                <div className="v8-reallife-image">
                  <img
                    src={img.image_url}
                    alt={img.title || config.defaultTitle}
                  />
                </div>
                <div className="v8-reallife-arrow">
                  <svg viewBox="0 0 50 50" className="arrow-svg">
                    <path
                      d="M10 25 L40 25 M35 20 L40 25 L35 30"
                      stroke="currentColor"
                      strokeWidth="3"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <div className="v8-reallife-content">
                  <div
                    className="v8-reallife-icon"
                    style={{ background: config.gradient }}
                  >
                    {config.icon}
                  </div>
                  <h3 className="v8-reallife-title">
                    {img.title || config.defaultTitle}
                  </h3>
                  {img.description && (
                    <p className="v8-reallife-desc">{img.description}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ==========================================================================
   V8 ORIGINAL VIEW (Source Content)
   ========================================================================== */

function V8OriginalView({ subtopic }) {
  return (
    <div className="v8-original-view animate-fade-in">
      <div className="v8-card">
        <h2 className="v8-section-title">📄 Original Content</h2>
        <div className="v8-original-meta">
          <span>Source: {subtopic.subtopic_id} - {subtopic.name}</span>
        </div>
        {subtopic.learning_objectives && subtopic.learning_objectives.length > 0 && (
          <div className="v8-original-section">
            <h3>Learning Objectives</h3>
            <ul>
              {subtopic.learning_objectives.map((obj, i) => (
                <li key={i}>{obj.objective_text}</li>
              ))}
            </ul>
          </div>
        )}
        {subtopic.key_terms && subtopic.key_terms.length > 0 && (
          <div className="v8-original-section">
            <h3>Key Terms</h3>
            <dl>
              {subtopic.key_terms.map((term, i) => (
                <React.Fragment key={i}>
                  <dt>{term.term}</dt>
                  <dd>{term.definition}</dd>
                </React.Fragment>
              ))}
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}

export default V8ContentView;
