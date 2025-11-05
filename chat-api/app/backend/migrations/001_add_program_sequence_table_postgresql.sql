-- ============================================================================
-- Migration: Add PROGRAM_SEQUENCE Table (PostgreSQL)
-- Created: 2025-11-05
-- Purpose: 프로그램 ID 자동 생성을 위한 시퀀스 테이블 추가
-- ============================================================================

-- 1. PROGRAM_SEQUENCE 테이블 생성
CREATE TABLE IF NOT EXISTS PROGRAM_SEQUENCE (
    ID INT NOT NULL DEFAULT 1,
    LAST_NUMBER INT NOT NULL DEFAULT 0,
    UPDATE_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ID),
    CONSTRAINT chk_single_row CHECK (ID = 1)
);

-- 2. 컬럼 주석 추가
COMMENT ON COLUMN PROGRAM_SEQUENCE.ID IS '고정 ID (항상 1)';
COMMENT ON COLUMN PROGRAM_SEQUENCE.LAST_NUMBER IS '마지막 생성된 번호';
COMMENT ON COLUMN PROGRAM_SEQUENCE.UPDATE_DT IS '마지막 업데이트 일시';
COMMENT ON TABLE PROGRAM_SEQUENCE IS '프로그램 ID 자동 생성용 시퀀스 테이블';

-- 3. UPDATE_DT 자동 업데이트 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_program_sequence_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.UPDATE_DT = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. 트리거 생성
DROP TRIGGER IF EXISTS trg_program_sequence_update ON PROGRAM_SEQUENCE;
CREATE TRIGGER trg_program_sequence_update
    BEFORE UPDATE ON PROGRAM_SEQUENCE
    FOR EACH ROW
    EXECUTE FUNCTION update_program_sequence_timestamp();

-- 5. 초기 데이터 삽입
INSERT INTO PROGRAM_SEQUENCE (ID, LAST_NUMBER)
VALUES (1, 0)
ON CONFLICT (ID) DO NOTHING;

-- 6. 확인 쿼리
SELECT 
    ID,
    LAST_NUMBER,
    UPDATE_DT,
    CONCAT('PGM_', LAST_NUMBER + 1) AS NEXT_PGM_ID
FROM PROGRAM_SEQUENCE;

-- ============================================================================
-- 사용 예시:
-- ============================================================================
-- 
-- 1. 다음 PGM_ID 생성:
--    UPDATE PROGRAM_SEQUENCE SET LAST_NUMBER = LAST_NUMBER + 1 WHERE ID = 1;
--    SELECT CONCAT('PGM_', LAST_NUMBER) FROM PROGRAM_SEQUENCE WHERE ID = 1;
--    결과: PGM_1, PGM_2, PGM_3 ...
--
-- 2. 현재 번호 조회:
--    SELECT LAST_NUMBER FROM PROGRAM_SEQUENCE WHERE ID = 1;
--
-- 3. 초기화 (테스트 환경만!):
--    UPDATE PROGRAM_SEQUENCE SET LAST_NUMBER = 0 WHERE ID = 1;
--
-- ============================================================================

-- 완료 메시지
SELECT '✅ PROGRAM_SEQUENCE 테이블이 성공적으로 생성되었습니다.' AS Status;
