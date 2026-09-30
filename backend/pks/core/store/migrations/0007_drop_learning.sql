-- Drop the learning-evidence groundwork from 0006. The 2026-09-30 rescope
-- (SPEC v2.0) removed the learning model it was collecting evidence for, and
-- nothing ever read these rows. 0006 stays so existing databases migrate in
-- order.

DROP INDEX IF EXISTS idx_learning_kind;
DROP INDEX IF EXISTS idx_learning_subject;
DROP TABLE IF EXISTS learning_events;
