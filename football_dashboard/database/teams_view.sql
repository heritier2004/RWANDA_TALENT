-- Teams View for AI Statistics Compatibility
-- This view provides a unified 'teams' reference that combines clubs, academies, and schools
-- Run this script after the main database is set up

-- Drop existing view if exists
DROP VIEW IF EXISTS teams;

-- Create unified teams view
CREATE OR REPLACE VIEW teams AS
SELECT 
    id,
    name,
    'club' as team_type,
    created_at
FROM clubs
UNION ALL
SELECT 
    id,
    name,
    'academy' as team_type,
    created_at
FROM academies
UNION ALL
SELECT 
    id,
    name,
    'school' as team_type,
    created_at
FROM schools;

SELECT 'Teams view created successfully!' as message;
