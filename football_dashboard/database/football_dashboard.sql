-- Football Academy Management System
-- MySQL Database Schema
-- Compatible with MySQL 5.7+ and XAMPP

-- Create database
CREATE DATABASE IF NOT EXISTS football_dashboard 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE football_dashboard;

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('school', 'academy', 'club', 'scout', 'ferwafa', 'superadmin') NOT NULL,
    entity_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_entity (entity_id)
) ENGINE=InnoDB;

-- ============================================
-- SCHOOLS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS schools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    established_year YEAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB;

-- ============================================
-- ACADEMIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS academies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    director_name VARCHAR(100),
    established_year YEAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB;

-- ============================================
-- CLUBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS clubs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10),
    address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    logo_url VARCHAR(500),
    stadium_name VARCHAR(100),
    founded_year YEAR,
    league_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_league (league_id)
) ENGINE=InnoDB;

-- ============================================
-- VENUES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS venues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    capacity INT,
    city VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_city (city)
) ENGINE=InnoDB;

-- ============================================
-- PLAYERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS players (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    jersey_number INT,
    position ENUM('Goalkeeper', 'Defender', 'Midfielder', 'Forward',
                  'Center Back', 'Left Back', 'Right Back',
                  'Central Midfielder', 'Attacking Midfielder', 'Defensive Midfielder',
                  'Striker', 'Left Winger', 'Right Winger') NOT NULL,
    photo_url VARCHAR(500),
    school_id INT NULL,
    academy_id INT NULL,
    club_id INT NULL,
    height_cm INT,
    weight_kg INT,
    status ENUM('active', 'injured', 'transferred', 'retired') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_registration (registration_number),
    INDEX idx_name (name),
    INDEX idx_position (position),
    INDEX idx_school (school_id),
    INDEX idx_academy (academy_id),
    INDEX idx_club (club_id),
    INDEX idx_status (status),
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE SET NULL,
    FOREIGN KEY (academy_id) REFERENCES academies(id) ON DELETE SET NULL,
    FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================
-- MATCHES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    match_date DATETIME NOT NULL,
    venue_id INT,
    home_score INT DEFAULT 0,
    away_score INT DEFAULT 0,
    status ENUM('scheduled', 'live', 'completed', 'postponed', 'cancelled') DEFAULT 'scheduled',
    match_time VARCHAR(10),
    half_time_home INT,
    half_time_away INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_match_date (match_date),
    INDEX idx_status (status),
    INDEX idx_home_team (home_team_id),
    INDEX idx_away_team (away_team_id),
    INDEX idx_venue (venue_id),
    FOREIGN KEY (home_team_id) REFERENCES clubs(id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES clubs(id) ON DELETE CASCADE,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================
-- MATCH LINEUPS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS match_lineups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    player_id INT NOT NULL,
    position_type ENUM('starting', 'bench') NOT NULL,
    position_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_match (match_id),
    INDEX idx_player (player_id),
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- STATISTICS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    match_id INT NOT NULL,
    goals INT DEFAULT 0,
    assists INT DEFAULT 0,
    minutes_played INT DEFAULT 0,
    yellow_cards INT DEFAULT 0,
    red_cards INT DEFAULT 0,
    rating DECIMAL(3,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_player_match (player_id, match_id),
    INDEX idx_player (player_id),
    INDEX idx_match (match_id),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- SCOUTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS scouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    region VARCHAR(50),
    specialization VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_region (region),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- FAVORITES TABLE (for scouts)
-- ============================================
CREATE TABLE IF NOT EXISTS favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scout_id INT NOT NULL,
    player_id INT NOT NULL,
    notes TEXT,
    rating INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_favorite (scout_id, player_id),
    INDEX idx_scout (scout_id),
    INDEX idx_player (player_id),
    FOREIGN KEY (scout_id) REFERENCES scouts(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- TRAINING SESSIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS training_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    academy_id INT,
    club_id INT,
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    session_type ENUM('technical', 'tactical', 'fitness', 'recovery', 'match_prep') NOT NULL,
    location VARCHAR(100),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (session_date),
    INDEX idx_academy (academy_id),
    INDEX idx_club (club_id),
    FOREIGN KEY (academy_id) REFERENCES academies(id) ON DELETE CASCADE,
    FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- GPS DATA TABLE (placeholder for future)
-- ============================================
CREATE TABLE IF NOT EXISTS gps_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    session_id INT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    altitude DECIMAL(6, 2),
    speed DECIMAL(6, 2),
    recorded_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_player (player_id),
    INDEX idx_session (session_id),
    INDEX idx_recorded (recorded_at),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES training_sessions(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================
-- ML PROCESSING TABLE (for player recognition)
-- ============================================
CREATE TABLE IF NOT EXISTS ml_processing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    photo_path VARCHAR(500),
    face_detected BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(5,4),
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    INDEX idx_player (player_id),
    INDEX idx_status (status),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- AUDIT LOG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================
-- INSERT SAMPLE DATA
-- ============================================

-- Insert sample schools
INSERT INTO schools (name, address, phone, email, established_year) VALUES
('Kigali Primary School', 'Kigali, Rwanda', '+250788123456', 'info@kigalips.rw', 2000),
('Remera Primary School', 'Remera, Kigali', '+250788234567', 'info@remeraps.rw', 1995),
('Kenyatta School', 'Kenyatta Avenue, Kigali', '+250788345678', 'info@kenyattaschool.rw', 1985);

-- Insert sample academies
INSERT INTO academies (name, address, phone, email, director_name, established_year) VALUES
('Aspire Football Academy', 'Kigali, Rwanda', '+250788456789', 'info@aspireacademy.rw', 'John Smith', 2010),
('Rising Stars Academy', 'Kicukiro, Kigali', '+250788567890', 'info@risingstars.rw', 'Marie Uwimana', 2015),
('Elite Football Academy', 'Gasabo, Kigali', '+250788678901', 'info@eliteacademy.rw', 'Patrick Niyonzima', 2012);

-- Insert sample clubs
INSERT INTO clubs (name, short_name, address, phone, email, stadium_name, founded_year) VALUES
('Amazulu FC', 'AMZ', 'Kigali Stadium', '+250788111111', 'info@amazulu.rw', 'Amazulu Stadium', 1970),
('Police FC', 'POL', 'Kigali', '+250788222222', 'info@policefc.rw', 'Police Stadium', 1980),
('Armed Forces FC', 'AF', 'Kigali', '+250788333333', 'info@armedforces.rw', 'Army Stadium', 1975),
('Rayon Sports FC', 'RAY', 'Kigali', '+250788444444', 'info@rayonsports.rw', 'Amahoro Stadium', 1989),
('APR FC', 'APR', 'Kigali', '+250788555555', 'info@aprfc.rw', 'APR Stadium', 1990);

-- Insert sample venues
INSERT INTO venues (name, address, capacity, city) VALUES
('Amahoro National Stadium', 'Kigali', 25000, 'Kigali'),
('Kigali Regional Stadium', 'Kigali', 10000, 'Kigali'),
('Rubavu Stadium', 'Rubavu', 5000, 'Rubavu'),
('Huye Stadium', 'Huye', 5000, 'Huye');

-- Insert sample users (password: password123 for all)
INSERT INTO users (username, email, password, role, entity_id) VALUES
('admin', 'admin@football.rw', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pVHvPLZZw6L2', 'superadmin', NULL),
('ferwafa', 'ferwafa@ferwafa.rw', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pVHvPLZZw6L2', 'ferwafa', NULL),
('school1', 'school1@school.rw', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pVHvPLZZw6L2', 'school', 1),
('academy1', 'academy1@academy.rw', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pVHvPLZZw6L2', 'academy', 1),
('club1', 'club1@club.rw', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pVHvPLZZw6L2', 'club', 1),
('scout1', 'scout1@scout.rw', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pVHvPLZZw6L2', 'scout', NULL);

-- Insert sample players
INSERT INTO players (registration_number, name, dob, nationality, jersey_number, position, school_id, academy_id, club_id) VALUES
('SCH-1-A1B2C3D4', 'Emmanuel Mukama', '2008-05-15', 'Rwandan', 1, 'Goalkeeper', 1, NULL, NULL),
('SCH-1-E5F6G7H8', 'Jean Pierre Niyonkuru', '2007-08-20', 'Rwandan', 2, 'Defender', 1, NULL, NULL),
('SCH-1-I9J0K1L2', 'Didier Nkurunziza', '2007-03-10', 'Rwandan', 3, 'Midfielder', 1, NULL, NULL),
('ACA-1-M3N4O5P6', 'Alexis Uwimbabazi', '2005-11-22', 'Rwandan', 10, 'Forward', NULL, 1, NULL),
('ACA-1-Q7R8S9T0', 'Boniface Habiyambere', '2004-07-08', 'Rwandan', 11, 'Striker', NULL, 1, NULL),
('CLB-1-U1V2W3X4', 'Yannick Mukunzi', '2000-01-15', 'Rwandan', 7, 'Midfielder', NULL, NULL, 1),
('CLB-1-Y5Z6A7B8', 'Djokovic Mutesasira', '1998-06-20', 'Rwandan', 9, 'Forward', NULL, NULL, 1),
('CLB-1-C9D0E1F2', 'Joseph Rwibasira', '1995-12-10', 'Rwandan', 1, 'Goalkeeper', NULL, NULL, 2);

-- Insert sample matches
INSERT INTO matches (home_team_id, away_team_id, match_date, venue_id, home_score, away_score, status) VALUES
(1, 2, DATE_ADD(NOW(), INTERVAL 7 DAY), 1, NULL, NULL, 'scheduled'),
(3, 4, DATE_ADD(NOW(), INTERVAL 14 DAY), 2, NULL, NULL, 'scheduled'),
(1, 3, DATE_SUB(NOW(), INTERVAL 3 DAY), 1, 2, 1, 'completed'),
(2, 4, DATE_SUB(NOW(), INTERVAL 5 DAY), 2, 1, 1, 'completed'),
(5, 1, NOW(), 1, 1, 0, 'live');

-- Insert sample statistics
INSERT INTO statistics (player_id, match_id, goals, assists, minutes_played, yellow_cards, red_cards) VALUES
(6, 3, 1, 1, 90, 0, 0),
(7, 3, 1, 0, 85, 1, 0),
(8, 4, 1, 0, 90, 0, 0);

-- Insert sample match lineups
INSERT INTO match_lineups (match_id, player_id, position_type, position_order) VALUES
(3, 6, 'starting', 1),
(3, 7, 'starting', 2),
(3, 6, 'bench', 12);

-- Insert sample training sessions
INSERT INTO training_sessions (academy_id, club_id, session_date, start_time, end_time, session_type, location) VALUES
(1, NULL, DATE_ADD(NOW(), INTERVAL 1 DAY), '09:00:00', '11:00:00', 'technical', 'Academy Ground'),
(NULL, 1, DATE_ADD(NOW(), INTERVAL 2 DAY), '10:00:00', '12:00:00', 'tactical', 'Club Stadium');

-- ============================================
-- CREATE VIEWS
-- ============================================

-- View for player statistics summary
CREATE OR REPLACE VIEW player_stats_summary AS
SELECT 
    p.id,
    p.name,
    p.position,
    p.nationality,
    p.registration_number,
    COALESCE(p.club_id, p.academy_id, p.school_id) as entity_id,
    COALESCE(c.name, a.name, s.name) as entity_name,
    COALESCE(
        (SELECT SUM(goals) FROM statistics WHERE player_id = p.id), 0
    ) as total_goals,
    COALESCE(
        (SELECT SUM(assists) FROM statistics WHERE player_id = p.id), 0
    ) as total_assists,
    COALESCE(
        (SELECT COUNT(*) FROM statistics WHERE player_id = p.id), 0
    ) as matches_played
FROM players p
LEFT JOIN clubs c ON p.club_id = c.id
LEFT JOIN academies a ON p.academy_id = a.id
LEFT JOIN schools s ON p.school_id = s.id;

-- View for match results
CREATE OR REPLACE VIEW match_results AS
SELECT 
    m.id,
    m.match_date,
    m.status,
    h.name as home_team,
    a.name as away_team,
    m.home_score,
    m.away_score,
    v.name as venue,
    CASE 
        WHEN m.home_score > m.away_score THEN h.name
        WHEN m.away_score > m.home_score THEN a.name
        ELSE 'Draw'
    END as winner
FROM matches m
JOIN clubs h ON m.home_team_id = h.id
JOIN clubs a ON m.away_team_id = a.id
LEFT JOIN venues v ON m.venue_id = v.id;

-- View for entity summary (clubs, academies, schools)
CREATE OR REPLACE VIEW entity_summary AS
SELECT 'club' as entity_type, id, name, created_at FROM clubs
UNION ALL
SELECT 'academy', id, name, created_at FROM academies
UNION ALL
SELECT 'school', id, name, created_at FROM schools;

-- ============================================
-- STORED PROCEDURES
-- ============================================

DELIMITER //

-- Procedure to generate unique registration number
CREATE PROCEDURE generate_player_registration(
    IN p_role VARCHAR(20),
    IN p_entity_id INT,
    OUT p_registration_number VARCHAR(50)
)
BEGIN
    DECLARE prefix VARCHAR(3);
    
    CASE p_role
        WHEN 'school' THEN SET prefix = 'SCH';
        WHEN 'academy' THEN SET prefix = 'ACA';
        WHEN 'club' THEN SET prefix = 'CLB';
        ELSE SET prefix = 'GEN';
    END CASE;
    
    SET p_registration_number = CONCAT(prefix, '-', p_entity_id, '-', UPPER(SUBSTRING(MD5(RAND()), 1, 8)));
END //

-- Procedure to update match statistics automatically
CREATE PROCEDURE update_match_stats(
    IN p_match_id INT
)
BEGIN
    -- This would be called by a scheduled event every 15 minutes
    -- Updates live match statistics
    UPDATE matches 
    SET status = 'live'
    WHERE id = p_match_id 
    AND status = 'scheduled'
    AND match_date <= NOW();
END //

DELIMITER ;

-- ============================================
-- SCHEDULED EVENTS (for live updates)
-- ============================================

-- Enable the event scheduler
SET GLOBAL event_scheduler = ON;

-- Event to update live match status every 15 minutes
CREATE EVENT IF NOT EXISTS update_live_matches
ON SCHEDULE EVERY 15 MINUTE
DO
BEGIN
    -- Update matches that have started
    UPDATE matches 
    SET status = 'live'
    WHERE status = 'scheduled' 
    AND match_date <= NOW()
    AND match_date >= DATE_SUB(NOW(), INTERVAL 2 HOUR);
    
    -- Update matches that have ended (90 minutes after start)
    UPDATE matches 
    SET status = 'completed'
    WHERE status = 'live'
    AND match_date <= DATE_SUB(NOW(), INTERVAL 90 MINUTE);
END //

-- ============================================
-- FINISH
-- ============================================

SELECT 'Database schema created successfully!' as message;
SELECT 'Tables created: users, schools, academies, clubs, venues, players, matches, match_lineups, statistics, scouts, favorites, training_sessions, gps_data, ml_processing, audit_logs' as info;
