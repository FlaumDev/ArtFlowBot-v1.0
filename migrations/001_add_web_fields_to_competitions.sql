BEGIN;

-- Add optional web fields for future ArtFlowWeb pages.
ALTER TABLE competitions
    ADD COLUMN IF NOT EXISTS event_date DATE,
    ADD COLUMN IF NOT EXISTS application_deadline DATE,
    ADD COLUMN IF NOT EXISTS city TEXT,
    ADD COLUMN IF NOT EXISTS short_description TEXT,
    ADD COLUMN IF NOT EXISTS directions TEXT,
    ADD COLUMN IF NOT EXISTS poster_url TEXT,
    ADD COLUMN IF NOT EXISTS rules_url TEXT,
    ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Keep existing competitions hidden from the website until published explicitly.
COMMIT;
