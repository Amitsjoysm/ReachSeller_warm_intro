import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { MaterialIcons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/');
          },
        },
      ]
    );
  };

  const MenuItem = ({ icon, title, onPress, color = '#0066cc' }: any) => (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <View style={styles.menuItemLeft}>
        <MaterialIcons name={icon} size={24} color={color} />
        <Text style={styles.menuItemText}>{title}</Text>
      </View>
      <MaterialIcons name="chevron-right" size={24} color="#999" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.full_name?.charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text style={styles.userName}>{user?.full_name}</Text>
          <Text style={styles.userEmail}>{user?.email}</Text>
          <View style={styles.roleBadge}>
            <Text style={styles.roleText}>
              {user?.role === 'both' ? 'Buyer & Seller' : user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
            </Text>
          </View>
        </View>

        {/* Seller Stats */}
        {(user?.role === 'seller' || user?.role === 'both') && (
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                ${user?.seller_profile?.total_earnings?.toFixed(2) || '0.00'}
              </Text>
              <Text style={styles.statLabel}>Total Earnings</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {user?.seller_profile?.total_orders || 0}
              </Text>
              <Text style={styles.statLabel}>Orders</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {user?.seller_profile?.tier || 'New'}
              </Text>
              <Text style={styles.statLabel}>Tier</Text>
            </View>
          </View>
        )}

        {/* Buyer Balance */}
        {(user?.role === 'buyer' || user?.role === 'both') && (
          <View style={styles.balanceCard}>
            <View style={styles.balanceInfo}>
              <Text style={styles.balanceLabel}>Credit Balance</Text>
              <Text style={styles.balanceValue}>
                ${user?.buyer_profile?.credit_balance?.toFixed(2) || '0.00'}
              </Text>
            </View>
            <TouchableOpacity style={styles.addCreditsButton}>
              <MaterialIcons name="add" size={20} color="#fff" />
              <Text style={styles.addCreditsText}>Add Credits</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Menu Section */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Account</Text>
          <View style={styles.menuList}>
            <MenuItem
              icon="person"
              title="Edit Profile"
              onPress={() => Alert.alert('Edit Profile', 'Coming soon')}
            />
            <MenuItem
              icon="link"
              title="Connected Accounts"
              onPress={() => Alert.alert('Connected Accounts', 'LinkedIn status')}
            />
            <MenuItem
              icon="receipt"
              title="Transaction History"
              onPress={() => Alert.alert('Transaction History', 'Coming soon')}
            />
          </View>
        </View>

        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Support</Text>
          <View style={styles.menuList}>
            <MenuItem
              icon="help"
              title="Help Center"
              onPress={() => Alert.alert('Help Center', 'Coming soon')}
            />
            <MenuItem
              icon="description"
              title="Terms & Conditions"
              onPress={() => Alert.alert('Terms', 'Coming soon')}
            />
            <MenuItem
              icon="privacy-tip"
              title="Privacy Policy"
              onPress={() => Alert.alert('Privacy', 'Coming soon')}
            />
          </View>
        </View>

        <View style={styles.menuSection}>
          <View style={styles.menuList}>
            <MenuItem
              icon="logout"
              title="Logout"
              onPress={handleLogout}
              color="#f44336"
            />
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Warm Connects v1.0.0</Text>
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
  profileHeader: {
    backgroundColor: '#fff',
    padding: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#0066cc',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  roleBadge: {
    backgroundColor: '#e6f2ff',
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 12,
  },
  roleText: {
    fontSize: 14,
    color: '#0066cc',
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#eee',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0066cc',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  balanceCard: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 20,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#eee',
  },
  balanceInfo: {},
  balanceLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  balanceValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0066cc',
  },
  addCreditsButton: {
    flexDirection: 'row',
    backgroundColor: '#0066cc',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    gap: 4,
  },
  addCreditsText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  menuSection: {
    marginTop: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#999',
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  menuList: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#eee',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  menuItemText: {
    fontSize: 16,
    color: '#1a1a1a',
  },
  footer: {
    padding: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
  },
});
