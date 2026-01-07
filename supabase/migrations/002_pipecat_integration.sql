-- Migration: Add Pipecat support to agents table
-- This migration adds voice_system and pipeline_config columns to support Pipecat voice framework

-- Add voice_system column to agents table
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS voice_system TEXT DEFAULT 'retell' CHECK (voice_system IN ('retell', 'pipecat'));

-- Add pipeline_config column for Pipecat configuration
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS pipeline_config JSONB;

-- Add comment for documentation
COMMENT ON COLUMN agents.voice_system IS 'Voice system backend: retell or pipecat';
COMMENT ON COLUMN agents.pipeline_config IS 'Pipecat pipeline configuration (STT, TTS, LLM, Transport)';

-- Update existing agents to have retell as voice_system (for backward compatibility)
UPDATE agents
SET voice_system = 'retell'
WHERE voice_system IS NULL;

-- Create index on voice_system for faster filtering
CREATE INDEX IF NOT EXISTS idx_agents_voice_system ON agents(voice_system);
