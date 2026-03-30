-- DEPRECATED: This file's schema has been merged into unified_schema.sql
-- Use unified_schema.sql for fresh installs or run_safe_migration.py for existing databases.
--
-- Live Streams and ML Training Tables
-- These tables are now part of the unified schema with additional columns:
--   - live_streams: added started_at, ended_at, team_id
--   - ml_training: added team_id, progress

SELECT 'DEPRECATED: Use unified_schema.sql instead. This file is kept for reference only.' as warning;
