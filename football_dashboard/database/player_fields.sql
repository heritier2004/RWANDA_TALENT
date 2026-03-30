-- DEPRECATED: This file's schema has been merged into unified_schema.sql
-- Use unified_schema.sql for fresh installs or run_safe_migration.py for existing databases.
--
-- Enhanced Player Table Fields
-- These columns are now part of the unified players table:
--   district, sector, cell, village
--
-- NOTE: The unified schema uses:
--   - height_cm (not 'height')
--   - weight_kg (not 'weight')
--   - photo_url (not 'photo')
--   - status (not 'player_status')
--   - nationality and dob are already in the main schema

SELECT 'DEPRECATED: Use unified_schema.sql instead. This file is kept for reference only.' as warning;
