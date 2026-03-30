-- Add test user with known password
-- WARNING: Do NOT commit actual passwords or hashes to version control!
-- Use environment variables or a secure secrets manager in production.
-- Run this script locally for development only.

-- For production, create users through the /api/auth/register endpoint
-- or use a secure database migration tool.

-- Example (DO NOT USE IN PRODUCTION - use the register endpoint instead):
-- INSERT INTO users (username, email, password, role, entity_id, created_at, updated_at)
-- VALUES ('admin', 'admin@example.com', '$2b$12$YOUR_HASH_HERE', 'superadmin', NULL, NOW(), NOW());

SELECT 'Test user creation disabled for security. Use /api/auth/register endpoint instead.' as message;
