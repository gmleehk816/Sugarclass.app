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
    <div className="v8-content-view animate-fade-in">
      {/* V8 Tab Navigation - Premium Glass Effect */}
      <div className="v8-tab-bar glass-effect">
        <button
          className={`v8-tab ${activeTab === 'learn' ? 'active' : ''}`}
          onClick={() => setActiveTab('learn')}
        >
          <span className="tab-icon">📖</span>
          <span className="tab-label">Learning objective</span>
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
          <div className="v8-card glass-effect">
            <ul className="v8-bullet-list">
              {learningObjectives.map((obj, index) => (
                <li key={index}>
                  {obj.objective_text}
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
                  <div
                    className="v8-bullet-list"
                    dangerouslySetInnerHTML={{
                      __html: concept.generated.bullets
                        .replace(/<ul>/g, '<ul class="v8-bullet-list">')
                        .replace(/\$\$([^$]+)\$\$/g, '<span style="font-family: serif; font-style: italic;">$1</span>')
                        .replace(/\$([^$]+)\$/g, '<span style="font-family: serif; font-style: italic;">$1</span>')
                    }}
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
                  <div className="v8-visual-placeholder flex-center" style={{ flexDirection: 'column', height: '100%' }}>
                    <div className="placeholder-icon" style={{ fontSize: '3rem', opacity: 0.2 }}>📊</div>
                    <div className="placeholder-text" style={{ opacity: 0.5 }}>Diagram not available</div>
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
          <div className="v8-card glass-effect">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '24px' }}>
              {keyTerms.map((term, index) => (
                <div key={index}>
                  <div style={{ fontWeight: 800, color: 'var(--accent)', marginBottom: '4px' }}>{term.term}</div>
                  <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>{term.definition}</div>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {formulas.map((formula, index) => (
              <div key={index} className="v8-card" style={{ borderLeft: '4px solid var(--accent)' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '8px', fontFamily: 'serif' }}>{formula.formula}</div>
                {formula.description && (
                  <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>{formula.description}</div>
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
        <div className="v8-quiz-summary glass-effect" style={{
          padding: '40px',
          borderRadius: 'var(--radius-lg)',
          textAlign: 'center',
          marginBottom: '40px',
          border: '1px solid var(--accent-muted)'
        }}>
          <div className="score-circle" style={{
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background: 'var(--primary)',
            color: 'white',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px'
          }}>
            <div className="score-value" style={{ fontSize: '2rem', fontWeight: 800 }}>{score}%</div>
            <div className="score-label" style={{ fontSize: '0.75rem', opacity: 0.7 }}>
              {correctCount}/{quiz.length} Correct
            </div>
          </div>
          <button className="btn-primary" onClick={handleReset}>
            Retry Assessment
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
              <span className="v8-q-number">Assessment Item {questionIndex + 1}</span>
              {q.difficulty && (
                <span className={`v8-q-badge v8-q-badge-${q.difficulty}`} style={{
                  background: q.difficulty === 'hard' ? 'var(--error)' : 'var(--primary)',
                  color: 'white',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  fontSize: '0.7rem',
                  textTransform: 'uppercase',
                  fontWeight: 800
                }}>
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
                      <span className="option-check" style={{ marginLeft: 'auto', color: 'var(--success)', fontWeight: 800 }}>✓</span>
                    )}
                  </div>
                );
              })}
            </div>

            {showResults && q.explanation && (
              <div className={`v8-q-explanation ${isCorrect ? 'correct' : 'incorrect'}`} style={{
                marginTop: '24px',
                padding: '20px',
                background: isCorrect ? 'rgba(61, 90, 69, 0.05)' : 'rgba(153, 27, 27, 0.05)',
                borderRadius: 'var(--radius-md)',
                borderLeft: `4px solid ${isCorrect ? 'var(--success)' : 'var(--error)'}`
              }}>
                <strong style={{ color: isCorrect ? 'var(--success)' : 'var(--error)' }}>Synthesis Insight:</strong> {q.explanation}
              </div>
            )}
          </div>
        );
      })}

      {!showResults && Object.keys(selectedAnswers).length === quiz.length && (
        <div className="v8-quiz-actions" style={{ textAlign: 'center', marginTop: '32px' }}>
          <button className="btn-primary" style={{ padding: '16px 48px', fontSize: '1rem' }} onClick={handleCheckAnswers}>
            Finalize Assessment
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
                <div className="flashcard-hint" style={{
                  position: 'absolute',
                  bottom: '16px',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  fontWeight: 700,
                  opacity: 0.4
                }}>Tap to Reveal</div>
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
                  <svg viewBox="0 0 50 50" style={{
                    width: '32px',
                    height: '32px',
                    color: 'var(--accent)',
                    opacity: 0.3
                  }}>
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
                    style={{
                      background: config.gradient,
                      boxShadow: '0 8px 16px -4px rgba(0,0,0,0.2)'
                    }}
                  >
                    {config.icon}
                  </div>
                  <h3 className="v8-reallife-title">
                    {img.title || config.defaultTitle}
                  </h3>
                  {img.description && (
                    <p className="v8-reallife-desc">{img.description}</p>
                  )}
                  {img.prompt && (
                    <div style={{
                      marginTop: '24px',
                      padding: '16px',
                      background: 'var(--background)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.85rem',
                      borderLeft: '3px solid var(--accent)',
                      opacity: 0.9
                    }}>
                      <strong style={{ display: 'block', color: 'var(--accent)', marginBottom: '4px', textTransform: 'uppercase', fontSize: '0.7rem' }}>Directive Insight:</strong>
                      {img.prompt}
                    </div>
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
      <div className="v8-card glass-effect">
        <h2 className="v8-section-title">📄 Original Dataset</h2>
        <div className="v8-original-meta" style={{
          fontSize: '0.85rem',
          opacity: 0.6,
          marginBottom: '32px',
          padding: '12px',
          background: 'var(--primary-muted)',
          borderRadius: 'var(--radius-sm)'
        }}>
          <span>Resource Reference: {subtopic.subtopic_id} — {subtopic.name}</span>
        </div>
        {subtopic.learning_objectives && subtopic.learning_objectives.length > 0 && (
          <div className="v8-original-section" style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent)', marginBottom: '16px' }}>Learning Objectives</h3>
            <ul className="v8-bullet-list">
              {subtopic.learning_objectives.map((obj, i) => (
                <li key={i}>{obj.objective_text}</li>
              ))}
            </ul>
          </div>
        )}
        {subtopic.key_terms && subtopic.key_terms.length > 0 && (
          <div className="v8-original-section">
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent)', marginBottom: '16px' }}>Key Terminology</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px' }}>
              {subtopic.key_terms.map((term, i) => (
                <div key={i} style={{ padding: '16px', background: 'var(--background)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontWeight: 800, color: 'var(--primary)', marginBottom: '4px' }}>{term.term}</div>
                  <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>{term.definition}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default V8ContentView;
