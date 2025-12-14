import React from 'react';
import { Bot, Settings, Trash2, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '@/components/ui';
import { formatDateTime } from '@/lib/utils';
import type { Agent } from '@/types';

interface AgentListProps {
  agents: Agent[];
  onSelectAgent: (agent: Agent) => void;
  onDeleteAgent: (agent: Agent) => void;
  selectedAgentId?: string;
}

export function AgentList({ 
  agents, 
  onSelectAgent, 
  onDeleteAgent,
  selectedAgentId 
}: AgentListProps) {
  if (agents.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No agents configured</p>
          <p className="text-sm mt-1">Create your first agent to get started</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Configured Agents</span>
          <Badge variant="secondary">{agents.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {agents.map((agent) => (
            <AgentListItem
              key={agent.id}
              agent={agent}
              isSelected={agent.id === selectedAgentId}
              onSelect={() => onSelectAgent(agent)}
              onDelete={() => onDeleteAgent(agent)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface AgentListItemProps {
  agent: Agent;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

function AgentListItem({ agent, isSelected, onSelect, onDelete }: AgentListItemProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Delete agent "${agent.name}"? This cannot be undone.`)) {
      onDelete();
    }
  };

  return (
    <div
      className={`p-4 hover:bg-muted/50 transition-colors cursor-pointer ${
        isSelected ? 'bg-primary/5 border-l-2 border-l-primary' : ''
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Bot className="w-4 h-4 text-primary" />
            <span className="font-medium truncate">{agent.name}</span>
            {agent.is_active ? (
              <Badge variant="success" className="flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                Active
              </Badge>
            ) : (
              <Badge variant="secondary" className="flex items-center gap-1">
                <XCircle className="w-3 h-3" />
                Inactive
              </Badge>
            )}
          </div>
          
          {agent.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {agent.description}
            </p>
          )}
          
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span>Type: {agent.agent_type}</span>
            <span>Updated: {formatDateTime(agent.updated_at)}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
            }}
          >
            <Settings className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
