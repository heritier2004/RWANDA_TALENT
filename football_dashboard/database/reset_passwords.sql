-- Reset all user passwords to 'password123'
-- WARNING: This file contains hardcoded password hashes for development only!
-- DO NOT use in production - use proper password management instead.
-- Run this in phpMyAdmin SQL tab

-- For development/testing only - these hashes correspond to 'password123'
-- In production, use the application's password reset functionality
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pV0e0KzJ9y' WHERE username = 'admin';
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pV0e0KzJ9y' WHERE username = 'ferwafa';
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pV0e0KzJ9y' WHERE username = 'school1';
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pV0e0KzJ9y' WHERE username = 'academy1';
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pV0e0KzJ9y' WHERE username = 'club1';
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G/pV0e0KzJ9y' WHERE username = 'scout1';

SELECT 'Passwords reset!' as message;
