import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import { ChevronLeft, ChevronRight, MenuBook } from '@mui/icons-material';
import ContentArea from './ContentArea';
import QuestionCard from './QuestionCard';
import ExerciseArea from './ExerciseArea';

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

  const handlePrev = () => {
    if (currentQuestionIndex > 0) onQuestionIndexChange(currentQuestionIndex - 1);
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) onQuestionIndexChange(currentQuestionIndex + 1);
  };

  const handleExercisePrev = () => {
    if (currentExerciseIndex > 0) onExerciseIndexChange(currentExerciseIndex - 1);
  };

  const handleExerciseNext = () => {
    if (currentExerciseIndex < exercises.length - 1) onExerciseIndexChange(currentExerciseIndex + 1);
  };

  if (!selectedTopic) {
    return (
      <Box className="empty-state">
        <MenuBook className="empty-icon" style={{ fontSize: 24, width: 24, height: 24, color: '#a5b4fc', display: 'block' }} />
        <Typography className="empty-title">Select a topic to start</Typography>
        <Typography className="empty-desc">Choose a chapter from the left sidebar</Typography>
      </Box>
    );
  }

  return (
    <Box className="middle-area" style={{ boxShadow: '0 2px 16px 0 #e0e7ef', borderRadius: 16, margin: 16, minHeight: 600, background: '#f8fafc' }}>
      {/* Compact Header - Only show for exercise/qa modes */}
      {(viewMode === 'exercise' || viewMode === 'qa') && (
        <Box className="middle-header" style={{ borderRadius: '16px 16px 0 0', boxShadow: '0 1px 4px #e0e7ef', background: '#fff', padding: '18px 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography className="middle-header-title" style={{ fontSize: 22, fontWeight: 700, color: '#3730a3', margin: 0 }}>{selectedTopic.name}</Typography>

          {viewMode === 'exercise' && exercises.length > 0 && (
            <Box className="nav-controls">
              <IconButton onClick={handleExercisePrev} disabled={currentExerciseIndex === 0} size="small">
                <ChevronLeft />
              </IconButton>
              <span className="nav-counter">{currentExerciseIndex + 1} / {exercises.length}</span>
              <IconButton onClick={handleExerciseNext} disabled={currentExerciseIndex >= exercises.length - 1} size="small">
                <ChevronRight />
              </IconButton>
            </Box>
          )}

          {viewMode === 'qa' && questions.length > 0 && (
            <Box className="nav-controls">
              <IconButton onClick={handlePrev} disabled={currentQuestionIndex === 0} size="small">
                <ChevronLeft />
              </IconButton>
              <span className="nav-counter">{currentQuestionIndex + 1} / {questions.length}</span>
              <IconButton onClick={handleNext} disabled={currentQuestionIndex >= questions.length - 1} size="small">
                <ChevronRight />
              </IconButton>
            </Box>
          )}
        </Box>
      )}

      {/* Main Content Area */}
      <Box className="middle-content" style={{ padding: 32, background: '#f8fafc', borderRadius: '0 0 16px 16px', minHeight: 400 }}>
        {viewMode === 'content' && (
          selectedSubtopicId ? (
            <ContentArea
              subtopicId={selectedSubtopicId}
              subjectId={subjectId}
              contentMode={contentMode}
              onContentModeChange={onContentModeChange}
            />
          ) : (
            <Box className="empty-state small">
              <Typography className="empty-desc">Select a subtopic from the right sidebar</Typography>
            </Box>
          )
        )}

        {viewMode === 'exercise' && (
          exercises.length > 0 ? (
            <ExerciseArea
              exercise={exercises[currentExerciseIndex]}
              index={currentExerciseIndex}
              total={exercises.length}
            />
          ) : (
            <Box className="empty-state small">
              <Typography className="empty-desc">No exercises available for this topic yet.</Typography>
            </Box>
          )
        )}

        {viewMode === 'qa' && (
          questions.length > 0 ? (
            <QuestionCard
              question={questions[currentQuestionIndex]}
              index={currentQuestionIndex}
              total={questions.length}
            />
          ) : (
            <Box className="empty-state small">
              <Typography className="empty-desc">No questions available for this topic yet.</Typography>
            </Box>
          )
        )}
      </Box>
    </Box>
  );
}

export default MiddleArea;
