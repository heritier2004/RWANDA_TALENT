-- System Error Logging Table
CREATE TABLE IF NOT EXISTS system_errors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    endpoint VARCHAR(255),
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    browser_info TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_severity (severity),
    INDEX idx_created (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Add some initial categories if needed, or indices
ALTER TABLE audit_logs ADD INDEX IF NOT EXISTS idx_table_record (table_name, record_id);
