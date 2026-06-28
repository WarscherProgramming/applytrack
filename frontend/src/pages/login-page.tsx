import { Loader2, LogIn } from 'lucide-react';
import type { FormEvent, ReactNode } from 'react';
import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';

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
import { useAuth } from '@/features/auth/auth-provider';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const state = location.state as LocationState | null;
  const redirectTo = state?.from?.pathname ?? '/';

  if (isAuthenticated) return <Navigate to={redirectTo} replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    try {
      await login({ email: email.trim(), password });
      navigate(redirectTo, { replace: true });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Login failed',
        description: getErrorMessage(error),
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell>
      <Card>
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>Use your ApplyTrack account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submit}>
            <div className="space-y-2">
              <Label htmlFor="login-email">Email</Label>
              <Input
                id="login-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                required
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="login-password">Password</Label>
              <Input
                id="login-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <LogIn className="h-4 w-4" />
              )}
              Sign in
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            No account?{' '}
            <Link to="/register" className="text-primary hover:underline">
              Create one
            </Link>
          </p>
        </CardContent>
      </Card>
    </AuthShell>
  );
}

function AuthShell({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-semibold">ApplyTrack</h1>
          <p className="text-sm text-muted-foreground">Career operating system</p>
        </div>
        {children}
      </div>
    </main>
  );
}
