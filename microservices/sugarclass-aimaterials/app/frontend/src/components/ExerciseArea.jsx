import React, { useState } from 'react';
import { Box, Paper, Typography, Button, Chip, Collapse, Alert } from '@mui/material';
import { Visibility, CheckCircle, Cancel } from '@mui/icons-material';

function ExerciseArea({ exercise, index, total }) {
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showAnswer, setShowAnswer] = useState(false);

  // Reset state when exercise changes
  React.useEffect(() => {
    setSelectedAnswer(null);
    setShowAnswer(false);
  }, [exercise]);

  if (!exercise) return null;

  // Handle both generated exercises (with options object) and textbook questions
  const isGeneratedExercise = exercise.question_text && exercise.options && typeof exercise.options === 'object';
  const exerciseText = exercise.question_text || exercise.name || '';
  const exerciseId = exercise.subtopic_id || exercise.id || '';
  const options = exercise.options || {};
  const correctAnswer = exercise.correct_answer;
  const explanation = exercise.explanation;
  const imagePath = exercise.image_path;

  const handleOptionClick = (letter) => {
    if (!showAnswer) {
      setSelectedAnswer(letter);
    }
  };

  const handleCheckAnswer = () => {
    setShowAnswer(true);
  };

  const isCorrect = selectedAnswer === correctAnswer;

  return (
    <Paper elevation={0} sx={{ p: 4, borderRadius: 2, bgcolor: 'white', border: 1, borderColor: 'divider' }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" gap={1} alignItems="center">
          <Chip label={`Exercise ${index + 1}`} color="secondary" size="small" />
          <Typography variant="caption" color="text.secondary">
            {exerciseId}
          </Typography>
        </Box>
        <Chip
          label={isGeneratedExercise ? "AI Generated" : "Textbook"}
          size="small"
          variant="outlined"
          sx={{ borderColor: '#8b5cf6', color: '#8b5cf6' }}
        />
      </Box>

      {/* Exercise Question */}
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 'medium', color: '#1e293b' }}>
        {exerciseText}
      </Typography>

      {/* Exercise Image */}
      {imagePath && (
        <Box sx={{ mb: 3, p: 2, border: 1, borderColor: 'divider', borderRadius: 1, bgcolor: '#f8fafc', display: 'inline-block' }}>
          <img
            src={`/exercise_images/${imagePath}`}
            alt="Exercise diagram"
            style={{ maxHeight: 250, maxWidth: '100%', borderRadius: 4 }}
          />
        </Box>
      )}

      {/* Multiple Choice Options */}
      {isGeneratedExercise && options && (Array.isArray(options) ? options.length > 0 : Object.keys(options).length > 0) && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { md: '1fr 1fr', xs: '1fr' }, gap: 2, mb: 4 }}>
          {/* Handle both array format [{text, is_correct}] and object format {A: text, B: text} */}
          {(Array.isArray(options)
            ? options.map((opt, idx) => ({ letter: String.fromCharCode(65 + idx), text: opt.text || opt, isCorrectOption: opt.is_correct }))
            : Object.entries(options).map(([letter, text]) => ({ letter, text, isCorrectOption: letter === correctAnswer }))
          ).map(({ letter, text, isCorrectOption }) => {
            const isSelected = selectedAnswer === letter;

            let borderColor = 'divider';
            let bgcolor = 'white';

            if (showAnswer) {
              if (isCorrectOption) {
                borderColor = '#22c55e';
                bgcolor = '#f0fdf4';
              } else if (isSelected && !isCorrectOption) {
                borderColor = '#ef4444';
                bgcolor = '#fef2f2';
              }
            } else if (isSelected) {
              borderColor = '#8b5cf6';
              bgcolor = '#faf5ff';
            }

            return (
              <Box
                key={letter}
                onClick={() => handleOptionClick(letter)}
                sx={{
                  p: 2,
                  border: 2,
                  borderColor,
                  bgcolor,
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  cursor: showAnswer ? 'default' : 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': showAnswer ? {} : { bgcolor: '#faf5ff', borderColor: '#8b5cf6' }
                }}
              >
                <Box sx={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  bgcolor: isSelected ? '#8b5cf6' : '#e2e8f0',
                  color: isSelected ? 'white' : '#64748b',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>
                  {letter}
                </Box>
                <Typography variant="body2">{text}</Typography>
                {showAnswer && isCorrectOption && (
                  <CheckCircle sx={{ ml: 'auto', color: '#22c55e' }} />
                )}
                {showAnswer && isSelected && !isCorrectOption && (
                  <Cancel sx={{ ml: 'auto', color: '#ef4444' }} />
                )}
              </Box>
            );
          })}
        </Box>
      )}

      {/* Check Answer / Show Answer Button */}
      <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 2 }}>
        {isGeneratedExercise ? (
          <>
            {!showAnswer && selectedAnswer && (
              <Button
                startIcon={<CheckCircle />}
                onClick={handleCheckAnswer}
                color="primary"
                variant="contained"
                sx={{ textTransform: 'none' }}
              >
                Check Answer
              </Button>
            )}
            {!showAnswer && !selectedAnswer && (
              <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                Select an option above
              </Typography>
            )}
          </>
        ) : (
          <Button
            startIcon={<Visibility />}
            onClick={() => setShowAnswer(!showAnswer)}
            sx={{ textTransform: 'none' }}
            variant="outlined"
          >
            {showAnswer ? 'Hide Hint' : 'Show Hint'}
          </Button>
        )}
      </Box>

      {/* Answer Explanation */}
      <Collapse in={showAnswer} sx={{ mt: 2 }}>
        <Alert
          severity={isCorrect ? "success" : "error"}
          icon={false}
          sx={{
            border: 1,
            borderColor: isCorrect ? 'success.light' : 'error.light',
            bgcolor: isCorrect ? '#f0fdf4' : '#fef2f2'
          }}
        >
          <Box display="flex" gap={2}>
            <Box sx={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              bgcolor: isCorrect ? 'success.main' : 'error.main',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '1.2rem',
              flexShrink: 0
            }}>
              {correctAnswer}
            </Box>
            <Box>
              <Typography variant="subtitle2" color={isCorrect ? 'success.dark' : 'error.dark'} fontWeight="bold" gutterBottom>
                {isCorrect ? 'Correct!' : 'Incorrect'}
              </Typography>
              <Typography variant="body2" color={isCorrect ? 'success.dark' : 'error.dark'}>
                {explanation || 'Review the content section for more details.'}
              </Typography>
            </Box>
          </Box>
        </Alert>
      </Collapse>
    </Paper>
  );
}

export default ExerciseArea;
