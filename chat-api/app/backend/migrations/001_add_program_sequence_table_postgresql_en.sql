-- ============================================================================
-- Migration: Add PROGRAM_SEQUENCE Table (PostgreSQL)
-- Created: 2025-11-05
-- Purpose: Sequence table for automatic program ID generation
-- ============================================================================

-- 1. Create PROGRAM_SEQUENCE table
CREATE TABLE IF NOT EXISTS PROGRAM_SEQUENCE (
    ID INT NOT NULL DEFAULT 1,
    LAST_NUMBER INT NOT NULL DEFAULT 0,
    UPDATE_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ID),
    CONSTRAINT chk_single_row CHECK (ID = 1)
);

-- 2. Add column comments
COMMENT ON COLUMN PROGRAM_SEQUENCE.ID IS 'Fixed ID (always 1)';
COMMENT ON COLUMN PROGRAM_SEQUENCE.LAST_NUMBER IS 'Last generated number';
COMMENT ON COLUMN PROGRAM_SEQUENCE.UPDATE_DT IS 'Last update timestamp';
COMMENT ON TABLE PROGRAM_SEQUENCE IS 'Sequence table for automatic program ID generation';

-- 3. Create trigger function for UPDATE_DT auto-update
CREATE OR REPLACE FUNCTION update_program_sequence_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.UPDATE_DT = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create trigger
DROP TRIGGER IF EXISTS trg_program_sequence_update ON PROGRAM_SEQUENCE;
CREATE TRIGGER trg_program_sequence_update
    BEFORE UPDATE ON PROGRAM_SEQUENCE
    FOR EACH ROW
    EXECUTE FUNCTION update_program_sequence_timestamp();

-- 5. Insert initial data
INSERT INTO PROGRAM_SEQUENCE (ID, LAST_NUMBER)
VALUES (1, 0)
ON CONFLICT (ID) DO NOTHING;

-- 6. Verification query
SELECT 
    ID,
    LAST_NUMBER,
    UPDATE_DT,
    CONCAT('PGM_', LAST_NUMBER + 1) AS NEXT_PGM_ID
FROM PROGRAM_SEQUENCE;

-- ============================================================================
-- Usage Examples:
-- ============================================================================
-- 
-- 1. Generate next PGM_ID:
--    UPDATE PROGRAM_SEQUENCE SET LAST_NUMBER = LAST_NUMBER + 1 WHERE ID = 1;
--    SELECT CONCAT('PGM_', LAST_NUMBER) FROM PROGRAM_SEQUENCE WHERE ID = 1;
--    Result: PGM_1, PGM_2, PGM_3 ...
--
-- 2. Get current number:
--    SELECT LAST_NUMBER FROM PROGRAM_SEQUENCE WHERE ID = 1;
--
-- 3. Reset sequence (test environment only!):
--    UPDATE PROGRAM_SEQUENCE SET LAST_NUMBER = 0 WHERE ID = 1;
--
-- ============================================================================

-- Completion message
SELECT 'PROGRAM_SEQUENCE table created successfully!' AS Status;
