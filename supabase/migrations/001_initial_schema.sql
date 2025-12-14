-- AI Voice Agent Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    agent_type VARCHAR(50) NOT NULL DEFAULT 'custom',
    system_prompt TEXT NOT NULL,
    begin_message TEXT,
    voice_settings JSONB NOT NULL DEFAULT '{}',
    states JSONB DEFAULT '[]',
    starting_state VARCHAR(100),
    emergency_triggers TEXT[] DEFAULT ARRAY['accident', 'blowout', 'emergency', 'breakdown', 'medical', 'help'],
    is_active BOOLEAN DEFAULT true,
    retell_agent_id VARCHAR(100),
    retell_llm_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on retell_agent_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_agents_retell_agent_id ON agents(retell_agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active);

-- Calls table
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    retell_call_id VARCHAR(100),
    access_token TEXT,
    driver_name VARCHAR(100) NOT NULL,
    load_number VARCHAR(50) NOT NULL,
    origin VARCHAR(200),
    destination VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    duration_seconds INTEGER,
    transcript TEXT,
    recording_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_calls_retell_call_id ON calls(retell_call_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent_id ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);

-- Call results table (structured extraction)
CREATE TABLE IF NOT EXISTS call_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    call_outcome VARCHAR(50) NOT NULL,
    is_emergency BOOLEAN DEFAULT false,

    -- Routine call fields
    driver_status VARCHAR(50),
    current_location TEXT,
    eta VARCHAR(100),
    delay_reason TEXT,
    unloading_status TEXT,
    pod_reminder_acknowledged BOOLEAN,

    -- Emergency call fields
    emergency_type VARCHAR(50),
    safety_status TEXT,
    injury_status TEXT,
    emergency_location TEXT,
    load_secure BOOLEAN,
    escalation_status VARCHAR(100),

    -- Metadata
    raw_extraction JSONB,
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for call_id lookup
CREATE INDEX IF NOT EXISTS idx_call_results_call_id ON call_results(call_id);
CREATE INDEX IF NOT EXISTS idx_call_results_is_emergency ON call_results(is_emergency);

-- Prompts table (for versioning and history)
CREATE TABLE IF NOT EXISTS prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    system_prompt TEXT NOT NULL,
    begin_message TEXT,
    states JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Create index for agent prompt history
CREATE INDEX IF NOT EXISTS idx_prompts_agent_id ON prompts(agent_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_agent_version ON prompts(agent_id, version);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
-- Enable RLS on all tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;

-- For now, allow all authenticated users full access
-- In production, you'd want more granular policies
CREATE POLICY "Allow all for authenticated users" ON agents
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON calls
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON call_results
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON prompts
    FOR ALL USING (true);

-- Also allow service role key (backend) full access
CREATE POLICY "Allow service role" ON agents
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role" ON calls
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role" ON call_results
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role" ON prompts
    FOR ALL USING (auth.role() = 'service_role');

-- Comments for documentation
COMMENT ON TABLE agents IS 'Voice agent configurations including prompts and voice settings';
COMMENT ON TABLE calls IS 'Call records with metadata and transcripts';
COMMENT ON TABLE call_results IS 'Structured data extracted from call transcripts';
COMMENT ON TABLE prompts IS 'Prompt version history for agents';

COMMENT ON COLUMN agents.voice_settings IS 'JSON object containing voice configuration (speed, backchannel, etc.)';
COMMENT ON COLUMN agents.states IS 'JSON array of conversation states for multi-state flows';
COMMENT ON COLUMN calls.status IS 'pending, ringing, in_progress, completed, failed, no_answer, busy, voicemail';
COMMENT ON COLUMN call_results.call_outcome IS 'In-Transit Update, Arrival Confirmation, Emergency Escalation, Incomplete, Unknown';