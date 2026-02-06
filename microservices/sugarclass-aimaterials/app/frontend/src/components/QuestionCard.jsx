import React, { useState } from 'react';
import { Box, Paper, Typography, Button, Chip, Collapse, Alert } from '@mui/material';
import { Visibility, BookmarkBorder } from '@mui/icons-material';

function QuestionCard({ question, index, total }) {
  const [showAnswer, setShowAnswer] = useState(false);

  // Reset answer visibility when question changes
  React.useEffect(() => {
    setShowAnswer(false);
  }, [question]);

  if (!question) return null;

  // Parse options from string format "A. option1\nB. option2\n..."
  const parseOptions = (optionsStr) => {
    if (!optionsStr || typeof optionsStr !== 'string') return null;
    const options = {};
    // Clean up HTML artifacts
    const cleanStr = optionsStr.replace(/<[^>]*>/g, '').trim();
    const lines = cleanStr.split('\n').filter(l => l.trim());
    lines.forEach(line => {
      const match = line.match(/^([A-D])[\.\)]\s*(.+)$/);
      if (match) {
        options[match[1]] = match[2].trim();
      }
    });
    return Object.keys(options).length > 0 ? options : null;
  };

  const options = parseOptions(question.options);
  const questionText = question.question_text || question.text || '';
  
  // Parse images - can be comma-separated list
  const imagePaths = (question.image_path || question.image || '').split(',').filter(p => p.trim());

  return (
    <Paper elevation={0} sx={{ p: 4, borderRadius: 2, bgcolor: 'white', border: 1, borderColor: 'divider' }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" gap={1} alignItems="center">
            <Chip label={`Q${index + 1}`} color="primary" size="small" />
            <Typography variant="caption" color="text.secondary">
                {question.year} {question.paper} • {question.source_file}
            </Typography>
        </Box>
        <BookmarkBorder color="action" sx={{ cursor: 'pointer' }} />
      </Box>

      {/* Question Text */}
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 'medium', color: '#1e293b' }}>
        {questionText}
      </Typography>

      {/* Images from Q&A past papers */}
      {imagePaths.length > 0 && (
          <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              {imagePaths.map((imgPath, idx) => (
                  <Box key={idx} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, bgcolor: '#f8fafc' }}>
                      <img 
                          src={`/qa_images/${imgPath.trim()}`} 
                          alt={`Question Diagram ${idx + 1}`} 
                          style={{ maxHeight: 250, maxWidth: '100%', borderRadius: 4 }} 
                      />
                  </Box>
              ))}
          </Box>
      )}

      {/* Options */}
      {options && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { md: '1fr 1fr', xs: '1fr' }, gap: 2, mb: 4 }}>
            {Object.entries(options).map(([key, val]) => (
                <Box 
                    key={key} 
                    sx={{ 
                        p: 2, 
                        border: 1, 
                        borderColor: 'divider', 
                        borderRadius: 1, 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 2,
                        cursor: 'pointer',
                        '&:hover': { bgcolor: '#f1f5f9' }
                    }}
                >
                    <Box sx={{ width: 24, height: 24, borderRadius: '50%', bgcolor: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 'bold', color: '#64748b' }}>
                        {key}
                    </Box>
                    <Typography variant="body2">{val}</Typography>
                </Box>
            ))}
        </Box>
      )}

      {/* Show Answer Button */}
      <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
        <Button 
            startIcon={<Visibility />} 
            onClick={() => setShowAnswer(!showAnswer)}
            sx={{ textTransform: 'none' }}
        >
            {showAnswer ? 'Hide Answer' : 'Show Answer'}
        </Button>

        <Collapse in={showAnswer} sx={{ mt: 2 }}>
            <Alert severity="success" icon={false} sx={{ border: 1, borderColor: 'success.light', bgcolor: '#f0fdf4' }}>
                <Box display="flex" gap={2}>
                    <Box sx={{ width: 40, height: 40, borderRadius: '50%', bgcolor: 'success.main', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1.2rem', flexShrink: 0 }}>
                        {question.answer}
                    </Box>
                    <Box>
                        <Typography variant="subtitle2" color="success.dark" fontWeight="bold" gutterBottom>Correct Answer</Typography>
                        <Typography variant="body2" color="success.dark">
                            {question.explanation}
                        </Typography>
                    </Box>
                </Box>
            </Alert>
        </Collapse>
      </Box>
    </Paper>
  );
}

export default QuestionCard;
