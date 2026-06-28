import { Loader2, UserPlus } from 'lucide-react';
import type { FormEvent } from 'react';
import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

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

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    try {
      await register({
        full_name: fullName.trim() || null,
        email: email.trim(),
        password,
      });
      navigate('/', { replace: true });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Registration failed',
        description: getErrorMessage(error),
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-semibold">ApplyTrack</h1>
          <p className="text-sm text-muted-foreground">Create your workspace</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Create account</CardTitle>
            <CardDescription>
              Password must include uppercase, lowercase, and a number.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <Label htmlFor="register-name">Name</Label>
                <Input
                  id="register-name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  autoComplete="name"
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-email">Email</Label>
                <Input
                  id="register-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-password">Password</Label>
                <Input
                  id="register-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <UserPlus className="h-4 w-4" />
                )}
                Create account
              </Button>
            </form>
            <p className="mt-4 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
