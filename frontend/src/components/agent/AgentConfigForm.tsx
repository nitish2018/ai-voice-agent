import React, { useState } from 'react';
import { Settings, Save, Loader2, Volume2, Mic, Zap, VolumeX, Clock, Cpu, Radio } from 'lucide-react';
import {
  Button,
  Input,
  Textarea,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from '@/components/ui';
import { agentApi } from '@/lib/api';
import type { Agent, AgentCreate, VoiceSettings, VoiceSystem, PipelineConfig } from '@/types';

interface AgentConfigFormProps {
  agent?: Agent;
  onSaved: (agent: Agent) => void;
}

const defaultVoiceSettings: VoiceSettings = {
  voice_id: '11labs-Adrian',
  voice_speed: 1.0,
  voice_temperature: 0.8,
  volume: 1.0,
  enable_backchannel: true,
  backchannel_frequency: 0.8,
  backchannel_words: ['yeah', 'uh-huh', 'I see', 'right', 'okay'],
  responsiveness: 0.8,
  interruption_sensitivity: 0.7,
  ambient_sound: 'call-center',
  ambient_sound_volume: 0.2,
  language: 'en-US',
  boosted_keywords: [],
  enable_background_speech_cancellation: false,
  end_call_after_silence_seconds: 30.0,
};

export function AgentConfigForm({ agent, onSaved }: AgentConfigFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<AgentCreate>({
    name: agent?.name || '',
    description: agent?.description || '',
    voice_system: (agent?.voice_system as VoiceSystem) || 'retell',
    system_prompt: agent?.system_prompt || '',
    voice_settings: agent?.voice_settings || defaultVoiceSettings,
    pipeline_config: agent?.pipeline_config || {
      stt_config: {
        service: 'deepgram',
        deepgram: {
          model: 'nova-2',
          language: 'en-US',
          interim_results: true
        }
      },
      tts_config: {
        service: 'cartesia',
        cartesia: {
          voice_id: '0ad65e7f-006c-47cf-bd31-52279d487913', // British Man
          model_id: 'sonic-english',
          language: 'en',
          speed: 1.0
        }
      },
      llm_config: {
        service: 'openai',
        openai: {
          model: 'gpt-4o',
          temperature: 0.7
        }
      },
      transport: 'daily_webrtc',
      enable_interruptions: true,
      vad_enabled: true,
    },
    emergency_triggers: agent?.emergency_triggers || [
      'accident', 'blowout', 'emergency', 'breakdown', 'medical', 'help'
    ],
    is_active: agent?.is_active ?? true,
  });

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;

    // Special handling for voice_settings fields (but not voice_system!)
    if (name.startsWith('voice_') && name !== 'voice_system') {
      const voiceKey = name.replace('voice_', '') as keyof VoiceSettings;
      setFormData(prev => ({
        ...prev,
        voice_settings: {
          ...prev.voice_settings!,
          [voiceKey]: type === 'number' ? parseFloat(value) :
                      type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
        },
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
      }));
    }
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError('Agent name is required');
      return;
    }
    if (!formData.system_prompt.trim()) {
      setError('System prompt is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let savedAgent: Agent;

      if (agent) {
        savedAgent = await agentApi.update(agent.id, formData);
      } else {
        savedAgent = await agentApi.create(formData);
      }

      onSaved(savedAgent);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save agent');
    } finally {
      setIsLoading(false);
    }
  };

  const voiceSettings = formData.voice_settings!;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Agent Configuration
          </CardTitle>
          <CardDescription>
            Configure the agent's identity and core behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="name" className="form-label">Agent Name *</label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="e.g., Logistics Dispatch Agent"
              required
            />
          </div>

          <div>
            <label htmlFor="description" className="form-label">Description</label>
            <Textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Brief description of what this agent does..."
              rows={2}
            />
          </div>

          <div>
            <label htmlFor="voice_system" className="form-label">Voice System *</label>
            <select
              id="voice_system"
              name="voice_system"
              value={formData.voice_system}
              onChange={handleInputChange}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="retell">Retell AI</option>
              <option value="pipecat">Pipecat</option>
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              {formData.voice_system === 'pipecat' 
                ? 'Pipecat: Multi-service voice framework with flexible STT/TTS/LLM providers'
                : 'Retell AI: Managed voice infrastructure with built-in LLM'}
            </p>
          </div>

          <div>
            <label htmlFor="system_prompt" className="form-label">System Prompt *</label>
            <Textarea
              id="system_prompt"
              name="system_prompt"
              value={formData.system_prompt}
              onChange={handleInputChange}
              placeholder="You are a friendly dispatch coordinator..."
              rows={10}
              className="font-mono text-sm"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              Use {"{{driver_name}}"}, {"{{load_number}}"}, etc. for dynamic variables
            </p>
          </div>

        </CardContent>
      </Card>

      {/* Pipecat Pipeline Configuration */}
      {formData.voice_system === 'pipecat' && formData.pipeline_config && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Radio className="w-5 h-5" />
              Pipecat Pipeline Configuration
            </CardTitle>
            <CardDescription>
              Configure STT, TTS, LLM services and transport for Pipecat
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* STT Configuration */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Mic className="w-4 h-4" />
                Speech-to-Text (STT)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">STT Service</label>
                  <select
                    value={formData.pipeline_config.stt_config.service}
                    onChange={(e) => {
                      const service = e.target.value as any;
                      const defaultModel = service === 'deepgram' ? 'nova-2' : service === 'azure_speech' ? 'en-US' : 'best';
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          stt_config: {
                            service,
                            deepgram: service === 'deepgram' ? { model: defaultModel, language: 'en-US', interim_results: true } : prev.pipeline_config!.stt_config.deepgram,
                            azure_speech: service === 'azure_speech' ? { language: 'en-US', recognition_mode: 'conversation' } : prev.pipeline_config!.stt_config.azure_speech,
                            assemblyai: service === 'assemblyai' ? { language: 'en_us' } : prev.pipeline_config!.stt_config.assemblyai
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="deepgram">Deepgram</option>
                    <option value="azure_speech">Azure Speech</option>
                    <option value="assemblyai">AssemblyAI</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Model</label>
                  <select
                    value={
                      formData.pipeline_config.stt_config.service === 'deepgram' 
                        ? formData.pipeline_config.stt_config.deepgram?.model || 'nova-2'
                        : formData.pipeline_config.stt_config.service === 'azure_speech'
                        ? formData.pipeline_config.stt_config.azure_speech?.language || 'en-US'
                        : 'best'
                    }
                    onChange={(e) => {
                      const service = formData.pipeline_config.stt_config.service;
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          stt_config: {
                            ...prev.pipeline_config!.stt_config,
                            deepgram: service === 'deepgram' ? { ...prev.pipeline_config!.stt_config.deepgram!, model: e.target.value } : prev.pipeline_config!.stt_config.deepgram,
                            azure_speech: service === 'azure_speech' ? { ...prev.pipeline_config!.stt_config.azure_speech!, language: e.target.value } : prev.pipeline_config!.stt_config.azure_speech,
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {formData.pipeline_config.stt_config.service === 'deepgram' && (
                      <>
                        <option value="nova-2">Nova 2 (Latest)</option>
                        <option value="nova">Nova</option>
                        <option value="enhanced">Enhanced</option>
                        <option value="base">Base</option>
                      </>
                    )}
                    {formData.pipeline_config.stt_config.service === 'azure_speech' && (
                      <>
                        <option value="en-US">English (US)</option>
                        <option value="en-GB">English (UK)</option>
                        <option value="es-ES">Spanish</option>
                        <option value="fr-FR">French</option>
                      </>
                    )}
                    {formData.pipeline_config.stt_config.service === 'assemblyai' && (
                      <>
                        <option value="best">Best</option>
                        <option value="nano">Nano (Fast)</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
            </div>

            {/* TTS Configuration */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Volume2 className="w-4 h-4" />
                Text-to-Speech (TTS)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">TTS Service</label>
                  <select
                    value={formData.pipeline_config.tts_config.service}
                    onChange={(e) => {
                      const service = e.target.value as any;
                      const defaults = {
                        cartesia: { voice_id: '0ad65e7f-006c-47cf-bd31-52279d487913', model_id: 'sonic-english', language: 'en', speed: 1.0 }, // British Man
                        eleven_labs: { voice_id: '21m00Tcm4TlvDq8ikWAM', model_id: 'eleven_turbo_v2_5', stability: 0.5, similarity_boost: 0.75, speed: 1.0 },
                        azure_tts: { voice: 'en-US-AriaNeural', language: 'en-US', speed: 1.0 }
                      };
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          tts_config: {
                            service,
                            cartesia: service === 'cartesia' ? defaults.cartesia : prev.pipeline_config!.tts_config.cartesia,
                            eleven_labs: service === 'eleven_labs' ? defaults.eleven_labs : prev.pipeline_config!.tts_config.eleven_labs,
                            azure_tts: service === 'azure_tts' ? defaults.azure_tts : prev.pipeline_config!.tts_config.azure_tts
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="cartesia">Cartesia</option>
                    <option value="eleven_labs">ElevenLabs</option>
                    <option value="azure_tts">Azure TTS</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Voice</label>
                  <select
                    value={
                      formData.pipeline_config.tts_config.service === 'cartesia'
                        ? formData.pipeline_config.tts_config.cartesia?.voice_id || '79a125e8-cd45-4c13-8a67-188112f4dd22'
                        : formData.pipeline_config.tts_config.service === 'eleven_labs'
                        ? formData.pipeline_config.tts_config.eleven_labs?.voice_id || '21m00Tcm4TlvDq8ikWAM'
                        : formData.pipeline_config.tts_config.azure_tts?.voice || 'en-US-AriaNeural'
                    }
                    onChange={(e) => {
                      const service = formData.pipeline_config.tts_config.service;
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          tts_config: {
                            ...prev.pipeline_config!.tts_config,
                            cartesia: service === 'cartesia' ? { ...prev.pipeline_config!.tts_config.cartesia!, voice_id: e.target.value } : prev.pipeline_config!.tts_config.cartesia,
                            eleven_labs: service === 'eleven_labs' ? { ...prev.pipeline_config!.tts_config.eleven_labs!, voice_id: e.target.value } : prev.pipeline_config!.tts_config.eleven_labs,
                            azure_tts: service === 'azure_tts' ? { ...prev.pipeline_config!.tts_config.azure_tts!, voice: e.target.value } : prev.pipeline_config!.tts_config.azure_tts
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {formData.pipeline_config.tts_config.service === 'cartesia' && (
                      <>
                        <option value="47c38ca4-5f35-497b-b1a3-415245fb35e1">English Man</option>
                        <option value="0ad65e7f-006c-47cf-bd31-52279d487913">British Man</option>
                        <option value="e07c00bc-4134-4eae-9ea4-1a55fb45746b">English Girl</option>
                      </>
                    )}
                    {formData.pipeline_config.tts_config.service === 'eleven_labs' && (
                      <>
                        <option value="21m00Tcm4TlvDq8ikWAM">Rachel (Female)</option>
                        <option value="AZnzlk1XvdvUeBnXmlld">Domi (Female)</option>
                        <option value="EXAVITQu4vr4xnSDxMaL">Bella (Female)</option>
                        <option value="ErXwobaYiN019PkySvjV">Antoni (Male)</option>
                        <option value="MF3mGyEYCl7XYWbV9V6O">Elli (Female)</option>
                        <option value="TxGEqnHWrfWFTfGW9XjX">Josh (Male)</option>
                        <option value="VR6AewLTigWG4xSOukaG">Arnold (Male)</option>
                        <option value="pNInz6obpgDQGcFmaJgB">Adam (Male)</option>
                      </>
                    )}
                    {formData.pipeline_config.tts_config.service === 'azure_tts' && (
                      <>
                        <option value="en-US-AriaNeural">Aria (Female)</option>
                        <option value="en-US-JennyNeural">Jenny (Female)</option>
                        <option value="en-US-GuyNeural">Guy (Male)</option>
                        <option value="en-GB-SoniaNeural">Sonia (UK Female)</option>
                        <option value="en-GB-RyanNeural">Ryan (UK Male)</option>
                      </>
                    )}
                  </select>
                </div>
                <div>
                  <label className="form-label">Model</label>
                  <select
                    value={
                      formData.pipeline_config.tts_config.service === 'cartesia'
                        ? formData.pipeline_config.tts_config.cartesia?.model_id || 'sonic-english'
                        : formData.pipeline_config.tts_config.service === 'eleven_labs'
                        ? formData.pipeline_config.tts_config.eleven_labs?.model_id || 'eleven_turbo_v2_5'
                        : 'standard'
                    }
                    onChange={(e) => {
                      const service = formData.pipeline_config.tts_config.service;
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          tts_config: {
                            ...prev.pipeline_config!.tts_config,
                            cartesia: service === 'cartesia' ? { ...prev.pipeline_config!.tts_config.cartesia!, model_id: e.target.value } : prev.pipeline_config!.tts_config.cartesia,
                            eleven_labs: service === 'eleven_labs' ? { ...prev.pipeline_config!.tts_config.eleven_labs!, model_id: e.target.value } : prev.pipeline_config!.tts_config.eleven_labs,
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {formData.pipeline_config.tts_config.service === 'cartesia' && (
                      <>
                        <option value="sonic-english">Sonic English</option>
                        <option value="sonic-multilingual">Sonic Multilingual</option>
                      </>
                    )}
                    {formData.pipeline_config.tts_config.service === 'eleven_labs' && (
                      <>
                        <option value="eleven_turbo_v2_5">Turbo v2.5 (Fastest)</option>
                        <option value="eleven_turbo_v2">Turbo v2</option>
                        <option value="eleven_monolingual_v1">Monolingual v1</option>
                        <option value="eleven_multilingual_v2">Multilingual v2</option>
                      </>
                    )}
                    {formData.pipeline_config.tts_config.service === 'azure_tts' && (
                      <>
                        <option value="standard">Standard</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
              
              {/* TTS Speed Slider */}
              <div className="mt-4">
                <label className="form-label">
                  Speech Speed ({
                    formData.pipeline_config.tts_config.service === 'cartesia'
                      ? (formData.pipeline_config.tts_config.cartesia?.speed || 1.0).toFixed(2)
                      : formData.pipeline_config.tts_config.service === 'eleven_labs'
                      ? (formData.pipeline_config.tts_config.eleven_labs?.speed || 1.0).toFixed(2)
                      : (formData.pipeline_config.tts_config.azure_tts?.speed || 1.0).toFixed(2)
                  }x)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={
                    formData.pipeline_config.tts_config.service === 'cartesia'
                      ? formData.pipeline_config.tts_config.cartesia?.speed || 1.0
                      : formData.pipeline_config.tts_config.service === 'eleven_labs'
                      ? formData.pipeline_config.tts_config.eleven_labs?.speed || 1.0
                      : formData.pipeline_config.tts_config.azure_tts?.speed || 1.0
                  }
                  onChange={(e) => {
                    const speed = parseFloat(e.target.value);
                    const service = formData.pipeline_config.tts_config.service;
                    setFormData(prev => ({
                      ...prev,
                      pipeline_config: {
                        ...prev.pipeline_config!,
                        tts_config: {
                          ...prev.pipeline_config!.tts_config,
                          cartesia: service === 'cartesia' ? { ...prev.pipeline_config!.tts_config.cartesia!, speed } : prev.pipeline_config!.tts_config.cartesia,
                          eleven_labs: service === 'eleven_labs' ? { ...prev.pipeline_config!.tts_config.eleven_labs!, speed } : prev.pipeline_config!.tts_config.eleven_labs,
                          azure_tts: service === 'azure_tts' ? { ...prev.pipeline_config!.tts_config.azure_tts!, speed } : prev.pipeline_config!.tts_config.azure_tts
                        }
                      }
                    }));
                  }}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0.5x (Slower)</span>
                  <span>1.0x (Normal)</span>
                  <span>2.0x (Faster)</span>
                </div>
              </div>
            </div>

            {/* LLM Configuration */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                Language Model (LLM)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">LLM Service</label>
                  <select
                    value={formData.pipeline_config.llm_config.service}
                    onChange={(e) => {
                      const service = e.target.value as any;
                      const defaultModel = service === 'openai' ? 'gpt-4o' : 'claude-3-5-sonnet-20241022';
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          llm_config: {
                            service,
                            model: defaultModel,
                            openai: service === 'openai' ? { model: defaultModel, temperature: 0.7 } : prev.pipeline_config!.llm_config.openai,
                            anthropic: service === 'anthropic' ? { model: defaultModel, temperature: 0.7, max_tokens: 1024 } : prev.pipeline_config!.llm_config.anthropic
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Model</label>
                  <select
                    value={formData.pipeline_config.llm_config.model}
                    onChange={(e) => {
                      const service = formData.pipeline_config.llm_config.service;
                      setFormData(prev => ({
                        ...prev,
                        pipeline_config: {
                          ...prev.pipeline_config!,
                          llm_config: {
                            ...prev.pipeline_config!.llm_config,
                            model: e.target.value,
                            openai: service === 'openai' ? { ...prev.pipeline_config!.llm_config.openai!, model: e.target.value } : prev.pipeline_config!.llm_config.openai,
                            anthropic: service === 'anthropic' ? { ...prev.pipeline_config!.llm_config.anthropic!, model: e.target.value } : prev.pipeline_config!.llm_config.anthropic
                          }
                        }
                      }));
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {formData.pipeline_config.llm_config.service === 'openai' && (
                      <>
                        <option value="gpt-4o">GPT-4o (Latest)</option>
                        <option value="gpt-4o-mini">GPT-4o Mini (Faster)</option>
                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                      </>
                    )}
                    {formData.pipeline_config.llm_config.service === 'anthropic' && (
                      <>
                        <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet (Latest)</option>
                        <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku (Faster)</option>
                        <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                        <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                        <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
            </div>

            {/* Transport Configuration */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Radio className="w-4 h-4" />
                Transport
              </h4>
              <div>
                <select
                  value={formData.pipeline_config.transport}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    pipeline_config: {
                      ...prev.pipeline_config!,
                      transport: e.target.value as any
                    }
                  }))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="daily_webrtc">Daily.co WebRTC (Recommended)</option>
                  <option value="websocket">WebSocket</option>
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  WebRTC provides better audio quality and lower latency
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Voice Settings */}
      {formData.voice_system === 'retell' && (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            Voice Settings
          </CardTitle>
          <CardDescription>
            Configure voice characteristics for a natural conversation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="voice_voice_speed" className="form-label">
                Voice Speed ({voiceSettings.voice_speed})
              </label>
              <input
                type="range"
                id="voice_voice_speed"
                name="voice_voice_speed"
                min="0.5"
                max="2"
                step="0.1"
                value={voiceSettings.voice_speed}
                onChange={handleInputChange}
                className="w-full"
              />
            </div>

            <div>
              <label htmlFor="voice_responsiveness" className="form-label">
                Responsiveness ({voiceSettings.responsiveness})
              </label>
              <input
                type="range"
                id="voice_responsiveness"
                name="voice_responsiveness"
                min="0"
                max="1"
                step="0.1"
                value={voiceSettings.responsiveness}
                onChange={handleInputChange}
                className="w-full"
              />
            </div>

            <div>
              <label htmlFor="voice_interruption_sensitivity" className="form-label">
                Interruption Sensitivity ({voiceSettings.interruption_sensitivity})
              </label>
              <input
                type="range"
                id="voice_interruption_sensitivity"
                name="voice_interruption_sensitivity"
                min="0"
                max="1"
                step="0.1"
                value={voiceSettings.interruption_sensitivity}
                onChange={handleInputChange}
                className="w-full"
              />
            </div>
          </div>

          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                name="voice_enable_backchannel"
                checked={voiceSettings.enable_backchannel}
                onChange={handleInputChange}
                className="rounded"
              />
              <Mic className="w-4 h-4" />
              <span className="text-sm">Enable Backchanneling</span>
            </label>
            <p className="text-xs text-muted-foreground">
              Agent uses "uh-huh", "yeah" to show active listening
            </p>
          </div>

          {voiceSettings.enable_backchannel && (
            <div>
              <label htmlFor="voice_backchannel_frequency" className="form-label">
                Backchannel Frequency ({voiceSettings.backchannel_frequency})
              </label>
              <input
                type="range"
                id="voice_backchannel_frequency"
                name="voice_backchannel_frequency"
                min="0"
                max="1"
                step="0.1"
                value={voiceSettings.backchannel_frequency}
                onChange={handleInputChange}
                className="w-full"
              />
            </div>
          )}
        </CardContent>
      </Card>
      )}

      {/* Call Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Call Settings
          </CardTitle>
          <CardDescription>
            Configure call behavior and noise handling
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Background Speech Cancellation */}
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                name="voice_enable_background_speech_cancellation"
                checked={voiceSettings.enable_background_speech_cancellation ?? false}
                onChange={handleInputChange}
                className="rounded"
              />
              <VolumeX className="w-4 h-4" />
              <span className="text-sm">Enable Background Speech Cancellation</span>
            </label>
            <p className="text-xs text-muted-foreground">
              Filters out background conversations and noise during the call
            </p>
          </div>

          {/* End Call After Silence */}
          <div>
            <label htmlFor="voice_end_call_after_silence_seconds" className="form-label">
              End Call After Unresponsiveness (Seconds)
            </label>
            <div className="flex items-center gap-3">
              <Input
                type="number"
                id="voice_end_call_after_silence_seconds"
                name="voice_end_call_after_silence_seconds"
                min="10"
                max="120"
                value={voiceSettings.end_call_after_silence_seconds ?? 30}
                onChange={handleInputChange}
                className="w-32"
              />
              <span className="text-sm text-muted-foreground">seconds</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Automatically end the call if no speech is detected for this duration (10-120 seconds)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Emergency Triggers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Emergency Protocol
          </CardTitle>
          <CardDescription>
            Words/phrases that trigger emergency handling
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div>
            <label htmlFor="emergency_triggers" className="form-label">
              Emergency Trigger Words
            </label>
            <Input
              id="emergency_triggers"
              name="emergency_triggers"
              value={formData.emergency_triggers?.join(', ')}
              onChange={(e) => {
                setFormData(prev => ({
                  ...prev,
                  emergency_triggers: e.target.value.split(',').map(s => s.trim()).filter(Boolean),
                }));
              }}
              placeholder="accident, blowout, emergency, breakdown..."
            />
            <p className="text-xs text-muted-foreground mt-1">
              Comma-separated list of words that trigger emergency protocol
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Error & Submit */}
      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Saving...
          </>
        ) : (
          <>
            <Save className="w-4 h-4 mr-2" />
            {agent ? 'Update Agent' : 'Create Agent'}
          </>
        )}
      </Button>
    </form>
  );
}