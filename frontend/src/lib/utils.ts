import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPhoneNumber(phone: string): string {
  // Remove all non-numeric characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Format as (XXX) XXX-XXXX for US numbers
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  
  // Format with country code
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  
  return phone;
}

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '—';
  
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  
  return `${secs}s`;
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    ringing: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-green-100 text-green-800',
    completed: 'bg-gray-100 text-gray-800',
    failed: 'bg-red-100 text-red-800',
    no_answer: 'bg-orange-100 text-orange-800',
    busy: 'bg-purple-100 text-purple-800',
    voicemail: 'bg-indigo-100 text-indigo-800',
  };
  
  return statusColors[status] || 'bg-gray-100 text-gray-800';
}

export function getOutcomeColor(outcome: string): string {
  const outcomeColors: Record<string, string> = {
    'In-Transit Update': 'bg-blue-100 text-blue-800 border-blue-200',
    'Arrival Confirmation': 'bg-green-100 text-green-800 border-green-200',
    'Emergency Escalation': 'bg-red-100 text-red-800 border-red-200',
    'Incomplete': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'Unknown': 'bg-gray-100 text-gray-800 border-gray-200',
  };
  
  return outcomeColors[outcome] || 'bg-gray-100 text-gray-800 border-gray-200';
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
