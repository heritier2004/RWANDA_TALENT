-- MySQL Events for Auto-Updating Live Matches
-- For MariaDB/MySQL

-- Enable event scheduler
SET GLOBAL event_scheduler = ON;

-- Event to update live match status every 15 minutes
-- Use DELIMITER for stored procedures/events

DELIMITER //

CREATE EVENT IF NOT EXISTS update_live_matches
ON SCHEDULE EVERY 15 MINUTE
DO
BEGIN
    -- Update matches that have started
    UPDATE matches 
    SET status = 'live'
    WHERE status = 'scheduled' 
    AND match_date <= NOW()
    AND match_date >= DATE_SUB(NOW(), INTERVAL 2 HOUR);
    
    -- Update matches that have ended (90 minutes after start)
    UPDATE matches
    SET status = 'completed'
    WHERE status = 'live'
    AND DATE_ADD(match_date, INTERVAL 90 MINUTE) <= NOW();
END//

DELIMITER ;

SELECT 'Event created successfully!' as message;
