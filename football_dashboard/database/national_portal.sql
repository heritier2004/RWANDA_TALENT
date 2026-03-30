-- National Portal Enhancements
-- Adds Leagues and Announcements

USE football_dashboard;

-- ============================================
-- LEAGUES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS leagues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM('Professional', 'Academy', 'School', 'Amateur') NOT NULL,
    season VARCHAR(20) NOT NULL, -- e.g. "2023/2024"
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
) ENGINE=InnoDB;

-- ============================================
-- ANNOUNCEMENTS TABLE (News)
-- ============================================
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category ENUM('General', 'Match Update', 'Scouting', 'Regulation', 'Urgent') DEFAULT 'General',
    target_role ENUM('all', 'school', 'academy', 'club', 'scout') DEFAULT 'all',
    author_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_created (created_at),
    INDEX idx_target (target_role)
) ENGINE=InnoDB;

-- ============================================
-- UPDATE CLUBS TO USE LEAGUE FOREIGN KEY
-- ============================================
-- Note: league_id already exists as INT, we just add the constraint
ALTER TABLE clubs ADD CONSTRAINT fk_club_league FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE SET NULL;

-- ============================================
-- INSERT SAMPLE LEAGUES
-- ============================================
INSERT INTO leagues (name, category, season, description) VALUES
('Rwanda Premier League', 'Professional', '2023/2024', 'The top tier of professional football in Rwanda.'),
('National Academy Series U17', 'Academy', '2023/2024', 'Elite youth development league for U17 players.'),
('Inter-School Championship', 'School', '2023/2024', 'Annual football competition for secondary schools.');

-- ============================================
-- INSERT SAMPLE ANNOUNCEMENTS
-- ============================================
INSERT INTO announcements (title, content, category, target_role, author_id) VALUES
('New Regulations on Youth Transfers', 'FERWAFA has released new guidelines regarding the transfer of players under 18 from academies to professional clubs.', 'Regulation', 'all', 2),
('Scouting Seminar in Kigali', 'A mandatory seminar for all registered scouts will be held at Amahoro Stadium next month.', 'Scouting', 'scout', 2),
('League Expansion Notice', 'The Rwanda Premier League will expand to 18 teams for the upcoming season.', 'General', 'club', 2);
