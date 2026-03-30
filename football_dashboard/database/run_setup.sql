-- Combined SQL Setup Script for Football Dashboard
-- Run this file in phpMyAdmin to add all required tables and columns
-- Compatible with MySQL 5.7+

-- =====================================================
-- PART 1: Add new columns to players table (MySQL 5.7 compatible)
-- =====================================================
-- Use procedure to safely add columns if they don't exist
DELIMITER //
CREATE PROCEDURE add_player_columns_if_not_exists()
BEGIN
    -- age column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'age') THEN
        ALTER TABLE players ADD COLUMN age INT;
    END IF;
    
    -- height column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'height') THEN
        ALTER TABLE players ADD COLUMN height VARCHAR(10);
    END IF;
    
    -- weight column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'weight') THEN
        ALTER TABLE players ADD COLUMN weight VARCHAR(10);
    END IF;
    
    -- nationality column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'nationality') THEN
        ALTER TABLE players ADD COLUMN nationality VARCHAR(100);
    END IF;
    
    -- dob column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'dob') THEN
        ALTER TABLE players ADD COLUMN dob DATE;
    END IF;
    
    -- photo column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'photo') THEN
        ALTER TABLE players ADD COLUMN photo VARCHAR(255);
    END IF;
    
    -- district column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'district') THEN
        ALTER TABLE players ADD COLUMN district VARCHAR(100);
    END IF;
    
    -- sector column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'sector') THEN
        ALTER TABLE players ADD COLUMN sector VARCHAR(100);
    END IF;
    
    -- cell column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'cell') THEN
        ALTER TABLE players ADD COLUMN cell VARCHAR(100);
    END IF;
    
    -- village column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'village') THEN
        ALTER TABLE players ADD COLUMN village VARCHAR(100);
    END IF;
    
    -- player_status column
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'players' AND COLUMN_NAME = 'player_status') THEN
        ALTER TABLE players ADD COLUMN player_status VARCHAR(50) DEFAULT 'active';
    END IF;
END//
DELIMITER ;

-- Execute the procedure
CALL add_player_columns_if_not_exists();

-- Drop the procedure after use
DROP PROCEDURE IF EXISTS add_player_columns_if_not_exists;

-- =====================================================
-- PART 2: Create live_streams table
-- =====================================================
CREATE TABLE IF NOT EXISTS live_streams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT,
    team_id INT,
    stream_name VARCHAR(255),
    stream_url VARCHAR(500),
    rtmp_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'inactive',
    started_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 3: Create ml_training table
-- =====================================================
CREATE TABLE IF NOT EXISTS ml_training (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    model_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    accuracy FLOAT,
    trained_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 4: Create training_data table
-- =====================================================
CREATE TABLE IF NOT EXISTS training_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ml_training_id INT,
    video_path VARCHAR(500),
    annotations TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 5: Create statistics table
-- =====================================================
CREATE TABLE IF NOT EXISTS statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    match_id INT,
    distance FLOAT DEFAULT 0,
    avg_speed FLOAT DEFAULT 0,
    max_speed FLOAT DEFAULT 0,
    sprint_count INT DEFAULT 0,
    high_speed_count INT DEFAULT 0,
    minutes FLOAT DEFAULT 0,
    performance_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- =====================================================
-- PART 6: Create ai_processing_jobs table
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_processing_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT,
    team_id INT,
    video_source VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',
    progress INT DEFAULT 0,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 7: Create player_talent_history table
-- =====================================================
CREATE TABLE IF NOT EXISTS player_talent_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    match_id INT,
    analysis_date DATE,
    talent_score FLOAT,
    speed_avg FLOAT,
    distance_covered FLOAT,
    sprints INT,
    top_speed FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- =====================================================
-- PART 8: Create talent_recommendations table
-- =====================================================
CREATE TABLE IF NOT EXISTS talent_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    source VARCHAR(50),
    recommendation_text TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    scout_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- =====================================================
-- PART 9: Create camera_streams table
-- =====================================================
CREATE TABLE IF NOT EXISTS camera_streams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    stream_url VARCHAR(500),
    team_id INT,
    status VARCHAR(50) DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 10: Insert sample data
-- =====================================================
INSERT INTO live_streams (match_id, team_id, stream_name, stream_url, status) 
SELECT 1, 1, 'Match Stream 1', 'rtmp://localhost/live/stream1', 'inactive'
WHERE NOT EXISTS (SELECT 1 FROM live_streams WHERE stream_name = 'Match Stream 1');

INSERT INTO ml_training (name, description, model_type, status)
SELECT 'Player Detection', 'YOLO model for detecting players', 'yolov8', 'pending'
WHERE NOT EXISTS (SELECT 1 FROM ml_training WHERE name = 'Player Detection');

SELECT 'Database setup completed successfully!' as message;
