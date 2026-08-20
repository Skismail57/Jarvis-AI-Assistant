import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Switch,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

export default function SettingsScreen() {
  const [serverUrl, setServerUrl] = useState('http://192.168.1.100:8000');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(true);

  const SettingItem = ({icon, title, subtitle, rightComponent}) => (
    <View style={styles.settingItem}>
      <Icon name={icon} size={24} color="#7b2ff7" />
      <View style={styles.settingText}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {rightComponent}
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
        <Text style={styles.headerSubtitle}>Configure your Jarvis experience</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Connection</Text>
        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Server URL</Text>
          <TextInput
            style={styles.input}
            value={serverUrl}
            onChangeText={setServerUrl}
            placeholder="http://192.168.1.100:8000"
            placeholderTextColor="#666"
          />
        </View>
        <SettingItem
          icon="wifi"
          title="Connection Status"
          subtitle="Connected"
          rightComponent={<View style={styles.statusDot} />}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Preferences</Text>
        <SettingItem
          icon="notifications"
          title="Push Notifications"
          subtitle="Get reminder alerts"
          rightComponent={
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{false: '#3e3e4e', true: '#7b2ff7'}}
            />
          }
        />
        <SettingItem
          icon="mic"
          title="Voice Input"
          subtitle="Enable speech recognition"
          rightComponent={
            <Switch
              value={voiceEnabled}
              onValueChange={setVoiceEnabled}
              trackColor={{false: '#3e3e4e', true: '#7b2ff7'}}
            />
          }
        />
        <SettingItem
          icon="dark-mode"
          title="Dark Mode"
          subtitle="Use dark theme"
          rightComponent={
            <Switch
              value={darkMode}
              onValueChange={setDarkMode}
              trackColor={{false: '#3e3e4e', true: '#7b2ff7'}}
            />
          }
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <SettingItem
          icon="info"
          title="Version"
          subtitle="1.0.0"
          rightComponent={<Icon name="chevron-right" size={24} color="#666" />}
        />
        <SettingItem
          icon="help"
          title="Help & Support"
          subtitle="Get assistance"
          rightComponent={<Icon name="chevron-right" size={24} color="#666" />}
        />
      </View>

      <TouchableOpacity style={styles.saveButton}>
        <Text style={styles.saveButtonText}>Save Settings</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.disconnectButton}>
        <Text style={styles.disconnectButtonText}>Disconnect from Server</Text>
      </TouchableOpacity>
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
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  headerSubtitle: {
    color: '#a0a0b0',
    fontSize: 14,
  },
  section: {
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    marginBottom: 16,
    padding: 16,
  },
  sectionTitle: {
    color: '#7b2ff7',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    color: '#a0a0b0',
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#1e1e2e',
    color: '#ffffff',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  settingText: {
    flex: 1,
    marginLeft: 12,
  },
  settingTitle: {
    color: '#ffffff',
    fontSize: 16,
  },
  settingSubtitle: {
    color: '#a0a0b0',
    fontSize: 12,
    marginTop: 2,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#4ade80',
  },
  saveButton: {
    backgroundColor: '#7b2ff7',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  disconnectButton: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    marginHorizontal: 16,
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  disconnectButtonText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
