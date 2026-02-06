import React, { useState, useEffect } from 'react';
import { Box, List, ListItemButton, ListItemText, Typography, ToggleButton, ToggleButtonGroup, FormControl, Select, MenuItem, Chip } from '@mui/material';
import { Circle, CheckCircle, School, MenuBook, FitnessCenter, Assignment } from '@mui/icons-material';
import axios from 'axios';

function ChapterSidebar({ selectedChapter, onSelectChapter, viewMode, onModeChange, onSubjectChange }) {
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const res = await axios.get('/api/db/subjects');
        setSubjects(res.data);

        if (res.data.length > 0) {
          const first = res.data[0];
          setSelectedSubject(first.id);
          if (onSubjectChange) onSubjectChange(first.id);
        }
      } catch (err) {
        console.error('Error loading subjects', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSubjects();
  }, []);

  useEffect(() => {
    const fetchChapters = async (subjectId) => {
      if (!subjectId) return;
      try {
        // Changed: Get topics (chapters) instead of all subtopics
        const res = await axios.get(`/api/db/subjects/${subjectId}/topics`);
        const topicList = res.data || [];
        
        // Convert topics to chapter format
        const chapters = topicList.map((t, index) => ({
          id: t.id,
          chapter_num: t.order_num !== undefined ? t.order_num : index + 1,
          title: t.name,
          type: t.type,
          subtopic_count: t.subtopic_count || 0,
          processed_count: t.processed_count || 0,
        })).sort((a, b) => (a.chapter_num || 0) - (b.chapter_num || 0));
        
        setChapters(chapters);

        if (!selectedChapter && chapters.length > 0) {
          handleChapterClick(chapters[0]);
        }
      } catch (err) {
        console.error('Error loading chapters', err);
      }
    };
    fetchChapters(selectedSubject);
  }, [selectedSubject, selectedChapter]);

  const handleSubjectChange = (e) => {
    const id = e.target.value;
    setSelectedSubject(id);
    if (onSubjectChange) onSubjectChange(id);
  };

  const handleChapterClick = (chapter) => {
    if (onSelectChapter) {
      onSelectChapter(chapter);
    }
  };

  const handleMode = (_event, newMode) => {
    if (newMode !== null && onModeChange) onModeChange(newMode);
  };

  // Get current subject name
  const currentSubjectName = subjects.find(s => s.id === selectedSubject)?.name || 'Select Subject';

  return (
    <>
      <Box sx={{ p: 2, bgcolor: '#0ea5e9', color: 'white' }}>
        <Typography variant="h6" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <School /> AI Tutor
        </Typography>
        <Typography variant="caption" sx={{ opacity: 0.9 }}>
          {currentSubjectName}
        </Typography>
      </Box>

      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>
          SUBJECT
        </Typography>
        <FormControl fullWidth size="small">
          <Select
            value={selectedSubject}
            onChange={handleSubjectChange}
            displayEmpty
            disabled={loading}
            sx={{ bgcolor: 'white', fontSize: '0.85rem' }}
          >
            {subjects.map((s) => (
              <MenuItem key={s.id} value={s.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  {s.subtopic_count > 0 ? (
                    <CheckCircle sx={{ fontSize: 16, color: '#22c55e' }} />
                  ) : (
                    <Circle sx={{ fontSize: 16, color: '#f59e0b' }} />
                  )}
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</span>
                  <Chip label={`${s.subtopic_count} topics`} size="small" sx={{ height: 20, fontSize: '0.65rem', bgcolor: '#e2e8f0' }} />
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={handleMode}
          fullWidth
          size="small"
          sx={{ '& .MuiToggleButton-root': { px: 1, py: 0.5, fontSize: '0.7rem', minWidth: 0 } }}
        >
          <ToggleButton value="content" sx={{ flex: 1 }}>
            <MenuBook sx={{ fontSize: 16, mr: 0.3 }} /> Content
          </ToggleButton>
          <ToggleButton value="exercise" sx={{ flex: 1 }}>
            <FitnessCenter sx={{ fontSize: 16, mr: 0.3 }} /> Exercise
          </ToggleButton>
          <ToggleButton value="qa" sx={{ flex: 1 }}>
            <Assignment sx={{ fontSize: 16, mr: 0.3 }} /> Exam
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto' }}>
        {loading ? (
          <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
            <Typography variant="body2">Loading chapters…</Typography>
          </Box>
        ) : chapters.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
            <Typography variant="body2">No chapters found</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {chapters.map((ch) => (
              <ListItemButton
                key={ch.id}
                selected={selectedChapter?.id === ch.id}
                onClick={() => handleChapterClick(ch)}
                sx={{
                  py: 1.5,
                  borderBottom: '1px solid #f1f5f9',
                  '&.Mui-selected': {
                    bgcolor: '#f0f9ff',
                    color: '#0ea5e9',
                    borderRight: '3px solid #0ea5e9',
                  },
                  '&:hover': { bgcolor: '#f8fafc' },
                }}
              >
                <ListItemText
                  primary={`${ch.chapter_num}. ${ch.title}`}
                  primaryTypographyProps={{ fontWeight: 'bold', fontSize: '0.85rem', lineHeight: 1.4 }}
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </Box>
    </>
  );
}

export default ChapterSidebar;