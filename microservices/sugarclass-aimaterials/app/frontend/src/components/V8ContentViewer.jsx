import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';

// ============================================================================
// V8 CONTENT VIEWER - Matches V8 Generator HTML Layout
// ============================================================================

const V8ContentViewer = ({ subtopicId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [v8Data, setV8Data] = useState(null);
  const [activeView, setActiveView] = useState('content');
  const [activeSection, setActiveSection] = useState(null);
  const [flippedCards, setFlippedCards] = useState({});
  const [quizAnswers, setQuizAnswers] = useState({});

  useEffect(() => {
    if (!subtopicId) return;
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
    setActiveSection(sectionId);
    const element = document.getElementById(`section-${sectionId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const toggleCard = (cardId) => {
    setFlippedCards(prev => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  const selectQuizAnswer = (questionId, answer) => {
    setQuizAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

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
          <div style={styles.logoIcon}>V8</div>
          <div style={styles.headerTitle}>
            <span>{v8Data.name || 'V8 Content'}</span>
            <span style={styles.headerSubtitle}>Interactive Learning</span>
          </div>
        </div>
        <nav style={styles.headerNav}>
          <button
            style={{ ...styles.navBtn, ...(activeView === 'content' ? styles.navBtnActive : {}) }}
            onClick={() => setActiveView('content')}
          >
            Learn
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
        </nav>
      </header>

      <div style={styles.layoutContainer}>
        {/* Sidebar */}
        <aside style={styles.sidebar}>
          <div style={styles.sidebarSectionTitle}>Table of Contents</div>
          <ul style={styles.tocList}>
            {v8Data.concepts.map((concept) => (
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
              {v8Data.concepts.map((concept, index) => (
                <section
                  key={concept.concept_key}
                  id={`section-${concept.concept_key}`}
                  style={styles.section}
                >
                  <h2 style={styles.sectionTitle}>
                    {concept.icon || '📚'} {concept.title}
                  </h2>
                  <div style={styles.twoColumnLayout}>
                    <div style={styles.columnLeft}>
                      <div style={{ ...styles.card, ...styles.contentCard }}>
                        <div style={styles.cardBody}>
                          {concept.description && (
                            <p style={{ marginBottom: '1rem' }}>{concept.description}</p>
                          )}
                          {concept.generated?.bullets ? (
                            <div
                              style={styles.bulletContent}
                              dangerouslySetInnerHTML={{
                                __html: concept.generated.bullets
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
                          {concept.generated?.svg ? (
                            <div
                              dangerouslySetInnerHTML={{ __html: concept.generated.svg }}
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
              ))}
            </div>
          )}

          {/* VIEW: QUIZ */}
          {activeView === 'quiz' && (
            <div id="view-quiz">
              <h2 style={styles.sectionTitle}>❓ Practice Quiz</h2>
              {v8Data.quiz && v8Data.quiz.length > 0 ? (
                v8Data.quiz.map((q, index) => (
                  <div key={q.id || index} style={styles.quizQuestion}>
                    <div style={styles.qHeader}>
                      <span style={styles.qBadge}>Question {q.question_num || index + 1}</span>
                      <span style={{
                        ...styles.qBadge,
                        background: quizAnswers[q.id] === q.correct_answer ? '#059669' :
                          quizAnswers[q.id] ? '#be123c' : '#0f172a'
                      }}>
                        {quizAnswers[q.id] === q.correct_answer ? '✓ Correct' :
                          quizAnswers[q.id] ? '✗ Incorrect' : 'Not answered'}
                      </span>
                    </div>
                    <div style={styles.qText}>{q.question_text}</div>
                    <div style={styles.qOptions}>
                      {['A', 'B', 'C', 'D'].map(opt => (
                        <div
                          key={opt}
                          style={{
                            ...styles.qOption,
                            ...(quizAnswers[q.id] === opt ? styles.qOptionSelected : {}),
                            ...(quizAnswers[q.id] && opt === q.correct_answer ? styles.qOptionCorrect : {})
                          }}
                          onClick={() => selectQuizAnswer(q.id, opt)}
                        >
                          <strong>{opt}.</strong> {q.options?.[opt]}
                        </div>
                      ))}
                    </div>
                    {quizAnswers[q.id] && (
                      <div style={styles.qExplanation}>
                        <strong>Explanation:</strong> {q.explanation}
                      </div>
                    )}
                  </div>
                ))
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
              {v8Data.flashcards && v8Data.flashcards.length > 0 ? (
                <div style={styles.flashcardContainer}>
                  {v8Data.flashcards.map((card, index) => (
                    <div
                      key={card.id || index}
                      style={styles.flashcard}
                      onClick={() => toggleCard(card.id || index)}
                    >
                      <div style={{
                        ...styles.flashcardInner,
                        ...(flippedCards[card.id || index] ? styles.flashcardFlipped : {})
                      }}>
                        <div style={styles.flashcardFront}>
                          <h3>{card.front}</h3>
                          <span style={styles.tapHint}>Tap to flip</span>
                        </div>
                        <div style={styles.flashcardBack}>
                          <p>{card.back}</p>
                          <span style={styles.tapHint}>Tap to flip back</span>
                        </div>
                      </div>
                    </div>
                  ))}
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
              {v8Data.reallife_images && v8Data.reallife_images.length > 0 ? (
                <div style={styles.reallifeGrid}>
                  {v8Data.reallife_images.map((item, index) => (
                    <div key={item.id || index} style={styles.reallifeCard}>
                      <div style={styles.reallifeLayout}>
                        <div style={styles.reallifeImage}>
                          {item.image_url ? (
                            <img src={item.image_url} alt={item.title} style={styles.reallifeImg} />
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
                            background: index % 3 === 0 ? '#fff1f2' : index % 3 === 1 ? '#e0f2fe' : '#fef3c7',
                            color: index % 3 === 0 ? '#be123c' : index % 3 === 1 ? '#0369a1' : '#d97706'
                          }}>
                            {item.image_type === 'example' ? '🔬' : item.image_type === 'application' ? '💡' : '🌍'}
                          </div>
                          <h3 style={styles.reallifeTitle}>{item.title || `Application ${index + 1}`}</h3>
                          <p style={styles.reallifeDesc}>{item.description}</p>
                          {item.prompt && (
                            <div style={{
                              ...styles.reallifeBox,
                              ...(index % 3 === 0 ? styles.reallifeBoxPrimary :
                                index % 3 === 1 ? styles.reallifeBoxSecondary : styles.reallifeBoxWarning)
                            }}>
                              <h4>Key Insight</h4>
                              <p>{item.prompt}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
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
    minHeight: '100vh',
    color: '#1a1a1b',
    lineHeight: 1.6,
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
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    minHeight: 'calc(100vh - 72px)',
    maxWidth: '1800px',
    margin: '0 auto',
    gap: '0',
  },

  // Bullet content styling
  bulletContent: {
    lineHeight: 1.9,
    color: '#334155',
    fontSize: '1.05rem',
  },

  sidebar: {
    width: '300px',
    background: 'rgba(255, 255, 255, 0.5)',
    borderRight: '1px solid rgba(0, 0, 0, 0.04)',
    padding: '2rem 1.5rem',
    overflowY: 'auto',
    height: 'calc(100vh - 72px)',
    position: 'sticky',
    top: '72px',
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

  flashcard: {
    perspective: '1200px',
    height: '280px',
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
