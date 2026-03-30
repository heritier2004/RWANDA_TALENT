/**
 * Football Academy Management System
 * Main JavaScript File - Consolidated
 * Handles API calls, UI interactions, and role-based functionality across all dashboards
 */

/** Football Management System - main.js v1.1 */
console.log("Rwanda Talent - Premium JS v1.1 Loaded");

// API Base URL - automatically detect from current origin
const API_BASE = 'http://127.0.0.1:5000/api';

// Cache tracking for performance optimization
const dataCache = {
    timestamps: {},
    TTL: 30000 // 30 seconds cache TTL
};

// Current user data
let currentUser = null;

// ==========================================
// CORE UTILITIES & AUTHENTICATION
// ==========================================

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

/**
 * Safely sets the text content of an element by ID
 */
function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function showToast(message, type = 'info') {
    // Remove any existing toast
    const existing = document.getElementById('appToast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.id = 'appToast';
    toast.style.cssText = `
        position: fixed; top: 24px; right: 24px; z-index: 99999;
        padding: 16px 24px; border-radius: 12px; max-width: 420px;
        font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500;
        color: #FFFFFF; backdrop-filter: blur(16px);
        border: 1px solid rgba(0,240,255,0.3);
        background: ${type === 'error' ? 'rgba(11,15,25,0.95)' : 'rgba(0,240,255,0.15)'};
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        animation: fadeSlideUp 0.4s ease;
        cursor: pointer;
    `;
    const icon = type === 'error' ? '✖' : type === 'success' ? '✔' : 'ℹ';
    toast.innerHTML = `<span style="margin-right:10px; font-size:16px;">${icon}</span>${message}`;
    toast.onclick = () => toast.remove();
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 4500);
}

function copyToClipboard(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Link copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy link', 'error');
    });
}
window.copyToClipboard = copyToClipboard;

function getAuthHeaders() {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    if (!token) {
        return { 'Content-Type': 'application/json' };
    }
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

function checkAuth() {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    
    if (!token) {
        if (!window.location.href.includes('index.html') && !window.location.href.includes('login.html')) {
            window.location.href = 'index.html';
        }
        return false;
    }
    
    try {
        if (userStr) {
            currentUser = JSON.parse(userStr);
            const userNameEl = document.getElementById('userName');
            if (userNameEl) userNameEl.textContent = currentUser.username || currentUser.name || 'User';
            applyRoleAccess();
        }
        return true;
    } catch (e) {
        logout();
        return false;
    }
}

function applyRoleAccess() {
    if (!currentUser) return;
    const role = currentUser.role;
    document.querySelectorAll('.role-only').forEach(el => {
        const allowedRoles = el.dataset.roles ? el.dataset.roles.split(',') : [];
        if (allowedRoles.includes(role)) {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    });
}

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                ...getAuthHeaders(),
                ...options.headers
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                logout();
                throw new Error('Session expired. Please login again.');
            }
            let errorMessage = `HTTP ${response.status}: Request failed`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorData.message || errorMessage;
            } catch (e) {}
            throw new Error(errorMessage);
        }
        
        // Some endpoints (like DELETE) might not return JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
             return await response.json();
        }
        return null;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}


// ==========================================
// INITIALIZATION ROUTER
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const isPublicPage = window.location.href.includes('index.html') || window.location.href.includes('login.html');
    
    // Clean up camera if user closes/navigates away from page
    window.addEventListener('beforeunload', () => {
        if (_cameraStream) {
            _cameraStream.getTracks().forEach(t => t.stop());
        }
        if (window._cameraSessionId) {
            const token = localStorage.getItem('token') || localStorage.getItem('access_token');
            if (token) {
                navigator.sendBeacon?.(`${API_BASE}/live-stream/camera-stop`,
                    new Blob([JSON.stringify({ session_id: window._cameraSessionId })], { type: 'application/json' })
                );
            }
        }
    });
    
    // Only proceed with dashboard setup if we are on a protected page and authenticated
    if (!isPublicPage && checkAuth()) {
        
        initMobileMenu();
        
        // Auto-detect which dashboard we are on
        const path = window.location.pathname;
        
        if (path.includes('superadmin.html')) loadSuperAdminDashboard();
        else if (path.includes('ferwafa.html')) loadFERWAFADashboard();
        else if (path.includes('scout.html')) loadScoutDashboard();
        else if (path.includes('player.html')) loadPlayerProfile();
        else if (path.includes('match.html')) loadMatchPage();
        else if (path.includes('club.html')) loadClubDashboard();
        else if (path.includes('academy.html')) loadAcademyDashboard();
        else if (path.includes('school.html')) loadSchoolDashboard();
        else if (path.includes('dashboard.html')) loadDashboard();
        
        // Setup modals closing on outside click
        setupModals();
    }
});

function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }
}

function showSection(sectionId) {
    // Hide ALL sections — works across superadmin (.content-area) AND club/school/academy (main > section)
    document.querySelectorAll('.content-area .section, main .section, .main-content .section, section.section').forEach(el => {
        el.style.display = 'none';
        el.classList.remove('active');
    });

    // Show the target section
    const target = document.getElementById(sectionId);
    if (target) {
        target.style.display = 'block';
        setTimeout(() => target.classList.add('active'), 10);
        
        // Smart Data Loading with Caching
        loadSectionData(sectionId);
    }

    // Update Sidebar Active State
    document.querySelectorAll('.sidebar nav a, .sidebar-nav ul li').forEach(el => {
        el.classList.remove('active');
    });

    // Find the link that points to this section
    const activeLink = document.querySelector(`.sidebar nav a[onclick*="'${sectionId}'"]`);
    if (activeLink) {
        activeLink.classList.add('active');
        // If inside an li (premium layout), mark the li as active too
        const parentLi = activeLink.closest('li');
        if (parentLi) parentLi.classList.add('active');
    }
}
window.showSection = showSection;

async function loadSectionData(sectionId, force = false) {
    const now = Date.now();
    const lastLoad = dataCache.timestamps[sectionId] || 0;
    
    // Skip if loaded recently and not forced
    if (!force && lastLoad && (now - lastLoad < dataCache.TTL)) {
        console.log(`Cache Hit: ${sectionId} (Loaded ${Math.round((now-lastLoad)/1000)}s ago)`);
        return;
    }

    try {
        if (sectionId === 'clubs') await loadEntities('club', 'clubsTableBody');
        else if (sectionId === 'academies') await loadEntities('academy', 'academiesTableBody');
        else if (sectionId === 'schools') await loadEntities('school', 'schoolsTableBody');
        else if (sectionId === 'users') await loadUsers();
        else if (sectionId === 'players') await loadAllPlayers();
        else if (sectionId === 'matches') await loadNationalMatches();
        else if (sectionId === 'statistics') await loadTalentDiscovery();
        else if (sectionId === 'leagues') await loadLeagues();
        else if (sectionId === 'news') await loadNationalNews();
        else if (sectionId === 'system-logs') await loadSystemLogs();
        else if (sectionId === 'error-tracking') await loadErrorLogs();
        
        dataCache.timestamps[sectionId] = now;
    } catch (e) {
        console.error(`Load failed for ${sectionId}`, e);
    }
}
window.loadSectionData = loadSectionData;

// ==========================================
// SPECIFIC DASHBOARD LOADERS
// ==========================================

async function loadDashboard() {
    try {
        const overview = await apiRequest('/dashboard/overview');
        
        safeSetText('totalPlayers', overview?.total_players || 0);
        safeSetText('totalMatches', overview?.total_matches || 0);
        safeSetText('activeScouts', overview?.active_scouts || 0);
        safeSetText('totalUsers', overview?.total_users || 0);
        safeSetText('totalSchools', overview?.total_schools || 0);
        safeSetText('totalAcademies', overview?.total_academies || 0);
        safeSetText('totalClubs', overview?.total_clubs || 0);
        
        // Load detailed statistics for the Overview tab
        await loadDetailedStats();
        
        // Load recent matches and wrap them in clickable routes
        await loadRecentMatches();
        await loadNationalNews();
        
        // Initialize statistics tabs
        initStatsTabs();
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

/**
 * Loads comprehensive statistics for the Dashboard Overview tab
 */
async function loadDetailedStats() {
    try {
        const stats = await apiRequest('/stats/overview');
        
        // Update Overview tab cards
        // Note: some IDs might overlap with top summary cards, ensure unique targeting if needed
        const overviewTab = document.getElementById('tab-overview');
        if (overviewTab) {
            safeSetText('totalGoals', stats?.total_goals || 0);
            safeSetText('totalAssists', stats?.total_assists || 0);
            safeSetText('totalMinutes', stats?.total_minutes || 0);
            safeSetText('avgPerformance', stats?.avg_performance || 0);
        }
        
        // Also update any other global stats cards if they exist
        if (document.getElementById('dbSize')) {
            safeSetText('dbSize', (stats?.db_size || '0') + ' MB');
        }
    } catch (error) {
        console.error('Error loading detailed stats:', error);
    }
}

/**
 * Loads Top Players for the Statistics tab
 */
async function loadTopPlayers() {
    try {
        const scorers = await apiRequest('/stats/top-scorers?limit=10');
        const tbody = document.getElementById('topPlayersTableBody');
        
        if (!tbody) return;
        
        if (!scorers || scorers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No player data available</td></tr>';
            return;
        }
        
        tbody.innerHTML = scorers.map((p, index) => `
            <tr>
                <td><span class="rank-badge">${index + 1}</span></td>
                <td>
                    <div class="player-cell">
                        <img src="${p.photo_url || 'images/default-player.png'}" class="table-player-img small">
                        <span>${escapeHtml(p.name)}</span>
                    </div>
                </td>
                <td>${escapeHtml(p.position)}</td>
                <td><strong>${p.goals}</strong></td>
                <td>${p.total_assists || p.assists || 0}</td>
                <td>${p.matches_played || p.matches || 0}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="viewPlayerProfile(${p.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading top players:', error);
        const tbody = document.getElementById('topPlayersTableBody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="empty-state error">Failed to load rankings</td></tr>';
    }
}

/**
 * Loads AI Performance metrics for the Statistics tab
 */
async function loadAIPerformance() {
    try {
        const data = await apiRequest('/ai/top-players?limit=10');
        const tbody = document.getElementById('aiTopPlayersTableBody');
        
        if (!tbody) return;
        
        const players = data.top_players || [];
        
        if (players.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No AI metrics processed yet</td></tr>';
            return;
        }
        
        // Update summary cards in AI tab if they exist
        // Calculating averages from the top 10 for display
        const totalDist = players.reduce((sum, p) => sum + (p.avg_distance || 0), 0);
        const totalSpeed = players.reduce((sum, p) => sum + (p.avg_speed || 0), 0);
        const totalScore = players.reduce((sum, p) => sum + (p.avg_performance || 0), 0);
        const totalSprints = players.reduce((sum, p) => sum + (p.avg_sprints || 0), 0);
        
        safeSetText('avgDistance', (totalDist / players.length).toFixed(1));
        safeSetText('avgSpeed', (totalSpeed / players.length).toFixed(2));
        safeSetText('topPerformanceScore', (totalScore / players.length).toFixed(1));
        safeSetText('totalSprints', Math.round(totalSprints));
        
        tbody.innerHTML = players.map((p, index) => `
            <tr>
                <td><span class="rank-badge ai">${index + 1}</span></td>
                <td>${escapeHtml(p.name)}</td>
                <td>${(p.avg_distance || 0).toFixed(1)}m</td>
                <td>${(p.avg_speed || 0).toFixed(2)}m/s</td>
                <td>${Math.round(p.avg_sprints || 0)}</td>
                <td><span class="score-pill">${(p.avg_performance || 0).toFixed(1)}</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading AI performance:', error);
        const tbody = document.getElementById('aiTopPlayersTableBody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="empty-state error">AI Data Unavailable</td></tr>';
    }
}

/**
 * Initializes tab switching logic for the Statistics section
 */
function initStatsTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabBtns.length === 0) return;
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // Update button active state
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update content visibility
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `tab-${targetTab}`) {
                    content.classList.add('active');
                }
            });
            
            // Trigger data load based on tab
            if (targetTab === 'top-players') loadTopPlayers();
            else if (targetTab === 'ai-performance') loadAIPerformance();
            else if (targetTab === 'overview') loadDetailedStats();
        });
    });
}

async function loadClubDashboard() {
    await loadDashboard(); 
    loadStreams();
    loadTrainingJobs();
    if(document.getElementById('aiStatsPolling')) startAIStatsRefresh();
}

async function loadAcademyDashboard() {
    await loadDashboard();
}

async function loadSchoolDashboard() {
    await loadDashboard();
}

async function loadSuperAdminDashboard() {
    try {
        // Show loading state or refresh icons if needed
        const stats = await apiRequest('/stats/overview');
        safeSetText('totalUsers', stats?.users || 0);
        safeSetText('dbSize', (stats?.db_size || '12') + ' MB');
        
        // Load the shared dashboard metrics (Players, Schools, Matches etc)
        await loadDashboard();
        
    } catch(e) {
        console.error("Dashboard core load failed", e);
    }
}

/**
 * Dynamically loads Schools, Academies, or Clubs into the player registration dropdown
 */
async function loadEntitiesForSelect() {
    const type = document.getElementById('playerEntityType').value;
    const select = document.getElementById('playerEntityId');
    
    // Clear current options
    select.innerHTML = '<option value="">Loading list...</option>';
    
    try {
        let endpoint = '';
        if (type === 'school') endpoint = '/schools';
        else if (type === 'academy') endpoint = '/academies';
        else if (type === 'club') endpoint = '/clubs';
        
        const entities = await apiRequest(endpoint);
        
        select.innerHTML = '<option value="">Select ' + type + '...</option>';
        if (entities && Array.isArray(entities)) {
            entities.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.id;
                opt.textContent = item.name + (item.location ? ` (${item.location})` : '');
                select.appendChild(opt);
            });
        } else {
             select.innerHTML = '<option value="">No ' + type + 's found</option>';
        }
    } catch (error) {
        console.error('Error loading entities:', error);
        select.innerHTML = '<option value="">Error loading list</option>';
    }
}

async function loadFERWAFADashboard() {
    try {
        const stats = await apiRequest('/ferwafa/stats');
        safeSetText('totalClubs', stats?.clubs || 0);
        safeSetText('totalAcademies', stats?.academies || 0);
        safeSetText('totalSchools', stats?.schools || 0);
        safeSetText('totalPlayers', stats?.players || 0);
        
        // Load initial data for the active section (Players)
        loadAllPlayers();
        
        // Setup form listeners
        const leagueForm = document.getElementById('leagueForm');
        if (leagueForm) leagueForm.onsubmit = createLeague;
        
        const newsForm = document.getElementById('newsForm');
        if (newsForm) newsForm.onsubmit = publishNews;

    } catch (e) { console.error('Error loading ferwafa', e); }
}

// ==========================================
// LEAGUE MANAGEMENT (FERWAFA)
// ==========================================

function showCreateLeagueModal() {
    const modal = document.getElementById('leagueModal');
    if (modal) modal.style.display = 'flex';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}
window.closeModal = closeModal;

async function loadLeagues() {
    try {
        const leagues = await apiRequest('/leagues');
        const grid = document.getElementById('leaguesGrid');
        if (!grid) return;
        
        grid.innerHTML = leagues.map(l => `
            <div class="league-card">
                <div class="league-cat">${escapeHtml(l.category)}</div>
                <h3>${escapeHtml(l.name)}</h3>
                <p><strong>Season:</strong> ${escapeHtml(l.season)}</p>
                <p>${escapeHtml(l.description || 'No description provided.')}</p>
                <div class="card-actions" style="margin-top: 15px;">
                    <button class="btn btn-sm btn-secondary" onclick="editLeague(${l.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteLeague(${l.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (e) { console.error('Failed to load leagues', e); }
}

async function createLeague(e) {
    if (e) e.preventDefault();
    const data = {
        name: document.getElementById('leagueName').value,
        category: document.getElementById('leagueCategory').value,
        season: document.getElementById('leagueSeason').value,
        description: document.getElementById('leagueDescription').value
    };
    
    try {
        await apiRequest('/leagues', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showToast('League created successfully!', 'success');
        closeModal('leagueModal');
        loadLeagues();
    } catch (e) { showToast('Failed to create league', 'error'); }
}

// ==========================================
// NATIONAL NEWS (FERWAFA)
// ==========================================

function showCreateNewsModal() {
    const modal = document.getElementById('newsModal');
    if (modal) modal.style.display = 'flex';
}

async function loadNationalNews() {
    const role = currentUser?.role || 'all';
    try {
        const news = await apiRequest(`/announcements?role=${role}`);
        const list = document.getElementById('announcementsList');
        if (!list) return;
        
        list.innerHTML = news.map(n => `
            <div class="announcement-item">
                <div class="ann-meta">
                    ${formatDate(n.created_at)} by <strong>${escapeHtml(n.author || 'FERWAFA')}</strong>
                    <span class="ann-tag tag-${n.category.toLowerCase().replace(' ', '-')}">${n.category}</span>
                </div>
                <h4 style="margin: 5px 0;">${escapeHtml(n.title)}</h4>
                <p style="font-size: 0.9rem; color: #444;">${escapeHtml(n.content)}</p>
            </div>
        `).join('');
    } catch (e) { console.error('Failed to load news', e); }
}

async function publishNews(e) {
    if (e) e.preventDefault();
    const data = {
        title: document.getElementById('newsTitle').value,
        content: document.getElementById('newsContent').value,
        category: document.getElementById('newsCategory').value,
        target_role: document.getElementById('newsTarget').value
    };
    
    try {
        await apiRequest('/announcements', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showToast('Official announcement published!', 'success');
        closeModal('newsModal');
        loadNationalNews();
    } catch (e) { showToast('Failed to publish news', 'error'); }
}

// ==========================================
// TALENT DISCOVERY & MATCH TRACKER
// ==========================================

async function loadTalentDiscovery() {
    const position = document.getElementById('talentPosition').value;
    const ageMax = document.getElementById('talentAgeMax').value;
    
    try {
        const talents = await apiRequest(`/ferwafa/talent-discovery?position=${position}&age_max=${ageMax}`);
        const grid = document.getElementById('talentDiscoveryGrid');
        if (!grid) return;
        
        if (talents.length === 0) {
            grid.innerHTML = '<p class="empty-state">No players matching these criteria found.</p>';
            return;
        }
        
        grid.innerHTML = talents.map(t => `
            <div class="talent-card">
                <div class="talent-badge">#${Math.round(t.talent_score)}</div>
                <img src="${t.photo_url || 'images/default-player.png'}" style="width: 100%; height: 200px; object-fit: cover;">
                <div class="talent-info">
                    <div class="league-cat">${t.position} | Age: ${t.age}</div>
                    <h3 style="margin: 5px 0;">${escapeHtml(t.name)}</h3>
                    <p style="font-size: 0.8rem; color: #666;">${escapeHtml(t.entity_name)}</p>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; font-weight: bold;">
                        <span>Goals: ${t.total_goals}</span>
                        <span>Rating: ${parseFloat(t.avg_rating).toFixed(1)}</span>
                    </div>
                    <button class="btn btn-sm btn-primary" style="width: 100%; margin-top: 15px;" onclick="downloadPerformancePassport(${t.id})">
                        <i class="fas fa-file-pdf"></i> Download Passport
                    </button>
                </div>
            </div>
        `).join('');
    } catch (e) { console.error('Talent load failed', e); }
}

async function loadNationalMatches() {
    try {
        const matches = await apiRequest('/ferwafa/matches');
        const tbody = document.getElementById('nationalMatchesTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = matches.map(m => `
            <tr>
                <td>${formatDate(m.match_date).split(',')[0]}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>${escapeHtml(m.home_team)}</span>
                        <span>vs</span>
                        <span>${escapeHtml(m.away_team)}</span>
                    </div>
                </td>
                <td>${escapeHtml(m.venue_name || 'TBD')}</td>
                <td><strong>${m.home_score} - ${m.away_score}</strong></td>
                <td><span class="badge badge-primary">${m.status}</span></td>
            </tr>
        `).join('');
    } catch (e) { console.error('Match tracker load failed', e); }
}

async function downloadPerformancePassport(playerId) {
    try {
        const res = await apiRequest(`/ferwafa/player-report/${playerId}`);
        const p = res.player;
        const stats = res.recent_stats;
        
        // Simple printable summary (could be a PDF generator on server but this is instant)
        const win = window.open('', '_blank');
        win.document.write(`
            <html>
                <head>
                    <title>Player Passport - ${p.name}</title>
                    <style>
                        body { font-family: sans-serif; padding: 40px; }
                        header { border-bottom: 2px solid #1e3c72; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
                        .passport-card { border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th, td { border: 1px solid #eee; padding: 10px; text-align: left; }
                        .photo { width: 150px; height: 150px; background: #eee; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <header>
                        <h1>RWANDA FOOTBALL FEDERATION</h1>
                        <img src="images/logo.png" height="50">
                    </header>
                    <div class="passport-card">
                        <div style="display: flex; gap: 30px;">
                            <div class="photo"></div>
                            <div>
                                <h2>${p.name}</h2>
                                <p><strong>Reg Number:</strong> ${p.registration_number}</p>
                                <p><strong>Position:</strong> ${p.position}</p>
                                <p><strong>Age:</strong> ${p.age}</p>
                                <p><strong>Current Entity:</strong> ${p.entity_name}</p>
                            </div>
                        </div>
                        <h3>Recent Match Performance</h3>
                        <table>
                            <thead>
                                <tr><th>Date</th><th>Match</th><th>Goals</th><th>Assists</th><th>Rating</th></tr>
                            </thead>
                            <tbody>
                                ${stats.map(s => `<tr><td>${s.match_date}</td><td>${s.home_team} vs ${s.away_team}</td><td>${s.goals}</td><td>${s.assists}</td><td>${s.rating}</td></tr>`).join('')}
                            </tbody>
                        </table>
                        <p style="margin-top: 40px; font-size: 0.8rem; color: #888;">Report generated on ${res.generated_at} by Rwanda National Talent System.</p>
                    </div>
                    <script>window.print();</script>
                </body>
            </html>
        `);
        win.document.close();
    } catch (e) { console.error('Report failed', e); }
}

async function loadScoutDashboard() {
    loadTopPerformers();
    loadAllPlayers();
}

function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}


// ==========================================
// PLAYERS MANAGEMENT
// ==========================================

async function loadPlayers(endpoint = '/players') {
    try {
        const players = await apiRequest(endpoint);
        const container = document.getElementById('playersTableBody');
        if (!container) return;
        
        if (!players || players.length === 0) {
            container.innerHTML = '<tr><td colspan="7" class="empty-state">No players found</td></tr>';
            return;
        }
        
        container.innerHTML = players.map(player => `
            <tr>
                <td><div class="player-photo-cell">
                    <img src="${player.photo_url || 'images/default-player.png'}" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&background=1e3c72&color=fff'" class="table-player-img">
                    <code>${escapeHtml(player.registration_number || player.id)}</code>
                </div></td>
                <td>${escapeHtml(player.name)}</td>
                <td>${escapeHtml(player.position)}</td>
                <td>${player.jersey_number || '-'}</td>
                <td>${escapeHtml(player.nationality || 'Rwandan')}</td>
                <td>${player.dob ? new Date(player.dob).toLocaleDateString() : '-'}</td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editPlayer(${player.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deletePlayer(${player.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="btn btn-sm btn-info" onclick="viewPlayerProfile(${player.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading players:', error);
    }
}

async function loadAllPlayers() {
    // Specifically used by Scout and FERWAFA to see all entities' players
    loadPlayers('/players');
}

function searchPlayers() {
    const term = document.getElementById('playerSearch')?.value.toLowerCase();
    const posFilter = document.getElementById('filterPosition')?.value.toLowerCase();
    
    document.querySelectorAll('#playersTableBody tr, #allPlayersTableBody tr, #talentTableBody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        const matchesTerm = !term || text.includes(term);
        const matchesPos = !posFilter || text.includes(posFilter);
        
        if (matchesTerm && matchesPos) row.style.display = '';
        else row.style.display = 'none';
    });
}

function showAddPlayerModal() {
    safeSetText('playerModalTitle', 'Add New Player');
    const form = document.getElementById('playerForm');
    if (form) form.reset();
    const idField = document.getElementById('playerId');
    if (idField) idField.value = '';
    
    document.getElementById('playerModal')?.classList.add('active');
}

function closePlayerModal() {
    document.getElementById('playerModal')?.classList.remove('active');
}

async function uploadPlayerPhoto(file) {
    const formData = new FormData();
    formData.append('photo', file);
    
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/players/upload-photo`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Photo upload failed');
    }
    
    return await response.json();
}

async function editPlayer(playerId) {
    try {
        const player = await apiRequest(`/players/${playerId}`);
        showAddPlayerModal();
        safeSetText('playerModalTitle', 'Edit Player');
        
        const map = {
            'playerId': player.id,
            'playerName': player.name,
            'playerDob': player.dob ? player.dob.split('T')[0] : '',
            'playerNationality': player.nationality,
            'playerPosition': player.position,
            'playerJersey': player.jersey_number,
            'playerPhoto': player.photo_url,
            'playerHeight': player.height_cm,
            'playerWeight': player.weight_kg,
            'playerWeightKg': player.weight_kg,
            'playerDistrict': player.district,
            'playerSector': player.sector,
            'playerCell': player.cell,
            'playerVillage': player.village
        };
        
        for (const [id, val] of Object.entries(map)) {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null) el.value = val;
        }
    } catch (error) {
        console.error('Error loading player for edit:', error);
    }
}

async function savePlayer(e) {
    if(e) e.preventDefault();
    
    const playerId = document.getElementById('playerId')?.value;
    const isEditing = !!playerId;
    
    const photoFile = document.getElementById('playerPhotoFile')?.files[0];
    let photoUrl = document.getElementById('playerPhoto')?.value || null;

    try {
        // If a new file is selected, upload it first
        if (photoFile) {
            showToast('Uploading player photo...', 'info');
            const uploadRes = await uploadPlayerPhoto(photoFile);
            photoUrl = uploadRes.photo_url;
        }
        
        // Determine entity type and ID for new players
        let schoolId = null, academyId = null, clubId = null;
        const entityTypeEl = document.getElementById('playerEntityType');
        const entityIdEl = document.getElementById('playerEntityId');
        
        if (entityTypeEl && entityIdEl && !isEditing) {
            const entityType = entityTypeEl.value;
            const entityId = entityIdEl.value;
            
            if (!entityId) {
                showToast('Please select a valid ' + entityType, 'error');
                return;
            }
            
            if (entityType === 'school') schoolId = entityId;
            else if (entityType === 'academy') academyId = entityId;
            else if (entityType === 'club') clubId = entityId;
        }
        
        const data = {
            name: document.getElementById('playerName')?.value,
            dob: document.getElementById('playerDob')?.value,
            nationality: document.getElementById('playerNationality')?.value || 'Rwandan',
            position: document.getElementById('playerPosition')?.value,
            jersey_number: document.getElementById('playerJersey')?.value,
            photo_url: photoUrl,
            height_cm: document.getElementById('playerHeight')?.value,
            weight_kg: document.getElementById('playerWeight')?.value,
            district: document.getElementById('playerDistrict')?.value,
            sector: document.getElementById('playerSector')?.value,
            cell: document.getElementById('playerCell')?.value,
            village: document.getElementById('playerVillage')?.value,
            school_id: schoolId,
            academy_id: academyId,
            club_id: clubId
        };
        
        // Clean nulls
        Object.keys(data).forEach(k => data[k] == null && delete data[k]);
        
        const url = isEditing ? `/players/${playerId}` : '/players';
        const method = isEditing ? 'PUT' : 'POST';
        
        const responseData = await apiRequest(url, {
            method: method,
            body: JSON.stringify(data)
        });
        
        // Generate Shareable Link
        const generatedId = isEditing ? playerId : responseData.player_id;
        const profileLink = `${window.location.origin}/player.html?id=${generatedId}`;
        
        showToast(`Player ${isEditing ? 'updated' : 'registered'} successfully!`, 'success');
        closePlayerModal();
        
        // INSTANT SYNC: Refresh both list and dashboard counters
        loadPlayers();
        loadDashboard();
        if (typeof loadSuperAdminDashboard === 'function') loadSuperAdminDashboard();

    } catch (error) {
        console.error('Error saving player:', error);
        showToast('Failed to save player: ' + error.message, 'error');
    }
}

window.deletePlayer = async function(id) {
    if(!confirm('Delete this player?')) return;
    try {
        await apiRequest(`/players/${id}`, { method: 'DELETE' });
        loadPlayers();
    } catch(e) {}
}

function viewPlayerProfile(id) {
    window.location.href = `player.html?id=${id}`;
}


// ==========================================
// Player Profile Dashboard (player.html)
// ==========================================

async function loadPlayerProfile() {
    const urlParams = new URLSearchParams(window.location.search);
    let playerId = urlParams.get('id') || '1';
    
    const spinner = document.getElementById('loadingSpinner');
    const errorDiv = document.getElementById('errorMessage');
    const content = document.getElementById('playerContent');
    
    try {
        const data = await apiRequest(`/stats/player/${playerId}`);
        if(spinner) spinner.style.display = 'none';
        if(content) content.style.display = 'block';
        
        const player = data.player || {};
        safeSetText('playerName', player.name);
        safeSetText('playerReg', player.registration_number || 'N/A');
        safeSetText('playerNumber', player.jersey_number ? `#${player.jersey_number}` : 'N/A');
        safeSetText('playerPosition', player.position || 'N/A');
        safeSetText('playerNationality', player.nationality || 'N/A');
        safeSetText('playerDob', player.dob ? formatDate(player.dob).split(',')[0] : 'N/A');
        
        const stats = data.total_stats || {};
        safeSetText('totalGoals', stats.total_goals || 0);
        safeSetText('totalAssists', stats.total_assists || 0);
        safeSetText('totalMinutes', stats.total_minutes || 0);
        safeSetText('yellowCards', stats.yellow_cards || 0);
        safeSetText('redCards', stats.red_cards || 0);
        safeSetText('matchesPlayed', stats.total_matches || 0);
        
        const tbody = document.getElementById('matchHistoryBody');
        const matches = data.recent_matches || [];
        if(tbody) {
            if(matches.length === 0) tbody.innerHTML = '<tr><td colspan="8" class="text-center p-3">No history</td></tr>';
            else tbody.innerHTML = matches.map(m => `
                <tr>
                    <td>${formatDate(m.match_date).split(',')[0]}</td>
                    <td>${escapeHtml(m.home_team)}</td>
                    <td>${m.home_score !== null ? m.home_score + ' - ' + m.away_score : 'vs'}</td>
                    <td>${escapeHtml(m.away_team)}</td>
                    <td>${m.goals || 0}</td>
                    <td>${m.assists || 0}</td>
                    <td>${m.minutes_played || 0}</td>
                    <td>${m.yellow_cards ? m.yellow_cards + 'Y' : ''} ${m.red_cards ? m.red_cards + 'R' : ''}</td>
                </tr>
            `).join('');
        }
    } catch (e) {
        if(spinner) spinner.style.display = 'none';
        if(errorDiv) {
            errorDiv.style.display = 'block';
            safeSetText('errorText', 'Failed to load player profile');
        }
    }
}


// ==========================================
// MATCHES MANAGEMENT
// ==========================================

async function loadMatches() {
    try {
        const matches = await apiRequest('/matches');
        const tbody = document.getElementById('matchesTableBody');
        
        if (tbody && matches) {
            tbody.innerHTML = matches.map(m => `
                <tr onclick="window.location.href='match.html?id=${m.id}'" style="cursor: pointer; transition: all 0.3s;" class="clickable-row">
                    <td>${m.id}</td>
                    <td><div class="team-badge"></div> ${m.home_team_name}</td>
                    <td><div class="team-badge"></div> ${m.away_team_name}</td>
                    <td>${new Date(m.match_date).toLocaleDateString()}</td>
                    <td><strong>${m.home_score !== null ? m.home_score : '-'} : ${m.away_score !== null ? m.away_score : '-'}</strong></td>
                    <td><span class="badge ${m.status === 'Completed' ? 'badge-primary' : 'badge-secondary'}">${m.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); editMatch(${m.id})"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteMatch(${m.id})"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
            `).join('');
        }
    } catch(e) {}
}

function searchMatches() {
    const term = document.getElementById('matchSearch')?.value.toLowerCase();
    const statusFilter = document.getElementById('filterMatchStatus')?.value.toLowerCase();
    
    document.querySelectorAll('#matchesTableBody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        const matchesTerm = !term || text.includes(term);
        const matchesStatus = !statusFilter || text.includes(statusFilter);
        
        row.style.display = (matchesTerm && matchesStatus) ? '' : 'none';
    });
}

function showAddMatchModal() {
    safeSetText('matchModalTitle', 'Add New Match');
    const form = document.getElementById('matchForm');
    if (form) form.reset();
    const idField = document.getElementById('matchId');
    if (idField) idField.value = '';
    
    populateMatchDropdowns();
    document.getElementById('matchModal')?.classList.add('active');
}

function closeMatchModal() {
    document.getElementById('matchModal')?.classList.remove('active');
}

async function editMatch(id) {
    try {
        const match = await apiRequest(`/matches/${id}`);
        await populateMatchDropdowns();
        showAddMatchModal();
        safeSetText('matchModalTitle', 'Edit Match');
        
        const map = {
            'matchId': match.id,
            'matchDate': match.match_date ? match.match_date.slice(0, 16) : '',
            'matchOpponentId': match.away_team_id,
            'awayTeamId': match.away_team_id,
            'venueId': match.venue_id,
            'homeScore': match.home_score,
            'awayScore': match.away_score,
            'matchStatus': match.status
        };
        
        Object.keys(map).forEach(id => {
            const el = document.getElementById(id);
            if(el) el.value = map[id];
        });
    } catch(e) {}
}

async function saveMatch(e) {
    if(e) e.preventDefault();
    const id = document.getElementById('matchId')?.value;
    
    // Attempt to get IDs from select elements first (new standard)
    const homeTeamId = document.getElementById('homeTeamId')?.value || currentUser?.entity_id;
    const awayTeamId = document.getElementById('awayTeamId')?.value || document.getElementById('matchOpponentId')?.value;
    const venueId = document.getElementById('venueId')?.value;

    const data = {
        match_date: document.getElementById('matchDate')?.value,
        home_team_id: parseInt(homeTeamId),
        away_team_id: parseInt(awayTeamId),
        venue_id: parseInt(venueId),
        home_score: document.getElementById('homeScore')?.value ? parseInt(document.getElementById('homeScore').value) : 0,
        away_score: document.getElementById('awayScore')?.value ? parseInt(document.getElementById('awayScore').value) : 0,
        status: document.getElementById('matchStatus')?.value || 'scheduled',
        match_time: document.getElementById('matchTime')?.value || null
    };
    
    // Fallback for legacy text fields if IDs are missing (though we're phasing this out)
    if (!data.away_team_id) {
        data.opponent_name = document.getElementById('matchOpponent')?.value || document.getElementById('opponent')?.value;
    }
    
    try {
        await apiRequest(id ? `/matches/${id}` : '/matches', {
            method: id ? 'PUT' : 'POST',
            body: JSON.stringify(data)
        });
        showToast(`Match ${id ? 'updated' : 'synchronized'} successfully`, 'success');
        closeMatchModal();
        loadMatches();
    } catch(error) {
        showToast('Match Save Failed: ' + error.message, 'error');
    }
}

/**
 * Populates dropdowns for Match creation/edit
 * Fetches all possible teams and venues
 */
async function populateMatchDropdowns() {
    try {
        const [clubs, venues] = await Promise.all([
            apiRequest('/entities/clubs'),
            apiRequest('/entities/venues') // Assuming there is a venues endpoint, or fallback to stadiums
        ]);
        
        const opponentSelectors = document.querySelectorAll('#awayTeamId, #matchOpponentId, #opponentSelect');
        const venueSelectors = document.querySelectorAll('#venueId, #matchVenueId');
        
        const clubsList = clubs.clubs || clubs || [];
        const venuesList = venues.venues || venues || [];

        opponentSelectors.forEach(sel => {
            sel.innerHTML = '<option value="">Select Opponent...</option>' + 
                clubsList.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        });

        venueSelectors.forEach(sel => {
            sel.innerHTML = '<option value="">Select Venue...</option>' + 
                venuesList.map(v => `<option value="${v.id}">${v.name}</option>`).join('');
        });
    } catch(e) {
        console.warn('Failed to populate match dropdowns, using defaults', e);
    }
}
window.populateMatchDropdowns = populateMatchDropdowns;

window.deleteMatch = async function(id) {
    if(!confirm('Delete this match?')) return;
    try {
        await apiRequest(`/matches/${id}`, { method: 'DELETE' });
        loadMatches();
    } catch(e) {}
}

// ==========================================
// MATCH DAY SQUADS (match.html)
// ==========================================

let matchSquadState = { available: [], starting: [], bench: [], selectedIds: new Set() };

async function loadMatchPage() {
    loadPlayerStatsForMatch();
    const matchId = new URLSearchParams(window.location.search).get('id');
    if (matchId) {
        try {
            const data = await apiRequest(`/matches/${matchId}`);
            if (data) {
                const map = {
                    'matchDay': data.match_day, 'matchDate': data.match_date,
                    'matchTime': data.match_time, 'matchVenue': data.venue,
                    'opponentName': data.opponent || data.away_team_name
                };
                for(let k in map) {
                    if(document.getElementById(k)) document.getElementById(k).value = map[k] || '';
                }
            }
        } catch(e){}
    }
}

async function loadPlayerStatsForMatch() {
    try {
        const data = await apiRequest('/players');
        matchSquadState.available = data.players || data || [];
    } catch(e) {}
}

// Global scope bindings for match.html inline handlers
window.openPlayerSelector = () => {
    const list = document.getElementById('playerSelectorList');
    if(list) {
        list.innerHTML = matchSquadState.available.map(p => `
            <div class="player-item" data-id="${p.id}">
                <input type="checkbox" class="player-checkbox" value="${p.id}">
                <div class="jersey">${p.jersey_number || '?'}</div>
                <div class="player-details"><h4>${p.name}</h4><p>${p.position}</p></div>
            </div>
        `).join('');
        document.getElementById('playerSelectorModal').style.display = 'flex';
    }
}

window.closePlayerSelector = () => document.getElementById('playerSelectorModal').style.display = 'none';

window.addSelectedPlayers = () => {
    document.querySelectorAll('.player-checkbox:checked').forEach(cb => {
        const id = parseInt(cb.value);
        if(!matchSquadState.selectedIds.has(id)) {
            matchSquadState.selectedIds.add(id);
            const player = matchSquadState.available.find(p => p.id === id);
            if(matchSquadState.starting.length < 11) matchSquadState.starting.push(player);
            else matchSquadState.bench.push(player);
        }
    });
    renderMatchSquads();
    closePlayerSelector();
}

function renderMatchSquads() {
    const s = matchSquadState;
    const startCont = document.getElementById('startingPlayers');
    const benchCont = document.getElementById('benchPlayers');
    const availCont = document.getElementById('availablePlayers');
    
    if(startCont) {
        startCont.innerHTML = s.starting.length ? s.starting.map(p => squadTpl(p, 'toBench')).join('') : 'Empty';
    }
    if(benchCont) {
        benchCont.innerHTML = s.bench.length ? s.bench.map(p => squadTpl(p, 'toStart')).join('') : 'Empty';
    }
    
    safeSetText('startingCount', `${s.starting.length}/11 Selected`);
    safeSetText('benchCount', `${s.bench.length}/7 Selected`);
}

function squadTpl(player, action) {
    const btn = action === 'toBench' 
        ? `<button onclick="switchSquad(${player.id}, 'bench')"><i class="fas fa-arrow-down"></i></button>`
        : `<button onclick="switchSquad(${player.id}, 'start')"><i class="fas fa-arrow-up"></i></button><button onclick="removeSquad(${player.id})"><i class="fas fa-times"></i></button>`;
    return `<div class="player-item"><div class="jersey">${player.jersey_number||'?'}</div><div class="player-details"><h4>${player.name}</h4><p>${player.position}</p></div>${btn}</div>`;
}

window.switchSquad = (id, target) => {
    if(target === 'bench') {
        const idx = matchSquadState.starting.findIndex(p=>p.id===id);
        if(idx>-1) matchSquadState.bench.push(matchSquadState.starting.splice(idx,1)[0]);
    } else {
        const idx = matchSquadState.bench.findIndex(p=>p.id===id);
        if(idx>-1) matchSquadState.starting.push(matchSquadState.bench.splice(idx,1)[0]);
    }
    renderMatchSquads();
}
window.removeSquad = (id) => {
    const idx = matchSquadState.bench.findIndex(p=>p.id===id);
    if(idx>-1) {
        matchSquadState.bench.splice(idx,1);
        matchSquadState.selectedIds.delete(id);
    }
    renderMatchSquads();
}


// ==========================================
// ML & LIVE STREAMING
// ==========================================

async function loadStreams() {
    try {
        const resp = await apiRequest('/live-stream/list');
        const streams = resp?.streams || [];
        const list = document.getElementById('streamsList');
        const tbody = document.getElementById('streamsTableBody'); // superadmin
        if(list) {
             list.innerHTML = streams.length > 0 ? streams.map(s => `<div class="p-2 border">Stream ${s.id}</div>`).join('') : '<p>No active streams</p>';
        }
        if (tbody) {
            tbody.innerHTML = streams.length > 0 ? streams.map(s => `<tr><td>${s.id}</td><td>${s.match_id}</td><td>Ready</td><td>Active</td><td>Now</td><td>-</td></tr>`).join('') : '';
        }
    } catch(e){}
}

window.createStream = async function() {
    try {
        const data = await apiRequest('/live-stream/create', { method: 'POST', body: JSON.stringify({ team_id: currentUser?.entity_id || 1, stream_name: 'New Match Stream' }) });
        const info = document.getElementById('streamInfo');
        if (info) {
            info.style.display = 'block';
            document.getElementById('rtmpUrl').value = data.rtmp_url || 'rtmp://stream.rwandatalent.com/live';
            document.getElementById('streamKey').value = data.stream_key || 'XXXX-XXXX-XXXX-XXXX';
            document.getElementById('watchUrl').value = data.stream_url || 'https://rwandatalent.com/watch/' + (data.stream_id || 'demo');
        }
        showToast('Stream credentials generated', 'success');
        loadStreams();
    } catch (e) {}
}

window.startStream = () => { showToast('Stream is now live', 'success'); }
window.stopStream = () => { document.getElementById('streamInfo').style.display='none'; showToast('Stream ended', 'info'); }

// ==========================================
// ML TRAINING & AI ANALYTICS
// ==========================================

function openMLModal() {
    const modal = document.getElementById('mlModal');
    if (modal) modal.classList.add('active');
}
window.openMLModal = openMLModal;

function closeMLModal() {
    const modal = document.getElementById('mlModal');
    if (modal) modal.classList.remove('active');
}
window.closeMLModal = closeMLModal;

function toggleMLSourceInput() {
    const type = document.getElementById('mlVideoSourceType').value;
    const cont = document.getElementById('mlSourceContainer');
    if (type === 'upload') {
        cont.innerHTML = '<label>Upload File</label><input type="file" id="mlVideoFile" class="form-control" required>';
    } else {
        cont.innerHTML = `<label>${type === 'stream' ? 'RTMP Stream' : 'Video Link'}</label><input type="text" id="mlVideoSource" placeholder="https://..." required>`;
    }
}
window.toggleMLSourceInput = toggleMLSourceInput;

async function submitMLJob(event) {
    event.preventDefault();
    const type = document.getElementById('mlType').value;
    const sourceType = document.getElementById('mlVideoSourceType').value;
    const sourceEl = document.getElementById('mlVideoSource');
    const source = sourceEl ? sourceEl.value : 'File Upload';

    try {
        const resp = await apiRequest('/ml/train', {
            method: 'POST',
            body: JSON.stringify({ type, source, sourceType })
        });

        if (resp.success) {
            showToast('ML Training Job Queued', 'success');
            closeMLModal();
            loadTrainingJobs();
        }
    } catch (e) {
        showToast('Failed to start training', 'error');
    }
}
window.submitMLJob = submitMLJob;

async function loadTrainingJobs() {
    const cont = document.getElementById('trainingJobs');
    if (!cont) return;

    try {
        const jobs = await apiRequest('/ml/jobs');
        if (!jobs || jobs.length === 0) {
            cont.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-brain fa-3x" style="margin-bottom: 20px; opacity: 0.5;"></i>
                    <p>No active analytics jobs. Start your first analysis to see results.</p>
                </div>`;
            return;
        }

        cont.innerHTML = jobs.map(job => `
            <div class="card mb-3 bg-dark-soft">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h4 class="m-0" style="color: var(--primary); font-size: 16px;">
                            <i class="fas fa-robot"></i> ${job.type}
                        </h4>
                        <span class="badge ${job.status === 'Completed' ? 'bg-success' : 'bg-warning text-dark'}">
                            ${job.status}
                        </span>
                    </div>
                    <div class="job-meta mb-2" style="font-size: 13px; color: var(--text-muted);">
                        <span><i class="fas fa-id-card"></i> ID: #${job.id}</span>
                        <span class="ms-3"><i class="fas fa-clock"></i> Started: ${job.created_at}</span>
                    </div>
                    <div class="progress mb-2" style="height: 6px; background: rgba(255,255,255,0.1);">
                        <div class="progress-bar ${job.status === 'Completed' ? 'bg-success' : 'bg-primary'}" 
                             style="width: ${job.progress}%"></div>
                    </div>
                    <div class="job-links" style="font-size: 12px; display: flex; gap: 15px;">
                        <a href="${job.upload_endpoint}" target="_blank" style="color: var(--accent);"><i class="fas fa-upload"></i> Upload Endpoint</a>
                        <a href="#" onclick="copyToClipboard('${job.stream_ingest}')" style="color: var(--text-secondary);"><i class="fas fa-copy"></i> Copy RTMP Ingest</a>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {}
}
window.loadTrainingJobs = loadTrainingJobs;


// ==========================================
// TOP PERFORMERS / LEADERBOARDS
// ==========================================

async function loadTopPerformers() {
    try {
        const tops = await apiRequest('/stats/top-scorers?limit=5');
        const tS = document.getElementById('topScorers');
        if (tS && tops) tS.innerHTML = tops.map(p => `<div>${p.name} - ${p.goals} Goals</div>`).join('');
        
        // Similarly for assists if API supports
    } catch(e){}
}

// ==========================================
// USER & ENTITY MANAGEMENT (Superadmin)
// ==========================================

function openUserModal() {
    const form = document.getElementById('userForm');
    if (form) form.reset();
    
    const idEl = document.getElementById('newUserId');
    if (idEl) idEl.value = '';
    
    const pwField = document.getElementById('newPassword');
    if (pwField) {
        pwField.placeholder = "";
        pwField.required = true;
    }
    
    safeSetText('userModalTitle', 'Generate System Account');
    document.getElementById('userModal')?.classList.add('active');
}

function closeUserModal() {
    document.getElementById('userModal')?.classList.remove('active');
}

// Expose to global scope so HTML onclick can find them
window.closeUserModal = closeUserModal;
window.showAddUserModal = openUserModal;

async function loadEntities(type, tbodyId) {
    try {
        const data = await apiRequest(`/entities/${type}s`);
        const entities = data[type + 's'] || data; // handle typical wrapped pagination responses
        const tbody = document.getElementById(tbodyId);
        if (tbody && entities) {
            tbody.innerHTML = entities.map(e => `
                <tr>
                    <td>${e.id}</td>
                    <td><div class="team-badge"></div> ${e.name}</td>
                    <td>${e.director || e.contact_person || '-'}</td>
                    <td>${e.phone || '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editEntity('${type}', ${e.id})"><i class="fas fa-edit"></i></button>
                    </td>
                </tr>
            `).join('');
        }
    } catch(err) {
        console.error(`Failed to load ${type} lists`, err);
    }
}

async function loadUsers() {
    try {
        const data = await apiRequest('/auth/users');
        const usersList = data.users || data; // Fallback if pagination is returned
        const tbody = document.getElementById('userTable') || document.getElementById('usersTableBody');
        if(tbody && usersList) {
            tbody.innerHTML = usersList.map(u => `
                <tr>
                    <td>${u.id}</td>
                    <td>${u.username}</td>
                    <td>${u.email}</td>
                    <td><span class="badge badge-primary">${u.role}</span></td>
                    <td>${u.entity_id || '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editUser(${u.id})"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id})"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
            `).join('');
        }
    } catch(e) {
        console.error("Failed to load users", e);
    }
}

// ==========================================
// UNIFIED ENTITY MANAGEMENT
// ==========================================

window.showAddEntityModal = (type) => {
    document.getElementById('entityForm')?.reset();
    document.getElementById('entityId').value = '';
    document.getElementById('entityType').value = type;
    
    const titleMap = {
        'club': 'Register New Club',
        'academy': 'Register New Academy',
        'school': 'Register New School',
        'scout': 'Register New Scout'
    };
    
    document.getElementById('entityModalTitle').textContent = titleMap[type] || 'Register Entity';
    
    // Tweak form based on type
    const shortNameGroup = document.getElementById('entityShortNameGroup');
    if(shortNameGroup) shortNameGroup.style.display = (type === 'club') ? 'block' : 'none';
    
    document.getElementById('entityModal')?.classList.add('active');
};

window.closeEntityModal = () => {
    document.getElementById('entityModal')?.classList.remove('active');
};

async function saveEntity(e) {
    if(e) e.preventDefault();
    
    const type = document.getElementById('entityType').value;
    const id = document.getElementById('entityId').value;
    const isEditing = !!id;
    
    const data = {
        name: document.getElementById('entityName')?.value,
        email: document.getElementById('entityEmail')?.value,
        address: document.getElementById('entityLocation')?.value || document.getElementById('entityAddress')?.value,
        phone: document.getElementById('entityPhone')?.value,
        // Entity specific fields
        stadium_name: document.getElementById('entityStadium')?.value,
        founded_year: document.getElementById('entityFounded')?.value,
        director_name: document.getElementById('entityDirector')?.value,
        established_year: document.getElementById('entityEstablished')?.value
    };
    
    if (type === 'club') {
        data.short_name = document.getElementById('entityShortName')?.value;
    }

    // Clean nulls and empty strings
    Object.keys(data).forEach(k => (data[k] == null || data[k] === '') && delete data[k]);
    
    try {
        const url = isEditing ? `/entities/${type}s/${id}` : `/entities/${type}s`;
        const method = isEditing ? 'PUT' : 'POST';
        
        await apiRequest(url, {
            method: method,
            body: JSON.stringify(data)
        });
        
        showToast(`Success! The ${type} has been securely synchronized with the database.`, 'success');
        closeEntityModal();
        
        // Refresh specific tables dynamically
        if(type === 'club') loadEntities('club', 'clubsTableBody');
        if(type === 'school') loadEntities('school', 'schoolsTableBody');
        if(type === 'academy') loadEntities('academy', 'academiesTableBody');

    } catch (error) {
        showToast('Database Sync Error: ' + error.message, 'error');
    }
}

// User Creation — Admin sets username, email, password, and role
async function editUser(userId) {
    try {
        const data = await apiRequest('/auth/users');
        const users = data.users || data;
        const user = users.find(u => u.id === userId);
        
        if (!user) throw new Error('User not found');
        
        openUserModal();
        safeSetText('userModalTitle', 'Edit System Account');
        
        const map = {
            'newUserId': user.id,
            'newUsername': user.username,
            'newEmail': user.email,
            'newRole': user.role,
            'newEntityId': user.entity_id
        };
        
        for (const [id, val] of Object.entries(map)) {
            const el = document.getElementById(id);
            if (el) el.value = val !== null ? val : '';
        }

        // Hide password field for edits (optional)
        const pwField = document.getElementById('newPassword');
        if (pwField) {
            pwField.placeholder = "Leave blank to keep current password";
            pwField.required = false;
        }

    } catch (error) {
        showToast('Error loading user: ' + error.message, 'error');
    }
}

async function saveUser(e) {
    if (e) e.preventDefault();
    
    const userId = document.getElementById('newUserId')?.value;
    const isEditing = !!userId;
    
    const username = document.getElementById('newUsername')?.value?.trim();
    const email = document.getElementById('newEmail')?.value?.trim();
    const password = document.getElementById('newPassword')?.value;
    const role = document.getElementById('newRole')?.value;
    const entityId = document.getElementById('newEntityId')?.value || null;

    // Validate required fields before sending
    if (!username || !email || (!isEditing && !password) || !role) {
        showToast('Please fill in ALL required fields: Username, Email, Password, and Role.', 'error');
        return;
    }

    if (password && password.length < 6) {
        showToast('Password must be at least 6 characters long.', 'error');
        return;
    }

    const data = {
        username,
        email,
        role,
        entity_id: entityId === '' ? null : entityId
    };
    
    if (password && password.trim() !== '') {
        data.password = password;
    }

    try {
        const url = isEditing ? `/auth/users/${userId}` : '/auth/register';
        const method = isEditing ? 'PUT' : 'POST';
        
        await apiRequest(url, {
            method: method,
            body: JSON.stringify(data)
        });
        
        showToast(`Account ${isEditing ? 'updated' : 'generated'} successfully!`, 'success');
        closeUserModal();
        loadUsers();
    } catch (error) {
        showToast('Account Fault: ' + error.message, 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to permanently delete this account?')) return;
    
    try {
        await apiRequest(`/auth/users/${userId}`, { method: 'DELETE' });
        showToast('Account removed from system', 'success');
        loadUsers();
    } catch (error) {
        showToast('Deletion failed: ' + error.message, 'error');
    }
}

// ==========================================
// MISSING FUNCTION STUBS
// ==========================================

async function editLeague(id) {
    try {
        const leagues = await apiRequest('/leagues');
        const league = leagues.find(l => l.id === id);
        if (!league) { showToast('League not found', 'error'); return; }
        
        document.getElementById('leagueName').value = league.name || '';
        document.getElementById('leagueCategory').value = league.category || '';
        document.getElementById('leagueSeason').value = league.season || '';
        document.getElementById('leagueDescription').value = league.description || '';
        
        showCreateLeagueModal();
        safeSetText('leagueModalTitle', 'Edit League');
    } catch (e) { showToast('Error loading league', 'error'); }
}

async function deleteLeague(id) {
    if (!confirm('Delete this league?')) return;
    try {
        await apiRequest(`/leagues/${id}`, { method: 'DELETE' });
        showToast('League deleted', 'success');
        loadLeagues();
    } catch (e) { showToast('Failed to delete league', 'error'); }
}

async function editEntity(type, id) {
    try {
        const data = await apiRequest(`/entities/${type}s`);
        const entities = data[type + 's'] || data;
        const entity = entities.find(e => e.id === id);
        if (!entity) { showToast('Entity not found', 'error'); return; }
        
        document.getElementById('entityName').value = entity.name || '';
        document.getElementById('entityEmail').value = entity.email || '';
        document.getElementById('entityPhone').value = entity.phone || '';
        document.getElementById('entityLocation').value = entity.address || '';
        document.getElementById('entityId').value = entity.id;
        document.getElementById('entityType').value = type;
        
        showAddEntityModal(type);
        safeSetText('entityModalTitle', 'Edit ' + type.charAt(0).toUpperCase() + type.slice(1));
    } catch (e) { showToast('Error loading entity', 'error'); }
}

function viewErrorDetails(id) {
    showToast('Error details view - ID: ' + id, 'info');
}

function filterMatches() {
    searchMatches();
}

function loadTalentDiscoveryStats() {
    const position = document.getElementById('talentPositionStats')?.value;
    const ageMax = document.getElementById('talentAgeMaxStats')?.value;
    
    apiRequest(`/ferwafa/talent-discovery?position=${position}&age_max=${ageMax}`).then(talents => {
        const grid = document.getElementById('talentDiscoveryGridStats');
        if (!grid) return;
        
        if (!talents || talents.length === 0) {
            grid.innerHTML = '<p class="empty-state">No players matching these criteria found.</p>';
            return;
        }
        
        grid.innerHTML = talents.map(t => `
            <div class="talent-card">
                <div class="talent-badge">#${Math.round(t.talent_score)}</div>
                <div class="talent-info">
                    <div class="league-cat">${t.position} | Age: ${t.age}</div>
                    <h3 style="margin: 5px 0;">${escapeHtml(t.name)}</h3>
                    <p style="font-size: 0.8rem; color: #666;">${escapeHtml(t.entity_name)}</p>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; font-weight: bold;">
                        <span>Goals: ${t.total_goals}</span>
                        <span>Rating: ${parseFloat(t.avg_rating || 0).toFixed(1)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }).catch(e => console.error('Talent stats load failed', e));
}

function generatePDF() {
    showToast('PDF generation not yet implemented', 'info');
}

// ==========================================
// EVENT LISTENERS & MODAL UTILS
// ==========================================

function setupModals() {
    // Auto-bind form submissions
    const pForm = document.getElementById('playerForm');
    if (pForm) pForm.addEventListener('submit', savePlayer);
    
    const mForm = document.getElementById('matchForm');
    if (mForm) mForm.addEventListener('submit', saveMatch);
    
    const eForm = document.getElementById('entityForm');
    if (eForm) eForm.addEventListener('submit', saveEntity);
    
    const uForm = document.getElementById('userForm');
    if (uForm) uForm.addEventListener('submit', saveUser);
    
    // Close modal-overlay on clicking the dark background (not the inner modal box)
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });
    
    // Close all modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
        }
    });
}

// ==========================================
// UNIFIED ANALYTICS HUB (THE HEART)
// ==========================================

function openAnalyticsModal(mode = 'hardware') {
    const modal = document.getElementById('analyticsModal');
    if (!modal) return;
    
    modal.classList.add('active');
    switchAnalyticsMode(mode);
}
window.openAnalyticsModal = openAnalyticsModal;

function closeAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    if (modal) modal.classList.remove('active');
    // Stop camera if active
    if (_cameraStream) {
        stopDeviceCamera();
    }
}
window.closeAnalyticsModal = closeAnalyticsModal;

function switchAnalyticsMode(mode) {
    const hardwareTab = document.getElementById('hardwareTab');
    const externalTab = document.getElementById('externalTab');
    const cameraTab = document.getElementById('cameraTab');
    const sourceInput = document.getElementById('analyticsSourceType');
    const tabs = document.querySelectorAll('#analyticsModal .tab-btn');
    
    sourceInput.value = mode;
    
    tabs.forEach(t => t.classList.remove('active'));
    if (hardwareTab) hardwareTab.style.display = 'none';
    if (externalTab) externalTab.style.display = 'none';
    if (cameraTab) cameraTab.style.display = 'none';
    
    if (mode === 'hardware') {
        if (hardwareTab) hardwareTab.style.display = 'block';
        if (tabs[0]) tabs[0].classList.add('active');
    } else if (mode === 'external') {
        if (externalTab) externalTab.style.display = 'block';
        if (tabs[1]) tabs[1].classList.add('active');
    } else if (mode === 'camera') {
        if (cameraTab) cameraTab.style.display = 'block';
        if (tabs[2]) tabs[2].classList.add('active');
    }
}
window.switchAnalyticsMode = switchAnalyticsMode;

async function submitAnalyticsSession(event) {
    event.preventDefault();
    const type = document.getElementById('analyticsSourceType').value;
    const aiModel = document.getElementById('analyticsAIModel').value;
    
    let payload = { source_type: type, ai_model: aiModel };
    
    if (type === 'hardware') {
        const sessionName = document.getElementById('hardwareSessionName').value.trim();
        if (!sessionName) {
            showToast('Session name is required', 'error');
            return;
        }
        payload.session_name = sessionName;
    } else if (type === 'external') {
        const sessionName = document.getElementById('externalSessionName').value.trim();
        const sourceUrl = document.getElementById('externalSourceUrl').value.trim();
        if (!sessionName) {
            showToast('Session name is required', 'error');
            return;
        }
        if (!sourceUrl) {
            showToast('Source URL is required', 'error');
            return;
        }
        payload.session_name = sessionName;
        payload.external_url = sourceUrl;
    } else if (type === 'camera') {
        const sessionName = document.getElementById('cameraSessionName')?.value?.trim() || '';
        if (!sessionName) {
            showToast('Session name is required', 'error');
            return;
        }
        payload.session_name = sessionName;
        payload.external_url = 'device_camera';
    }

    try {
        const resp = await apiRequest('/live-stream/create-session', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (resp.success) {
            showToast('Analytics Session Initialized', 'success');
            
            if (type === 'hardware') {
                document.getElementById('generatedCredentials').style.display = 'block';
                document.getElementById('generatedIngestUrl').value = resp.rtmp_url;
                // Leave modal open for the user to copy RTMP details
            } else if (type === 'camera') {
                // Store session ID for camera streaming
                window._cameraSessionId = resp.session_id || resp.stream_id;
                showToast('Session created. Start your camera to begin streaming.', 'info');
            } else if (type === 'external') {
                // Trigger video processing for the external URL
                const videoUrl = document.getElementById('externalSourceUrl').value.trim();
                const sessionName = document.getElementById('externalSessionName').value.trim();
                showToast('Downloading video from YouTube... Please wait.', 'info');
                closeAnalyticsModal();
                
                try {
                    const procResp = await apiRequest('/live-stream/process-video', {
                        method: 'POST',
                        body: JSON.stringify({
                            video_url: videoUrl,
                            session_name: sessionName,
                            match_id: 1,
                            team_id: currentUser?.entity_id || 1
                        })
                    });
                    if (procResp.success) {
                        showToast('Video analysis started! Processing frames...', 'success');
                        // Poll for status
                        const procSessionId = procResp.session_id;
                        pollProcessStatus(procSessionId);
                    }
                } catch (procErr) {
                    console.warn('Video processing trigger failed:', procErr);
                    showToast('Failed to start video processing', 'error');
                }
            } else {
                closeAnalyticsModal();
            }
            loadActiveSessions();
        }
    } catch (e) {
        showToast('Failed to initialize session', 'error');
    }
}
window.submitAnalyticsSession = submitAnalyticsSession;

// ==========================================
// DEVICE CAMERA FUNCTIONS
// ==========================================

let _cameraStream = null;
let _mediaRecorder = null;
let _cameraWs = null;

async function startDeviceCamera(facingMode) {
    try {
        // Stop any existing camera stream
        if (_cameraStream) {
            _cameraStream.getTracks().forEach(t => t.stop());
        }

        const constraints = {
            video: {
                facingMode: facingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: true
        };

        _cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        
        const preview = document.getElementById('cameraPreview');
        if (preview) {
            preview.srcObject = _cameraStream;
            preview.play();
        }

        const previewContainer = document.getElementById('cameraPreviewContainer');
        if (previewContainer) previewContainer.style.display = 'block';

        showToast(`${facingMode === 'user' ? 'Front' : 'Rear'} camera activated`, 'success');
    } catch (err) {
        console.error('Camera error:', err);
        if (err.name === 'NotAllowedError') {
            showToast('Camera access denied. Please allow camera permissions.', 'error');
        } else if (err.name === 'NotFoundError') {
            showToast('No camera found on this device.', 'error');
        } else {
            showToast('Failed to access camera: ' + err.message, 'error');
        }
    }
}
window.startDeviceCamera = startDeviceCamera;

function stopDeviceCamera() {
    // Notify server to clean up temp files
    if (window._cameraSessionId) {
        const token = localStorage.getItem('token') || localStorage.getItem('access_token');
        fetch(`${API_BASE}/live-stream/camera-stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: window._cameraSessionId })
        }).catch(err => console.warn('Cleanup request failed:', err));
        window._cameraSessionId = null;
    }

    if (_cameraStream) {
        _cameraStream.getTracks().forEach(t => t.stop());
        _cameraStream = null;
    }
    if (_mediaRecorder && _mediaRecorder.state !== 'inactive') {
        _mediaRecorder.stop();
        _mediaRecorder = null;
    }
    if (_cameraWs) {
        _cameraWs.close();
        _cameraWs = null;
    }

    const preview = document.getElementById('cameraPreview');
    if (preview) preview.srcObject = null;

    const previewContainer = document.getElementById('cameraPreviewContainer');
    if (previewContainer) previewContainer.style.display = 'none';

    const statusDiv = document.getElementById('cameraStreamStatus');
    if (statusDiv) statusDiv.style.display = 'none';

    showToast('Camera stopped & temp files cleaned', 'info');
}
window.stopDeviceCamera = stopDeviceCamera;

async function startCameraStream() {
    if (!_cameraStream) {
        showToast('Please start the camera first', 'error');
        return;
    }

    try {
        // Create session if not already created
        if (!window._cameraSessionId) {
            const sessionName = document.getElementById('cameraSessionName')?.value || 'Device Camera Stream';
            const resp = await apiRequest('/live-stream/create-session', {
                method: 'POST',
                body: JSON.stringify({
                    source_type: 'camera',
                    session_name: sessionName,
                    external_url: 'device_camera'
                })
            });
            if (resp.success) {
                window._cameraSessionId = resp.session_id || resp.stream_id;
            } else {
                showToast('Failed to create session', 'error');
                return;
            }
        }

        // Check for supported MIME types
        let mimeType = 'video/webm;codecs=vp9,opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'video/webm;codecs=vp8,opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'video/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'video/mp4';
                }
            }
        }

        _mediaRecorder = new MediaRecorder(_cameraStream, {
            mimeType: mimeType,
            videoBitsPerSecond: 2500000
        });

        // Use WebSocket to send chunks to server
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.hostname}:5000/ws/camera/${window._cameraSessionId}`;
        
        try {
            _cameraWs = new WebSocket(wsUrl);
            _cameraWs.onopen = () => {
                showToast('Connected to streaming server', 'success');
            };
            _cameraWs.onerror = () => {
                console.warn('WebSocket not available, using HTTP fallback');
            };
        } catch (e) {
            console.warn('WebSocket connection failed, using HTTP fallback');
        }

        _mediaRecorder.ondataavailable = async (event) => {
            if (event.data && event.data.size > 0) {
                if (_cameraWs && _cameraWs.readyState === WebSocket.OPEN) {
                    _cameraWs.send(event.data);
                } else {
                    // HTTP fallback: send chunk to server
                    try {
                        const formData = new FormData();
                        formData.append('chunk', event.data);
                        formData.append('session_id', window._cameraSessionId);
                        const token = localStorage.getItem('token') || localStorage.getItem('access_token');
                        await fetch(`${API_BASE}/live-stream/camera-chunk`, {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${token}` },
                            body: formData
                        });
                    } catch (err) {
                        console.error('Failed to send chunk:', err);
                    }
                }
            }
        };

        _mediaRecorder.onstop = () => {
            showToast('Camera streaming stopped', 'info');
            const statusDiv = document.getElementById('cameraStreamStatus');
            if (statusDiv) statusDiv.style.display = 'none';
        };

        _mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            showToast('Streaming error: ' + event.error.message, 'error');
        };

        // Start recording with 1-second chunks
        _mediaRecorder.start(1000);

        // Show streaming status
        const statusDiv = document.getElementById('cameraStreamStatus');
        if (statusDiv) statusDiv.style.display = 'block';

        showToast('Camera streaming started!', 'success');
        loadActiveSessions();
    } catch (err) {
        console.error('Stream start error:', err);
        showToast('Failed to start streaming: ' + err.message, 'error');
    }
}
window.startCameraStream = startCameraStream;

// ==========================================
// VIDEO PROCESSING STATUS POLLING
// ==========================================

async function runAITest() {
    showToast('Sending test AI stats...', 'info');
    
    const testPlayers = [];
    for (let i = 1; i <= 11; i++) {
        testPlayers.push({
            track_id: i,
            total_distance: Math.round(800 + Math.random() * 400),
            avg_speed: parseFloat((3 + Math.random() * 4).toFixed(1)),
            max_speed: parseFloat((6 + Math.random() * 5).toFixed(1)),
            sprint_count: Math.floor(5 + Math.random() * 15),
            high_speed_count: Math.floor(10 + Math.random() * 30),
            minutes: parseFloat((10 + Math.random() * 80).toFixed(1)),
            performance_score: parseFloat((50 + Math.random() * 50).toFixed(1))
        });
    }
    
    try {
        const resp = await apiRequest('/ai/test-stats', {
            method: 'POST',
            body: JSON.stringify({
                match_id: 1,
                players: testPlayers
            })
        });
        
        if (resp.success) {
            showToast(`Test stats saved! ${resp.message}. Select match ${resp.match_id || 1} in Statistics to view.`, 'success');
            // Reload matches and analytics
            if (typeof loadMatchListForAnalytics === 'function') {
                loadMatchListForAnalytics();
            }
        } else {
            showToast('Test failed: ' + (resp.error || 'Unknown error'), 'error');
        }
    } catch (e) {
        showToast('Test failed: ' + e.message, 'error');
    }
}
window.runAITest = runAITest;

function pollProcessStatus(sessionId) {
    let attempts = 0;
    const maxAttempts = 120; // Poll for up to 10 minutes

    const interval = setInterval(async () => {
        attempts++;
        try {
            const status = await apiRequest(`/live-stream/process-status/${sessionId}`);

            if (status.status === 'completed') {
                showToast('Video analysis complete! Check AI Match Statistics.', 'success');
                loadActiveSessions();
                clearInterval(interval);
            } else if (status.status === 'error') {
                showToast('Video processing failed: ' + (status.message || 'Unknown error'), 'error');
                clearInterval(interval);
            } else if (status.status === 'downloading') {
                if (attempts % 5 === 0) {
                    showToast('Downloading video from YouTube...', 'info');
                }
            } else if (status.status === 'processing') {
                if (attempts % 10 === 0) {
                    showToast(`Analyzing video frames... (${status.players_found || 0} players found)`, 'info');
                }
            }
        } catch (e) {
            console.warn('Status poll error:', e);
        }

        if (attempts >= maxAttempts) {
            showToast('Processing is taking longer than expected. Check back later.', 'info');
            clearInterval(interval);
        }
    }, 5000); // Poll every 5 seconds
}
window.pollProcessStatus = pollProcessStatus;

async function loadActiveSessions() {
    const cont = document.getElementById('sessionsList');
    if (!cont) return;

    try {
        const resp = await apiRequest('/live-stream/sessions');
        const sessions = resp.sessions || [];
        
        if (sessions.length === 0) {
            cont.innerHTML = `
                <i class="fas fa-video-slash fa-3x mb-3" style="opacity: 0.3;"></i>
                <p>No active analytics sessions. Connect your camera or link to begin.</p>`;
            return;
        }

        cont.innerHTML = sessions.map(s => {
            let icon = 'fa-link';
            let label = 'External Source Ingest';
            let borderColor = 'accent';
            if (s.source_type === 'hardware') {
                icon = 'fa-camera';
                label = 'Live Hardware Ingest';
                borderColor = 'primary';
            } else if (s.source_type === 'camera') {
                icon = 'fa-mobile-alt';
                label = 'Device Camera Stream';
                borderColor = 'success';
            }
            
            let statusBadge = '';
            if (s.status === 'Processing') {
                statusBadge = '<span class="badge bg-warning"><i class="fas fa-spinner fa-spin"></i> Processing</span>';
            } else if (s.status === 'Completed') {
                statusBadge = '<span class="badge bg-success">Completed</span>';
            } else if (s.status === 'In-Progress') {
                statusBadge = '<span class="badge bg-success">In-Progress</span>';
            } else {
                statusBadge = `<span class="badge bg-primary">${s.status}</span>`;
            }
            
            return `
            <div class="card bg-dark-soft mb-3 border-left-${borderColor}">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h4 class="mb-1" style="font-size: 16px;">${s.session_name}</h4>
                            <div style="font-size: 12px; color: var(--text-muted);">
                                <i class="fas ${icon}"></i> 
                                ${label}
                            </div>
                        </div>
                        ${statusBadge}
                    </div>
                </div>
            </div>
            `;
        }).join('');
    } catch (e) {}
}
window.loadActiveSessions = loadActiveSessions;

// ==========================================
// AI MATCH STATISTICS TOOL (Unified UI)
// ==========================================

async function loadMatchListForAnalytics() {
    const selector = document.getElementById('matchAnalyticsSelector');
    if (!selector) return;
    
    try {
        const matches = await apiRequest('/matches');
        if (matches && matches.length > 0) {
            selector.innerHTML = '<option value="">Select a Match to Analyze...</option>' + 
                matches.map(m => `<option value="${m.id}">${new Date(m.match_date).toLocaleDateString()} - ${m.home_team_name} vs ${m.away_team_name}</option>`).join('');
        }
    } catch (e) {
        console.error('Failed to load matches for analytics:', e);
    }
}
window.loadMatchListForAnalytics = loadMatchListForAnalytics;

async function loadMatchAnalytics(matchId) {
    if (!matchId) {
        document.getElementById('analyticsDashboard').style.display = 'none';
        document.getElementById('analyticsEmptyState').style.display = 'block';
        return;
    }
    
    const dashboard = document.getElementById('analyticsDashboard');
    const emptyState = document.getElementById('analyticsEmptyState');
    const tbody = document.getElementById('toolPlayerStatsBody');
    
    if (dashboard) dashboard.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Processing AI Data...</td></tr>';
    
    try {
        const data = await apiRequest(`/ai_stats/report/${matchId}`);
        if (!data.success) throw new Error(data.error);
        
        // Update Team Overview
        const team = data.team_stats;
        safeSetText('toolTeamQuality', Math.round(team.quality_score) + '%');
        safeSetText('toolTeamDistance', (team.total_distance || 0).toFixed(1) + ' km');
        safeSetText('toolTeamAvgSpeed', (team.avg_speed || 0).toFixed(1) + ' km/h');
        safeSetText('toolTeamTopSpeed', (team.top_speed || 0).toFixed(1) + ' km/h');
        safeSetText('toolTeamSprints', team.total_sprints || 0);
        
        // Update Individual Player Stats
        if (tbody) {
            tbody.innerHTML = data.player_stats.map(p => `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="jersey-sm mr-2" style="width:24px;height:24px;background:var(--primary);color:#000;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:bold;margin-right:10px;">
                                ${p.jersey_number || '??'}
                            </div>
                            <span class="font-weight-bold">${p.name}</span>
                        </div>
                    </td>
                    <td><span class="badge bg-secondary px-2">${p.position}</span></td>
                    <td>${(p.distance || 0).toFixed(2)}</td>
                    <td>${(p.max_speed || 0).toFixed(1)}</td>
                    <td>${p.sprint_count || 0}</td>
                    <td>
                        <div class="d-flex align-items-center" style="gap: 12px;">
                            <div class="progress" style="height:8px;width:100px;background:rgba(255,255,255,0.1);border-radius:4px;">
                                <div class="progress-bar ${p.performance_score > 80 ? 'bg-success' : 'bg-primary'}" 
                                     style="width:${p.performance_score}%"></div>
                            </div>
                            <span class="small font-weight-bold">${Math.round(p.performance_score)}/100</span>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
        
    } catch (e) {
        if (dashboard) dashboard.style.display = 'none';
        if (emptyState) {
            emptyState.style.display = 'block';
            emptyState.innerHTML = `<i class="fas fa-exclamation-triangle fa-3x mb-3 text-warning"></i><h3>No Analytics Data</h3><p>${e.message || 'The AI server has not yet generated statistics for this match.'}</p>`;
        }
    }
}
window.loadMatchAnalytics = loadMatchAnalytics;

// Initialize tool on load
document.addEventListener('DOMContentLoaded', () => {
    loadMatchListForAnalytics();
});

// ==========================================
// AI MATCH REPORT TOOL (THE STATISTICS)
// ==========================================

function openMatchReport() {
    const urlParams = new URLSearchParams(window.location.search);
    const matchId = urlParams.get('id');
    
    if (!matchId) return;
    
    const modal = document.getElementById('matchReportModal');
    if (modal) {
        modal.classList.add('active');
        loadMatchReport(matchId);
    }
}
window.openMatchReport = openMatchReport;

function closeMatchReport() {
    const modal = document.getElementById('matchReportModal');
    if (modal) modal.classList.remove('active');
}
window.closeMatchReport = closeMatchReport;

async function loadMatchReport(matchId) {
    const tbody = document.getElementById('playerReportBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Analyzing...</td></tr>';
    
    try {
        const data = await apiRequest(`/ai_stats/report/${matchId}`);
        if (!data.success) throw new Error(data.error);
        
        // Update Team Statistics Overview
        const team = data.team_stats;
        safeSetText('teamQuality', Math.round(team.quality_score) + '%');
        safeSetText('teamDistance', (team.total_distance || 0).toFixed(1) + ' km');
        safeSetText('teamAvgSpeed', (team.avg_speed || 0).toFixed(1) + ' km/h');
        safeSetText('teamTopSpeed', (team.top_speed || 0).toFixed(1) + ' km/h');
        safeSetText('teamSprints', team.total_sprints || 0);
        
        // Update Individual Player Performance Table
        tbody.innerHTML = data.player_stats.map(p => `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="jersey-sm" style="width:24px;height:24px;background:var(--primary);color:#000;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:bold;margin-right:10px;">
                            ${p.jersey_number || '??'}
                        </div>
                        ${p.name}
                    </div>
                </td>
                <td><span class="badge ${p.position === 'GK' ? 'bg-warning' : 'bg-secondary'}">${p.position}</span></td>
                <td>${(p.distance || 0).toFixed(2)} km</td>
                <td>${(p.max_speed || 0).toFixed(1)} km/h</td>
                <td>${p.sprint_count || 0}</td>
                <td>
                    <div class="d-flex align-items-center" style="gap: 10px;">
                        <div class="progress" style="height:6px;width:60px;background:rgba(255,255,255,0.1);border-radius:3px;">
                            <div class="progress-bar ${p.performance_score > 80 ? 'bg-success' : 'bg-primary'}" 
                                 style="width:${p.performance_score}%"></div>
                        </div>
                        <span style="font-size:12px;font-weight:bold;">${Math.round(p.performance_score)}</span>
                    </div>
                </td>
            </tr>
        `).join('');
        
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-danger"><i class="fas fa-exclamation-triangle"></i> ${e.message || 'No AI data available.'}</td></tr>`;
    }
}
window.loadMatchReport = loadMatchReport;

// ==========================================
// SYSTEM LOGS & ERROR TRACKING
// ==========================================

async function loadSystemLogs() {
    const tbody = document.getElementById('logsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Loading logs...</td></tr>';
    
    try {
        const logs = await apiRequest('/logs/usage');
        if (!logs) throw new Error('Failed to load logs');
        
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td><span class="font-weight-bold">${log.username || 'System'}</span></td>
                <td><span class="badge bg-secondary">${log.action}</span></td>
                <td>${log.table_name || '-'}</td>
                <td>${log.record_id || '-'}</td>
                <td><small>${log.ip_address || '-'}</small></td>
                <td>${new Date(log.created_at).toLocaleString()}</td>
            </tr>
        `).join('');
        
        // Cache the logs for search
        window.allLogs = logs;
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${e.message}</td></tr>`;
    }
}
window.loadSystemLogs = loadSystemLogs;

async function loadErrorLogs() {
    const tbody = document.getElementById('errorsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Loading errors...</td></tr>';
    
    try {
        const severity = document.getElementById('errorSeverityFilter')?.value;
        const url = severity ? `/logs/errors?severity=${severity}` : '/logs/errors';
        const errors = await apiRequest(url);
        
        if (!errors) throw new Error('Failed to load errors');
        
        tbody.innerHTML = errors.map(err => `
            <tr>
                <td><span class="badge ${getSeverityClass(err.severity)}">${err.severity}</span></td>
                <td title="${err.stack_trace || ''}">${err.error_message}</td>
                <td><small>${err.endpoint || '-'}</small></td>
                <td>${err.username || 'Guest'}</td>
                <td>${new Date(err.created_at).toLocaleString()}</td>
                <td>
                    <button class="btn-sm btn-outline-primary" onclick="viewErrorDetails(${err.id})">
                        <i class="fas fa-search-plus"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${e.message}</td></tr>`;
    }
}
window.loadErrorLogs = loadErrorLogs;

function getSeverityClass(severity) {
    switch (severity) {
        case 'critical': return 'bg-danger pulsate';
        case 'high': return 'bg-danger';
        case 'medium': return 'bg-warning';
        case 'low': return 'bg-info';
        default: return 'bg-secondary';
    }
}

function filterLogs() {
    const query = document.getElementById('logSearch').value.toLowerCase();
    const tbody = document.getElementById('logsTableBody');
    if (!window.allLogs || !tbody) return;
    
    const filtered = window.allLogs.filter(log => 
        log.username?.toLowerCase().includes(query) || 
        log.action?.toLowerCase().includes(query) ||
        log.table_name?.toLowerCase().includes(query)
    );
    
    tbody.innerHTML = filtered.map(log => `
        <tr>
            <td><span class="font-weight-bold">${log.username || 'System'}</span></td>
            <td><span class="badge bg-secondary">${log.action}</span></td>
            <td>${log.table_name || '-'}</td>
            <td>${log.record_id || '-'}</td>
            <td><small>${log.ip_address || '-'}</small></td>
            <td>${new Date(log.created_at).toLocaleString()}</td>
        </tr>
    `).join('');
}
window.filterLogs = filterLogs;

// Global Error Handler for reporting to backend
window.addEventListener('error', function(event) {
    reportErrorToBackend({
        message: event.message,
        stack: event.error ? event.error.stack : null,
        url: window.location.href,
        severity: 'medium'
    });
});

async function reportErrorToBackend(errorData) {
    try {
        // Use fetch directly to avoid infinite loops if apiRequest fails
        await fetch('/api/logs/report-error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...errorData,
                user_id: localStorage.getItem('userId') // Assuming userId is stored in localStorage
            })
        });
    } catch (e) {
        console.warn('Failed to report error to backend:', e);
    }
}
window.reportErrorToBackend = reportErrorToBackend;
