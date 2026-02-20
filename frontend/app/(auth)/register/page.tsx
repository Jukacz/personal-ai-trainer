import type { Metadata } from 'next';
import { RegisterForm } from '@/components/auth/register-form';

export const metadata: Metadata = {
  title: 'Utwórz konto - AI Personal Trainer',
  description: 'Zarejestruj się w AI Personal Trainer i zacznij planować treningi',
};

export default function RegisterPage() {
  return <RegisterForm />;
}
