import React, { useState, useEffect, useCallback } from 'react';
import { Phone, Bot, Settings, RefreshCw, Plus, X } from 'lucide-react';
import { Button, Badge } from '@/components/ui';
import { CallTriggerForm, CallList, CallResultsView, WebCallInterface, PipecatCallInterface } from '@/components/call';
import { AgentConfigForm, AgentList } from '@/components/agent';
import { agentApi, callApi } from '@/lib/api';
import type { Agent, Call } from '@/types';

type TabType = 'calls' | 'agents';

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('calls');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [activeCall, setActiveCall] = useState<Call | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showAgentForm, setShowAgentForm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [agentsResponse, callsResponse] = await Promise.all([
        agentApi.list(0, 50, false),
        callApi.list(0, 50),
      ]);
      setAgents(agentsResponse.agents);
      setCalls(callsResponse.calls);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll for call updates
  useEffect(() => {
    const interval = setInterval(async () => {
      if (selectedCall && ['pending', 'ringing', 'in_progress'].includes(selectedCall.status)) {
        try {
          const updatedCall = await callApi.get(selectedCall.id);
          setSelectedCall(updatedCall);
          setCalls(prev => prev.map(c => c.id === updatedCall.id ? updatedCall : c));
        } catch (err) {
          console.error('Failed to poll call status:', err);
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [selectedCall]);

  const handleCallTriggered = (call: Call) => {
    console.log('Call triggered:', call);
    console.log('Access token:', call.access_token);
    setCalls(prev => [call, ...prev]);
    setSelectedCall(call);
    // Set as active call to show web call interface
    if (call.access_token) {
      console.log('Setting active call with access token');
      setActiveCall(call);
    } else {
      console.warn('No access token in call response!');
    }
  };

  const handleCallEnded = async () => {
    // Clear active call and refresh the call data
    if (activeCall) {
      try {
        const updatedCall = await callApi.get(activeCall.id);
        setCalls(prev => prev.map(c => c.id === updatedCall.id ? updatedCall : c));
        setSelectedCall(updatedCall);
      } catch (err) {
        console.error('Failed to fetch updated call:', err);
      }
    }
    setActiveCall(null);
  };

  const handleAgentSaved = (agent: Agent) => {
    setAgents(prev => {
      const exists = prev.find(a => a.id === agent.id);
      if (exists) {
        return prev.map(a => a.id === agent.id ? agent : a);
      }
      return [agent, ...prev];
    });
    setSelectedAgent(null);
    setShowAgentForm(false);
  };

  const handleDeleteAgent = async (agent: Agent) => {
    try {
      await agentApi.delete(agent.id);
      setAgents(prev => prev.filter(a => a.id !== agent.id));
      if (selectedAgent?.id === agent.id) {
        setSelectedAgent(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete agent');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                <Phone className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">Dispatcher Voice Agent Admin</h1>
                <p className="text-xs text-muted-foreground">Dispatch Call Management</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={loadData} disabled={isLoading}>
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 -mb-px">
            <button
              onClick={() => setActiveTab('calls')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'calls'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Phone className="w-4 h-4 inline mr-2" />
              Calls
              <Badge variant="secondary" className="ml-2">{calls.length}</Badge>
            </button>
            <button
              onClick={() => setActiveTab('agents')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'agents'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Bot className="w-4 h-4 inline mr-2" />
              Agents
              <Badge variant="secondary" className="ml-2">{agents.length}</Badge>
            </button>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-center justify-between">
            <span>{error}</span>
            <Button variant="ghost" size="icon" onClick={() => setError(null)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'calls' ? (
          <CallsTab
            agents={agents}
            calls={calls}
            selectedCall={selectedCall}
            activeCall={activeCall}
            onSelectCall={setSelectedCall}
            onCallTriggered={handleCallTriggered}
            onCallEnded={handleCallEnded}
          />
        ) : (
          <AgentsTab
            agents={agents}
            selectedAgent={selectedAgent}
            showAgentForm={showAgentForm}
            onSelectAgent={setSelectedAgent}
            onDeleteAgent={handleDeleteAgent}
            onAgentSaved={handleAgentSaved}
            onShowForm={() => setShowAgentForm(true)}
            onHideForm={() => { setShowAgentForm(false); setSelectedAgent(null); }}
          />
        )}
      </main>
    </div>
  );
}

interface CallsTabProps {
  agents: Agent[];
  calls: Call[];
  selectedCall: Call | null;
  activeCall: Call | null;
  onSelectCall: (call: Call) => void;
  onCallTriggered: (call: Call) => void;
  onCallEnded: () => void;
}

function CallsTab({
  agents,
  calls,
  selectedCall,
  activeCall,
  onSelectCall,
  onCallTriggered,
  onCallEnded
}: CallsTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Trigger & List */}
      <div className="lg:col-span-1 space-y-6">
        <CallTriggerForm agents={agents} onCallTriggered={onCallTriggered} />
        <CallList calls={calls} onSelectCall={onSelectCall} selectedCallId={selectedCall?.id} />
      </div>

      {/* Right: Active Call or Results */}
      <div className="lg:col-span-2">
        {activeCall && activeCall.access_token ? (
          <div className="animate-fade-in">
            {activeCall.agent_id && agents.find(a => a.id === activeCall.agent_id)?.voice_system === 'pipecat' ? (
              <PipecatCallInterface call={activeCall} onCallEnded={onCallEnded} />
            ) : (
              <WebCallInterface call={activeCall} onCallEnded={onCallEnded} />
            )}
          </div>
        ) : selectedCall ? (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">
                Call Details: {selectedCall.driver_name} - {selectedCall.load_number}
              </h2>
              <Badge className={selectedCall.status === 'in_progress' ? 'animate-pulse' : ''}>
                {selectedCall.status.replace('_', ' ')}
              </Badge>
            </div>
            <CallResultsView call={selectedCall} />
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Phone className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p>Select a call to view details</p>
              <p className="text-sm">or create a new web call to test</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface AgentsTabProps {
  agents: Agent[];
  selectedAgent: Agent | null;
  showAgentForm: boolean;
  onSelectAgent: (agent: Agent) => void;
  onDeleteAgent: (agent: Agent) => void;
  onAgentSaved: (agent: Agent) => void;
  onShowForm: () => void;
  onHideForm: () => void;
}

function AgentsTab({
  agents,
  selectedAgent,
  showAgentForm,
  onSelectAgent,
  onDeleteAgent,
  onAgentSaved,
  onShowForm,
  onHideForm,
}: AgentsTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Agent List */}
      <div className="lg:col-span-1 space-y-4">
        <Button onClick={onShowForm} className="w-full">
          <Plus className="w-4 h-4 mr-2" />
          Create New Agent
        </Button>
        <AgentList
          agents={agents}
          onSelectAgent={(agent) => { onSelectAgent(agent); onShowForm(); }}
          onDeleteAgent={onDeleteAgent}
          selectedAgentId={selectedAgent?.id}
        />
      </div>

      {/* Right: Agent Form */}
      <div className="lg:col-span-2">
        {showAgentForm ? (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Settings className="w-5 h-5" />
                {selectedAgent ? `Edit: ${selectedAgent.name}` : 'Create New Agent'}
              </h2>
              <Button variant="ghost" size="icon" onClick={onHideForm}>
                <X className="w-4 h-4" />
              </Button>
            </div>
            <AgentConfigForm agent={selectedAgent || undefined} onSaved={onAgentSaved} />
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Bot className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p>Select an agent to edit</p>
              <p className="text-sm">or create a new one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}