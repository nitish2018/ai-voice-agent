import React, { useEffect, useRef, useState, useCallback } from 'react';
import { RetellWebClient } from 'retell-client-js-sdk';
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import type { Call } from '@/types';

interface WebCallInterfaceProps {
  call: Call;
  onCallEnded: () => void;
}

type CallState = 'idle' | 'connecting' | 'active' | 'ended' | 'error';

interface TranscriptEntry {
  role: 'agent' | 'user';
  content: string;
}

export function WebCallInterface({ call, onCallEnded }: WebCallInterfaceProps) {
  const retellClientRef = useRef<RetellWebClient | null>(null);
  const [callState, setCallState] = useState<CallState>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isAgentTalking, setIsAgentTalking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  const startCall = useCallback(async () => {
    if (!call.access_token) {
      setError('No access token available for this call');
      return;
    }

    try {
      setCallState('connecting');
      setError(null);

      // Initialize Retell client
      const retellClient = new RetellWebClient();
      retellClientRef.current = retellClient;

      // Set up event listeners
      retellClient.on('call_started', () => {
        console.log('Call started');
        setCallState('active');
      });

      retellClient.on('call_ended', () => {
        console.log('Call ended');
        setCallState('ended');
        onCallEnded();
      });

      retellClient.on('agent_start_talking', () => {
        setIsAgentTalking(true);
      });

      retellClient.on('agent_stop_talking', () => {
        setIsAgentTalking(false);
      });

      retellClient.on('update', (update) => {
        // Update transcript from the update event
        if (update.transcript) {
          // Parse transcript - it contains the last few utterances
          const lines = update.transcript.split('\n').filter(Boolean);
          const entries: TranscriptEntry[] = lines.map(line => {
            if (line.startsWith('Agent:')) {
              return { role: 'agent' as const, content: line.replace('Agent:', '').trim() };
            } else if (line.startsWith('User:')) {
              return { role: 'user' as const, content: line.replace('User:', '').trim() };
            }
            return { role: 'agent' as const, content: line };
          });
          setTranscript(entries);
        }
      });

      retellClient.on('error', (err) => {
        console.error('Retell error:', err);
        setError(`Call error: ${err.message || 'Unknown error'}`);
        setCallState('error');
      });

      // Start the call
      await retellClient.startCall({
        accessToken: call.access_token,
        sampleRate: 24000,
      });

    } catch (err) {
      console.error('Failed to start call:', err);
      setError(err instanceof Error ? err.message : 'Failed to start call');
      setCallState('error');
    }
  }, [call.access_token, onCallEnded]);

  const endCall = useCallback(() => {
    if (retellClientRef.current) {
      retellClientRef.current.stopCall();
      retellClientRef.current = null;
    }
    setCallState('ended');
    onCallEnded();
  }, [onCallEnded]);

  const toggleMute = useCallback(() => {
    if (retellClientRef.current) {
      if (isMuted) {
        retellClientRef.current.unmute();
      } else {
        retellClientRef.current.mute();
      }
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (retellClientRef.current) {
        retellClientRef.current.stopCall();
      }
    };
  }, []);

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-primary" />
            Web Call: {call.driver_name}
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
            <span className="text-muted-foreground">Route:</span>{' '}
            <span className="font-medium">
              {call.origin || 'N/A'} → {call.destination || 'N/A'}
            </span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Agent Speaking Indicator */}
        {callState === 'active' && (
          <div className="flex items-center justify-center py-4">
            <div className={`relative ${isAgentTalking ? 'animate-pulse' : ''}`}>
              <div className={`w-20 h-20 rounded-full flex items-center justify-center ${
                isAgentTalking
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}>
                <Volume2 className="w-8 h-8" />
              </div>
              {isAgentTalking && (
                <>
                  <div className="absolute inset-0 rounded-full bg-primary/30 animate-ping" />
                  <div className="absolute -inset-2 rounded-full border-2 border-primary/50 animate-pulse-ring" />
                </>
              )}
            </div>
          </div>
        )}

        {/* Live Transcript */}
        {callState === 'active' && transcript.length > 0 && (
          <div className="bg-muted/30 rounded-lg p-3 max-h-48 overflow-y-auto">
            <div className="text-xs font-medium text-muted-foreground mb-2">Live Transcript</div>
            <div className="space-y-2">
              {transcript.map((entry, index) => (
                <div
                  key={index}
                  className={`text-sm ${
                    entry.role === 'agent'
                      ? 'text-primary'
                      : 'text-foreground'
                  }`}
                >
                  <span className="font-medium">
                    {entry.role === 'agent' ? 'Agent: ' : 'You: '}
                  </span>
                  {entry.content}
                </div>
              ))}
              <div ref={transcriptEndRef} />
            </div>
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

          {callState === 'active' && (
            <>
              <Button
                variant={isMuted ? 'destructive' : 'outline'}
                size="icon"
                onClick={toggleMute}
                className="w-12 h-12 rounded-full"
              >
                {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </Button>
              <Button
                variant="destructive"
                size="lg"
                onClick={endCall}
                className="gap-2"
              >
                <PhoneOff className="w-5 h-5" />
                End Call
              </Button>
            </>
          )}

          {(callState === 'ended' || callState === 'error') && (
            <div className="text-center">
              <p className="text-muted-foreground mb-2">
                {callState === 'ended' ? 'Call ended' : 'Call failed'}
              </p>
              <Button onClick={onCallEnded} variant="outline">
                View Results
              </Button>
            </div>
          )}
        </div>

        {/* Microphone Permission Note */}
        {callState === 'idle' && (
          <p className="text-xs text-center text-muted-foreground">
            Your browser will request microphone access when you start the call
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function CallStatusBadge({ state }: { state: CallState }) {
  const config = {
    idle: { label: 'Ready', variant: 'secondary' as const },
    connecting: { label: 'Connecting', variant: 'warning' as const },
    active: { label: 'In Progress', variant: 'success' as const },
    ended: { label: 'Ended', variant: 'secondary' as const },
    error: { label: 'Error', variant: 'destructive' as const },
  };

  const { label, variant } = config[state];

  return (
    <Badge variant={variant} className={state === 'active' ? 'animate-pulse' : ''}>
      {label}
    </Badge>
  );
}