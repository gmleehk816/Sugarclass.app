import React from 'react';
import { Box, Typography, List, ListItemButton, ListItemText, Chip } from '@mui/material';
import { Layers, HelpOutline, CheckCircle, Pending, FitnessCenter } from '@mui/icons-material';

function SubtopicSidebar({ viewMode, selectedTopic, subtopics, selectedSubtopicId, onSelectSubtopic, exercises, currentExerciseIndex, onSelectExercise, questions, currentQuestionIndex, onSelectQuestion }) {

  if (subtopics.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
        <Typography variant="body2">Select a topic to see details</Typography>
      </Box>
    );
  }

  return (
    <>
      <Box sx={{ p: 2, bgcolor: '#f1f5f9', borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="subtitle1" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {viewMode === 'content' && <><Layers fontSize="small" /> Subtopics</>}
          {viewMode === 'exercise' && <><FitnessCenter fontSize="small" /> Exercises</>}
          {viewMode === 'qa' && <><HelpOutline fontSize="small" /> Exam Questions</>}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {viewMode === 'content' && `${subtopics.length} items`}
          {viewMode === 'exercise' && `${exercises?.length || 0} exercises`}
          {viewMode === 'qa' && `${questions.length} exam questions`}
        </Typography>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto' }}>
        {viewMode === 'content' && (
          <List disablePadding>
            {subtopics.map((sub) => (
              <ListItemButton
                key={sub.full_id || sub.id}
                selected={selectedSubtopicId === sub.full_id || selectedSubtopicId === sub.id}
                onClick={() => onSelectSubtopic(sub.full_id || sub.id)}
                disabled={!sub.has_content}
                sx={{
                  borderBottom: '1px solid #f1f5f9',
                  opacity: sub.has_content ? 1 : 0.6,
                  py: 2,
                  '&.Mui-selected': { bgcolor: '#f0f9ff', borderLeft: '3px solid #0ea5e9' },
                  '&:hover': { bgcolor: '#f8fafc' }
                }}
              >
                <ListItemText
                  disableTypography
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="subtitle2" fontWeight="bold" color={selectedSubtopicId === (sub.full_id || sub.id) ? 'primary.main' : 'text.primary'}>
                        {sub.name}
                      </Typography>
                      {sub.is_processed && (
                        <Chip
                          label="✓"
                          size="small"
                          color="success"
                          sx={{ height: 18, fontSize: '0.65rem', minWidth: 24 }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.2, mb: 1 }}>
                        {sub.name}
                      </Typography>
                      {sub.is_processed ? (
                        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#16a34a', fontWeight: 'medium' }}>
                          <CheckCircle sx={{ fontSize: 14 }} /> Processed
                        </Typography>
                      ) : sub.has_content ? (
                        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#f59e0b', fontWeight: 'medium' }}>
                          <Pending sx={{ fontSize: 14 }} /> Raw content
                        </Typography>
                      ) : (
                        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'text.disabled' }}>
                          <Pending sx={{ fontSize: 14 }} /> No content
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItemButton>
            ))}
          </List>
        )}

        {viewMode === 'exercise' && (
          <List disablePadding>
            {exercises && exercises.length > 0 && (
              <Box sx={{ p: 2, bgcolor: '#faf5ff', borderBottom: '1px solid #f3e8ff' }}>
                <Typography variant="caption" color="secondary.dark" fontWeight="bold">
                  ALL EXERCISES
                </Typography>
              </Box>
            )}
            {(exercises || []).map((ex, idx) => (
              <ListItemButton
                key={ex.id || idx}
                selected={currentExerciseIndex === idx}
                onClick={() => onSelectExercise(idx)}
                sx={{
                  borderBottom: '1px solid #f1f5f9',
                  py: 1.5,
                  '&.Mui-selected': { bgcolor: '#f3e8ff', borderLeft: '3px solid #8b5cf6' },
                  '&:hover': { bgcolor: '#faf5ff' }
                }}
              >
                <ListItemText
                  disableTypography
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle2" fontWeight="bold" color={currentExerciseIndex === idx ? 'secondary.dark' : 'text.primary'}>
                          Ex {idx + 1}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Layers fontSize="tiny" />
                          {subtopics.find(s => s.full_id === ex.subtopic_id || s.id === ex.subtopic_id)?.name || 'Unknown subtopic'}
                        </Typography>
                      </Box>
                      <Chip label="AI Generated" size="small" sx={{ height: 18, fontSize: '0.6rem', borderColor: '#8b5cf6', color: '#8b5cf6' }} variant="outlined" />
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary" sx={{
                      lineHeight: 1.3,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {ex.question_text || ''}
                    </Typography>
                  }
                />
              </ListItemButton>
            ))}
          </List>
        )}

        {viewMode === 'qa' && (
          <List disablePadding>
            {questions.map((q, idx) => (
              <ListItemButton
                key={q.id}
                selected={currentQuestionIndex === idx}
                onClick={() => onSelectQuestion(idx)}
                sx={{
                  borderBottom: '1px solid #f1f5f9',
                  py: 2,
                  '&.Mui-selected': { bgcolor: '#fef3c7', borderLeft: '3px solid #f59e0b' },
                  '&:hover': { bgcolor: '#fffbeb' }
                }}
              >
                <ListItemText
                  disableTypography
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="subtitle2" fontWeight="bold" color={currentQuestionIndex === idx ? 'warning.dark' : 'text.primary'}>
                        Q{idx + 1}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {q.year} {q.paper}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary" sx={{
                      lineHeight: 1.3,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {(q.question_text || q.text || '').slice(0, 100)}...
                    </Typography>
                  }
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </Box>
    </>
  );
}

export default SubtopicSidebar;
