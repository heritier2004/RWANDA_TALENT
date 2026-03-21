/**
 * Football Academy Management System
 * Main JavaScript File
 * Handles API calls, UI interactions, and role-based functionality
 */

// API Base URL
const API_BASE = 'http://localhost:5000/api';

// Current user data
let currentUser = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    checkAuth();
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Auto-refresh for live data
    setInterval(refreshLiveData, 900000); // 15 minutes
});

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    
    if (!token || !userStr) {
        // Not logged in, redirect to login
        if (!window.location.href.includes('index.html')) {
            window.location.href = 'index.html';
        }
        return false;
    }
    
    try {
        currentUser = JSON.parse(userStr);
        
        // Update user info in UI
        const userNameEl = document.getElementById('userName');
        if (userNameEl) {
            userNameEl.textContent = currentUser.username;
        }
        
        // Apply role-based access
        applyRoleAccess();
        
        return true;
    } catch (e) {
        logout();
        return false;
    }
}

// Apply role-based access control
function applyRoleAccess() {
    if (!currentUser) return;
    
    const role = currentUser.role;
    
    // Show/hide role-specific elements
    document.querySelectorAll('.role-only').forEach(el => {
        const allowedRoles = el.dataset.roles ? el.dataset.roles.split(',') : [];
        if (allowedRoles.includes(role)) {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    });
}

// Mobile menu toggle
function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }
}

// Get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// API Request helper
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                ...getAuthHeaders(),
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        const overview = await apiRequest('/dashboard/overview');
        
        // Update stats
        document.getElementById('totalPlayers').textContent = overview.total_players || 0;
        document.getElementById('activeMatches').textContent = overview.active_matches || 0;
        document.getElementById('scheduledMatches').textContent = overview.scheduled_matches || 0;
        
        if (overview.top_scorer) {
            document.getElementById('topScorer').textContent = overview.top_scorer.name || 'N/A';
            document.getElementById('topScorerGoals').textContent = `${overview.top_scorer.goals || 0} goals`;
        }
        
        // Load recent and upcoming matches
        loadRecentMatches();
        loadUpcomingMatches();
        
        // Load players
        loadPlayers();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load recent matches
async function loadRecentMatches() {
    try {
        const matches = await apiRequest('/dashboard/recent-matches?limit=5');
        const container = document.getElementById('recentMatches');
        
        if (!container) return;
        
        if (matches.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-futbol"></i><p>No recent matches</p></div>';
            return;
        }
        
        container.innerHTML = matches.map(match => `
            <div class="match-item">
                <div class="match-teams">
                    <div class="match-team">
                        <div class="team-logo"><i class="fas fa-shield-alt"></i></div>
                        <span class="team-name">${match.home_team_name || 'TBD'}</span>
                    </div>
                    <span class="match-score">${match.home_score || 0} - ${match.away_score || 0}</span>
                    <div class="match-team">
                        <span class="team-name">${match.away_team_name || 'TBD'}</span>
                        <div class="team-logo"><i class="fas fa-shield-alt"></i></div>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading recent matches:', error);
    }
}

// Load upcoming matches
async function loadUpcomingMatches() {
    try {
        const matches = await apiRequest('/dashboard/upcoming-matches?limit=5');
        const container = document.getElementById('upcomingMatches');
        
        if (!container) return;
        
        if (matches.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-calendar"></i><p>No upcoming matches</p></div>';
            return;
        }
        
        container.innerHTML = matches.map(match => {
            const date = new Date(match.match_date);
            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            
            return `
                <div class="match-item">
                    <div class="match-teams">
                        <div class="match-team">
                            <div class="team-logo"><i class="fas fa-shield-alt"></i></div>
                            <span class="team-name">${match.home_team_name || 'TBD'}</span>
                        </div>
                        <span class="match-score">VS</span>
                        <div class="match-team">
                            <span class="team-name">${match.away_team_name || 'TBD'}</span>
                            <div class="team-logo"><i class="fas fa-shield-alt"></i></div>
                        </div>
                    </div>
                    <div class="match-info">
                        <div class="match-date">${dateStr}</div>
                        <div class="match-venue">${timeStr}</div>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading upcoming matches:', error);
    }
}

// Load players
async function loadPlayers() {
    try {
        const players = await apiRequest('/players');
        const container = document.getElementById('playersTableBody');
        
        if (!container) return;
        
        if (players.length === 0) {
            container.innerHTML = '<tr><td colspan="7" class="empty-state">No players found</td></tr>';
            return;
        }
        
        container.innerHTML = players.map(player => `
            <tr>
                <td><code>${player.registration_number}</code></td>
                <td>${player.name}</td>
                <td>${player.position}</td>
                <td>${player.jersey_number || '-'}</td>
                <td>${player.nationality}</td>
                <td>${player.dob ? new Date(player.dob).toLocaleDateString() : '-'}</td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editPlayer(${player.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deletePlayer(${player.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading players:', error);
    }
}

// Show add player modal
function showAddPlayerModal() {
    document.getElementById('playerModalTitle').textContent = 'Add New Player';
    document.getElementById('playerId').value = '';
    document.getElementById('playerForm').reset();
    document.getElementById('playerModal').classList.add('active');
}

// Close player modal
function closePlayerModal() {
    document.getElementById('playerModal').classList.remove('active');
}

// Edit player
async function editPlayer(playerId) {
    try {
        const player = await apiRequest(`/players/${playerId}`);
        
        document.getElementById('playerModalTitle').textContent = 'Edit Player';
        document.getElementById('playerId').value = player.id;
        document.getElementById('playerName').value = player.name;
        document.getElementById('playerDob').value = player.dob ? player.dob.split('T')[0] : '';
        document.getElementById('playerNationality').value = player.nationality;
        document.getElementById('playerPosition').value = player.position;
        document.getElementById('playerJersey').value = player.jersey_number || '';
        document.getElementById('playerPhoto').value = player.photo_url || '';
        
        document.getElementById('playerModal').classList.add('active');
        
    } catch (error) {
        console.error('Error loading player:', error);
    }
}

// Save player (create or update)
async function savePlayer(e) {
    e.preventDefault();
    
    const playerId = document.getElementById('playerId').value;
    const data = {
        name: document.getElementById('playerName').value,
        dob: document.getElementById('playerDob').value,
        nationality: document.getElementById('playerNationality').value,
        position: document.getElementById('playerPosition').value,
        jersey_number: document.getElementById('playerJersey').value || null,
        photo_url: document.getElementById('playerPhoto').value || null
    };
    
    try {
        if (playerId) {
            await apiRequest(`/players/${playerId}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showToast('Player updated successfully', 'success');
        } else {
            await apiRequest('/players', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('Player created successfully', 'success');
        }
        
        closePlayerModal();
        loadPlayers();
        
    } catch (error) {
        console.error('Error saving player:', error);
    }
}

// Delete player
async function deletePlayer(playerId) {
    if (!confirm('Are you sure you want to delete this player?')) {
        return;
    }
    
    try {
        await apiRequest(`/players/${playerId}`, {
            method: 'DELETE'
        });
        
        showToast('Player deleted successfully', 'success');
        loadPlayers();
        
    } catch (error) {
        console.error('Error deleting player:', error);
    }
}

// Player form submission
const playerForm = document.getElementById('playerForm');
if (playerForm) {
    playerForm.addEventListener('submit', savePlayer);
}

// Logout function
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Refresh live data
async function refreshLiveData() {
    try {
        await apiRequest('/stats/live');
        loadDashboard();
    } catch (error) {
        console.error('Error refreshing live data:', error);
    }
}

// FERWAFA Dashboard functions
async function loadFERWAFADashboard() {
    try {
        const overview = await apiRequest('/dashboard/overview');
        const entitySummary = await apiRequest('/dashboard/entity-summary');
        
        document.getElementById('totalPlayers').textContent = overview.total_players || 0;
        document.getElementById('totalClubs').textContent = overview.total_clubs || 0;
        
        // Load all players
        loadAllPlayers();
        
        // Load top performers
        loadTopPerformers();
        
    } catch (error) {
        console.error('Error loading FERWAFA dashboard:', error);
    }
}

// Load all players (for FERWAFA/Super Admin)
async function loadAllPlayers() {
    try {
        const players = await apiRequest('/players');
        const container = document.getElementById('allPlayersTableBody');
        
        if (!container) return;
        
        if (players.length === 0) {
            container.innerHTML = '<tr><td colspan="7" class="empty-state">No players found</td></tr>';
            return;
        }
        
        container.innerHTML = players.map(player => `
            <tr>
                <td><code>${player.registration_number}</code></td>
                <td>${player.name}</td>
                <td>${player.entity_name || 'N/A'}</td>
                <td>${player.position}</td>
                <td>${player.jersey_number || '-'}</td>
                <td>${player.nationality}</td>
                <td>${player.total_goals || 0}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading all players:', error);
    }
}

// Search all players
async function searchAllPlayers() {
    const searchTerm = document.getElementById('playerSearch').value;
    
    if (searchTerm.length < 2) {
        loadAllPlayers();
        return;
    }
    
    try {
        const players = await apiRequest(`/players?search=${encodeURIComponent(searchTerm)}`);
        const container = document.getElementById('allPlayersTableBody');
        
        if (!container) return;
        
        container.innerHTML = players.map(player => `
            <tr>
                <td><code>${player.registration_number}</code></td>
                <td>${player.name}</td>
                <td>${player.entity_name || 'N/A'}</td>
                <td>${player.position}</td>
                <td>${player.jersey_number || '-'}</td>
                <td>${player.nationality}</td>
                <td>${player.total_goals || 0}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error searching players:', error);
    }
}

// Load top performers
async function loadTopPerformers() {
    try {
        const scorers = await apiRequest('/stats/top-scorers?limit=5');
        const assists = await apiRequest('/stats/top-assists?limit=5');
        
        const scorersContainer = document.getElementById('topScorers');
        const assistsContainer = document.getElementById('topAssists');
        
        if (scorersContainer) {
            scorersContainer.innerHTML = scorers.map((player, index) => `
                <div class="performer-item">
                    <div class="performer-rank">${index + 1}</div>
                    <div class="performer-info">
                        <div class="performer-name">${player.name}</div>
                        <div class="performer-details">${player.entity_name || ''} • ${player.position}</div>
                    </div>
                    <div class="performer-stat">${player.total_goals || 0}</div>
                </div>
            `).join('');
        }
        
        if (assistsContainer) {
            assistsContainer.innerHTML = assists.map((player, index) => `
                <div class="performer-item">
                    <div class="performer-rank">${index + 1}</div>
                    <div class="performer-info">
                        <div class="performer-name">${player.name}</div>
                        <div class="performer-details">${player.entity_name || ''} • ${player.position}</div>
                    </div>
                    <div class="performer-stat">${player.total_assists || 0}</div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading top performers:', error);
    }
}

// Scout functions
async function loadTopPerformers() {
    loadTopPerformersScout();
}

async function loadTopPerformersScout() {
    try {
        const scorers = await apiRequest('/stats/top-scorers?limit=5');
        const assists = await apiRequest('/stats/top-assists?limit=5');
        
        const scorersContainer = document.getElementById('topScorers');
        const assistsContainer = document.getElementById('topAssists');
        
        if (scorersContainer) {
            scorersContainer.innerHTML = scorers.map((player, index) => `
                <div class="performer-item">
                    <div class="performer-rank">${index + 1}</div>
                    <div class="performer-info">
                        <div class="performer-name">${player.name}</div>
                        <div class="performer-details">${player.position}</div>
                    </div>
                    <div class="performer-stat">${player.total_goals || 0}</div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading top performers:', error);
    }
}

// Search players for scout
async function searchPlayers() {
    const position = document.getElementById('filterPosition').value;
    const nationality = document.getElementById('filterNationality').value;
    
    try {
        let url = '/players?';
        if (position) url += `position=${position}&`;
        if (nationality) url += `nationality=${nationality}&`;
        
        const players = await apiRequest(url);
        const container = document.getElementById('talentTableBody');
        
        if (!container) return;
        
        if (players.length === 0) {
            container.innerHTML = '<tr><td colspan="7" class="empty-state">No players found</td></tr>';
            return;
        }
        
        container.innerHTML = players.map(player => `
            <tr>
                <td>${player.name}</td>
                <td>${player.position}</td>
                <td>${calculateAge(player.dob)}</td>
                <td>${player.nationality}</td>
                <td>${player.entity_name || 'N/A'}</td>
                <td>${player.total_goals || 0}</td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-secondary" onclick="viewPlayerProfile(${player.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="addToFavorites(${player.id})">
                        <i class="fas fa-heart"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error searching players:', error);
    }
}

// Calculate age from DOB
function calculateAge(dob) {
    if (!dob) return '-';
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

// View player profile
function viewPlayerProfile(playerId) {
    window.location.href = `dashboard.html#player/${playerId}`;
}

// Add to favorites (scout)
function addToFavorites(playerId) {
    showToast('Added to favorites', 'success');
}

// Super Admin functions
async function loadSuperAdminDashboard() {
    try {
        const overview = await apiRequest('/dashboard/overview');
        
        document.getElementById('totalUsers').textContent = overview.total_users || 0;
        document.getElementById('totalClubs').textContent = overview.total_clubs || 0;
        document.getElementById('totalPlayers').textContent = overview.total_players || 0;
        
        // Load users
        loadUsers();
        
    } catch (error) {
        console.error('Error loading super admin dashboard:', error);
    }
}

// Load all users
async function loadUsers() {
    try {
        const users = await apiRequest('/auth/users');
        const container = document.getElementById('usersTableBody');
        
        if (!container) return;
        
        if (users.length === 0) {
            container.innerHTML = '<tr><td colspan="7" class="empty-state">No users found</td></tr>';
            return;
        }
        
        container.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td><span class="badge role-${user.role}">${user.role}</span></td>
                <td>${user.entity_id || '-'}</td>
                <td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editUser(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Show add user modal
function showAddUserModal() {
    document.getElementById('userForm').reset();
    document.getElementById('userModal').classList.add('active');
}

// Close user modal
function closeUserModal() {
    document.getElementById('userModal').classList.remove('active');
}

// Save user
async function saveUser(e) {
    e.preventDefault();
    
    const data = {
        username: document.getElementById('newUsername').value,
        email: document.getElementById('newEmail').value,
        password: document.getElementById('newPassword').value,
        role: document.getElementById('newRole').value
    };
    
    try {
        await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast('User created successfully', 'success');
        closeUserModal();
        loadUsers();
        
    } catch (error) {
        console.error('Error creating user:', error);
    }
}

// User form submission
const userForm = document.getElementById('userForm');
if (userForm) {
    userForm.addEventListener('submit', saveUser);
}

// Delete user
async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        await apiRequest(`/auth/users/${userId}`, {
            method: 'DELETE'
        });
        
        showToast('User deleted successfully', 'success');
        loadUsers();
        
    } catch (error) {
        console.error('Error deleting user:', error);
    }
}

// Save settings
function saveSettings() {
    const updateInterval = document.getElementById('updateInterval').value;
    const mlSetting = document.getElementById('mlSetting').value;
    const retention = document.getElementById('retention').value;
    
    // Save to local storage (in real app, save to server)
    localStorage.setItem('settings', JSON.stringify({
        updateInterval,
        mlSetting,
        retention
    }));
    
    showToast('Settings saved successfully', 'success');
}

// Club-specific ML upload functionality
function initMLUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const mlInput = document.getElementById('mlInput');
    
    if (!uploadArea || !mlInput) return;
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#3182ce';
        uploadArea.style.background = '#ebf8ff';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#e2e8f0';
        uploadArea.style.background = 'transparent';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#e2e8f0';
        uploadArea.style.background = 'transparent';
        
        const files = e.dataTransfer.files;
        handleMLUpload(files);
    });
    
    // File input change
    mlInput.addEventListener('change', (e) => {
        handleMLUpload(e.target.files);
    });
}

// Handle ML file upload
async function handleMLUpload(files) {
    if (!files.length) return;
    
    const mlStatus = document.getElementById('mlStatus');
    if (mlStatus) {
        mlStatus.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Processing photos...</p>';
    }
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('photo', file);
        
        try {
            const response = await fetch(`${API_BASE}/players/upload-photo`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (mlStatus) {
                mlStatus.innerHTML = `
                    <p><i class="fas fa-check-circle"></i> ${file.name} processed successfully</p>
                    <p class="ml-note">Face detected: ${data.result?.face_detected ? 'Yes' : 'No'} | Confidence: ${(data.result?.confidence * 100).toFixed(1)}%</p>
                `;
            }
            
        } catch (error) {
            console.error('Error uploading photo:', error);
            if (mlStatus) {
                mlStatus.innerHTML = `<p><i class="fas fa-exclamation-circle"></i> Error processing ${file.name}</p>`;
            }
        }
    }
}

// Match functions for club
function showAddMatchModal() {
    document.getElementById('matchForm').reset();
    document.getElementById('matchModal').classList.add('active');
}

function closeMatchModal() {
    document.getElementById('matchModal').classList.remove('active');
}

async function saveMatch(e) {
    e.preventDefault();
    
    const data = {
        home_team_id: 1, // Would be dynamic based on club
        away_team: document.getElementById('awayTeam').value,
        match_date: document.getElementById('matchDate').value,
        venue_id: 1, // Would be dynamic
        venue: document.getElementById('matchVenue').value
    };
    
    try {
        await apiRequest('/matches', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast('Match scheduled successfully', 'success');
        closeMatchModal();
        
    } catch (error) {
        console.error('Error creating match:', error);
    }
}

const matchForm = document.getElementById('matchForm');
if (matchForm) {
    matchForm.addEventListener('submit', saveMatch);
}

// Export functions to window for onclick handlers
window.logout = logout;
window.showAddPlayerModal = showAddPlayerModal;
window.closePlayerModal = closePlayerModal;
window.editPlayer = editPlayer;
window.deletePlayer = deletePlayer;
window.showAddUserModal = showAddUserModal;
window.closeUserModal = closeUserModal;
window.deleteUser = deleteUser;
window.saveSettings = saveSettings;
window.showAddMatchModal = showAddMatchModal;
window.closeMatchModal = closeMatchModal;
window.searchPlayers = searchPlayers;
window.searchAllPlayers = searchAllPlayers;
window.viewPlayerProfile = viewPlayerProfile;
window.addToFavorites = addToFavorites;
window.loadLineup = loadLineup;
window.initMLUpload = initMLUpload;

// Placeholder functions
function loadLineup() {
    console.log('Load lineup for selected match');
}

function showAddEntityModal(type) {
    console.log('Add entity:', type);
}
