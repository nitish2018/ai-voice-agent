import React, { useState } from 'react';
import { Settings, Save, Loader2, Volume2, Mic, Zap, VolumeX, Clock } from 'lucide-react';
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
import type { Agent, AgentCreate, VoiceSettings } from '@/types';

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
    system_prompt: agent?.system_prompt || '',
    begin_message: agent?.begin_message || '',
    voice_settings: agent?.voice_settings || defaultVoiceSettings,
    emergency_triggers: agent?.emergency_triggers || [
      'accident', 'blowout', 'emergency', 'breakdown', 'medical', 'help'
    ],
    is_active: agent?.is_active ?? true,
  });

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;

    if (name.startsWith('voice_')) {
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

          <div>
            <label htmlFor="begin_message" className="form-label">Opening Message</label>
            <Input
              id="begin_message"
              name="begin_message"
              value={formData.begin_message}
              onChange={handleInputChange}
              placeholder="Hi, this is Dispatch calling about your load..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Voice Settings */}
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