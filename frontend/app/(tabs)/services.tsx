import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { servicesAPI, linkedInAPI } from '../../services/api';
import { MaterialIcons } from '@expo/vector-icons';

export default function ServicesScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [linkedInConnected, setLinkedInConnected] = useState(false);

  useEffect(() => {
    checkLinkedInStatus();
    if (user?.role === 'seller' || user?.role === 'both') {
      loadMyServices();
    }
  }, []);

  const checkLinkedInStatus = async () => {
    try {
      await linkedInAPI.getMyMetrics();
      setLinkedInConnected(true);
    } catch (error) {
      setLinkedInConnected(false);
    }
  };

  const loadMyServices = async () => {
    try {
      setLoading(true);
      const response = await servicesAPI.getMyServices();
      setServices(response.data.services);
    } catch (error: any) {
      console.error('Error loading services:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectLinkedIn = async () => {
    try {
      // For mock implementation
      const response = await linkedInAPI.callback({ mock_data: true });
      Alert.alert('Success', 'LinkedIn connected successfully!', [
        { text: 'OK', onPress: () => {
          setLinkedInConnected(true);
          loadMyServices();
        }}
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to connect LinkedIn');
    }
  };

  if (user?.role === 'buyer') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyState}>
          <MaterialIcons name="work-off" size={64} color="#ccc" />
          <Text style={styles.emptyStateText}>Not Available</Text>
          <Text style={styles.emptyStateSubtext}>
            Services management is only available for sellers
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!linkedInConnected) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.onboardingContainer}>
          <MaterialIcons name="link" size={80} color="#0077b5" />
          <Text style={styles.onboardingTitle}>Connect LinkedIn</Text>
          <Text style={styles.onboardingText}>
            To create and manage services, you need to connect your LinkedIn account.
            This helps verify your authenticity and reach.
          </Text>
          <TouchableOpacity 
            style={styles.linkedInButton}
            onPress={handleConnectLinkedIn}
          >
            <MaterialIcons name="link" size={24} color="#fff" />
            <Text style={styles.linkedInButtonText}>Connect LinkedIn</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const renderServiceCard = (service: any) => (
    <TouchableOpacity
      key={service._id}
      style={styles.serviceCard}
      onPress={() => Alert.alert('Service', service.title)}
    >
      <View style={styles.serviceHeader}>
        <View style={styles.serviceInfo}>
          <Text style={styles.serviceTitle} numberOfLines={2}>
            {service.title}
          </Text>
          <Text style={styles.servicePrice}>${service.base_price}</Text>
        </View>
        <View style={[styles.activeIndicator, { backgroundColor: service.active ? '#4caf50' : '#999' }]} />
      </View>

      <View style={styles.serviceStats}>
        <View style={styles.stat}>
          <MaterialIcons name="shopping-cart" size={16} color="#666" />
          <Text style={styles.statText}>{service.total_orders} orders</Text>
        </View>
        <View style={styles.stat}>
          <MaterialIcons name="star" size={16} color="#ffc107" />
          <Text style={styles.statText}>
            {service.average_rating > 0 ? service.average_rating.toFixed(1) : 'No ratings'}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView}>
        {/* Create Service Button */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.createButton}
            onPress={() => Alert.alert('Create Service', 'Service creation form coming soon!')}
          >
            <MaterialIcons name="add" size={24} color="#fff" />
            <Text style={styles.createButtonText}>Create New Service</Text>
          </TouchableOpacity>
        </View>

        {/* Services List */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#0066cc" />
          </View>
        ) : services.length > 0 ? (
          <View style={styles.servicesList}>
            {services.map(renderServiceCard)}
          </View>
        ) : (
          <View style={styles.emptyState}>
            <MaterialIcons name="work-outline" size={64} color="#ccc" />
            <Text style={styles.emptyStateText}>No services yet</Text>
            <Text style={styles.emptyStateSubtext}>
              Create your first service to start earning
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
  },
  scrollView: {
    flex: 1,
  },
  onboardingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  onboardingTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginTop: 24,
    marginBottom: 16,
  },
  onboardingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  linkedInButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0077b5',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 8,
    gap: 8,
  },
  linkedInButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  header: {
    padding: 16,
  },
  createButton: {
    flexDirection: 'row',
    backgroundColor: '#0066cc',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  servicesList: {
    padding: 16,
    gap: 12,
  },
  serviceCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#eee',
  },
  serviceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  serviceInfo: {
    flex: 1,
    marginRight: 12,
  },
  serviceTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  servicePrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0066cc',
  },
  activeIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  serviceStats: {
    flexDirection: 'row',
    gap: 20,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 14,
    color: '#666',
  },
  emptyState: {
    padding: 60,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#999',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});
