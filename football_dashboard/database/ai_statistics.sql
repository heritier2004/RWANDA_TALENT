-- DEPRECATED: This file's schema has been merged into unified_schema.sql
-- Use unified_schema.sql for fresh installs or run_safe_migration.py for existing databases.
--
-- AI Statistics Tables for Football Player Tracking
-- These tables are now part of the unified schema.
--
-- The 'statistics' table now contains BOTH:
--   - Traditional match stats: goals, assists, minutes_played, yellow_cards, red_cards, rating
--   - AI tracking stats: distance, avg_speed, max_speed, sprint_count, high_speed_count, performance_score, team_id

SELECT 'DEPRECATED: Use unified_schema.sql instead. This file is kept for reference only.' as warning;
