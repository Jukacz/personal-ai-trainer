import type { Metadata } from 'next';
import { ProfileForm } from '@/components/profile/profile-form';

export const metadata: Metadata = {
  title: 'Profil - AI Personal Trainer',
  description: 'Zarządzaj swoim profilem i danymi treningowymi',
  robots: { index: false, follow: false },
};

export default function ProfilePage() {
  return <ProfileForm />;
}
