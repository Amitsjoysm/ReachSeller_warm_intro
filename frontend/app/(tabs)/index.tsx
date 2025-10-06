import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { servicesAPI } from '../../services/api';
import { MaterialIcons } from '@expo/vector-icons';

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadServices();
  }, []);

  const loadServices = async () => {
    try {
      setLoading(true);
      const response = await servicesAPI.search({
        page: 1,
        limit: 20,
      });
      setServices(response.data.services);
    } catch (error: any) {
      console.error('Error loading services:', error);
      Alert.alert('Error', 'Failed to load services');
    } finally {
      setLoading(false);
    }
  };

  const renderServiceCard = (service: any) => (
    <TouchableOpacity
      key={service._id}
      style={styles.serviceCard}
      onPress={() => {
        // Navigate to service details
        Alert.alert('Service', service.title);
      }}
    >
      <View style={styles.serviceHeader}>
        <Text style={styles.serviceTitle} numberOfLines={2}>
          {service.title}
        </Text>
        <Text style={styles.servicePrice}>${service.base_price}</Text>
      </View>
      
      <Text style={styles.serviceDescription} numberOfLines={2}>
        {service.description}
      </Text>
      
      <View style={styles.serviceFooter}>
        <View style={styles.serviceMeta}>
          <MaterialIcons name="star" size={16} color="#ffc107" />
          <Text style={styles.serviceRating}>
            {service.average_rating > 0 ? service.average_rating.toFixed(1) : 'New'}
          </Text>
        </View>
        
        {service.platforms && service.platforms.length > 0 && (
          <View style={styles.platformBadge}>
            <Text style={styles.platformText}>{service.platforms[0]}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>
            Hello, {user?.full_name || 'User'}! 👋
          </Text>
          <Text style={styles.headerSubtitle}>
            {user?.role === 'seller' && 'Manage your services and orders'}
            {user?.role === 'buyer' && 'Find the perfect influencer for your brand'}
            {user?.role === 'both' && 'Buy services or offer your own'}
          </Text>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <MaterialIcons name="search" size={24} color="#999" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search services..."
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          {(user?.role === 'seller' || user?.role === 'both') && (
            <TouchableOpacity 
              style={styles.actionCard}
              onPress={() => router.push('/(tabs)/services')}
            >
              <MaterialIcons name="add-circle" size={32} color="#0066cc" />
              <Text style={styles.actionText}>Create Service</Text>
            </TouchableOpacity>
          )}
          
          {(user?.role === 'buyer' || user?.role === 'both') && (
            <TouchableOpacity style={styles.actionCard}>
              <MaterialIcons name="account-balance-wallet" size={32} color="#0066cc" />
              <Text style={styles.actionText}>Add Credits</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Services List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Popular Services</Text>
          
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
              <MaterialIcons name="search-off" size={64} color="#ccc" />
              <Text style={styles.emptyStateText}>No services available yet</Text>
              {(user?.role === 'seller' || user?.role === 'both') && (
                <TouchableOpacity 
                  style={styles.emptyStateButton}
                  onPress={() => router.push('/(tabs)/services')}
                >
                  <Text style={styles.emptyStateButtonText}>Create First Service</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>
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
  header: {
    padding: 20,
    backgroundColor: '#fff',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 16,
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    padding: 12,
    fontSize: 16,
  },
  quickActions: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
    marginBottom: 16,
  },
  actionCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e6f2ff',
  },
  actionText: {
    marginTop: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#0066cc',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  servicesList: {
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
    marginBottom: 8,
  },
  serviceTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginRight: 12,
  },
  servicePrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0066cc',
  },
  serviceDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    lineHeight: 20,
  },
  serviceFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  serviceMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  serviceRating: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  platformBadge: {
    backgroundColor: '#e6f2ff',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  platformText: {
    fontSize: 12,
    color: '#0066cc',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#999',
    marginTop: 16,
    marginBottom: 20,
  },
  emptyStateButton: {
    backgroundColor: '#0066cc',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  emptyStateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
