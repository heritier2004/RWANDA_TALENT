-- Add is_active column to users table for pause/activate functionality
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE AFTER entity_id;

-- Update existing users to be active
UPDATE users SET is_active = TRUE WHERE is_active IS NULL;

-- Verify the column was added
DESCRIBE users;