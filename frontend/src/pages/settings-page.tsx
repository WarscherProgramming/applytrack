import {
  Bell,
  Download,
  KeyRound,
  Loader2,
  Monitor,
  Moon,
  Save,
  Shield,
  Sun,
  User,
  WandSparkles,
} from 'lucide-react';
import type { FormEvent } from 'react';
import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';

import { ConfirmDeleteDialog } from '@/components/common/confirm-delete-dialog';
import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { CalendarIntegrationSettingsCard } from '@/features/calendar-integration/components/calendar-integration-settings-card';
import { GmailSettingsCard } from '@/features/gmail/components/gmail-settings-card';
import {
  useChangePassword,
  useExportData,
  useSessions,
  useSettingsCenter,
  useSignOutAllSessions,
  useSignOutCurrentSession,
  useUpdateAccountSettings,
  useUpdateNotificationSettings,
  useUpdatePreferences,
} from '@/features/settings/hooks';
import type {
  AiProviderPreference,
  CalendarProviderPreference,
  DashboardPagePreference,
  NotificationBehavior,
  NotificationPreferences,
  ThemePreference,
} from '@/features/settings/types';
import { useAuth } from '@/features/auth/auth-provider';
import { getErrorMessage } from '@/lib/errors';
import { useTheme } from '@/hooks/use-theme';
import { useToast } from '@/hooks/use-toast';

const DEFAULT_NOTIFICATIONS: NotificationPreferences = {
  follow_up_reminders: true,
  interview_reminders: true,
  gmail_activity: true,
  opportunity_alerts: true,
  ai_insight_alerts: true,
};

const DASHBOARD_OPTIONS: Array<{ value: DashboardPagePreference; label: string }> = [
  { value: 'career_copilot', label: 'Career Copilot' },
  { value: 'dashboard', label: 'Dashboard' },
  { value: 'career_intelligence', label: 'Career Intelligence' },
  { value: 'daily_briefing', label: 'Daily Briefing' },
  { value: 'tasks', label: 'Tasks' },
];

const NOTIFICATION_BEHAVIOR_OPTIONS: Array<{ value: NotificationBehavior; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'important_only', label: 'Important only' },
  { value: 'muted', label: 'Muted' },
];

const CALENDAR_PROVIDER_OPTIONS: Array<{ value: CalendarProviderPreference; label: string }> = [
  { value: 'ics', label: 'ICS' },
  { value: 'google', label: 'Google Calendar' },
  { value: 'outlook', label: 'Outlook Calendar' },
  { value: 'none', label: 'None' },
];

const THEME_OPTIONS: Array<{ value: ThemePreference; label: string; icon: typeof Sun }> = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

export function SettingsPage() {
  const settings = useSettingsCenter();
  const sessions = useSessions();
  const updateAccount = useUpdateAccountSettings();
  const updatePreferences = useUpdatePreferences();
  const updateNotifications = useUpdateNotificationSettings();
  const changePassword = useChangePassword();
  const signOutCurrent = useSignOutCurrentSession();
  const signOutAll = useSignOutAllSessions();
  const exportData = useExportData();
  const { logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const [confirmCurrentOpen, setConfirmCurrentOpen] = useState(false);
  const [confirmAllOpen, setConfirmAllOpen] = useState(false);

  const data = settings.data;
  const [accountForm, setAccountForm] = useState({
    full_name: '',
    email: '',
    timezone: 'UTC',
  });
  const [preferencesForm, setPreferencesForm] = useState({
    theme: theme as ThemePreference,
    default_dashboard_page: 'career_copilot' as DashboardPagePreference,
    default_notification_behavior: 'all' as NotificationBehavior,
    preferred_calendar_provider: 'ics' as CalendarProviderPreference,
    preferred_ai_provider: 'auto' as AiProviderPreference,
  });
  const [notificationForm, setNotificationForm] =
    useState<NotificationPreferences>(DEFAULT_NOTIFICATIONS);
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    if (!data) return;
    setAccountForm({
      full_name: data.account.full_name ?? '',
      email: data.account.email,
      timezone: data.settings.timezone,
    });
    setPreferencesForm({
      theme: data.settings.theme,
      default_dashboard_page: data.settings.default_dashboard_page,
      default_notification_behavior: data.settings.default_notification_behavior,
      preferred_calendar_provider: data.settings.preferred_calendar_provider,
      preferred_ai_provider: data.settings.preferred_ai_provider,
    });
    setNotificationForm(data.settings.notification_preferences);
  }, [data]);

  const accountDirty = useMemo(() => {
    if (!data) return false;
    return (
      accountForm.full_name !== (data.account.full_name ?? '') ||
      accountForm.email !== data.account.email ||
      accountForm.timezone !== data.settings.timezone
    );
  }, [accountForm, data]);

  const preferencesDirty = useMemo(() => {
    if (!data) return false;
    return (
      preferencesForm.theme !== data.settings.theme ||
      preferencesForm.default_dashboard_page !== data.settings.default_dashboard_page ||
      preferencesForm.default_notification_behavior !==
        data.settings.default_notification_behavior ||
      preferencesForm.preferred_calendar_provider !==
        data.settings.preferred_calendar_provider ||
      preferencesForm.preferred_ai_provider !== data.settings.preferred_ai_provider
    );
  }, [data, preferencesForm]);

  const notificationsDirty = useMemo(() => {
    if (!data) return false;
    return JSON.stringify(notificationForm) !== JSON.stringify(data.settings.notification_preferences);
  }, [data, notificationForm]);

  function saveAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateAccount.mutate(
      {
        full_name: accountForm.full_name.trim() || null,
        email: accountForm.email.trim(),
        timezone: accountForm.timezone.trim() || 'UTC',
      },
      {
        onSuccess: () => toast({ title: 'Account updated' }),
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not update account',
            description: getErrorMessage(error),
          }),
      },
    );
  }

  function savePreferences(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updatePreferences.mutate(preferencesForm, {
      onSuccess: (updated) => {
        setTheme(updated.theme);
        toast({ title: 'Preferences saved' });
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not save preferences',
          description: getErrorMessage(error),
        }),
    });
  }

  function saveNotifications(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateNotifications.mutate(
      {
        notification_preferences: notificationForm,
        default_notification_behavior: preferencesForm.default_notification_behavior,
      },
      {
        onSuccess: () => toast({ title: 'Notifications saved' }),
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not save notifications',
            description: getErrorMessage(error),
          }),
      },
    );
  }

  function submitPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast({
        variant: 'destructive',
        title: 'Passwords do not match',
      });
      return;
    }
    changePassword.mutate(
      {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      },
      {
        onSuccess: () => {
          setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
          toast({ title: 'Password changed' });
        },
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not change password',
            description: getErrorMessage(error),
          }),
      },
    );
  }

  function exportJson() {
    exportData.mutate(undefined, {
      onSuccess: (payload) => {
        const blob = new Blob([JSON.stringify(payload, null, 2)], {
          type: 'application/json',
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `applytrack-export-${new Date().toISOString().slice(0, 10)}.json`;
        link.click();
        URL.revokeObjectURL(url);
        toast({ title: 'Export downloaded' });
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not export data',
          description: getErrorMessage(error),
        }),
    });
  }

  function confirmSignOutCurrent() {
    signOutCurrent.mutate(undefined, {
      onSuccess: async () => {
        setConfirmCurrentOpen(false);
        await logout();
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not sign out',
          description: getErrorMessage(error),
        }),
    });
  }

  function confirmSignOutAll() {
    signOutAll.mutate(undefined, {
      onSuccess: async () => {
        setConfirmAllOpen(false);
        await logout();
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not sign out sessions',
          description: getErrorMessage(error),
        }),
    });
  }

  if (settings.isLoading) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (settings.isError || !data) {
    return (
      <ErrorState
        title="Settings unavailable"
        error={settings.error}
        onRetry={() => void settings.refetch()}
      />
    );
  }

  const aiOptions: Array<{ value: AiProviderPreference; label: string }> = [
    { value: 'auto', label: 'Automatic' },
    ...data.available_ai_providers.map((provider) => ({
      value: provider as AiProviderPreference,
      label: provider === 'openai' ? 'OpenAI' : 'Mock',
    })),
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Account, security, and data controls." />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <SectionTitle icon={User} title="Account" dirty={accountDirty} />
              <CardDescription>{data.account.email}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="grid gap-4 sm:grid-cols-2" onSubmit={saveAccount}>
                <Field label="Name" htmlFor="settings-full-name">
                  <Input
                    id="settings-full-name"
                    value={accountForm.full_name}
                    onChange={(event) =>
                      setAccountForm((current) => ({
                        ...current,
                        full_name: event.target.value,
                      }))
                    }
                  />
                </Field>
                <Field label="Email" htmlFor="settings-email">
                  <Input
                    id="settings-email"
                    type="email"
                    value={accountForm.email}
                    onChange={(event) =>
                      setAccountForm((current) => ({
                        ...current,
                        email: event.target.value,
                      }))
                    }
                  />
                </Field>
                <Field label="Timezone" htmlFor="settings-timezone">
                  <Input
                    id="settings-timezone"
                    value={accountForm.timezone}
                    onChange={(event) =>
                      setAccountForm((current) => ({
                        ...current,
                        timezone: event.target.value,
                      }))
                    }
                  />
                </Field>
                <div className="flex items-end">
                  <SubmitButton pending={updateAccount.isPending} label="Save account" />
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <SectionTitle icon={KeyRound} title="Security" />
              <CardDescription>Active sessions: {sessions.data?.active_count ?? 0}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <form className="grid gap-4 sm:grid-cols-3" onSubmit={submitPassword}>
                <Field label="Current password" htmlFor="current-password">
                  <Input
                    id="current-password"
                    type="password"
                    value={passwordForm.current_password}
                    onChange={(event) =>
                      setPasswordForm((current) => ({
                        ...current,
                        current_password: event.target.value,
                      }))
                    }
                  />
                </Field>
                <Field label="New password" htmlFor="new-password">
                  <Input
                    id="new-password"
                    type="password"
                    value={passwordForm.new_password}
                    onChange={(event) =>
                      setPasswordForm((current) => ({
                        ...current,
                        new_password: event.target.value,
                      }))
                    }
                  />
                </Field>
                <Field label="Confirm password" htmlFor="confirm-password">
                  <Input
                    id="confirm-password"
                    type="password"
                    value={passwordForm.confirm_password}
                    onChange={(event) =>
                      setPasswordForm((current) => ({
                        ...current,
                        confirm_password: event.target.value,
                      }))
                    }
                  />
                </Field>
                <div className="sm:col-span-3">
                  <SubmitButton pending={changePassword.isPending} label="Change password" />
                </div>
              </form>

              <div className="space-y-3">
                {sessions.isLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading sessions
                  </div>
                ) : sessions.data?.items.length ? (
                  <div className="divide-y rounded-md border">
                    {sessions.data.items.slice(0, 5).map((session) => (
                      <div
                        key={session.id}
                        className="flex flex-col gap-2 p-3 text-sm sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div>
                          <div className="font-medium">
                            {session.is_current ? 'Current session' : 'Refresh session'}
                          </div>
                          <div className="text-muted-foreground">
                            Created {formatDateTime(session.created_at)}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={session.is_active ? 'default' : 'secondary'}>
                            {session.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                          {session.is_current ? <Badge variant="outline">Current</Badge> : null}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState title="No sessions" className="border py-8" />
                )}
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={() => setConfirmCurrentOpen(true)}>
                    <Shield className="h-4 w-4" />
                    Sign out current
                  </Button>
                  <Button variant="destructive" onClick={() => setConfirmAllOpen(true)}>
                    <Shield className="h-4 w-4" />
                    Sign out all
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <SectionTitle icon={Monitor} title="Preferences" dirty={preferencesDirty} />
            </CardHeader>
            <CardContent>
              <form className="grid gap-4 sm:grid-cols-2" onSubmit={savePreferences}>
                <Field label="Theme" htmlFor="settings-theme">
                  <Select
                    value={preferencesForm.theme}
                    onValueChange={(value) =>
                      setPreferencesForm((current) => ({
                        ...current,
                        theme: value as ThemePreference,
                      }))
                    }
                  >
                    <SelectTrigger id="settings-theme">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
                        <SelectItem key={value} value={value}>
                          <span className="inline-flex items-center gap-2">
                            <Icon className="h-4 w-4" />
                            {label}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Default page" htmlFor="default-dashboard">
                  <Select
                    value={preferencesForm.default_dashboard_page}
                    onValueChange={(value) =>
                      setPreferencesForm((current) => ({
                        ...current,
                        default_dashboard_page: value as DashboardPagePreference,
                      }))
                    }
                  >
                    <SelectTrigger id="default-dashboard">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DASHBOARD_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Calendar provider" htmlFor="calendar-provider">
                  <Select
                    value={preferencesForm.preferred_calendar_provider}
                    onValueChange={(value) =>
                      setPreferencesForm((current) => ({
                        ...current,
                        preferred_calendar_provider: value as CalendarProviderPreference,
                      }))
                    }
                  >
                    <SelectTrigger id="calendar-provider">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CALENDAR_PROVIDER_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="AI provider" htmlFor="ai-provider">
                  <Select
                    value={preferencesForm.preferred_ai_provider}
                    onValueChange={(value) =>
                      setPreferencesForm((current) => ({
                        ...current,
                        preferred_ai_provider: value as AiProviderPreference,
                      }))
                    }
                  >
                    <SelectTrigger id="ai-provider">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {aiOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <div className="sm:col-span-2">
                  <SubmitButton pending={updatePreferences.isPending} label="Save preferences" />
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <SectionTitle icon={Bell} title="Notifications" dirty={notificationsDirty} />
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={saveNotifications}>
                <Field label="Behavior" htmlFor="notification-behavior">
                  <Select
                    value={preferencesForm.default_notification_behavior}
                    onValueChange={(value) =>
                      setPreferencesForm((current) => ({
                        ...current,
                        default_notification_behavior: value as NotificationBehavior,
                      }))
                    }
                  >
                    <SelectTrigger id="notification-behavior">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {NOTIFICATION_BEHAVIOR_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <div className="grid gap-3 sm:grid-cols-2">
                  {Object.entries(notificationForm).map(([key, value]) => (
                    <label
                      key={key}
                      className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                    >
                      <span>{notificationLabel(key)}</span>
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={(event) =>
                          setNotificationForm((current) => ({
                            ...current,
                            [key]: event.target.checked,
                          }))
                        }
                        className="h-4 w-4 accent-primary"
                      />
                    </label>
                  ))}
                </div>
                <SubmitButton
                  pending={updateNotifications.isPending}
                  label="Save notifications"
                />
              </form>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <CalendarIntegrationSettingsCard />
            <Card>
              <CardHeader>
                <SectionTitle icon={WandSparkles} title="AI" />
                <CardDescription>
                  Active provider: {data.available_ai_providers.join(', ')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border p-3 text-sm">
                  Preferred provider: <span className="font-medium">{preferencesForm.preferred_ai_provider}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <GmailSettingsCard />
        </div>

        <aside className="space-y-6">
          <Card>
            <CardHeader>
              <SectionTitle icon={Download} title="Export" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-2 text-sm">
                {[
                  'Companies',
                  'Applications',
                  'Recruiters',
                  'Interviews',
                  'Follow-ups',
                  'Resumes',
                  'Cover letters',
                  'Tasks',
                  'Notifications',
                ].map((item) => (
                  <div key={item} className="rounded-md border px-3 py-2">
                    {item}
                  </div>
                ))}
              </div>
              <Button onClick={exportJson} disabled={exportData.isPending} className="w-full">
                {exportData.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Export JSON
              </Button>
            </CardContent>
          </Card>
        </aside>
      </div>

      <ConfirmDeleteDialog
        open={confirmCurrentOpen}
        onOpenChange={setConfirmCurrentOpen}
        onConfirm={confirmSignOutCurrent}
        title="Sign out current session"
        description="This will end this browser session."
        confirmLabel="Sign out"
        isPending={signOutCurrent.isPending}
      />
      <ConfirmDeleteDialog
        open={confirmAllOpen}
        onOpenChange={setConfirmAllOpen}
        onConfirm={confirmSignOutAll}
        title="Sign out all sessions"
        description="This will end every active ApplyTrack session for your account."
        confirmLabel="Sign out all"
        isPending={signOutAll.isPending}
      />
    </div>
  );
}

function SectionTitle({
  icon: Icon,
  title,
  dirty,
}: {
  icon: typeof User;
  title: string;
  dirty?: boolean;
}) {
  return (
    <CardTitle className="flex items-center gap-2 text-base">
      <Icon className="h-4 w-4" />
      {title}
      {dirty ? <Badge variant="outline">Unsaved</Badge> : null}
    </CardTitle>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  );
}

function SubmitButton({ pending, label }: { pending: boolean; label: string }) {
  return (
    <Button type="submit" disabled={pending}>
      {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
      {label}
    </Button>
  );
}

function notificationLabel(key: string) {
  return key
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}
