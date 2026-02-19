import React, { useState, useEffect, useCallback } from 'react';
import { Menu, ListOrdered, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../api';

// ============================================================================
// V8 CONTENT VIEWER - Matches V8 Generator HTML Layout
// ============================================================================

const V8ContentViewer = ({ subtopicId, isParentSidebarVisible, onToggleParentSidebar }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [v8Data, setV8Data] = useState(null);
  const [activeView, setActiveView] = useState('content');
  const [activeSection, setActiveSection] = useState(null);
  const [flippedCards, setFlippedCards] = useState({});
  const [quizAnswers, setQuizAnswers] = useState({});
  const [isTocVisible, setIsTocVisible] = useState(true);
  const [viewIndexes, setViewIndexes] = useState({
    quiz: 0,
    flashcards: 0,
    reallife: 0,
  });

  const getQuizKey = (question, index) => String(question?.id ?? question?.question_num ?? index);
  const parseQuizOptions = (options) => {
    if (!options) return {};
    if (typeof options === 'string') {
      try {
        return JSON.parse(options);
      } catch {
        return {};
      }
    }
    return options;
  };

  useEffect(() => {
    if (!subtopicId) return;
    setActiveView('content');
    setActiveSection(null);
    setFlippedCards({});
    setQuizAnswers({});
    setViewIndexes({ quiz: 0, flashcards: 0, reallife: 0 });
    loadV8Content();
  }, [subtopicId]);

  const loadV8Content = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v8/subtopics/${subtopicId}`);
      setV8Data(res.data);
      // Set first concept as active section
      if (res.data.concepts && res.data.concepts.length > 0) {
        setActiveSection(res.data.concepts[0].concept_key);
      }
    } catch (err) {
      console.error('Error loading V8 content:', err);
      setError(err.response?.data?.detail || 'Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  const scrollToSection = (sectionId) => {
    setActiveView('content');
    setActiveSection(sectionId);
  };

  const toggleCard = (cardId) => {
    setFlippedCards(prev => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  const selectQuizAnswer = (questionId, answer) => {
    setQuizAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const concepts = v8Data?.concepts || [];
  const quizItems = v8Data?.quiz || [];
  const flashcards = v8Data?.flashcards || [];
  const reallifeItems = v8Data?.reallife_images || [];

  const currentConceptIndex = Math.max(0, concepts.findIndex(c => c.concept_key === activeSection));
  const currentConcept = concepts[currentConceptIndex] || null;

  const currentQuizIndex = Math.min(viewIndexes.quiz, Math.max(quizItems.length - 1, 0));
  const currentQuiz = quizItems[currentQuizIndex] || null;
  const currentQuizKey = currentQuiz ? getQuizKey(currentQuiz, currentQuizIndex) : null;
  const currentQuizOptions = currentQuiz ? parseQuizOptions(currentQuiz.options) : {};

  const currentFlashcardIndex = Math.min(viewIndexes.flashcards, Math.max(flashcards.length - 1, 0));
  const currentFlashcard = flashcards[currentFlashcardIndex] || null;

  const currentReallifeIndex = Math.min(viewIndexes.reallife, Math.max(reallifeItems.length - 1, 0));
  const currentReallife = reallifeItems[currentReallifeIndex] || null;

  useEffect(() => {
    if (!concepts.length) {
      setActiveSection(null);
      return;
    }
    const exists = concepts.some(c => c.concept_key === activeSection);
    if (!exists) {
      setActiveSection(concepts[0].concept_key);
    }
  }, [activeSection, concepts]);

  useEffect(() => {
    setViewIndexes(prev => ({
      quiz: Math.min(prev.quiz, Math.max(quizItems.length - 1, 0)),
      flashcards: Math.min(prev.flashcards, Math.max(flashcards.length - 1, 0)),
      reallife: Math.min(prev.reallife, Math.max(reallifeItems.length - 1, 0)),
    }));
  }, [quizItems.length, flashcards.length, reallifeItems.length]);

  const getPaginationConfig = () => {
    if (activeView === 'content') {
      return { key: 'content', index: currentConceptIndex, total: concepts.length, label: 'Concept' };
    }
    if (activeView === 'quiz') {
      return { key: 'quiz', index: currentQuizIndex, total: quizItems.length, label: 'Question' };
    }
    if (activeView === 'flashcards') {
      return { key: 'flashcards', index: currentFlashcardIndex, total: flashcards.length, label: 'Card' };
    }
    if (activeView === 'reallife') {
      return { key: 'reallife', index: currentReallifeIndex, total: reallifeItems.length, label: 'Application' };
    }
    return null;
  };

  const pagination = getPaginationConfig();

  const goToPage = useCallback((delta) => {
    if (!pagination || pagination.total <= 1) return;
    const nextIndex = Math.max(0, Math.min(pagination.total - 1, pagination.index + delta));
    if (nextIndex === pagination.index) return;

    if (pagination.key === 'content') {
      const nextConcept = concepts[nextIndex];
      if (nextConcept) setActiveSection(nextConcept.concept_key);
      return;
    }

    setViewIndexes(prev => ({ ...prev, [pagination.key]: nextIndex }));
  }, [pagination, concepts]);

  useEffect(() => {
    if (!pagination || pagination.total <= 1) return undefined;

    const isInputElement = (target) => {
      if (!target || !(target instanceof HTMLElement)) return false;
      const tag = target.tagName;
      return target.isContentEditable || tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
    };

    const handleKeyDown = (event) => {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
      if (isInputElement(event.target)) return;

      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        goToPage(-1);
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        goToPage(1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [pagination, goToPage]);

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner}></div>
        <div style={styles.loadingText}>Loading V8 Content...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.error}>
        <span style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</span>
        <div>{error}</div>
      </div>
    );
  }

  if (!v8Data || !v8Data.concepts || v8Data.concepts.length === 0) {
    return (
      <div style={styles.empty}>
        <span style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</span>
        <div>No V8 content available for this subtopic</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Top Header */}
      <header style={styles.topHeader}>
        <div style={styles.headerBrand}>
          <div
            style={styles.logoIcon}
            onClick={onToggleParentSidebar}
            title={isParentSidebarVisible ? "Hide Navigation" : "Show Navigation"}
          >
            {isParentSidebarVisible ? "V8" : <Menu size={20} />}
          </div>
          <div style={styles.headerTitle}>
            <span>{v8Data.name || 'V8 Content'}</span>
            <span style={styles.headerSubtitle}>Interactive Learning</span>
          </div>
        </div>
        <div style={styles.headerRight}>
          <nav style={styles.headerNav}>
            <button
              style={{ ...styles.navBtn, ...(activeView === 'content' ? styles.navBtnActive : {}) }}
              onClick={() => setActiveView('content')}
            >
              Learning objective
            </button>
            <button
              style={{ ...styles.navBtn, ...(activeView === 'quiz' ? styles.navBtnActive : {}) }}
              onClick={() => setActiveView('quiz')}
            >
              Quiz
            </button>
            <button
              style={{ ...styles.navBtn, ...(activeView === 'flashcards' ? styles.navBtnActive : {}) }}
              onClick={() => setActiveView('flashcards')}
            >
              Cards
            </button>
            <button
              style={{ ...styles.navBtn, ...(activeView === 'reallife' ? styles.navBtnActive : {}) }}
              onClick={() => setActiveView('reallife')}
            >
              Real Life
            </button>

            {activeView === 'content' && (
              <button
                onClick={() => setIsTocVisible(!isTocVisible)}
                style={{
                  ...styles.navBtn,
                  background: isTocVisible ? 'rgba(146, 117, 89, 0.1)' : 'transparent',
                  color: isTocVisible ? '#927559' : '#64748b',
                  marginLeft: '12px'
                }}
                title={isTocVisible ? "Hide Index" : "Show Index"}
              >
                <ListOrdered size={18} />
              </button>
            )}
          </nav>

        </div>
      </header>

      <div style={styles.layoutContainer}>
        {/* Sidebar (TOC) */}
        <aside style={{
          ...styles.sidebar,
          width: isTocVisible ? '300px' : '0',
          minWidth: isTocVisible ? '220px' : '0',
          opacity: isTocVisible ? 1 : 0,
          pointerEvents: isTocVisible ? 'auto' : 'none',
          padding: isTocVisible ? '2rem 1.5rem' : '0',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}>
          <div style={styles.sidebarSectionTitle}>Table of Contents</div>
          <ul style={styles.tocList}>
            {concepts.map((concept) => (
              <li
                key={concept.concept_key}
                style={{
                  ...styles.tocItem,
                  ...(activeSection === concept.concept_key ? styles.tocItemActive : {})
                }}
                onClick={() => scrollToSection(concept.concept_key)}
              >
                <span style={styles.tocIcon}>{concept.icon || '📚'}</span>
                <span>{concept.title}</span>
              </li>
            ))}
          </ul>

          <div style={{ ...styles.sidebarSectionTitle, marginTop: '2rem' }}>Tools</div>
          <ul style={styles.tocList}>
            <li style={styles.tocItem} onClick={() => setActiveView('quiz')}>
              <span style={styles.tocIcon}>❓</span> Practice Quiz
            </li>
            <li style={styles.tocItem} onClick={() => setActiveView('flashcards')}>
              <span style={styles.tocIcon}>⚡</span> Flashcards
            </li>
            <li style={styles.tocItem} onClick={() => setActiveView('reallife')}>
              <span style={styles.tocIcon}>🌍</span> Real Life
            </li>
          </ul>
        </aside>

        {/* Main Content */}
        <main style={styles.mainContent}>
          {/* VIEW: CONTENT */}
          {activeView === 'content' && (
            <div id="view-content">
              {currentConcept ? (
                <section
                  key={currentConcept.concept_key}
                  id={`section-${currentConcept.concept_key}`}
                  style={styles.section}
                >
                  <h2 style={styles.sectionTitle}>
                    {currentConcept.icon || '📚'} {currentConcept.title}
                  </h2>
                  <div style={styles.twoColumnLayout}>
                    <div style={styles.columnLeft}>
                      <div style={{ ...styles.card, ...styles.contentCard }}>
                        <div style={styles.cardBody}>
                          {currentConcept.description && (
                            <p style={{ marginBottom: '1rem' }}>{currentConcept.description}</p>
                          )}
                          {currentConcept.generated?.bullets ? (
                            <div
                              style={styles.bulletContent}
                              dangerouslySetInnerHTML={{
                                __html: currentConcept.generated.bullets
                                  .replace(/\$\$([^$]+)\$\$/g, '<span style="font-family: serif; font-style: italic;">$1</span>')
                                  .replace(/\$([^$]+)\$/g, '<span style="font-family: serif; font-style: italic;">$1</span>')
                              }}
                            />
                          ) : null}
                        </div>
                      </div>
                    </div>
                    <div style={styles.columnRight}>
                      <div style={{ ...styles.card, ...styles.visualCard }}>
                        <div style={styles.visualContainer}>
                          {currentConcept.generated?.svg ? (
                            <div
                              dangerouslySetInnerHTML={{ __html: currentConcept.generated.svg }}
                              style={{ width: '100%', height: '100%' }}
                            />
                          ) : (
                            <div style={styles.noVisual}>
                              <span style={{ fontSize: '3rem', opacity: 0.3 }}>📊</span>
                              <div style={{ color: '#94a3b8', marginTop: '0.5rem' }}>No visual available</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </section>
              ) : (
                <div style={styles.empty}>
                  <span style={{ fontSize: '3rem' }}>📚</span>
                  <div>No concepts available</div>
                </div>
              )}
            </div>
          )}

          {/* VIEW: QUIZ */}
          {activeView === 'quiz' && (
            <div id="view-quiz">
              <h2 style={styles.sectionTitle}>❓ Practice Quiz</h2>
              {currentQuiz ? (
                <div key={currentQuiz.id || currentQuizIndex} style={styles.quizQuestion}>
                  <div style={styles.qHeader}>
                    <span style={styles.qBadge}>Question {currentQuiz.question_num || currentQuizIndex + 1}</span>
                    <span style={{
                      ...styles.qBadge,
                      background: quizAnswers[currentQuizKey] === currentQuiz.correct_answer ? '#059669' :
                        quizAnswers[currentQuizKey] ? '#be123c' : '#0f172a'
                    }}>
                      {quizAnswers[currentQuizKey] === currentQuiz.correct_answer ? '✓ Correct' :
                        quizAnswers[currentQuizKey] ? '✗ Incorrect' : 'Not answered'}
                    </span>
                  </div>
                  <div style={styles.qText}>{currentQuiz.question_text}</div>
                  <div style={styles.qOptions}>
                    {['A', 'B', 'C', 'D'].map(opt => {
                      const currentAnswer = quizAnswers[currentQuizKey];
                      return (
                        <div
                          key={opt}
                          style={{
                            ...styles.qOption,
                            ...(currentAnswer === opt ? styles.qOptionSelected : {}),
                            ...(currentAnswer && opt === currentQuiz.correct_answer ? styles.qOptionCorrect : {})
                          }}
                          onClick={() => selectQuizAnswer(currentQuizKey, opt)}
                        >
                          <strong>{opt}.</strong> {currentQuizOptions?.[opt]}
                        </div>
                      );
                    })}
                  </div>
                  {quizAnswers[currentQuizKey] && (
                    <div style={styles.qExplanation}>
                      <strong>Explanation:</strong> {currentQuiz.explanation}
                    </div>
                  )}
                </div>
              ) : (
                <div style={styles.empty}>
                  <span style={{ fontSize: '3rem' }}>📝</span>
                  <div>No quiz questions available</div>
                </div>
              )}
            </div>
          )}

          {/* VIEW: FLASHCARDS */}
          {activeView === 'flashcards' && (
            <div id="view-flashcards">
              <h2 style={styles.sectionTitle}>⚡ Flashcards</h2>
              {currentFlashcard ? (
                <div style={styles.flashcardPagerContainer}>
                  <div
                    key={currentFlashcard.id || currentFlashcardIndex}
                    style={styles.flashcard}
                    onClick={() => toggleCard(String(currentFlashcard.id || currentFlashcardIndex))}
                  >
                    <div style={{
                      ...styles.flashcardInner,
                      ...(flippedCards[String(currentFlashcard.id || currentFlashcardIndex)] ? styles.flashcardFlipped : {})
                    }}>
                      <div style={styles.flashcardFront}>
                        <h3>{currentFlashcard.front}</h3>
                        <span style={styles.tapHint}>Tap to flip</span>
                      </div>
                      <div style={styles.flashcardBack}>
                        <p>{currentFlashcard.back}</p>
                        <span style={styles.tapHint}>Tap to flip back</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={styles.empty}>
                  <span style={{ fontSize: '3rem' }}>🃏</span>
                  <div>No flashcards available</div>
                </div>
              )}
            </div>
          )}

          {/* VIEW: REAL LIFE */}
          {activeView === 'reallife' && (
            <div id="view-reallife">
              <div style={styles.reallifeHeader}>
                <h2 style={styles.sectionTitle}>🌍 Real Life Applications</h2>
                <p style={styles.sectionDesc}>Connecting concepts to the world around us</p>
              </div>
              {currentReallife ? (
                <div style={styles.reallifeGrid}>
                  <div key={currentReallife.id || currentReallifeIndex} style={styles.reallifeCard}>
                    <div style={styles.reallifeLayout}>
                      <div style={styles.reallifeImage}>
                        {currentReallife.image_url ? (
                          <img src={currentReallife.image_url} alt={currentReallife.title} style={styles.reallifeImg} />
                        ) : (
                          <div style={styles.reallifePlaceholder}>
                            <span style={{ fontSize: '4rem' }}>🖼️</span>
                          </div>
                        )}
                      </div>
                      <div style={styles.reallifeArrow}>
                        <svg style={styles.arrowSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                      </div>
                      <div style={styles.reallifeContent}>
                        <div style={{
                          ...styles.reallifeIcon,
                          background: currentReallifeIndex % 3 === 0 ? '#fff1f2' : currentReallifeIndex % 3 === 1 ? '#e0f2fe' : '#fef3c7',
                          color: currentReallifeIndex % 3 === 0 ? '#be123c' : currentReallifeIndex % 3 === 1 ? '#0369a1' : '#d97706'
                        }}>
                          {currentReallife.image_type === 'example' ? '🔬' : currentReallife.image_type === 'application' ? '💡' : '🌍'}
                        </div>
                        <h3 style={styles.reallifeTitle}>{currentReallife.title || `Application ${currentReallifeIndex + 1}`}</h3>
                        <p style={styles.reallifeDesc}>{currentReallife.description}</p>
                        {currentReallife.prompt && (
                          <div style={{
                            ...styles.reallifeBox,
                            ...(currentReallifeIndex % 3 === 0 ? styles.reallifeBoxPrimary :
                              currentReallifeIndex % 3 === 1 ? styles.reallifeBoxSecondary : styles.reallifeBoxWarning)
                          }}>
                            <h4>Key Insight</h4>
                            <p>{currentReallife.prompt}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={styles.empty}>
                  <span style={{ fontSize: '3rem' }}>🌍</span>
                  <div>No real-life applications available</div>
                  <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                    Generate V8 content with images enabled to see real-life examples
                  </div>
                </div>
              )}
            </div>
          )}

          {pagination && pagination.total > 1 && (
            <div style={styles.paginationFooter}>
              <div style={styles.paginationBar}>
                <button
                  style={{ ...styles.paginationBtn, ...(pagination.index === 0 ? styles.paginationBtnDisabled : {}) }}
                  onClick={() => goToPage(-1)}
                  disabled={pagination.index === 0}
                  title={`Previous ${pagination.label}`}
                >
                  <ChevronLeft size={18} />
                </button>
                <div style={styles.paginationMeta}>
                  {pagination.label} {pagination.index + 1} / {pagination.total}
                </div>
                <button
                  style={{ ...styles.paginationBtn, ...(pagination.index >= pagination.total - 1 ? styles.paginationBtnDisabled : {}) }}
                  onClick={() => goToPage(1)}
                  disabled={pagination.index >= pagination.total - 1}
                  title={`Next ${pagination.label}`}
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

// ============================================================================
// STYLES
// ============================================================================

const styles = {
  container: {
    fontFamily: "'Outfit', sans-serif",
    background: '#fcfaf7',
    height: '100%',
    width: '100%',
    color: '#1a1a1b',
    lineHeight: 1.6,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },

  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4rem 2rem',
    color: '#334155',
  },

  spinner: {
    width: '48px',
    height: '48px',
    border: '3px solid rgba(146, 117, 89, 0.1)',
    borderTopColor: '#927559',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '1rem',
  },

  loadingText: {
    fontSize: '1rem',
    fontWeight: 500,
  },

  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4rem 2rem',
    color: '#991b1b',
    textAlign: 'center',
  },

  empty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4rem 2rem',
    color: '#64748b',
    textAlign: 'center',
  },

  // Header
  topHeader: {
    height: '72px',
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    borderBottom: '1px solid rgba(0, 0, 0, 0.04)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 2.5rem',
  },

  headerBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.25rem',
  },

  logoIcon: {
    width: '40px',
    height: '40px',
    background: '#1e293b',
    borderRadius: '12px',
    display: 'grid',
    placeItems: 'center',
    color: '#927559',
    fontWeight: 800,
    fontSize: '14px',
    boxShadow: '0 4px 12px rgba(30, 41, 59, 0.15)',
  },

  headerTitle: {
    fontWeight: 800,
    fontSize: '1.25rem',
    display: 'flex',
    flexDirection: 'column',
    lineHeight: 1.2,
    color: '#1e293b',
    letterSpacing: '-0.02em',
  },

  headerSubtitle: {
    fontSize: '0.75rem',
    color: '#927559',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },

  headerNav: {
    display: 'flex',
    background: 'rgba(30, 41, 59, 0.04)',
    padding: '6px',
    borderRadius: '16px',
    border: '1px solid rgba(0, 0, 0, 0.04)',
    gap: '4px',
  },

  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },

  paginationBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    background: 'rgba(30, 41, 59, 0.04)',
    border: '1px solid rgba(0, 0, 0, 0.04)',
    borderRadius: '999px',
    padding: '6px',
  },

  paginationFooter: {
    marginTop: '2rem',
    display: 'flex',
    justifyContent: 'center',
  },

  paginationBtn: {
    width: '32px',
    height: '32px',
    borderRadius: '999px',
    border: 'none',
    background: 'white',
    color: '#1e293b',
    display: 'grid',
    placeItems: 'center',
    cursor: 'pointer',
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.08)',
  },

  paginationBtnDisabled: {
    opacity: 0.35,
    cursor: 'not-allowed',
    boxShadow: 'none',
  },

  paginationMeta: {
    fontSize: '0.82rem',
    fontWeight: 700,
    color: '#334155',
    minWidth: '128px',
    textAlign: 'center',
  },

  navBtn: {
    padding: '0.6rem 1.25rem',
    border: 'none',
    background: 'transparent',
    color: '#475569',
    fontWeight: 600,
    fontSize: '0.9rem',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  },

  navBtnActive: {
    background: 'white',
    color: '#927559',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
  },

  // Layout
  layoutContainer: {
    display: 'flex',
    flex: 1,
    height: 'calc(100vh - 72px)',
    maxWidth: '100%',
    margin: '0',
    gap: '0',
    overflow: 'hidden',
  },

  // Bullet content styling
  bulletContent: {
    lineHeight: 1.9,
    color: '#334155',
    fontSize: '1.05rem',
  },

  sidebar: {
    background: 'rgba(255, 255, 255, 0.5)',
    borderRight: '1px solid rgba(0, 0, 0, 0.04)',
    overflowY: 'auto',
    height: '100%',
  },

  sidebarSectionTitle: {
    textTransform: 'uppercase',
    fontSize: '0.7rem',
    fontWeight: 800,
    color: '#927559',
    letterSpacing: '0.1em',
    marginBottom: '1rem',
    paddingLeft: '0.75rem',
  },

  tocList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },

  tocItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '12px 16px',
    borderRadius: '14px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    fontSize: '0.95rem',
    color: '#475569',
    fontWeight: 500,
  },

  tocItemActive: {
    background: 'rgba(146, 117, 89, 0.1)',
    color: '#1e293b',
    fontWeight: 700,
    boxShadow: 'inset 0 0 0 1px rgba(146, 117, 89, 0.2)',
  },

  tocIcon: {
    fontSize: '1.25rem',
    opacity: 0.8,
  },

  mainContent: {
    flex: 1,
    padding: '3rem 4rem',
    overflowY: 'auto',
    height: '100%',
  },

  // Section
  section: {
    marginBottom: '5rem',
    scrollMarginTop: 'calc(72px + 3rem)',
    animation: 'fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
  },

  sectionTitle: {
    fontSize: '2.25rem',
    fontWeight: 800,
    color: '#1e293b',
    letterSpacing: '-0.04em',
    marginBottom: '2rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },

  // Two Column Layout
  twoColumnLayout: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '2.5rem',
    alignItems: 'stretch',
  },

  columnLeft: {
    minWidth: 0,
  },

  columnRight: {
    minWidth: 0,
  },

  // Card
  card: {
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(8px)',
    border: '1px solid rgba(0, 0, 0, 0.04)',
    borderRadius: '24px',
    padding: '2.5rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.02)',
    transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
  },

  contentCard: {
    height: '100%',
  },

  visualCard: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    background: 'rgba(252, 250, 247, 0.7)',
  },

  cardBody: {
    color: '#334155',
    lineHeight: 1.9,
  },

  visualContainer: {
    background: 'white',
    border: '1px solid rgba(0, 0, 0, 0.03)',
    borderRadius: '20px',
    padding: '2rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)',
  },

  noVisual: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.3,
  },

  // Quiz
  quizQuestion: {
    background: 'white',
    borderRadius: '24px',
    padding: '3rem',
    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.04)',
    marginBottom: '2.5rem',
    border: '1px solid rgba(0,0,0,0.04)',
  },

  qHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
  },

  qBadge: {
    background: '#1e293b',
    color: 'white',
    padding: '0.5rem 1.25rem',
    borderRadius: '999px',
    fontWeight: 800,
    fontSize: '0.75rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },

  qText: {
    fontSize: '1.5rem',
    fontWeight: 800,
    color: '#1e293b',
    marginBottom: '2.5rem',
    letterSpacing: '-0.02em',
    lineHeight: 1.4,
  },

  qOptions: {
    display: 'grid',
    gap: '1rem',
  },

  qOption: {
    padding: '1.25rem 1.75rem',
    border: '2px solid rgba(0, 0, 0, 0.04)',
    borderRadius: '16px',
    cursor: 'pointer',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    fontWeight: 600,
    fontSize: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },

  qOptionSelected: {
    borderColor: '#927559',
    background: 'rgba(146, 117, 89, 0.05)',
    color: '#927559',
  },

  qOptionCorrect: {
    borderColor: '#3d5a45',
    background: 'rgba(61, 90, 69, 0.05)',
    color: '#3d5a45',
  },

  qExplanation: {
    marginTop: '2.5rem',
    padding: '2rem',
    background: 'rgba(146, 117, 89, 0.05)',
    borderRadius: '16px',
    fontSize: '1rem',
    borderLeft: '4px solid #927559',
    lineHeight: 1.7,
  },

  // Flashcards
  flashcardContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '2rem',
  },

  flashcardPagerContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: '8px',
  },

  flashcard: {
    perspective: '1200px',
    height: '280px',
    width: 'min(100%, 420px)',
    cursor: 'pointer',
  },

  flashcardInner: {
    position: 'relative',
    width: '100%',
    height: '100%',
    transition: 'transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    transformStyle: 'preserve-3d',
    borderRadius: '24px',
    boxShadow: '0 15px 35px -5px rgba(0,0,0,0.05)',
  },

  flashcardFlipped: {
    transform: 'rotateY(180deg)',
  },

  flashcardFront: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backfaceVisibility: 'hidden',
    borderRadius: '24px',
    padding: '3rem',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center',
    background: 'white',
    border: '1px solid rgba(0,0,0,0.03)',
  },

  flashcardBack: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backfaceVisibility: 'hidden',
    borderRadius: '24px',
    padding: '3rem',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center',
    background: '#1e293b',
    color: 'white',
    transform: 'rotateY(180deg)',
  },

  tapHint: {
    position: 'absolute',
    bottom: '1.5rem',
    fontSize: '0.7rem',
    opacity: 0.4,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    fontWeight: 800,
  },

  // Real Life View
  reallifeHeader: {
    textAlign: 'center',
    marginBottom: '4rem',
  },

  sectionDesc: {
    fontSize: '1.25rem',
    color: '#475569',
    marginTop: '0.5rem',
    fontWeight: 500,
  },

  reallifeGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '3rem',
    maxWidth: '1400px',
    margin: '0 auto',
  },

  reallifeCard: {
    background: 'white',
    borderRadius: '32px',
    boxShadow: '0 20px 50px -12px rgba(0,0,0,0.05)',
    border: '1px solid rgba(0,0,0,0.03)',
    overflow: 'hidden',
    transition: 'all 0.4s ease',
  },

  reallifeLayout: {
    display: 'grid',
    gridTemplateColumns: '450px 80px 1fr',
    gap: '0',
    padding: '0',
    alignItems: 'stretch',
  },

  reallifeImage: {
    display: 'flex',
    background: '#fcfaf7',
    overflow: 'hidden',
  },

  reallifeImg: {
    width: '100%',
    height: '400px',
    objectFit: 'cover',
  },

  reallifePlaceholder: {
    width: '100%',
    height: '400px',
    background: 'linear-gradient(135deg, #fcfaf7 0%, #f1f5f9 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  reallifeArrow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'white',
    opacity: 0.3,
  },

  arrowSvg: {
    width: '48px',
    height: '48px',
    color: '#927559',
  },

  reallifeContent: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    padding: '4rem',
    gap: '1.5rem',
  },

  reallifeIcon: {
    width: '64px',
    height: '64px',
    borderRadius: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2rem',
    boxShadow: '0 8px 16px -4px rgba(0,0,0,0.15)',
  },

  reallifeTitle: {
    fontSize: '2rem',
    fontWeight: 800,
    color: '#1e293b',
    margin: 0,
    letterSpacing: '-0.03em',
  },

  reallifeDesc: {
    color: '#475569',
    fontSize: '1.15rem',
    lineHeight: 1.7,
    margin: 0,
    opacity: 0.8,
  },

  reallifeBox: {
    padding: '1.5rem 2rem',
    borderRadius: '20px',
    marginTop: '1rem',
    boxShadow: '0 4px 12px rgba(0,0,0,0.03)',
  },

  reallifeBoxPrimary: {
    background: '#fcfaf7',
    borderLeft: '4px solid #927559',
    color: '#1e293b',
  },

  reallifeBoxSecondary: {
    background: '#fcfaf7',
    borderLeft: '4px solid #1e293b',
    color: '#1e293b',
  },

  reallifeBoxWarning: {
    background: '#fcfaf7',
    borderLeft: '4px solid #927559',
    color: '#1e293b',
  },
};

export default V8ContentViewer;
