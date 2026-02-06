import React, { useState, useEffect } from 'react';
import { Box, List, ListItemButton, ListItemText, Typography, Divider, ToggleButton, ToggleButtonGroup, FormControl, Select, MenuItem, Chip } from '@mui/material';
import { MenuBook, Quiz, Folder, Circle, School, Science, CheckCircle, FitnessCenter, Assignment } from '@mui/icons-material';
import axios from 'axios';

function MainSidebar({ topics, selectedTopic, onSelectTopic, viewMode, onModeChange, onSubjectChange }) {
  // Syllabus & Subject state
  const [syllabuses, setSyllabuses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [selectedSyllabus, setSelectedSyllabus] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [loadingSyllabuses, setLoadingSyllabuses] = useState(true);

  // Load syllabuses and subjects from SQLite
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Get subjects directly from SQLite API
        const res = await axios.get('/api/db/subjects');
        const dbSubjects = res.data;
        
        // Group by syllabus
        const syllabusMap = {};
        dbSubjects.forEach(s => {
          const syllabusId = s.syllabus_id || 'cie_igcse';
          if (!syllabusMap[syllabusId]) {
            syllabusMap[syllabusId] = {
              id: syllabusId,
              name: 'CIE IGCSE',
              subjects: [],
              has_content: false
            };
          }
          syllabusMap[syllabusId].subjects.push({
            id: s.id,
            name: s.name,  // Already formatted as "Combined Science (0653)"
            code: s.code,
            syllabus_id: syllabusId,
            topic_count: s.topic_count,
            subtopic_count: s.subtopic_count,
            processed_count: s.processed_count
          });
          if (s.processed_count > 0) {
            syllabusMap[syllabusId].has_content = true;
          }
        });
        
        // Convert to arrays
        const syllabusArr = Object.values(syllabusMap).map(s => ({
          ...s,
          subject_count: s.subjects.length
        }));
        
        setSyllabuses(syllabusArr);
        
        // Auto-select first syllabus
        if (syllabusArr.length > 0) {
          setSelectedSyllabus(syllabusArr[0].id);
          setSubjects(syllabusArr[0].subjects);
          
          // Auto-select first subject with processed content
          const withProcessed = syllabusArr[0].subjects.find(s => s.processed_count > 0);
          const firstSubject = withProcessed || syllabusArr[0].subjects[0];
          if (firstSubject) {
            setSelectedSubject(firstSubject.id);
            // Notify parent about subject change
            if (onSubjectChange) {
              onSubjectChange(firstSubject.id);
            }
          }
        }
      } catch (err) {
        console.error('Error loading data:', err);
      } finally {
        setLoadingSyllabuses(false);
      }
    };
    fetchData();
  }, []);

  const handleSyllabusChange = (event) => {
    setSelectedSyllabus(event.target.value);
    setSelectedSubject('');
  };

  const handleSubjectChange = (event) => {
    const newSubject = event.target.value;
    setSelectedSubject(newSubject);
    
    // Notify parent about subject change - parent will load topics
    if (onSubjectChange) {
      onSubjectChange(newSubject);
    }
  };
  
  const handleMode = (event, newMode) => {
    if (newMode !== null) {
      onModeChange(newMode);
    }
  };

  return (
    <>
      {/* Header with App Name */}
      <Box sx={{ p: 2, bgcolor: '#0ea5e9', color: 'white' }}>
        <Typography variant="h6" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <School /> AI Tutor
        </Typography>
        <Typography variant="caption" sx={{ opacity: 0.9 }}>
          Knowledge Base
        </Typography>
      </Box>

      {/* Syllabus Selector */}
      <Box sx={{ p: 2, bgcolor: '#f1f5f9', borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>
          SYLLABUS
        </Typography>
        <FormControl fullWidth size="small">
          <Select
            value={selectedSyllabus}
            onChange={handleSyllabusChange}
            displayEmpty
            sx={{ bgcolor: 'white', fontSize: '0.85rem' }}
          >
            {syllabuses.map((s) => (
              <MenuItem key={s.id} value={s.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  {s.has_content && <CheckCircle sx={{ fontSize: 16, color: '#22c55e' }} />}
                  <span>{s.name}</span>
                  <Chip label={s.subject_count} size="small" sx={{ ml: 'auto', height: 20, fontSize: '0.7rem' }} />
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Subject Selector */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>
          SUBJECT
        </Typography>
        <FormControl fullWidth size="small">
          <Select
            value={selectedSubject}
            onChange={handleSubjectChange}
            displayEmpty
            disabled={!selectedSyllabus}
            sx={{ bgcolor: 'white', fontSize: '0.85rem' }}
          >
            {subjects.map((s) => (
              <MenuItem key={s.id} value={s.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  {s.processed_count > 0 ? (
                    <CheckCircle sx={{ fontSize: 16, color: '#22c55e' }} />
                  ) : (
                    <Circle sx={{ fontSize: 16, color: '#f59e0b' }} />
                  )}
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</span>
                  <Chip 
                    label={`${s.topic_count} topics`} 
                    size="small" 
                    sx={{ height: 20, fontSize: '0.65rem', bgcolor: '#e2e8f0' }} 
                  />
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
          aria-label="view mode"
          fullWidth
          size="small"
          sx={{ 
            '& .MuiToggleButton-root': { 
              px: 1, 
              py: 0.5,
              fontSize: '0.7rem',
              minWidth: 0
            }
          }}
        >
          <ToggleButton value="content" sx={{ flex: 1 }}>
            <MenuBook sx={{ fontSize: 16, mr: 0.3 }} />
            <span>Content</span>
          </ToggleButton>
          <ToggleButton value="exercise" sx={{ flex: 1 }}>
            <FitnessCenter sx={{ fontSize: 16, mr: 0.3 }} />
            <span>Exercise</span>
          </ToggleButton>
          <ToggleButton value="qa" sx={{ flex: 1 }}>
            <Assignment sx={{ fontSize: 16, mr: 0.3 }} />
            <span>Exam</span>
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto' }}>
        <List component="nav" disablePadding>
          {topics
            .sort((a, b) => {
              // Sort by order_num, then by id for consistent ordering
              if (a.order_num !== b.order_num) {
                return (a.order_num || 999) - (b.order_num || 999);
              }
              return a.id.localeCompare(b.id, undefined, { numeric: true });
            })
            .map((topic) => (
            <ListItemButton
              key={topic.id}
              selected={selectedTopic?.id === topic.id}
              onClick={() => onSelectTopic(topic)}
              sx={{ 
                py: 1.5,
                borderBottom: '1px solid #f1f5f9',
                '&.Mui-selected': { bgcolor: '#f0f9ff', color: '#0ea5e9', borderRight: '3px solid #0ea5e9' },
                '&:hover': { bgcolor: '#f8fafc' }
              }}
            >
               {/* Topic Code Badge */}
               <Box sx={{ 
                   minWidth: 32, 
                   height: 32, 
                   borderRadius: 1, 
                   bgcolor: selectedTopic?.id === topic.id ? '#0ea5e9' : '#e2e8f0', 
                   color: selectedTopic?.id === topic.id ? 'white' : '#64748b',
                   display: 'flex', 
                   alignItems: 'center', 
                   justifyContent: 'center',
                   fontSize: '0.8rem',
                   fontWeight: 'bold',
                   mr: 2
               }}>
                   {topic.id}
               </Box>

              <ListItemText 
                primary={topic.name}
                secondary={topic.type}
                primaryTypographyProps={{ fontWeight: 'bold', fontSize: '0.85rem', lineHeight: 1.2 }}
                secondaryTypographyProps={{ fontSize: '0.75rem', mt: 0.5 }}
              />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </>
  );
}

export default MainSidebar;
