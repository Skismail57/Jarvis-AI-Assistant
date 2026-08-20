import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

export default function HomeScreen({navigation}) {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Jarvis AI Assistant</Text>
        <Text style={styles.subtitle}>Your Personal AI Companion</Text>
      </View>

      <View style={styles.statusCard}>
        <Icon name="wifi" size={24} color="#4ade80" />
        <Text style={styles.statusText}>Connected to Server</Text>
      </View>

      <View style={styles.grid}>
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Chat')}>
          <Icon name="mic" size={32} color="#ff2e88" />
          <Text style={styles.cardTitle}>Voice Chat</Text>
          <Text style={styles.cardSubtitle}>Talk to Jarvis</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Metrics')}>
          <Icon name="speed" size={32} color="#7b2ff7" />
          <Text style={styles.cardTitle}>System Metrics</Text>
          <Text style={styles.cardSubtitle}>View CPU/RAM</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Settings')}>
          <Icon name="settings" size={32} color="#00eaff" />
          <Text style={styles.cardTitle}>Settings</Text>
          <Text style={styles.cardSubtitle}>Configure Jarvis</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.card}>
          <Icon name="notifications" size={32} color="#fbbf24" />
          <Text style={styles.cardTitle}>Reminders</Text>
          <Text style={styles.cardSubtitle}>View upcoming</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Quick Commands</Text>
        <Text style={styles.infoText}>• "What's on my schedule today?"</Text>
        <Text style={styles.infoText}>• "Send email to john@example.com"</Text>
        <Text style={styles.infoText}>• "Add todo buy groceries"</Text>
        <Text style={styles.infoText}>• "What's on my screen?"</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  header: {
    padding: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#a0a0b0',
  },
  statusCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(74, 222, 128, 0.1)',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(74, 222, 128, 0.3)',
  },
  statusText: {
    marginLeft: 12,
    color: '#4ade80',
    fontSize: 16,
    fontWeight: '600',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
  },
  card: {
    width: '48%',
    margin: '1%',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 12,
  },
  cardSubtitle: {
    color: '#a0a0b0',
    fontSize: 12,
    marginTop: 4,
  },
  infoCard: {
    margin: 16,
    padding: 16,
    backgroundColor: 'rgba(123, 47, 247, 0.1)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(123, 47, 247, 0.3)',
  },
  infoTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  infoText: {
    color: '#c4b5fd',
    fontSize: 14,
    marginBottom: 8,
  },
});
