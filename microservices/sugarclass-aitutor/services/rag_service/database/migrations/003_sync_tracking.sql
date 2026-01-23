-- Sync Tracking Tables for Manual Database-Qdrant Synchronization
-- These tables track what content has been ingested and its sync status

-- Track which files have been ingested
CREATE TABLE IF NOT EXISTS sync_status (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(512) NOT NULL UNIQUE,
    file_hash VARCHAR(64),
    file_size BIGINT,
    last_modified TIMESTAMP,
    chunks_count INTEGER DEFAULT 0,
    embedding_ids TEXT[],
    qdrant_point_count INTEGER DEFAULT 0,
    synced_at TIMESTAMP DEFAULT NOW(),
    sync_status VARCHAR(20) DEFAULT 'synced',  -- 'synced', 'pending', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Track sync events for auditing
CREATE TABLE IF NOT EXISTS sync_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- 'ingest', 'update', 'delete', 'sync_check'
    file_path VARCHAR(512),
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'pending'
    chunks_processed INTEGER DEFAULT 0,
    qdrant_points INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track Qdrant collection status
CREATE TABLE IF NOT EXISTS qdrant_collection_status (
    id SERIAL PRIMARY KEY,
    collection_name VARCHAR(100) NOT NULL UNIQUE,
    point_count INTEGER DEFAULT 0,
    indexed_count INTEGER DEFAULT 0,
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sync_status_file_path ON sync_status(file_path);
CREATE INDEX IF NOT EXISTS idx_sync_status_sync_status ON sync_status(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_status_synced_at ON sync_status(synced_at);
CREATE INDEX IF NOT EXISTS idx_sync_events_file_path ON sync_events(file_path);
CREATE INDEX IF NOT EXISTS idx_sync_events_event_type ON sync_events(event_type);
CREATE INDEX IF NOT EXISTS idx_sync_events_created_at ON sync_events(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_sync_status_updated_at BEFORE UPDATE ON sync_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_qdrant_collection_status_updated_at BEFORE UPDATE ON qdrant_collection_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial Qdrant collection status
INSERT INTO qdrant_collection_status (collection_name, point_count, indexed_count, last_synced)
VALUES ('aitutor_documents', 0, 0, NULL)
ON CONFLICT (collection_name) DO NOTHING;

COMMENT ON TABLE sync_status IS 'Tracks which files have been ingested and their sync status';
COMMENT ON TABLE sync_events IS 'Logs all sync events for auditing';
COMMENT ON TABLE qdrant_collection_status IS 'Tracks Qdrant collection point counts';
