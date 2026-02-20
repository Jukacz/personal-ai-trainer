import type { Metadata } from 'next';
import { LoginForm } from '@/components/auth/login-form';

export const metadata: Metadata = {
  title: 'Zaloguj się - AI Personal Trainer',
  description: 'Zaloguj się do swojego konta AI Personal Trainer',
};

export default function LoginPage() {
  return <LoginForm />;
}
