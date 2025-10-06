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
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { ordersAPI } from '../../services/api';
import { MaterialIcons } from '@expo/vector-icons';

export default function OrdersScreen() {
  const { user } = useAuthStore();
  
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'buyer' | 'seller'>('buyer');

  useEffect(() => {
    loadOrders();
  }, [activeTab]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const response = activeTab === 'buyer' 
        ? await ordersAPI.getBuyerOrders()
        : await ordersAPI.getSellerOrders();
      setOrders(response.data.orders);
    } catch (error: any) {
      console.error('Error loading orders:', error);
      Alert.alert('Error', 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending_acceptance': return '#ff9800';
      case 'accepted': return '#2196f3';
      case 'delivered': return '#9c27b0';
      case 'approved': case 'completed': return '#4caf50';
      case 'disputed': return '#f44336';
      case 'cancelled': case 'refunded': return '#757575';
      default: return '#666';
    }
  };

  const getStatusText = (status: string) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const renderOrderCard = (order: any) => (
    <TouchableOpacity
      key={order._id}
      style={styles.orderCard}
      onPress={() => Alert.alert('Order', order.order_number)}
    >
      <View style={styles.orderHeader}>
        <View style={styles.orderInfo}>
          <Text style={styles.orderNumber}>#{order.order_number}</Text>
          <Text style={styles.orderTitle} numberOfLines={1}>
            {order.service_title}
          </Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(order.status) + '20' }]}>
          <Text style={[styles.statusText, { color: getStatusColor(order.status) }]}>
            {getStatusText(order.status)}
          </Text>
        </View>
      </View>

      <View style={styles.orderDetails}>
        <View style={styles.orderDetail}>
          <MaterialIcons name="attach-money" size={16} color="#666" />
          <Text style={styles.orderDetailText}>${order.total_cost}</Text>
        </View>
        <View style={styles.orderDetail}>
          <MaterialIcons name="calendar-today" size={16} color="#666" />
          <Text style={styles.orderDetailText}>
            {new Date(order.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>

      {order.status === 'pending_acceptance' && activeTab === 'seller' && (
        <View style={styles.orderActions}>
          <TouchableOpacity style={styles.acceptButton}>
            <Text style={styles.acceptButtonText}>Accept</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.declineButton}>
            <Text style={styles.declineButtonText}>Decline</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Tab Switcher */}
      {(user?.role === 'both') && (
        <View style={styles.tabSwitcher}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'buyer' && styles.tabActive]}
            onPress={() => setActiveTab('buyer')}
          >
            <Text style={[styles.tabText, activeTab === 'buyer' && styles.tabTextActive]}>
              As Buyer
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'seller' && styles.tabActive]}
            onPress={() => setActiveTab('seller')}
          >
            <Text style={[styles.tabText, activeTab === 'seller' && styles.tabTextActive]}>
              As Seller
            </Text>
          </TouchableOpacity>
        </View>
      )}

      <ScrollView style={styles.scrollView}>
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#0066cc" />
          </View>
        ) : orders.length > 0 ? (
          <View style={styles.ordersList}>
            {orders.map(renderOrderCard)}
          </View>
        ) : (
          <View style={styles.emptyState}>
            <MaterialIcons name="receipt-long" size={64} color="#ccc" />
            <Text style={styles.emptyStateText}>No orders yet</Text>
            <Text style={styles.emptyStateSubtext}>
              {activeTab === 'buyer' 
                ? 'Browse services to place your first order'
                : 'Orders will appear here once buyers contact you'
              }
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
  tabSwitcher: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#0066cc',
  },
  tabText: {
    fontSize: 16,
    color: '#999',
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#0066cc',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  ordersList: {
    padding: 16,
    gap: 12,
  },
  orderCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#eee',
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  orderInfo: {
    flex: 1,
    marginRight: 12,
  },
  orderNumber: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  orderTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  orderDetails: {
    flexDirection: 'row',
    gap: 20,
    marginBottom: 12,
  },
  orderDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  orderDetailText: {
    fontSize: 14,
    color: '#666',
  },
  orderActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#4caf50',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  acceptButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  declineButton: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#f44336',
  },
  declineButtonText: {
    color: '#f44336',
    fontWeight: '600',
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
