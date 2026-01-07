// Agent Types
export type AgentType = 'dispatch_checkin' | 'emergency_protocol' | 'custom';

export type VoiceSystem = 'retell' | 'pipecat';

// Pipecat Pipeline Configuration Types
export type STTService = 'deepgram' | 'azure_speech' | 'assemblyai';
export type TTSService = 'eleven_labs' | 'azure_tts' | 'cartesia';
export type LLMService = 'openai' | 'anthropic';
export type TransportType = 'websocket' | 'daily_webrtc';

// Cartesia Voice IDs (verified working voices)
export enum CartesiaVoice {
  ENGLISH_MAN = '47c38ca4-5f35-497b-b1a3-415245fb35e1',
  BRITISH_MAN = '0ad65e7f-006c-47cf-bd31-52279d487913',
  ENGLISH_GIRL = 'e07c00bc-4134-4eae-9ea4-1a55fb45746b',
}

// Nested configuration objects for each service
export interface DeepgramConfig {
  model: string;
  language: string;
  interim_results: boolean;
}

export interface AzureSpeechConfig {
  language: string;
  recognition_mode: string;
}

export interface AssemblyAIConfig {
  language: string;
}

export interface ElevenLabsConfig {
  voice_id: string;
  model_id: string;
  stability: number;
  similarity_boost: number;
  speed: number;
}

export interface AzureTTSConfig {
  voice: string;
  language: string;
  speed: number;
}

export interface CartesiaConfig {
  voice_id: string;
  model_id: string;
  language: string;
  speed: number;
}

export interface OpenAIConfig {
  model: string;
  temperature: number;
  max_tokens?: number;
}

export interface AnthropicConfig {
  model: string;
  temperature: number;
  max_tokens: number;
}

export interface STTConfig {
  service: STTService;
  model?: string;
  deepgram?: DeepgramConfig;
  azure_speech?: AzureSpeechConfig;
  assemblyai?: AssemblyAIConfig;
}

export interface TTSConfig {
  service: TTSService;
  model?: string;
  eleven_labs?: ElevenLabsConfig;
  azure_tts?: AzureTTSConfig;
  cartesia?: CartesiaConfig;
}

export interface LLMConfig {
  service: LLMService;
  model: string;
  openai?: OpenAIConfig;
  anthropic?: AnthropicConfig;
}

export interface PipelineConfig {
  stt_config: STTConfig;
  tts_config: TTSConfig;
  llm_config: LLMConfig;
  transport: TransportType;
  enable_interruptions?: boolean;
  vad_enabled?: boolean;
}

// Cost Breakdown Types
export interface ServiceCost {
  service_name: string;
  model?: string;
  units: number;
  unit_type: string;
  cost_per_unit: number;
  cost_usd: number;
}

export interface CostBreakdown {
  stt_cost?: ServiceCost;
  tts_cost?: ServiceCost;
  llm_cost?: ServiceCost;
  transport_cost?: ServiceCost;
  total_cost_usd: number;
  duration_seconds: number;
}

export interface VoiceSettings {
  voice_id: string;
  voice_speed: number;
  voice_temperature: number;
  volume: number;
  enable_backchannel: boolean;
  backchannel_frequency: number;
  backchannel_words: string[];
  responsiveness: number;
  interruption_sensitivity: number;
  ambient_sound: string | null;
  ambient_sound_volume: number;
  language: string;
  boosted_keywords: string[];

  // New fields for call settings
  enable_background_speech_cancellation?: boolean;
  end_call_after_silence_seconds?: number;
}

export interface AgentState {
  name: string;
  state_prompt: string;
  transitions: Record<string, string>;
  tools: Record<string, unknown>[];
}

export interface Agent {
  id: string;
  name: string;
  description: string | null;
  agent_type: AgentType;
  voice_system: VoiceSystem;
  system_prompt: string;
  voice_settings: VoiceSettings;
  pipeline_config: PipelineConfig | null;
  states: AgentState[];
  starting_state: string | null;
  emergency_triggers: string[];
  is_active: boolean;
  retell_agent_id: string | null;
  retell_llm_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  description?: string;
  agent_type?: AgentType;
  voice_system?: VoiceSystem;
  system_prompt: string;
  voice_settings?: Partial<VoiceSettings>;
  pipeline_config?: PipelineConfig;
  states?: AgentState[];
  starting_state?: string;
  emergency_triggers?: string[];
  is_active?: boolean;
}

export interface AgentUpdate extends Partial<AgentCreate> {}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}

// Call Types
export type CallStatus =
  | 'pending'
  | 'ringing'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'no_answer'
  | 'busy'
  | 'voicemail';

export type CallOutcome =
  | 'In-Transit Update'
  | 'Arrival Confirmation'
  | 'Emergency Escalation'
  | 'Incomplete'
  | 'Unknown';

export type DriverStatus =
  | 'Driving'
  | 'Delayed'
  | 'Arrived'
  | 'Unloading'
  | 'Waiting'
  | 'Unknown';

export type EmergencyType =
  | 'Accident'
  | 'Breakdown'
  | 'Medical'
  | 'Other';

export interface CallTriggerRequest {
  agent_id: string;
  driver_name: string;
  load_number: string;
  origin?: string;
  destination?: string;
  expected_eta?: string;
  additional_context?: Record<string, unknown>;
}

export interface CallResults {
  id: string;
  call_id: string;
  call_outcome: CallOutcome;
  is_emergency: boolean;

  // Routine fields
  driver_status?: DriverStatus;
  current_location?: string;
  eta?: string;
  delay_reason?: string;
  unloading_status?: string;
  pod_reminder_acknowledged?: boolean;

  // Emergency fields
  emergency_type?: EmergencyType;
  safety_status?: string;
  injury_status?: string;
  emergency_location?: string;
  load_secure?: boolean;
  escalation_status?: string;

  raw_extraction?: Record<string, unknown>;
  confidence_score?: number;
  created_at: string;
}

export interface Call {
  id: string;
  agent_id: string;
  retell_call_id: string | null;
  access_token: string | null;
  driver_name: string;
  load_number: string;
  origin: string | null;
  destination: string | null;
  status: CallStatus;
  duration_seconds: number | null;
  transcript: string | null;
  recording_url: string | null;
  created_at: string;
  updated_at: string;
  ended_at: string | null;
  results: CallResults | null;
}

export interface CallListResponse {
  calls: Call[];
  total: number;
}

// API Response wrapper
export interface ApiError {
  detail: string;
}