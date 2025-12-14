import React, { useState } from 'react';
import { Phone, Loader2, Truck, User, MapPin } from 'lucide-react';
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui';
import { callApi } from '@/lib/api';
import type { CallTriggerRequest, Call, Agent } from '@/types';

interface CallTriggerFormProps {
  agents: Agent[];
  onCallTriggered: (call: Call) => void;
}

export function CallTriggerForm({ agents, onCallTriggered }: CallTriggerFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<CallTriggerRequest>({
    agent_id: agents[0]?.id || '',
    driver_name: '',
    load_number: '',
    origin: '',
    destination: '',
    expected_eta: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.agent_id) {
      setError('Please select an agent');
      return;
    }
    if (!formData.driver_name.trim()) {
      setError('Driver name is required');
      return;
    }
    if (!formData.load_number.trim()) {
      setError('Load number is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const call = await callApi.trigger(formData);
      onCallTriggered(call);

      // Reset form except agent selection
      setFormData(prev => ({
        ...prev,
        driver_name: '',
        load_number: '',
        origin: '',
        destination: '',
        expected_eta: '',
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create call');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="w-5 h-5 text-primary" />
          Start Web Call
        </CardTitle>
        <CardDescription>
          Enter the driver's information to start a test call in your browser
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Agent Selection */}
          <div>
            <label htmlFor="agent_id" className="form-label">Select Agent</label>
            <select
              id="agent_id"
              name="agent_id"
              value={formData.agent_id}
              onChange={handleInputChange}
              className="form-input"
              disabled={agents.length === 0}
            >
              {agents.length === 0 ? (
                <option value="">No agents available</option>
              ) : (
                agents.map(agent => (
                  <option key={agent.id} value={agent.id}>{agent.name}</option>
                ))
              )}
            </select>
          </div>

          {/* Driver Name */}
          <div>
            <label htmlFor="driver_name" className="form-label flex items-center gap-1">
              <User className="w-4 h-4" />
              Driver Name *
            </label>
            <Input
              id="driver_name"
              name="driver_name"
              value={formData.driver_name}
              onChange={handleInputChange}
              placeholder="e.g., Mike Johnson"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              You will role-play as this driver during the call
            </p>
          </div>

          {/* Load Number */}
          <div>
            <label htmlFor="load_number" className="form-label flex items-center gap-1">
              <Truck className="w-4 h-4" />
              Load Number *
            </label>
            <Input
              id="load_number"
              name="load_number"
              value={formData.load_number}
              onChange={handleInputChange}
              placeholder="e.g., 7891-B"
              required
            />
          </div>

          {/* Route Information */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="origin" className="form-label flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                Origin
              </label>
              <Input
                id="origin"
                name="origin"
                value={formData.origin}
                onChange={handleInputChange}
                placeholder="e.g., Barstow, CA"
              />
            </div>

            <div>
              <label htmlFor="destination" className="form-label flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                Destination
              </label>
              <Input
                id="destination"
                name="destination"
                value={formData.destination}
                onChange={handleInputChange}
                placeholder="e.g., Phoenix, AZ"
              />
            </div>

            <div>
              <label htmlFor="expected_eta" className="form-label">Expected ETA</label>
              <Input
                id="expected_eta"
                name="expected_eta"
                value={formData.expected_eta}
                onChange={handleInputChange}
                placeholder="e.g., Tomorrow 8 AM"
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading || agents.length === 0}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating Call...
              </>
            ) : (
              <>
                <Phone className="w-4 h-4 mr-2" />
                Create Web Call
              </>
            )}
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            The call will open in your browser. Make sure to allow microphone access.
          </p>
        </form>
      </CardContent>
    </Card>
  );
}