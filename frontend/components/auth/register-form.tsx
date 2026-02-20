'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Dumbbell, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { GoogleLoginButton } from '@/components/auth/google-login-button';
import { useAuth } from '@/components/providers/auth-provider';

export function RegisterForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('Hasło musi mieć minimum 8 znaków');
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password, name);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Nie udało się utworzyć konta');
      } else {
        setError('Nie udało się utworzyć konta');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="space-y-1 flex flex-col items-center">
        <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mb-2">
          <Dumbbell className="h-6 w-6 text-primary-foreground" />
        </div>
        <CardTitle className="text-2xl font-bold">Utwórz konto</CardTitle>
        <CardDescription>
          Zacznij planować swoje treningi
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <GoogleLoginButton />

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-2 text-muted-foreground">
              lub
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Imię</Label>
            <Input
              id="name"
              type="text"
              placeholder="Jan Kowalski"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="twoj@email.pl"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Hasło</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Minimum 8 znaków
            </p>
          </div>

          {error && (
            <div className="text-sm text-destructive">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Tworzenie konta...
              </>
            ) : (
              'Utwórz konto'
            )}
          </Button>
        </form>

        <div className="text-center text-sm">
          Masz już konto?{' '}
          <Link href="/login" className="text-primary hover:underline">
            Zaloguj się
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
