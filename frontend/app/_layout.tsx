import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import * as SplashScreen from 'expo-splash-screen';

// Prevent splash screen from auto-hiding
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const { loadUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    const initializeApp = async () => {
      try {
        await loadUser();
      } catch (error) {
        console.error('Error loading user:', error);
      } finally {
        await SplashScreen.hideAsync();
      }
    };

    initializeApp();
  }, []);

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="(auth)/login" />
      <Stack.Screen name="(auth)/register" />
      <Stack.Screen name="(auth)/verify-email" />
      <Stack.Screen name="(tabs)" />
    </Stack>
  );
}
