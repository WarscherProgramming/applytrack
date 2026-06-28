import { formatDistanceToNow } from 'date-fns';
import {
  CalendarClock,
  Download,
  Loader2,
  RefreshCw,
  Unplug,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import { calendarIntegrationApi } from '../api';
import {
  useCalendarIntegrationStatus,
  useConnectCalendar,
  useDisconnectCalendar,
  useSyncCalendar,
} from '../hooks';
import type { CalendarConnection, CalendarProvider } from '../types';

const PROVIDERS: { provider: CalendarProvider; label: string }[] = [
  { provider: 'google', label: 'Google Calendar' },
  { provider: 'outlook', label: 'Outlook Calendar' },
];

export function CalendarIntegrationSettingsCard() {
  const { toast } = useToast();
  const { data: status, isLoading } = useCalendarIntegrationStatus();
  const connect = useConnectCalendar();
  const disconnect = useDisconnectCalendar();
  const sync = useSyncCalendar();

  function connection(provider: CalendarProvider): CalendarConnection | undefined {
    return status?.connections.find((item) => item.provider === provider);
  }

  function handleConnect(provider: CalendarProvider) {
    connect.mutate(provider, {
      onSuccess: (result) => {
        if (!result.authorization_url) toast({ title: result.message });
      },
      onError: (e) =>
        toast({
          variant: 'destructive',
          title: 'Connect failed',
          description: getErrorMessage(e),
        }),
    });
  }

  function handleDisconnect(provider: CalendarProvider) {
    disconnect.mutate(provider, {
      onSuccess: () => toast({ title: 'Calendar disconnected' }),
      onError: (e) =>
        toast({
          variant: 'destructive',
          title: 'Disconnect failed',
          description: getErrorMessage(e),
        }),
    });
  }

  function handleSync(provider: CalendarProvider) {
    sync.mutate(
      { provider, include_interviews: true, include_followups: true },
      {
        onSuccess: (result) =>
          toast({
            title: 'Calendar sync complete',
            description: `${result.created} created, ${result.updated} updated, ${result.skipped} unchanged, ${result.deleted} removed.`,
          }),
        onError: (e) =>
          toast({
            variant: 'destructive',
            title: 'Sync failed',
            description: getErrorMessage(e),
          }),
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Calendar Integration</CardTitle>
          </div>
          <Badge variant="secondary">Simulation sync</Badge>
        </div>
        <CardDescription>
          Sync interviews and follow-up reminders to external calendars, or
          export an ICS file without OAuth.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : (
          <>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {PROVIDERS.map(({ provider, label }) => {
                const item = connection(provider);
                const connected = item?.status === 'connected';
                return (
                  <div
                    key={provider}
                    className="rounded-lg border p-4"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="font-medium">{label}</p>
                        <p className="text-xs text-muted-foreground">
                          {connected
                            ? item?.account_email
                            : 'Not connected'}
                        </p>
                      </div>
                      <Badge variant={connected ? 'success' : 'outline'}>
                        {connected ? 'Connected' : 'Disconnected'}
                      </Badge>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-xs text-muted-foreground">
                          Last sync
                        </p>
                        <p className="font-medium">
                          {item?.last_sync_at
                            ? formatDistanceToNow(new Date(item.last_sync_at), {
                                addSuffix: true,
                              })
                            : 'Never'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Status</p>
                        <p className="font-medium">
                          {item?.last_sync_status ?? 'Idle'}
                        </p>
                      </div>
                    </div>
                    {item?.last_error ? (
                      <p className="mt-3 text-sm text-destructive">
                        {item.last_error}
                      </p>
                    ) : null}
                    <div className="mt-4 flex flex-wrap gap-2">
                      {connected ? (
                        <>
                          <Button
                            size="sm"
                            onClick={() => handleSync(provider)}
                            disabled={sync.isPending}
                          >
                            {sync.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <RefreshCw className="h-4 w-4" />
                            )}
                            Sync now
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDisconnect(provider)}
                            disabled={disconnect.isPending}
                          >
                            <Unplug className="h-4 w-4" />
                            Disconnect
                          </Button>
                        </>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleConnect(provider)}
                          disabled={connect.isPending}
                        >
                          {connect.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <CalendarClock className="h-4 w-4" />
                          )}
                          Connect
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4">
              <div>
                <p className="font-medium">ICS export</p>
                <p className="text-sm text-muted-foreground">
                  Downloads interviews and pending follow-ups as a calendar
                  file.
                </p>
              </div>
              <Button variant="outline" asChild>
                <a href={calendarIntegrationApi.icsUrl()}>
                  <Download className="h-4 w-4" />
                  Download ICS
                </a>
              </Button>
            </div>

            <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
              <div>
                <p className="text-xs text-muted-foreground">Synced events</p>
                <p className="text-lg font-semibold tabular-nums">
                  {status?.synced_event_count ?? 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Latest sync</p>
                <p className="font-medium">
                  {status?.last_sync_at
                    ? formatDistanceToNow(new Date(status.last_sync_at), {
                        addSuffix: true,
                      })
                    : 'Never'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Latest status</p>
                <p className="font-medium">
                  {status?.last_sync_status ?? 'Idle'}
                </p>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
