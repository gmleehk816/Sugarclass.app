"""
Enhanced NewsCollect Web Viewer - Grid layout with images and filters
Real-time updates via WebSocket
"""
from flask import Flask, jsonify, render_template_string, request
from flask_socketio import SocketIO, emit
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'realtimewriter-secret-key-2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# Enhanced HTML template with grid layout and filters
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NewsCollect - Article Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            margin: 0;
            padding: 0;
        }
        .app-container {
            display: grid;
            grid-template-columns: 280px 1fr 320px;
            min-height: 100vh;
            gap: 0;
        }
        
        /* LEFT SIDEBAR - Age + Categories */
        .left-sidebar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            overflow-y: auto;
        }
        .left-sidebar h1 {
            font-size: 1.5rem;
            margin: 0 0 30px 0;
            color: white;
        }
        
        /* RIGHT SIDEBAR - Statistics */
        .right-sidebar {
            background: white;
            border-left: 1px solid #e0e0e0;
            padding: 20px;
            overflow-y: auto;
        }
        .right-sidebar h2 {
            font-size: 1.2rem;
            margin: 0 0 20px 0;
            color: #333;
        }
        
        /* MAIN CONTENT - Articles */
        .main-content {
            background: #f5f7fa;
            padding: 20px;
            overflow-y: auto;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .subtitle { font-size: 1.1rem; opacity: 0.9; }
        section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2.5rem; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.9rem; opacity: 0.9; }
        
        .filters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            align-items: end;
            margin-bottom: 20px;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .filter-group label {
            font-weight: 500;
            color: #555;
            font-size: 0.9rem;
        }
        .filter-group select,
        .filter-group input {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 1rem;
        }
        .filter-group select:focus,
        .filter-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        /* Age Buttons - Compact for Sidebar */
        .age-buttons {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .age-btn {
            background: rgba(255,255,255,0.2);
            border: 2px solid transparent;
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: white;
            text-align: left;
        }
        
        .age-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateX(5px);
        }
        
        .age-btn.active {
            border-color: #ffd700;
            background: rgba(255,215,0,0.2);
            box-shadow: 0 4px 12px rgba(255,215,0,0.3);
        }
        
        .age-btn-all {
            background: rgba(17,153,142,0.3);
        }
        
        .age-emoji {
            font-size: 1.2rem;
            margin-bottom: 4px;
        }
        
        .age-label {
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .age-sublabel {
            font-size: 0.7rem;
            opacity: 0.85;
        }
        
        .age-info {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 8px;
            display: none;
            margin-top: 1rem;
        }
        
        .age-info.show {
            display: block;
        }
        
        .filter-hint {
            display: block;
            color: #666;
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }
        
        .articles-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        .article-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #fafafa;
        }
        .article-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        }
        .article-image {
            width: 100%;
            height: 180px;
            object-fit: cover;
            background: #e0e0e0;
        }
        .article-image-placeholder {
            width: 100%;
            height: 180px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 3rem;
        }
        .article-content { padding: 15px; }
        .article-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        .article-meta {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }
        .article-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .badge-source { background: #667eea; color: white; }
        .badge-date { background: #48bb78; color: white; }
        .badge-status { background: #ed8936; color: white; }
        .badge-status.full { background: #48bb78; }
        .badge-method { background: #a0aec0; color: white; }
        .article-description {
            color: #666;
            font-size: 0.9rem;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .article-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }
        .article-word-count {
            font-size: 0.8rem;
            color: #999;
        }
        .loading { text-align: center; padding: 40px; color: #999; font-size: 1.1rem; }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            overflow: auto;
        }
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border-radius: 12px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }
        .close-btn {
            font-size: 28px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
            background: none;
            border: none;
        }
        .close-btn:hover { color: #000; }
        .modal-body {
            line-height: 1.8;
            color: #333;
        }
        .modal-body img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 15px 0;
        }
        .modal-body p { margin-bottom: 12px; }
        .modal-body hr { margin: 20px 0; border: none; border-top: 1px solid #ddd; }
        
        /* Loading spinner animation */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    <!-- Socket.IO Client -->
    <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
</head>
<body>
    <div class="app-container">
        <!-- LEFT SIDEBAR -->
        <div class="left-sidebar">
            <h1>📰 NewsCollect</h1>
            
            <h3 style="margin: 0 0 15px 0; font-size: 1rem; opacity: 0.9;">🎓 Age Group</h3>
            <div class="age-buttons" style="display: flex; flex-wrap: wrap; gap: 6px; justify-content: space-between;">
                <button class="age-btn" onclick="selectAgeGroup('7-10')" style="padding: 5px 8px; font-size: 0.75rem; display: flex; align-items: center; gap: 4px; flex: 1; min-width: 48%;">
                    <span style="font-size: 1rem;">👶</span>
                    <span style="flex: 1; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">7-10</span>
                </button>
                <button class="age-btn" onclick="selectAgeGroup('11-13')" style="padding: 5px 8px; font-size: 0.75rem; display: flex; align-items: center; gap: 4px; flex: 1; min-width: 48%;">
                    <span style="font-size: 1rem;">🧒</span>
                    <span style="flex: 1; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">11-13</span>
                </button>
                <button class="age-btn" onclick="selectAgeGroup('14-16')" style="padding: 5px 8px; font-size: 0.75rem; display: flex; align-items: center; gap: 4px; flex: 1; min-width: 48%;">
                    <span style="font-size: 1rem;">👦</span>
                    <span style="flex: 1; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">14-16</span>
                </button>
                <button class="age-btn age-btn-all" onclick="selectAgeGroup('')" style="padding: 5px 8px; font-size: 0.75rem; display: flex; align-items: center; gap: 4px; flex: 1; min-width: 48%;">
                    <span style="font-size: 1rem;">🌍</span>
                    <span style="flex: 1; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">All</span>
                </button>
            </div>
            
            <div id="age-info" style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 6px; font-size: 0.85rem; display: none;"></div>
            
            <h3 style="margin: 30px 0 15px 0; font-size: 1rem; opacity: 0.9;">📑 Categories</h3>
            <div id="categories-list" style="display: flex; flex-direction: column; gap: 6px; max-height: 400px; overflow-y: auto;">
                <!-- Categories will be populated by JavaScript -->
            </div>
        </div>
        
        <!-- MAIN CONTENT -->
        <div class="main-content">
            <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h2 style="margin: 0; font-size: 1.3rem;">Articles</h2>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <select id="channel-filter" style="padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                            <option value="">All Sources</option>
                        </select>
                        <button class="btn btn-primary" onclick="loadArticles()" style="padding: 8px 16px;">🔄 Refresh</button>
                    </div>
                </div>
                <div style="color: #666; font-size: 0.9rem;">
                    Showing <span id="article-count" style="font-weight: 600;">0</span> articles
                </div>
            </div>
            
            <div class="articles-grid" id="articles">
                <div class="loading">Loading articles...</div>
            </div>
        </div>
        
        <!-- RIGHT SIDEBAR - STATISTICS -->
        <div class="right-sidebar">
            <h2>📊 Statistics</h2>
            <div style="margin-bottom: 10px; padding: 8px; background: #f0f0f0; border-radius: 6px; font-size: 0.85rem;">
                <span id="connection-status" style="font-weight: 600; color: #10b981;">🟢 Connected</span>
            </div>
            <div class="stats-grid" style="grid-template-columns: 1fr; gap: 15px;">
                <div class="stat-card">
                    <div class="stat-value" id="total-articles">-</div>
                    <div class="stat-label">Total Articles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="full-articles">-</div>
                    <div class="stat-label">Full Text</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="sources-count">-</div>
                    <div class="stat-label">Sources</div>
                </div>
            </div>
            
            <h2 style="margin-top: 30px;">🔧 Filters</h2>
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; font-size: 0.9rem; color: #555;">From:</label>
                    <input type="date" id="date-from" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-size: 0.9rem; color: #555;">To:</label>
                    <input type="date" id="date-to" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;">
                </div>
                <button class="btn btn-primary" onclick="applyFilters()" style="width: 100%;">Apply Filters</button>
            </div>
        </div>
    </div>
                    <label for="channel-filter">📺 Channel</label>
                    <select id="channel-filter">
                        <option value="">All Sources</option>
                    </select>
                    <small id="channel-count" class="filter-hint"></small>
                </div>
                <div class="filter-group">
                    <label for="date-from">From:</label>
                    <input type="date" id="date-from">
                </div>
                <div class="filter-group">
                    <label for="date-to">To:</label>
                    <input type="date" id="date-to">
                </div>
                <div class="filter-group">
                    <button class="btn btn-primary" onclick="applyFilters()">Apply Filters</button>
                </div>
            </div>
        </section>
        
        <section>
            <h2>📰 Articles</h2>
            <div class="articles-grid" id="articles">
                <div class="loading">Loading articles...</div>
            </div>
        </section>
    </div>
    
    <!-- Article Detail Modal -->
    <div class="modal" id="article-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modal-title">Article Details</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modal-body">
                <div class="loading">Loading...</div>
            </div>
        </div>
    </div>
    
    <script>
        let currentFilters = {};
        let selectedAge = '';
        let socket = null;
        let socketConnected = false;
        
        // INITIAL_DATA_PLACEHOLDER
        
        // Initialize Socket.IO connection (with fallback for Simple Browser)
        function initWebSocket() {
            try {
                if (typeof io !== 'undefined') {
                    socket = io('http://127.0.0.1:7000');
                    
                    socket.on('connect', () => {
                        console.log('WebSocket connected');
                        socketConnected = true;
                        const el = document.getElementById('connection-status');
                        if (el) {
                            el.textContent = 'Connected';
                            el.style.color = '#10b981';
                        }
                    });
                    
                    socket.on('disconnect', () => {
                        console.log('WebSocket disconnected');
                        socketConnected = false;
                        const el = document.getElementById('connection-status');
                        if (el) {
                            el.textContent = 'Disconnected';
                            el.style.color = '#ef4444';
                        }
                    });
                    
                    socket.on('categories_update', (data) => {
                        console.log('Categories updated:', data);
                        updateCategoryButtons(data.categories);
                    });
                    
                    socket.on('articles_update', (data) => {
                        console.log('Articles updated:', data.count, 'articles');
                        updateArticlesDisplay(data.articles);
                    });
                    
                    socket.on('database_update', (data) => {
                        console.log('Database updated:', data.type);
                        requestCategories();
                        loadArticles();
                    });
                    
                    socket.on('error', (data) => {
                        console.error('Socket error:', data.message);
                    });
                } else {
                    console.warn('Socket.IO not available, using HTTP fallback');
                    const el = document.getElementById('connection-status');
                    if (el) {
                        el.textContent = 'HTTP Mode';
                        el.style.color = '#f59e0b';
                    }
                }
            } catch (e) {
                console.warn('WebSocket init failed, using HTTP fallback:', e);
                const el = document.getElementById('connection-status');
                if (el) {
                    el.textContent = 'HTTP Mode';
                    el.style.color = '#f59e0b';
                }
            }
        }
        
        // Request categories via WebSocket or HTTP
        function requestCategories() {
            if (socket && socketConnected) {
                socket.emit('request_categories', { age_group: selectedAge });
            } else {
                // Fallback: populate via HTTP
                populateCategories();
            }
        }
        
        // Update category button counts from WebSocket data
        function updateCategoryButtons(categories) {
            const categoryDefs = [
                { name: 'general', displayName: 'General News', icon: '🌐' },
                { name: 'science', displayName: 'Science & Technology', icon: '🔬' },
                { name: 'health', displayName: 'Health & Medicine', icon: '🏥' },
                { name: 'arts', displayName: 'Arts & Culture', icon: '🎨' },
                { name: 'entertainment', displayName: 'Entertainment', icon: '🎬' },
                { name: 'sports', displayName: 'Sports', icon: '⚽' },
                { name: 'business', displayName: 'Business & Economics', icon: '💼' },
                { name: 'education', displayName: 'Education', icon: '📚' },
                { name: 'lifestyle', displayName: 'Lifestyle', icon: '✨' },
                { name: 'social', displayName: 'Social Issues', icon: '⚖️' },
                { name: 'history', displayName: 'History & Geography', icon: '🗺️' },
                { name: 'environment', displayName: 'Nature & Environment', icon: '🌿' }
            ];
            
            const container = document.getElementById('categories-list');
            container.innerHTML = '';
            
            categoryDefs.forEach(cat => {
                const count = categories[cat.name] || 0;
                const btn = document.createElement('button');
                btn.className = 'category-btn';
                btn.onclick = () => selectCategory(cat.name);
                btn.innerHTML = `
                    <span style="font-size: 1.1rem; margin-right: 6px;">${cat.icon}</span>
                    <span style="flex: 1; text-align: left; font-size: 0.8rem;">${cat.displayName}</span>
                    <span style="background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 10px; font-size: 0.7rem; font-weight: 600;">${count}</span>
                `;
                btn.style.cssText = `
                    display: flex;
                    align-items: center;
                    padding: 10px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-family: inherit;
                    width: 100%;
                `;
                btn.onmouseover = () => {
                    btn.style.background = 'rgba(255, 255, 255, 0.2)';
                    btn.style.transform = 'translateX(5px)';
                };
                btn.onmouseout = () => {
                    if (!btn.classList.contains('active')) {
                        btn.style.background = 'rgba(255, 255, 255, 0.1)';
                        btn.style.transform = 'translateX(0)';
                    }
                };
                container.appendChild(btn);
            });
        }
        
        // Age group to source mappings
        const ageSources = {
            '7-10': ['BBC Newsround', 'Time for Kids', 'Dogo News'],
            '11-13': ['NASA', 'NASA Space Station', 'Dogo News', 'CNN', 'BBC'],
            '14-16': ['Space.com', 'Live Science', 'Smithsonian', 'ScienceDaily', 'Phys.org', 'The Conversation', 'CNN', 'BBC'],
            '17+': ['MIT News', 'Stanford News', 'The Conversation', 'ScienceDaily', 'Phys.org', 'Ars Technica', 'Wired']
        };
        
        function selectAgeGroup(age) {
            selectedAge = age;
            currentFilters.age_group = age;
            
            // Update button active states
            document.querySelectorAll('.age-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.closest('.age-btn').classList.add('active');
            
            // Request updated category counts via WebSocket
            requestCategories();
            
            // Show age info
            const infoDiv = document.getElementById('age-info');
            if (age) {
                const sources = ageSources[age] || [];
                infoDiv.innerHTML = `<strong>📚 Recommended Sources:</strong> ${sources.join(', ')}`;
                infoDiv.classList.add('show');
                
                // Update channel filter to show only age-appropriate sources
                updateChannelFilter(sources);
                
                // Update source count hint
                const countHint = document.getElementById('channel-count');
                countHint.textContent = `${sources.length} sources available for this age group`;
            } else {
                infoDiv.classList.remove('show');
                loadChannels(); // Reset to all channels
                document.getElementById('channel-count').textContent = '';
            }
            
            // Auto-load articles
            loadArticles();
        }
        
        function updateChannelFilter(allowedSources) {
            const select = document.getElementById('channel-filter');
            select.innerHTML = '<option value="">All Recommended Sources</option>';
            allowedSources.forEach(source => {
                const option = document.createElement('option');
                option.value = source;
                option.textContent = source;
                select.appendChild(option);
            });
        }
        
        async function loadStats() {
            try {
                const resp = await fetch('/api/simple/stats');
                const data = await resp.json();
                document.getElementById('total-articles').textContent = data.total || 0;
                document.getElementById('full-articles').textContent = data.full || 0;
                document.getElementById('sources-count').textContent = data.sources || 0;
            } catch (e) {
                console.error('Failed to load stats:', e);
            }
        }
        
        async function populateCategories() {
            const categories = [
                { name: 'general', displayName: 'General News', icon: '🌐', color: '#3b82f6' },
                { name: 'science', displayName: 'Science & Technology', icon: '🔬', color: '#8b5cf6' },
                { name: 'health', displayName: 'Health & Medicine', icon: '🏥', color: '#ec4899' },
                { name: 'arts', displayName: 'Arts & Culture', icon: '🎨', color: '#f59e0b' },
                { name: 'entertainment', displayName: 'Entertainment', icon: '🎬', color: '#ef4444' },
                { name: 'sports', displayName: 'Sports', icon: '⚽', color: '#10b981' },
                { name: 'business', displayName: 'Business & Economics', icon: '💼', color: '#6366f1' },
                { name: 'education', displayName: 'Education', icon: '📚', color: '#14b8a6' },
                { name: 'lifestyle', displayName: 'Lifestyle', icon: '✨', color: '#f97316' },
                { name: 'social', displayName: 'Social Issues', icon: '⚖️', color: '#8b5cf6' },
                { name: 'history', displayName: 'History & Geography', icon: '🗺️', color: '#06b6d4' },
                { name: 'environment', displayName: 'Nature & Environment', icon: '🌿', color: '#22c55e' }
            ];
            
            // Fetch category counts (filtered by age_group if selected)
            let counts = {};
            try {
                const ageParam = selectedAge ? `?age_group=${selectedAge}` : '';
                const resp = await fetch(`/api/simple/categories${ageParam}`);
                const data = await resp.json();
                counts = data.categories || {};
            } catch (e) {
                console.error('Failed to load category counts:', e);
            }
            
            const container = document.getElementById('categories-list');
            container.innerHTML = '';
            
            categories.forEach(cat => {
                const count = counts[cat.name] || 0;
                const btn = document.createElement('button');
                btn.className = 'category-btn';
                btn.onclick = () => selectCategory(cat.name);
                btn.innerHTML = `
                    <span style="font-size: 1.1rem; margin-right: 6px;">${cat.icon}</span>
                    <span style="flex: 1; text-align: left; font-size: 0.8rem;">${cat.displayName}</span>
                    <span style="background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 10px; font-size: 0.7rem; font-weight: 600;">${count}</span>
                `;
                btn.style.cssText = `
                    display: flex;
                    align-items: center;
                    padding: 10px 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-family: inherit;
                    width: 100%;
                `;
                btn.onmouseover = () => {
                    btn.style.background = 'rgba(255, 255, 255, 0.2)';
                    btn.style.transform = 'translateX(5px)';
                };
                btn.onmouseout = () => {
                    if (!btn.classList.contains('active')) {
                        btn.style.background = 'rgba(255, 255, 255, 0.1)';
                        btn.style.transform = 'translateX(0)';
                    }
                };
                container.appendChild(btn);
            });
        }
        
        let selectedCategory = '';
        
        function selectCategory(category) {
            selectedCategory = selectedCategory === category ? '' : category;
            currentFilters.category = selectedCategory;
            
            // Update button active states
            document.querySelectorAll('.category-btn').forEach(btn => {
                const catName = btn.textContent.trim();
                if (catName === category && selectedCategory) {
                    btn.classList.add('active');
                    btn.style.background = 'rgba(255, 255, 255, 0.3)';
                    btn.style.fontWeight = '600';
                } else {
                    btn.classList.remove('active');
                    btn.style.background = 'rgba(255, 255, 255, 0.1)';
                    btn.style.fontWeight = 'normal';
                }
            });
            
            // Auto-load articles with category filter
            loadArticles();
        }
        
        async function loadChannels() {
            try {
                const resp = await fetch('/api/simple/sources');
                const data = await resp.json();
                const select = document.getElementById('channel-filter');
                select.innerHTML = '<option value="">All Channels</option>';
                data.sources.forEach(source => {
                    const option = document.createElement('option');
                    option.value = source;
                    option.textContent = source;
                    select.appendChild(option);
                });
            } catch (e) {
                console.error('Failed to load channels:', e);
            }
        }
        
        async function loadArticles() {
            console.log('[DEBUG] loadArticles called, socketConnected:', socketConnected);
            // Use WebSocket if connected, otherwise fall back to HTTP
            if (socket && socketConnected) {
                socket.emit('request_articles', {
                    age: currentFilters.age_group || '',
                    category: currentFilters.category || ''
                });
            } else {
                // Fallback to HTTP
                try {
                    console.log('[DEBUG] Using HTTP fallback for articles');
                    const params = new URLSearchParams(currentFilters);
                    const resp = await fetch(`/api/simple/articles?${params}`);
                    const data = await resp.json();
                    console.log('[DEBUG] Received', data.articles?.length || 0, 'articles');
                    updateArticlesDisplay(data.articles || []);
                } catch (e) {
                    console.error('Failed to load articles:', e);
                    document.getElementById('articles').innerHTML = '<div class="loading">Failed to load articles</div>';
                }
            }
        }
        
        function updateArticlesDisplay(articles) {
            const container = document.getElementById('articles');
            
            if (articles.length === 0) {
                container.innerHTML = '<div class="loading">No articles found</div>';
                document.getElementById('article-count').textContent = '0';
                return;
            }
            
            container.innerHTML = '';
            articles.forEach(article => {
                const card = createArticleCard(article);
                container.appendChild(card);
            });
            document.getElementById('article-count').textContent = articles.length;
        }
        
        function createArticleCard(article) {
            const card = document.createElement('div');
            card.className = 'article-card';
            card.onclick = () => showArticleDetail(article.id);
            
            const imageHtml = article.image_url 
                ? `<img src="${escapeHtml(article.image_url)}" alt="" class="article-image" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
                   <div class="article-image-placeholder" style="display:none;">📰</div>`
                : `<div class="article-image-placeholder">📰</div>`;
            
            const date = new Date(article.collected_at).toLocaleDateString();
            const preview = (article.description || article.full_text || '').substring(0, 150);
            const statusClass = article.has_full_article ? 'full' : '';
            const statusText = article.has_full_article ? 'Full' : 'Partial';
            
            card.innerHTML = `
                ${imageHtml}
                <div class="article-content">
                    <div class="article-title">${escapeHtml(article.title)}</div>
                    <div class="article-meta">
                        <span class="article-badge badge-source">${escapeHtml(article.source)}</span>
                        <span class="article-badge badge-date">${date}</span>
                        <span class="article-badge badge-status ${statusClass}">${statusText}</span>
                        ${article.extraction_method ? `<span class="article-badge badge-method">${escapeHtml(article.extraction_method)}</span>` : ''}
                    </div>
                    <div class="article-description">${escapeHtml(preview)}</div>
                    <div class="article-footer">
                        <span class="article-word-count">${article.word_count || 0} words</span>
                    </div>
                </div>
            `;
            
            return card;
        }
        
        async function showArticleDetail(articleId) {
            console.log(`[DEBUG] Opening article ${articleId}`);
            
            const modal = document.getElementById('article-modal');
            if (!modal) {
                console.error('[ERROR] Modal element not found!');
                alert('Error: Modal not found. Please refresh the page.');
                return;
            }
            
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scroll
            
            // Show loading state
            const modalBody = document.getElementById('modal-body');
            modalBody.innerHTML = '<div class="loading" style="text-align:center;padding:40px;"><div style="border:4px solid #f3f3f3;border-top:4px solid #667eea;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto 20px;"></div>Loading article...</div>';
            
            try {
                console.log(`[DEBUG] Fetching article ${articleId}...`);
                const resp = await fetch(`/api/simple/article/${articleId}`);
                
                if (!resp.ok) {
                    throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
                }
                
                const article = await resp.json();
                console.log('[DEBUG] Article loaded:', article.title);
                
                // Set title
                document.getElementById('modal-title').textContent = article.title || 'Article';
                
                // Build image HTML
                const imageHtml = article.image_url 
                    ? `<div class="article-image-container" style="width:100%;max-height:400px;overflow:hidden;border-radius:8px;margin-bottom:20px;">
                         <img src="${escapeHtml(article.image_url)}" 
                              alt="${escapeHtml(article.title || 'Article image')}"
                              style="width:100%;height:auto;object-fit:cover;"
                              onerror="this.parentElement.style.display='none';">
                       </div>`
                    : '';
                
                // Build metadata
                const formatDate = (dateStr) => {
                    if (!dateStr) return 'Unknown';
                    try {
                        return new Date(dateStr).toLocaleDateString('en-US', { 
                            year: 'numeric', month: 'long', day: 'numeric' 
                        });
                    } catch {
                        return dateStr;
                    }
                };
                
                const readingTime = article.word_count ? Math.ceil(article.word_count / 200) : '?';
                
                const metadata = `
                    <div class="article-metadata" style="background:#f8f9fa;padding:15px;border-radius:8px;margin-bottom:20px;">
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Source:</span>
                            <span style="color:#1f2937;">${escapeHtml(article.source || 'Unknown')}</span>
                        </div>
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Category:</span>
                            <span style="color:#1f2937;">${escapeHtml(article.category || 'General')}</span>
                        </div>
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Age Group:</span>
                            <span style="color:#1f2937;">${escapeHtml(article.age_group || 'All Ages')}</span>
                        </div>
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Published:</span>
                            <span style="color:#1f2937;">${formatDate(article.published_at)}</span>
                        </div>
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Reading Time:</span>
                            <span style="color:#1f2937;">${readingTime} min</span>
                        </div>
                        ${article.quality_score ? `
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Quality Score:</span>
                            <span style="color:#1f2937;">${Math.round(article.quality_score)}/100</span>
                        </div>
                        ` : ''}
                        ${article.word_count ? `
                        <div style="display:flex;margin-bottom:8px;">
                            <span style="font-weight:600;min-width:120px;color:#6b7280;">Word Count:</span>
                            <span style="color:#1f2937;">${article.word_count} words</span>
                        </div>
                        ` : ''}
                    </div>
                `;
                
                // Build content
                const fullText = article.full_text || article.description || 'No content available';
                const paragraphs = fullText
                    .split('\n\n')
                    .filter(p => p.trim().length > 0)
                    .map(p => `<p style="margin-bottom:16px;line-height:1.8;color:#374151;">${escapeHtml(p)}</p>`)
                    .join('');
                
                // Build external link
                const externalLink = article.url 
                    ? `<div class="article-actions" style="margin-top:20px;padding-top:20px;border-top:1px solid #e5e7eb;text-align:center;">
                         <a href="${escapeHtml(article.url)}" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            class="btn btn-primary"
                            style="display:inline-block;background:#667eea;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">
                            📖 Read Full Article on ${escapeHtml(article.source || 'Source')}
                         </a>
                       </div>`
                    : '';
                
                // Update modal content
                modalBody.innerHTML = `
                    ${imageHtml}
                    ${metadata}
                    <hr style="margin:20px 0;border:none;border-top:1px solid #ddd;">
                    <div class="article-content">
                        ${paragraphs}
                    </div>
                    ${externalLink}
                `;
                
                console.log('[DEBUG] Article rendered successfully');
                
            } catch (e) {
                console.error('[ERROR] Failed to load article:', e);
                modalBody.innerHTML = `
                    <div style="text-align:center;padding:40px;color:#dc2626;">
                        <h3 style="margin-bottom:10px;">Failed to Load Article</h3>
                        <p style="margin-bottom:20px;">${e.message}</p>
                        <button onclick="closeModal()" class="btn btn-secondary" style="background:#6b7280;color:white;padding:10px 20px;border:none;border-radius:6px;cursor:pointer;">
                            Close
                        </button>
                    </div>
                `;
            }
        }
        
        function closeModal() {
            const modal = document.getElementById('article-modal');
            if (modal) {
                modal.style.display = 'none';
                document.body.style.overflow = ''; // Restore scroll
            }
        }
        
        function applyFilters() {
            currentFilters = {};
            
            const channel = document.getElementById('channel-filter').value;
            const dateFrom = document.getElementById('date-from').value;
            const dateTo = document.getElementById('date-to').value;
            
            if (channel) currentFilters.source = channel;
            if (selectedAge) currentFilters.age_group = selectedAge;
            if (dateFrom) currentFilters.date_from = dateFrom;
            if (dateTo) currentFilters.date_to = dateTo;
            
            loadArticles();
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('article-modal');
            if (event.target == modal) {
                closeModal();
            }
        }
        
        // Initialize on page load
        console.log('[INIT] Starting NewsCollect...');
        
        // Use pre-loaded data if available (for Simple Browser compatibility)
        if (typeof INITIAL_ARTICLES !== 'undefined' && INITIAL_ARTICLES.length > 0) {
            console.log('[INIT] Using pre-loaded data:', INITIAL_ARTICLES.length, 'articles');
            updateArticlesDisplay(INITIAL_ARTICLES);
            
            if (typeof INITIAL_STATS !== 'undefined') {
                document.getElementById('total-articles').textContent = INITIAL_STATS.total || 0;
                document.getElementById('full-articles').textContent = INITIAL_STATS.full || 0;
                document.getElementById('sources-count').textContent = INITIAL_STATS.sources || 0;
            }
            
            const el = document.getElementById('connection-status');
            if (el) {
                el.textContent = 'Loaded';
                el.style.color = '#10b981';
            }
        } else {
            console.log('[INIT] No pre-loaded data, fetching from API...');
            try {
                initWebSocket();
            } catch(e) {
                console.warn('WebSocket init error:', e);
            }
            
            // Load data via API
            loadStats();
            loadArticles();
        }
        
        loadChannels();
        populateCategories();
        
        console.log('[INIT] NewsCollect initialization complete');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Pre-fetch articles to embed in page for Simple Browser compatibility
    import json
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, source, category, age_group, description, 
                       image_url, url, collected_at, 
                       CASE WHEN full_text IS NOT NULL AND full_text != '' THEN 1 ELSE 0 END as has_full,
                       COALESCE(word_count, 0) as word_count,
                       extraction_method
                FROM articles 
                ORDER BY collected_at DESC 
                LIMIT 100
            """)
            rows = cur.fetchall()
            articles = []
            for row in rows:
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'source': row[2],
                    'category': row[3],
                    'age_group': row[4],
                    'description': row[5] or '',
                    'image_url': row[6] or '',
                    'url': row[7] or '',
                    'collected_at': row[8] or '',
                    'has_full_article': bool(row[9]),
                    'word_count': row[10] or 0,
                    'extraction_method': row[11] or ''
                })
            
            # Get stats
            cur.execute("SELECT COUNT(*) FROM articles")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM articles WHERE full_text IS NOT NULL AND full_text != ''")
            full = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT source) FROM articles")
            sources = cur.fetchone()[0]
            
            stats = {'total': total, 'full': full, 'sources': sources}
    except Exception as e:
        articles = []
        stats = {'total': 0, 'full': 0, 'sources': 0}
        print(f"Error pre-fetching data: {e}")
    
    # Inject data into template
    template_with_data = TEMPLATE.replace(
        '// INITIAL_DATA_PLACEHOLDER',
        f'''
        // Pre-loaded data for Simple Browser compatibility
        const INITIAL_ARTICLES = {json.dumps(articles)};
        const INITIAL_STATS = {json.dumps(stats)};
        '''
    )
    return render_template_string(template_with_data)

@app.route('/api/simple/stats')
def api_stats():
    """Get simple statistics"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Total articles
            cur.execute("SELECT COUNT(*) FROM articles")
            total = cur.fetchone()[0]
            
            # Full text articles
            cur.execute("SELECT COUNT(*) FROM articles WHERE has_full_article = 1")
            full = cur.fetchone()[0]
            
            # Unique sources
            cur.execute("SELECT COUNT(DISTINCT source) FROM articles")
            sources = cur.fetchone()[0]
            
            return jsonify({
                'total': total,
                'full': full,
                'sources': sources
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simple/sources')
def api_sources():
    """Get list of sources"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT source FROM articles ORDER BY source")
            sources = [row[0] for row in cur.fetchall()]
            return jsonify({'sources': sources})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simple/categories')
def api_categories():
    """Get category counts, optionally filtered by age group"""
    try:
        age_group = request.args.get('age_group', '').strip()
        
        with get_db() as conn:
            cur = conn.cursor()
            
            if age_group:
                # Filter by age group
                cur.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM articles 
                    WHERE category IS NOT NULL AND category != ''
                      AND age_group = ?
                    GROUP BY category 
                    ORDER BY count DESC
                """, (age_group,))
            else:
                # All articles
                cur.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM articles 
                    WHERE category IS NOT NULL AND category != ''
                    GROUP BY category 
                    ORDER BY count DESC
                """)
            
            rows = cur.fetchall()
            categories = {}
            for row in rows:
                cat = row['category']
                count = row['count']
                categories[cat] = count
            return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simple/articles')
def api_articles():
    """Get articles with filtering"""
    try:
        source = request.args.get('source', '').strip()
        age_group = request.args.get('age_group', '').strip()
        category = request.args.get('category', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        limit = int(request.args.get('limit', '100'))
        
        with get_db() as conn:
            cur = conn.cursor()
            
            query = "SELECT * FROM articles WHERE 1=1"
            params = []
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if age_group:
                query += " AND age_group = ?"
                params.append(age_group)
            
            if category:
                query += " AND category LIKE ?"
                params.append(f'%{category}%')
            
            if date_from:
                query += " AND date(collected_at) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND date(collected_at) <= ?"
                params.append(date_to)
            
            query += " ORDER BY collected_at DESC LIMIT ?"
            params.append(limit)
            
            cur.execute(query, params)
            columns = [col[0] for col in cur.description]
            articles = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            return jsonify({'articles': articles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simple/article/<int:article_id>')
def api_article_detail(article_id):
    """Get single article details"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cur.fetchone()
            
            if not row:
                return jsonify({'error': 'Article not found'}), 404
            
            columns = [col[0] for col in cur.description]
            article = dict(zip(columns, row))
            
            return jsonify(article)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== WebSocket Events =====

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print('Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('Client disconnected')

@socketio.on('request_categories')
def handle_request_categories(data):
    """Get category counts with optional age filter"""
    age_group = data.get('age_group', '').strip() if data else ''
    
    try:
        with get_db() as db:
            if age_group:
                cursor = db.execute('''
                    SELECT category, COUNT(*) as count 
                    FROM articles 
                    WHERE age_group = ?
                    GROUP BY category 
                    ORDER BY category
                ''', (age_group,))
            else:
                cursor = db.execute('''
                    SELECT category, COUNT(*) as count 
                    FROM articles 
                    GROUP BY category 
                    ORDER BY category
                ''')
            
            rows = cursor.fetchall()
            categories = {row[0]: row[1] for row in rows}
            
            emit('categories_update', {
                'categories': categories,
                'age_group': age_group or 'all'
            })
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('request_articles')
def handle_request_articles(data):
    """Get articles with filters"""
    age = data.get('age', '') if data else ''
    category = data.get('category', '') if data else ''
    
    try:
        with get_db() as db:
            query = 'SELECT * FROM articles WHERE 1=1'
            params = []
            
            if age:
                query += ' AND age_group = ?'
                params.append(age)
            
            if category:
                query += ' AND category = ?'
                params.append(category)
            
            query += ' ORDER BY published_date DESC LIMIT 100'
            
            cursor = db.execute(query, params)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            
            articles = [dict(zip(columns, row)) for row in rows]
            
            emit('articles_update', {
                'articles': articles,
                'count': len(articles)
            })
    except Exception as e:
        emit('error', {'message': str(e)})

def broadcast_update(update_type='collection'):
    """Broadcast database update to all connected clients"""
    socketio.emit('database_update', {
        'type': update_type,
        'timestamp': str(os.times())
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=7000, debug=False)
