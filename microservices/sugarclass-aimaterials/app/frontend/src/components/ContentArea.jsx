import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, CircularProgress, Alert, Tabs, Tab, IconButton, Tooltip } from '@mui/material';
import { ArrowForward, AutoFixHigh } from '@mui/icons-material';
import axios from 'axios';

function ContentArea({ subtopicId, subjectId, contentMode, onContentModeChange }) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatingRewrite, setGeneratingRewrite] = useState(false);

  // All subjects now support raw/rewrite tabs
  // The API returns both raw and rewritten content for any subject
  const showTabs = true;

  useEffect(() => {
    const fetchContent = async () => {
      if (!subtopicId) return;

      setLoading(true);
      setError(null);
      try {
        // Use unified API endpoint that returns both raw and rewritten content
        const response = await axios.get(`/api/content/${subtopicId}/with-rewrite`);
        setContent(response.data);
      } catch (err) {
        console.error("Error fetching content:", err);
        setError("Content not found or server error.");
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [subtopicId, contentMode]);

  const handleTabChange = (event, newValue) => {
    if (onContentModeChange) {
      onContentModeChange(newValue);
    }
  };

  const handleGenerateRewrite = async () => {
    if (!subtopicId) return;

    setGeneratingRewrite(true);
    try {
      const response = await axios.post(`/api/rewrite/${subtopicId}`);
      alert('Rewrite generated successfully!');
      // Refetch content to show the rewrite
      const rewriteResponse = await axios.get(`/api/content/${subtopicId}/with-rewrite`);
      setContent(rewriteResponse.data);
    } catch (err) {
      console.error("Error generating rewrite:", err);
      alert(err.response?.data?.error || 'Failed to generate rewrite. Check API key.');
    } finally {
      setGeneratingRewrite(false);
    }
  };

  const convertMathScriptToDelimiters = (html) => {
    if (!html) return html;
    try {
      // display mode scripts
      html = html.replace(/<script[^>]*type=["']\s*math\/tex\s*;\s*mode=display["'][^>]*>([\s\S]*?)<\/script>/gi,
        (m, g1) => `<div class="math-display">\\[${g1.trim()}\\]</div>`);
      // inline scripts
      html = html.replace(/<script[^>]*type=["']\s*math\/tex["'][^>]*>([\s\S]*?)<\/script>/gi,
        (m, g1) => `<span class="math-inline">\\(${g1.trim()}\\)</span>`);
      return html;
    } catch (e) {
      console.error('convertMathScriptToDelimiters error', e);
      return html;
    }
  };

  useEffect(() => {
    if (content && content.html_content) {
      const timer = setTimeout(() => {
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise().catch(err => {
            console.error('MathJax rendering error:', err);
          });
        }
      }, 500);
      return () => clearTimeout(timer);
    }
    // Also render MathJax for engineering rewritten content
    if (content && content.rewrite?.html) {
      const timer = setTimeout(() => {
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise().catch(err => {
            console.error('MathJax rendering error:', err);
          });
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [content]);

  const sanitizeHtmlContent = (html) => {
    if (!html) return html;
    try {
      const withoutScripts = html.replace(/<script(?![^>]*type=["']math\/tex(?:;\\s*mode=display)?["'])[\s\S]*?<\/script>/gi, '');
      return withoutScripts.replace(/<style[\s\S]*?<\/style>/gi, '');
    } catch (e) {
      console.error('sanitizeHtmlContent error', e);
      return html;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!content) return null;

  return (
    <Box>
      {/* Header - Subtopic ID and Name */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'baseline', gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="h5" fontWeight="bold" sx={{ color: '#1e293b' }}>
          {content.subtopic_name || String(content.subtopic_id)?.split('_').pop() || subtopicId}
        </Typography>
        {content.rewrite?.has_rewrite && (
          <Tooltip title="AI-Enhanced Content Available">
            <AutoFixHigh sx={{ color: '#8b5cf6', fontSize: 20 }} />
          </Tooltip>
        )}
      </Box>

      {/* Tabs - Raw Content vs Rewritten Content (for all subjects) */}
      <Box sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Tabs value={contentMode} onChange={handleTabChange} aria-label="content rewrite tabs">
            <Tab label="Raw Content" value="raw" />
            <Tab label="Rewritten" value="rewrite" disabled={!content.rewrite?.has_rewrite} />
          </Tabs>

          {/* Generate Rewrite Button */}
          {contentMode === 'rewrite' && !content.rewrite?.has_rewrite && (
            <Tooltip title="Generate AI-Enhanced Version">
              <IconButton
                onClick={handleGenerateRewrite}
                disabled={generatingRewrite}
                sx={{ ml: 2, bgcolor: '#8b5cf6', color: 'white', '&:hover': { bgcolor: '#7c3aed' } }}
              >
                {generatingRewrite ? <CircularProgress size={24} sx={{ color: 'white' }} /> : <AutoFixHigh />}
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Content Card */}
      <Paper elevation={0} sx={{ p: 3, borderRadius: 1, bgcolor: 'white' }}>
        {/* Raw Content Tab */}
        {contentMode === 'raw' && (
          <>
            <Typography variant="h6" sx={{ color: '#334155', fontWeight: 600, mb: 2, pb: 1, borderBottom: '1px solid #e2e8f0' }}>
              {content.subtopic_name || content.title || 'Original Textbook Content'}
            </Typography>

            <Box
              sx={{
                bgcolor: '#ffffff',
                borderRadius: 1,
                maxHeight: '700px',
                overflow: 'auto',
                border: '1px solid #e2e8f0'
              }}
            >
              <div
                style={{
                  padding: '20px 40px',
                  fontFamily: 'Georgia, "Times New Roman", Times, serif',
                  lineHeight: 1.8,
                  color: '#1a1a1a',
                  fontSize: '16px'
                }}
                dangerouslySetInnerHTML={{ __html: sanitizeHtmlContent(content.raw_content?.html || '<p>No content available</p>') }}
              />
            </Box>
          </>
        )}

        {/* Rewritten Content Tab */}
        {contentMode === 'rewrite' && content.rewrite?.has_rewrite && (
          <>
            <Typography variant="h6" sx={{ color: '#334155', fontWeight: 600, mb: 2, pb: 1, borderBottom: '1px solid #e2e8f0' }}>
              AI-Enhanced Version
            </Typography>

            {/* Learning Objectives */}
            {content.rewrite.learning_objectives && (
              <Box sx={{ mb: 3, p: 2, bgcolor: '#eff6ff', borderRadius: 1, borderLeft: '4px solid #3b82f6' }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#1e40af', mb: 1 }}>
                  🎯 Learning Objectives
                </Typography>
                <Typography variant="body2" sx={{ color: '#1e3a8a', whiteSpace: 'pre-line' }}>
                  {content.rewrite.learning_objectives}
                </Typography>
              </Box>
            )}

            {/* Rewritten Content */}
            <div
              className="content-display"
              dangerouslySetInnerHTML={{ __html: sanitizeHtmlContent(content.rewrite.html || '') }}
            />

            {/* Key Takeaways */}
            {content.rewrite.key_takeaways && (
              <Box sx={{ mt: 3, p: 2, bgcolor: '#fef3c7', borderRadius: 1, borderLeft: '4px solid #f59e0b' }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#92400e', mb: 1 }}>
                  ✨ Key Takeaways
                </Typography>
                <Typography variant="body2" sx={{ color: '#78350f', whiteSpace: 'pre-line' }}>
                  {content.rewrite.key_takeaways}
                </Typography>
              </Box>
            )}

            <Typography variant="caption" sx={{ mt: 2, color: '#9ca3af', display: 'block' }}>
              Generated using {content.rewrite.model_used || 'AI'} • {content.rewrite.created_at}
            </Typography>
          </>
        )}

        {/* No Rewrite Available */}
        {contentMode === 'rewrite' && !content.rewrite?.has_rewrite && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <AutoFixHigh sx={{ fontSize: 48, color: '#d1d5db', mb: 2 }} />
            <Typography variant="h6" sx={{ color: '#9ca3af', mb: 1 }}>
              No Rewritten Content Available
            </Typography>
            <Typography variant="body2" sx={{ color: '#9ca3af', mb: 2 }}>
              Generate an AI-enhanced version of this content for better learning experience
            </Typography>
            <IconButton
              onClick={handleGenerateRewrite}
              disabled={generatingRewrite}
              sx={{ bgcolor: '#8b5cf6', color: 'white', '&:hover': { bgcolor: '#7c3aed' } }}
            >
              {generatingRewrite ? <CircularProgress size={24} sx={{ color: 'white' }} /> : <AutoFixHigh />}
            </IconButton>
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default ContentArea;