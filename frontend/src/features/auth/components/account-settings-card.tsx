import { Loader2, Save } from 'lucide-react';
import type { FormEvent } from 'react';
import { useEffect, useState } from 'react';

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
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import { useAuth } from '../auth-provider';

export function AccountSettingsCard() {
  const { user, updateMe } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    setFullName(user?.full_name ?? '');
    setEmail(user?.email ?? '');
  }, [user]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    try {
      await updateMe({
        full_name: fullName.trim() || null,
        email: email.trim(),
      });
      toast({ title: 'Account updated' });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Could not update account',
        description: getErrorMessage(error),
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account</CardTitle>
        <CardDescription>Manage your ApplyTrack profile.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid grid-cols-1 gap-4 sm:grid-cols-2" onSubmit={submit}>
          <div className="space-y-2">
            <Label htmlFor="account-full-name">Name</Label>
            <Input
              id="account-full-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="account-email">Email</Label>
            <Input
              id="account-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save account
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
