import React, {useState, useEffect} from 'react';
import {View, Text, StyleSheet, ActivityIndicator} from 'react-native';

export default function MetricsScreen() {
  const [metrics, setMetrics] = useState({
    cpu_percent: 0,
    ram_percent: 0,
    ram_used_gb: 0,
    ram_total_gb: 0,
    disk_percent: 0,
    disk_used_gb: 0,
    disk_total_gb: 0,
    uptime_seconds: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching metrics from WebSocket
    const interval = setInterval(() => {
      setMetrics({
        cpu_percent: Math.random() * 30 + 20,
        ram_percent: Math.random() * 20 + 40,
        ram_used_gb: 8 + Math.random() * 4,
        ram_total_gb: 16,
        disk_percent: 60 + Math.random() * 10,
        disk_used_gb: 480 + Math.random() * 20,
        disk_total_gb: 1000,
        uptime_seconds: 86400 + Math.random() * 3600,
      });
      setLoading(false);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const MetricCard = ({title, value, unit, color}) => (
    <View style={styles.metricCard}>
      <Text style={styles.metricTitle}>{title}</Text>
      <Text style={[styles.metricValue, {color}]}>
        {value.toFixed(1)}
      </Text>
      <Text style={styles.metricUnit}>{unit}</Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#7b2ff7" />
        <Text style={styles.loadingText}>Loading metrics...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>System Metrics</Text>
        <Text style={styles.uptime}>Uptime: {formatUptime(metrics.uptime_seconds)}</Text>
      </View>

      <View style={styles.grid}>
        <MetricCard
          title="CPU Usage"
          value={metrics.cpu_percent}
          unit="%"
          color="#ff2e88"
        />
        <MetricCard
          title="RAM Usage"
          value={metrics.ram_percent}
          unit="%"
          color="#7b2ff7"
        />
        <MetricCard
          title="RAM Used"
          value={metrics.ram_used_gb}
          unit="GB"
          color="#00eaff"
        />
        <MetricCard
          title="Disk Usage"
          value={metrics.disk_percent}
          unit="%"
          color="#fbbf24"
        />
      </View>

      <View style={styles.detailsCard}>
        <Text style={styles.detailsTitle}>Storage Details</Text>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Used:</Text>
          <Text style={styles.detailValue}>
            {metrics.disk_used_gb.toFixed(1)} GB
          </Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Total:</Text>
          <Text style={styles.detailValue}>
            {metrics.disk_total_gb.toFixed(1)} GB
          </Text>
        </View>
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              {width: `${metrics.disk_percent}%`},
            ]}
          />
        </View>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoText}>
          Real-time metrics from Jarvis server via WebSocket
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1a',
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#ffffff',
    marginTop: 16,
  },
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  uptime: {
    color: '#a0a0b0',
    fontSize: 14,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  metricCard: {
    width: '48%',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 16,
    borderRadius: 12,
    margin: '1%',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
  },
  metricTitle: {
    color: '#a0a0b0',
    fontSize: 12,
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  metricUnit: {
    color: '#ffffff',
    fontSize: 14,
  },
  detailsCard: {
    backgroundColor: 'rgba(123, 47, 247, 0.1)',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(123, 47, 247, 0.3)',
    marginBottom: 16,
  },
  detailsTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    color: '#c4b5fd',
    fontSize: 14,
  },
  detailValue: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  progressBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 4,
    overflow: 'hidden',
    marginTop: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#7b2ff7',
    borderRadius: 4,
  },
  infoCard: {
    backgroundColor: 'rgba(0, 234, 255, 0.1)',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(0, 234, 255, 0.3)',
  },
  infoText: {
    color: '#67e8f9',
    fontSize: 12,
    textAlign: 'center',
  },
});
