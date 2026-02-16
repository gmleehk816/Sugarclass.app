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
                              dangerouslySetInnerHTML={{ __html: concept.generated.bullets
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
    fontFamily: "'Inter', system-ui, sans-serif",
    background: '#f8fafc',
    minHeight: '100vh',
    color: '#0f172a',
    lineHeight: 1.6,
  },

  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4rem 2rem',
    color: '#64748b',
  },

  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid #e2e8f0',
    borderTopColor: '#be123c',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '1rem',
  },

  loadingText: {
    fontSize: '1rem',
  },

  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4rem 2rem',
    color: '#be123c',
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
    height: '64px',
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(8px)',
    borderBottom: '1px solid #e2e8f0',
    position: 'sticky',
    top: 0,
    zIndex: 50,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 1.5rem',
  },

  headerBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },

  logoIcon: {
    width: '32px',
    height: '32px',
    background: 'linear-gradient(135deg, #be123c, #0369a1)',
    borderRadius: '8px',
    display: 'grid',
    placeItems: 'center',
    color: 'white',
    fontWeight: 800,
    fontSize: '12px',
  },

  headerTitle: {
    fontWeight: 700,
    fontSize: '1.125rem',
    display: 'flex',
    flexDirection: 'column',
    lineHeight: 1.2,
  },

  headerSubtitle: {
    fontSize: '0.75rem',
    color: '#64748b',
    fontWeight: 500,
  },

  headerNav: {
    display: 'flex',
    background: '#f8fafc',
    padding: '4px',
    borderRadius: '10px',
    border: '1px solid #e2e8f0',
  },

  navBtn: {
    padding: '0.5rem 1rem',
    border: 'none',
    background: 'transparent',
    color: '#64748b',
    fontWeight: 600,
    fontSize: '0.875rem',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },

  navBtnActive: {
    background: 'white',
    color: '#be123c',
    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
  },

  // Layout
  layoutContainer: {
    display: 'flex',
    minHeight: 'calc(100vh - 64px)',
    maxWidth: '1600px',
    margin: '0 auto',
  },

  // Bullet content styling
  bulletContent: {
    lineHeight: 1.8,
    color: '#475569',
  },

  sidebar: {
    width: '240px',
    background: 'white',
    borderRight: '1px solid #e2e8f0',
    padding: '1.5rem 1rem',
    overflowY: 'auto',
    height: 'calc(100vh - 64px)',
    position: 'sticky',
    top: '64px',
  },

  sidebarSectionTitle: {
    textTransform: 'uppercase',
    fontSize: '0.75rem',
    fontWeight: 700,
    color: '#94a3b8',
    letterSpacing: '0.05em',
    marginBottom: '0.75rem',
    paddingLeft: '0.75rem',
  },

  tocList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },

  tocItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.75rem',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontSize: '0.9rem',
    color: '#64748b',
  },

  tocItemActive: {
    background: '#fff1f2',
    color: '#be123c',
    fontWeight: 600,
  },

  tocIcon: {
    fontSize: '1.25rem',
  },

  mainContent: {
    flex: 1,
    padding: '2rem',
    marginLeft: '0',
  },

  // Section
  section: {
    marginBottom: '3rem',
    scrollMarginTop: 'calc(64px + 2rem)',
  },

  sectionTitle: {
    fontSize: '1.875rem',
    fontWeight: 800,
    color: '#0f172a',
    letterSpacing: '-0.025em',
    marginBottom: '1.5rem',
  },

  // Two Column Layout
  twoColumnLayout: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1.5rem',
    alignItems: 'start',
  },

  columnLeft: {
    minWidth: 0,
  },

  columnRight: {
    minWidth: 0,
  },

  // Card
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '16px',
    padding: '1.5rem',
    marginBottom: '1.5rem',
    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
  },

  contentCard: {
    height: '100%',
  },

  visualCard: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },

  cardBody: {
    color: '#475569',
    lineHeight: 1.8,
  },

  visualContainer: {
    background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
    border: '1px solid #e2e8f0',
    borderRadius: '16px',
    padding: '1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '300px',
  },

  noVisual: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Feature List
  featureList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },

  styledListItem: {
    padding: '0.8rem 1.2rem',
    marginBottom: '0.6rem',
    background: 'linear-gradient(135deg, #ffffff 0%, #fff1f2 100%)',
    borderLeft: '4px solid #be123c',
    borderRadius: '8px',
    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
    fontSize: '1rem',
    lineHeight: 1.6,
  },

  // Quiz
  quizQuestion: {
    background: 'white',
    borderRadius: '16px',
    padding: '2rem',
    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    marginBottom: '2rem',
    border: '1px solid #e2e8f0',
  },

  qHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },

  qBadge: {
    background: '#0f172a',
    color: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '999px',
    fontWeight: 700,
    fontSize: '0.875rem',
  },

  qText: {
    fontSize: '1.25rem',
    fontWeight: 700,
    marginBottom: '1.5rem',
  },

  qOptions: {
    display: 'grid',
    gap: '0.75rem',
  },

  qOption: {
    padding: '1rem 1.25rem',
    border: '2px solid #e2e8f0',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontWeight: 500,
  },

  qOptionSelected: {
    borderColor: '#be123c',
    background: '#fff1f2',
  },

  qOptionCorrect: {
    borderColor: '#059669',
    background: '#d1fae5',
  },

  qExplanation: {
    marginTop: '1.5rem',
    padding: '1rem',
    background: '#fef3c7',
    borderRadius: '8px',
    fontSize: '0.95rem',
  },

  // Flashcards
  flashcardContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1.5rem',
  },

  flashcard: {
    perspective: '1000px',
    height: '220px',
    cursor: 'pointer',
  },

  flashcardInner: {
    position: 'relative',
    width: '100%',
    height: '100%',
    transition: 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
    transformStyle: 'preserve-3d',
    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    borderRadius: '16px',
  },

  flashcardFlipped: {
    transform: 'rotateY(180deg)',
  },

  flashcardFront: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backfaceVisibility: 'hidden',
    borderRadius: '16px',
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center',
    background: 'white',
    border: '1px solid rgba(0,0,0,0.05)',
  },

  flashcardBack: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backfaceVisibility: 'hidden',
    borderRadius: '16px',
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center',
    background: 'linear-gradient(135deg, #0369a1, #0284c7)',
    color: 'white',
    transform: 'rotateY(180deg)',
  },

  tapHint: {
    position: 'absolute',
    bottom: '1rem',
    fontSize: '0.75rem',
    opacity: 0.6,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },

  // Real Life View
  reallifeHeader: {
    textAlign: 'center',
    marginBottom: '2rem',
  },

  sectionDesc: {
    fontSize: '1.125rem',
    color: '#64748b',
    marginTop: '-0.5rem',
  },

  reallifeGrid: {
    display: 'grid',
    gap: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
  },

  reallifeCard: {
    background: 'white',
    borderRadius: '16px',
    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    border: '1px solid #e2e8f0',
    overflow: 'hidden',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  },

  reallifeLayout: {
    display: 'grid',
    gridTemplateColumns: '280px 40px 1fr',
    gap: '1.5rem',
    padding: '2rem',
    alignItems: 'center',
  },

  reallifeImage: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  reallifeImg: {
    width: '100%',
    maxWidth: '280px',
    height: 'auto',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    objectFit: 'cover',
  },

  reallifePlaceholder: {
    width: '280px',
    height: '200px',
    background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  reallifeArrow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  arrowSvg: {
    width: '40px',
    height: '40px',
    color: '#64748b',
    animation: 'arrowPulse 2s ease-in-out infinite',
  },

  reallifeContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },

  reallifeIcon: {
    width: '48px',
    height: '48px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.5rem',
    marginBottom: '0.5rem',
  },

  reallifeTitle: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#0f172a',
    margin: 0,
  },

  reallifeDesc: {
    color: '#475569',
    lineHeight: 1.6,
    margin: 0,
  },

  reallifeBox: {
    padding: '1rem 1.25rem',
    borderRadius: '12px',
    marginTop: '0.5rem',
  },

  reallifeBoxPrimary: {
    background: '#fff1f2',
    borderLeft: '4px solid #be123c',
    color: '#881337',
  },

  reallifeBoxSecondary: {
    background: '#e0f2fe',
    borderLeft: '4px solid #0369a1',
    color: '#0c4a6e',
  },

  reallifeBoxWarning: {
    background: '#fef3c7',
    borderLeft: '4px solid #d97706',
    color: '#78350f',
  },
};

export default V8ContentViewer;
