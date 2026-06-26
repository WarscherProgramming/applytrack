import { formatDistanceToNow } from 'date-fns';
import { Loader2, Mail, RefreshCw, Unplug } from 'lucide-react';

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

import {
  useConnectGmail,
  useDisconnectGmail,
  useGmailStatus,
  useSyncGmail,
} from '../hooks/use-gmail';

/** Connect / status / last-sync / manual sync for the Gmail integration. */
export function GmailSettingsCard() {
  const { toast } = useToast();
  const { data: status, isLoading } = useGmailStatus();
  const connect = useConnectGmail();
  const disconnect = useDisconnectGmail();
  const sync = useSyncGmail();

  function handleConnect() {
    connect.mutate(undefined, {
      onError: (e) =>
        toast({ variant: 'destructive', title: 'Connect failed', description: getErrorMessage(e) }),
    });
  }

  function handleSync() {
    sync.mutate(undefined, {
      onSuccess: (result) =>
        toast({
          title: 'Sync complete',
          description: `${result.imported} imported, ${result.matched} matched.`,
        }),
      onError: (e) =>
        toast({ variant: 'destructive', title: 'Sync failed', description: getErrorMessage(e) }),
    });
  }

  function handleDisconnect() {
    disconnect.mutate(undefined, {
      onSuccess: () => toast({ title: 'Gmail disconnected' }),
    });
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Gmail</CardTitle>
          </div>
          {status?.simulation ? <Badge variant="secondary">Simulation</Badge> : null}
        </div>
        <CardDescription>
          Import job-related emails and link them to companies, applications,
          recruiters, and interviews.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : status?.connected ? (
          <>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Account</p>
                <p className="font-medium">{status.email_address}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Imported emails</p>
                <p className="font-medium tabular-nums">{status.email_count}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Last sync</p>
                <p className="font-medium">
                  {status.last_sync_at
                    ? formatDistanceToNow(new Date(status.last_sync_at), {
                        addSuffix: true,
                      })
                    : 'Never'}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={handleSync} disabled={sync.isPending}>
                {sync.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {sync.isPending ? 'Syncing…' : 'Sync now'}
              </Button>
              <Button
                variant="outline"
                onClick={handleDisconnect}
                disabled={disconnect.isPending}
              >
                <Unplug className="h-4 w-4" />
                Disconnect
              </Button>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-start gap-3">
            <p className="text-sm text-muted-foreground">
              Not connected.{' '}
              {status?.simulation
                ? 'Connecting uses simulated sample emails (no real Google account needed).'
                : 'You will be redirected to Google to authorize read-only access.'}
            </p>
            <Button onClick={handleConnect} disabled={connect.isPending}>
              {connect.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Mail className="h-4 w-4" />
              )}
              Connect Gmail
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
