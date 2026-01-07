import React from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  Truck, 
  MapPin, 
  Clock, 
  FileText,
  Shield,
  Phone,
  DollarSign,
  Mic,
  Volume2,
  Cpu,
  Activity
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { getOutcomeColor } from '@/lib/utils';
import type { Call, CallResults, CostBreakdown, ServiceCost } from '@/types';

interface CallResultsViewProps {
  call: Call;
}

// Helper for currency formatting
const formatCurrency = (amount?: number) =>
  amount != null ? `$${amount.toFixed(4)}` : '$0.0000';

// Helper for duration formatting
const formatDuration = (seconds?: number) => {
  if (seconds == null) return '0m 0s';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
};

// Helper for unit formatting
const formatUnits = (units?: number, decimals = 0) =>
  units != null ? units.toFixed(decimals) : '0';

export function CallResultsView({ call }: CallResultsViewProps) {
  const results = call.results;

  if (!results) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Results not yet available</p>
          <p className="text-sm mt-1">Call may still be in progress</p>
        </CardContent>
      </Card>
    );
  }

  const isEmergency = results.is_emergency;
  const costBreakdown = results.raw_extraction?.cost_breakdown as CostBreakdown | undefined;

  return (
    <div className="space-y-4">
      {/* Outcome Badge */}
      <div className={`p-4 rounded-lg border ${getOutcomeColor(results.call_outcome)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isEmergency ? (
              <AlertTriangle className="w-5 h-5" />
            ) : (
              <CheckCircle className="w-5 h-5" />
            )}
            <span className="font-semibold">{results.call_outcome}</span>
          </div>
          {results.confidence_score && (
            <Badge variant="outline">
              {Math.round(results.confidence_score * 100)}% confidence
            </Badge>
          )}
        </div>
      </div>

      {/* Extracted Information */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Extracted Information</CardTitle>
        </CardHeader>
        <CardContent>
          {isEmergency ? (
            <EmergencyResults results={results} />
          ) : (
            <RoutineResults results={results} />
          )}
        </CardContent>
      </Card>

      {/* Cost Breakdown */}
      {costBreakdown && <CostBreakdownView costData={costBreakdown} />}

      {/* Transcript */}
      {call.transcript && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Full Transcript
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-muted/50 rounded-lg p-4 max-h-64 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono">
                {call.transcript}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RoutineResults({ results }: { results: CallResults }) {
  const dataPoints = [
    {
      icon: Truck,
      label: 'Driver Status',
      value: results.driver_status,
      highlight: true,
    },
    {
      icon: MapPin,
      label: 'Current Location',
      value: results.current_location,
    },
    {
      icon: Clock,
      label: 'ETA',
      value: results.eta,
    },
    {
      icon: AlertTriangle,
      label: 'Delay Reason',
      value: results.delay_reason,
      show: !!results.delay_reason,
    },
    {
      icon: Truck,
      label: 'Unloading Status',
      value: results.unloading_status,
      show: !!results.unloading_status,
    },
    {
      icon: FileText,
      label: 'POD Reminder Acknowledged',
      value: results.pod_reminder_acknowledged ? 'Yes' : 'No',
      highlight: results.pod_reminder_acknowledged,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {dataPoints
        .filter(point => point.show !== false)
        .map((point, index) => (
          <div key={index} className="data-row flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
            <point.icon className="w-4 h-4 mt-0.5 text-muted-foreground" />
            <div className="flex-1 min-w-0">
              <div className="data-label">{point.label}</div>
              <div className={`data-value ${point.highlight ? 'text-primary' : ''}`}>
                {point.value || '—'}
              </div>
            </div>
          </div>
        ))}
    </div>
  );
}

function EmergencyResults({ results }: { results: CallResults }) {
  const dataPoints = [
    {
      icon: AlertTriangle,
      label: 'Emergency Type',
      value: results.emergency_type,
      highlight: true,
      className: 'text-red-600',
    },
    {
      icon: Shield,
      label: 'Safety Status',
      value: results.safety_status,
    },
    {
      icon: AlertTriangle,
      label: 'Injury Status',
      value: results.injury_status,
    },
    {
      icon: MapPin,
      label: 'Emergency Location',
      value: results.emergency_location,
    },
    {
      icon: Truck,
      label: 'Load Secure',
      value: results.load_secure === null ? 'Unknown' : results.load_secure ? 'Yes' : 'No',
    },
    {
      icon: Phone,
      label: 'Escalation Status',
      value: results.escalation_status,
      highlight: true,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-medium">Emergency Call - Requires Immediate Attention</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {dataPoints.map((point, index) => (
          <div key={index} className="data-row flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
            <point.icon className={`w-4 h-4 mt-0.5 ${point.className || 'text-muted-foreground'}`} />
            <div className="flex-1 min-w-0">
              <div className="data-label">{point.label}</div>
              <div className={`data-value ${point.highlight ? point.className || 'text-primary' : ''}`}>
                {point.value || '—'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface CostBreakdownViewProps {
  costData: CostBreakdown;
}

function CostBreakdownView({ costData }: CostBreakdownViewProps) {
  const renderServiceCost = (serviceCost?: ServiceCost, icon?: React.ElementType) => {
    if (!serviceCost || serviceCost.cost_usd == null) return null;

    const IconComponent = icon;

    return (
      <div className="flex items-center justify-between py-2 border-b border-dashed last:border-b-0">
        <div className="flex items-center gap-2">
          {IconComponent && <IconComponent className="w-4 h-4 text-muted-foreground" />}
          <div>
            <div className="font-medium capitalize">
              {serviceCost.service_name?.replace('_', ' ') || 'Unknown Service'}
            </div>
            <div className="text-xs text-muted-foreground">
              {serviceCost.model || 'N/A'} • {formatUnits(serviceCost.units)} {serviceCost.unit_type || 'units'}
            </div>
          </div>
        </div>
        <div className="font-semibold">{formatCurrency(serviceCost.cost_usd)}</div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Cost Breakdown
          </div>
          <Badge variant="success" className="text-base px-3 py-1">
            Total: {formatCurrency(costData.total_cost_usd)}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {renderServiceCost(costData.stt_cost, Mic)}
          {renderServiceCost(costData.tts_cost, Volume2)}
          {renderServiceCost(costData.llm_cost, Cpu)}
          {renderServiceCost(costData.transport_cost, Activity)}
        </div>
        <div className="mt-4 text-sm text-muted-foreground flex justify-between items-center">
          <span>Call Duration:</span>
          <span className="font-medium text-primary">{formatDuration(costData.duration_seconds)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
