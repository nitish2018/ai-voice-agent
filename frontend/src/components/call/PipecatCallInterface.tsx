import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';
import { DailyTransport } from '@pipecat-ai/daily-transport';
import {
  PipecatClientProvider,
  usePipecatClient,
  usePipecatClientTransportState,
  PipecatClientAudio,
} from '@pipecat-ai/client-react';
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
  Activity
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import type { Call } from '@/types';

interface PipecatCallInterfaceProps {
  call: Call;
  onCallEnded: () => void;
}

type CallState = 'idle' | 'connecting' | 'connected' | 'ended' | 'error';

// Main component wrapper with provider
export function PipecatCallInterface({ call, onCallEnded }: PipecatCallInterfaceProps) {
  // Create client instance with Daily transport
  const client = useMemo(() => {
    console.log('[Pipecat] Creating PipecatClient...');
    try {
      const newClient = new PipecatClient({
        transport: new DailyTransport(),
        enableMic: true,
        enableCam: false,
      });
      console.log('[Pipecat] Client created successfully:', newClient);
      return newClient;
    } catch (err) {
      console.error('[Pipecat] Failed to create client:', err);
      throw err;
    }
  }, []);

  console.log('[Pipecat] Rendering PipecatCallInterface with client:', client);

  return (
    <PipecatClientProvider client={client}>
      <PipecatCallInterfaceInner call={call} onCallEnded={onCallEnded} />
    </PipecatClientProvider>
  );
}

// Inner component that uses the hooks
function PipecatCallInterfaceInner({ call, onCallEnded }: PipecatCallInterfaceProps) {
  const client = usePipecatClient();
  const transportState = usePipecatClientTransportState();

  const [isMuted, setIsMuted] = useState(false);
  const [speakerEnabled, setSpeakerEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [callState, setCallState] = useState<CallState>('idle');
  const hasAutoStarted = useRef(false);

  console.log('[Pipecat] Component mounted');
  console.log('[Pipecat] Client:', client);
  console.log('[Pipecat] Access Token:', call.access_token);
  console.log('[Pipecat] Call State:', callState);
  console.log('[Pipecat] Transport State:', transportState);

  // Helper function to end session on backend
  const endSessionOnBackend = useCallback(async () => {
    if (!call.retell_call_id) return;

    console.log('[Pipecat] Calling backend to end session:', call.retell_call_id);
    try {
      const response = await fetch(`/api/pipecat/sessions/${call.retell_call_id}/end`, {
        method: 'POST',
      });

      if (response.ok) {
        const result = await response.json();
        console.log('[Pipecat] Session ended successfully:', result);
        return result;
      } else {
        console.error('[Pipecat] Failed to end session:', response.statusText);
      }
    } catch (apiError) {
      console.error('[Pipecat] Error calling end session API:', apiError);
    }
  }, [call.retell_call_id]);

  // Initialize client event listeners
  useEffect(() => {
    if (!client || !call.access_token) return;

    const handleConnected = () => {
      console.log('[Pipecat Event] Connected to Pipecat');
      setCallState('connected');
    };

    const handleDisconnected = () => {
      console.log('[Pipecat Event] Disconnected from Pipecat');
      // Only end the call if we were actually connected or connecting
      if (callState === 'connecting' || callState === 'connected') {
        setCallState('ended');
        endSessionOnBackend(); // Call backend to end session
        onCallEnded();
      }
    };

    const handleError = (error: any) => {
      console.error('[Pipecat Event] Pipecat error:', error);
      setError(`Call error: ${error?.message || 'Unknown error'}`);
      setCallState('error');
    };

    const handleBotReady = () => {
      console.log('[Pipecat Event] Bot is ready');
    };

    const handleBotStartedSpeaking = () => {
      console.log('[Pipecat Event] Bot started speaking');
      setIsAgentSpeaking(true);
    };

    const handleBotStoppedSpeaking = () => {
      console.log('[Pipecat Event] Bot stopped speaking');
      setIsAgentSpeaking(false);
    };

    const handleUserTranscription = (transcript: any) => {
      console.log('[Pipecat Event] User transcript:', transcript);
    };

    const handleBotTranscription = (transcript: any) => {
      console.log('[Pipecat Event] Bot transcript:', transcript);
    };

    // Set up event listeners
    client.on('connected', handleConnected);
    client.on('disconnected', handleDisconnected);
    client.on('error', handleError);
    client.on('botReady', handleBotReady);
    client.on('botStartedSpeaking', handleBotStartedSpeaking);
    client.on('botStoppedSpeaking', handleBotStoppedSpeaking);
    client.on('userTranscription', handleUserTranscription);
    client.on('botTranscription', handleBotTranscription);

    return () => {
      client.off('connected', handleConnected);
      client.off('disconnected', handleDisconnected);
      client.off('error', handleError);
      client.off('botReady', handleBotReady);
      client.off('botStartedSpeaking', handleBotStartedSpeaking);
      client.off('botStoppedSpeaking', handleBotStoppedSpeaking);
      client.off('userTranscription', handleUserTranscription);
      client.off('botTranscription', handleBotTranscription);
    };
  }, [client, call.access_token, onCallEnded, callState, endSessionOnBackend]);

  // Monitor transport state changes
  useEffect(() => {
    if (!transportState) return;

    console.log('[Pipecat] Transport state changed to:', transportState);

    switch (transportState) {
      case 'initializing':
      case 'authenticating':
      case 'connecting':
        setCallState('connecting');
        break;
      case 'connected':
      case 'ready':
        setCallState('connected');
        break;
      case 'disconnected':
        // Only end the call if we were previously connected
        // Don't end on initial disconnected state (before connection starts)
        if (callState === 'connected') {
          console.log('[Pipecat] Transport disconnected after being connected, ending call');
          setCallState('ended');
          endSessionOnBackend(); // Call backend to end session
          onCallEnded();
        }
        break;
      case 'error':
        console.error('[Pipecat] Transport error state');
        setCallState('error');
        break;
    }
  }, [transportState, callState, onCallEnded, endSessionOnBackend]);

  const startCall = useCallback(async () => {
    if (!client || !call.access_token) {
      setError('No Daily.co room URL available for this call');
      return;
    }

    try {
      setCallState('connecting');
      setError(null);

      console.log('[Pipecat] Starting call with URL:', call.access_token);
      console.log('[Pipecat] Calling client.connect()...');

      // Initialize devices (request mic permissions)
      console.log('[Pipecat] Initializing devices...');
      await client.initDevices();
      console.log('[Pipecat] Devices initialized');

      // Connect to Daily.co room via Pipecat client
      await client.connect({ url: call.access_token });
      console.log('[Pipecat] Client.connect() completed');

    } catch (err) {
      console.error('[Pipecat] Failed to start call:', err);
      setError(err instanceof Error ? err.message : 'Failed to start call');
      setCallState('error');
    }
  }, [client, call.access_token]);

  const endCall = useCallback(async () => {
    if (!client) return;

    try {
      await client.disconnect();
      setCallState('ended');
      await endSessionOnBackend(); // Ensure backend session is ended
      onCallEnded();
    } catch (err) {
      console.error('Error ending call:', err);
      // Still end the call even if there's an error
      setCallState('ended');
      await endSessionOnBackend(); // Try to end backend session even on error
      onCallEnded();
    }
  }, [client, onCallEnded, endSessionOnBackend]);

  const toggleMute = useCallback(async () => {
    if (!client) return;

    try {
      const newMutedState = !isMuted;
      await client.enableMic(!newMutedState);
      setIsMuted(newMutedState);
    } catch (err) {
      console.error('Error toggling mute:', err);
    }
  }, [client, isMuted]);

  const toggleSpeaker = useCallback(() => {
    // Toggle speaker output
    setSpeakerEnabled(!speakerEnabled);
    // Note: Actual speaker control may need additional implementation
    // The PipecatClientAudio component handles playback, but we can
    // use this state to visually indicate speaker status or
    // potentially control a global audio context if needed.
  }, [speakerEnabled]);

  // Auto-start the call when component mounts
  useEffect(() => {
    if (!hasAutoStarted.current && callState === 'idle' && call.access_token && client) {
      console.log('[Pipecat] Auto-starting call...');
      hasAutoStarted.current = true;
      startCall();
    }
  }, [callState, call.access_token, client, startCall]);

  if (!client) {
    return (
      <Card className="border-2 border-primary/20">
        <CardHeader>
          <CardTitle>Initializing Pipecat Client...</CardTitle>
        </CardHeader>
        <CardContent>
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
          <p className="text-center text-muted-foreground mt-2">Please wait</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-2 border-red-500/20">
        <CardHeader>
          <CardTitle className="text-red-500 flex items-center gap-2">
            <AlertCircle className="w-6 h-6" /> Call Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-400">{error}</p>
          <Button onClick={onCallEnded} className="mt-4">
            End Call
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-primary" />
            Pipecat Call: {call.driver_name}
          </div>
          <CallStatusBadge state={callState} />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Call Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Load:</span>{' '}
            <span className="font-medium">{call.load_number}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Origin:</span>{' '}
            <span className="font-medium">{call.origin || 'N/A'}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Destination:</span>{' '}
            <span className="font-medium">{call.destination || 'N/A'}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Agent ID:</span>{' '}
            <span className="font-medium">{call.agent_id.substring(0, 8)}...</span>
          </div>
        </div>

        {/* Visual Indicator for Bot Speaking */}
        {callState === 'connected' && (
          <div className="flex flex-col items-center justify-center py-4">
            <div className="relative w-24 h-24 flex items-center justify-center rounded-full bg-primary/10">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isAgentSpeaking
                    ? 'bg-primary text-primary-foreground shadow-lg scale-105'
                    : 'bg-muted text-muted-foreground'
              }`}>
                <Volume2 className="w-10 h-10" />
              </div>
              {isAgentSpeaking && (
                <>
                  <div className="absolute inset-0 rounded-full bg-primary/30 animate-ping" />
                  <div className="absolute -inset-2 rounded-full border-2 border-primary/50" style={{
                    animation: 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                  }} />
                </>
              )}
            </div>

            {/* Connection Info */}
            <div className="text-sm text-muted-foreground mt-4">
              <Activity className="w-4 h-4 inline mr-1" />
              Connected via Pipecat
            </div>
          </div>
        )}

        {/* Transport State Info */}
        {callState === 'connecting' && (
          <div className="text-center py-4">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
            <p className="text-sm text-muted-foreground">
              {transportState === 'initializing' && 'Initializing audio...'}
              {transportState === 'authenticating' && 'Connecting to room...'}
              {!transportState && 'Setting up call...'}
            </p>
          </div>
        )}

        {/* Call Controls */}
        <div className="flex items-center justify-center gap-4 pt-4">
          {callState === 'idle' && (
            <Button onClick={startCall} size="lg" className="gap-2">
              <Phone className="w-5 h-5" />
              Start Call
            </Button>
          )}

          {callState === 'connecting' && (
            <Button disabled size="lg" className="gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              Connecting...
            </Button>
          )}

          {callState === 'connected' && (
            <>
              <Button
                variant={isMuted ? 'destructive' : 'outline'}
                size="lg"
                onClick={toggleMute}
                className="gap-2"
                title={isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
              >
                {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                {isMuted ? 'Unmute' : 'Mute'}
              </Button>
              <Button
                variant={!speakerEnabled ? 'destructive' : 'outline'}
                size="lg"
                onClick={toggleSpeaker}
                className="gap-2"
                title={speakerEnabled ? 'Mute Speaker' : 'Unmute Speaker'}
              >
                {speakerEnabled ? <Volume2 className="w-6 h-6" /> : <VolumeX className="w-6 h-6" />}
                Speaker
              </Button>
              <Button onClick={endCall} size="lg" variant="destructive" className="gap-2">
                <PhoneOff className="w-6 h-6" />
                End Call
              </Button>
            </>
          )}

          {callState === 'ended' && (
            <Button onClick={onCallEnded} variant="outline">
              View Results
            </Button>
          )}
        </div>
        {/* PipecatClientAudio component for audio playback */}
        <PipecatClientAudio />
      </CardContent>
    </Card>
  );
}

interface CallStatusBadgeProps {
  state: CallState;
}

function CallStatusBadge({ state }: CallStatusBadgeProps) {
  let variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'info' | null = 'secondary';
  let text = '';

  switch (state) {
    case 'idle':
      text = 'Idle';
      variant = 'secondary';
      break;
    case 'connecting':
      text = 'Connecting...';
      variant = 'info';
      break;
    case 'connected':
      text = 'Connected';
      variant = 'success';
      break;
    case 'ended':
      text = 'Ended';
      variant = 'outline';
      break;
    case 'error':
      text = 'Error';
      variant = 'destructive';
      break;
    default:
      text = 'Unknown';
      variant = 'secondary';
  }

  return (
    <Badge
      variant={variant}
      className={state === 'connecting' || (state === 'connected' && text === 'Connected') ? 'animate-pulse' : ''}
    >
      {text}
    </Badge>
  );
}
