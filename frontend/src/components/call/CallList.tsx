import React from 'react';
import { Phone, Clock, User, Truck, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { formatDateTime, formatDuration, getStatusColor } from '@/lib/utils';
import type { Call } from '@/types';

interface CallListProps {
  calls: Call[];
  onSelectCall: (call: Call) => void;
  selectedCallId?: string;
}

export function CallList({ calls, onSelectCall, selectedCallId }: CallListProps) {
  if (calls.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <Phone className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No calls yet</p>
          <p className="text-sm mt-1">Trigger a test call to see results here</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Recent Calls</span>
          <Badge variant="secondary">{calls.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {calls.map((call) => (
            <CallListItem
              key={call.id}
              call={call}
              isSelected={call.id === selectedCallId}
              onClick={() => onSelectCall(call)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface CallListItemProps {
  call: Call;
  isSelected: boolean;
  onClick: () => void;
}

function CallListItem({ call, isSelected, onClick }: CallListItemProps) {
  const statusBadge = (
    <span className={`status-badge ${getStatusColor(call.status)}`}>
      {call.status.replace('_', ' ')}
    </span>
  );

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 hover:bg-muted/50 transition-colors ${
        isSelected ? 'bg-primary/5 border-l-2 border-l-primary' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <User className="w-4 h-4 text-muted-foreground" />
            <span className="font-medium truncate">{call.driver_name}</span>
            {statusBadge}
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Truck className="w-3 h-3" />
              {call.load_number}
            </span>
            {call.origin && call.destination && (
              <span className="truncate">
                {call.origin} → {call.destination}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDateTime(call.created_at)}
            </span>
            {call.duration_seconds && (
              <span>Duration: {formatDuration(call.duration_seconds)}</span>
            )}
          </div>

          {call.results && (
            <div className="mt-2">
              <Badge
                variant={call.results.is_emergency ? 'destructive' : 'info'}
                className="text-xs"
              >
                {call.results.call_outcome}
              </Badge>
            </div>
          )}
        </div>

        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
      </div>
    </button>
  );
}