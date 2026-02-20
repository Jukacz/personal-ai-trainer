'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, User as UserIcon, Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/components/providers/auth-provider';
import { authApi } from '@/lib/api-client';

export function ProfileForm() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    age: null as number | null,
    weight: null as number | null,
    target_weight: null as number | null,
  });

  // Pre-fill form from user data
  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name,
        age: user.profile.age,
        weight: user.profile.weight,
        target_weight: user.profile.target_weight,
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setIsLoading(true);

    try {
      await authApi.updateProfile({
        name: formData.name,
        age: formData.age ?? undefined,
        weight: formData.weight ?? undefined,
        target_weight: formData.target_weight ?? undefined,
      });

      await refreshUser();
      setSuccess(true);

      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Nie udało się zaktualizować profilu');
      } else {
        setError('Nie udało się zaktualizować profilu');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5">
      <div className="container mx-auto px-4 py-8">
        {/* Back Button */}
        <Button
          variant="ghost"
          className="mb-6"
          onClick={() => router.push('/')}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Powrót
        </Button>

        {/* Profile Card */}
        <Card className="max-w-2xl mx-auto shadow-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                <UserIcon className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <CardTitle className="text-2xl">Twój profil</CardTitle>
                <CardDescription>{user.email}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Name Input */}
              <div className="space-y-2">
                <Label htmlFor="name" className="text-base">
                  Imię i nazwisko
                </Label>
                <Input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                  className="text-lg"
                  disabled={isLoading}
                  required
                />
              </div>

              {/* Age Input */}
              <div className="space-y-2">
                <Label htmlFor="age" className="text-base">
                  Wiek (lata)
                </Label>
                <Input
                  id="age"
                  type="number"
                  min={16}
                  max={100}
                  value={formData.age ?? ''}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      age: e.target.value ? parseInt(e.target.value) : null,
                    }))
                  }
                  className="text-lg"
                  disabled={isLoading}
                  placeholder="Opcjonalne"
                />
              </div>

              {/* Current Weight Input */}
              <div className="space-y-2">
                <Label htmlFor="weight" className="text-base">
                  Waga obecna (kg)
                </Label>
                <Input
                  id="weight"
                  type="number"
                  min={30}
                  max={300}
                  step={0.1}
                  value={formData.weight ?? ''}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      weight: e.target.value ? parseFloat(e.target.value) : null,
                    }))
                  }
                  className="text-lg"
                  disabled={isLoading}
                  placeholder="Opcjonalne"
                />
              </div>

              {/* Target Weight Input */}
              <div className="space-y-2">
                <Label htmlFor="target_weight" className="text-base">
                  Waga docelowa (kg)
                </Label>
                <Input
                  id="target_weight"
                  type="number"
                  min={30}
                  max={300}
                  step={0.1}
                  value={formData.target_weight ?? ''}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      target_weight: e.target.value
                        ? parseFloat(e.target.value)
                        : null,
                    }))
                  }
                  className="text-lg"
                  disabled={isLoading}
                  placeholder="Opcjonalne"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              )}

              {/* Success Message */}
              {success && (
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                    <Check className="h-4 w-4" />
                    <span>Profil został zaktualizowany</span>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                size="lg"
                className="w-full text-lg h-14"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Zapisywanie...
                  </>
                ) : (
                  'Zapisz zmiany'
                )}
              </Button>
            </form>

            {/* Info Box */}
            <div className="mt-6 p-4 bg-accent/50 rounded-lg">
              <p className="text-sm text-muted-foreground">
                <strong>Wskazówka:</strong> Dane z profilu będą automatycznie wypełniane
                w formularzu tworzenia planu treningowego.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
