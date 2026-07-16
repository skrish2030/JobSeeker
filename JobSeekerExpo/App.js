// JobSeekerExpo/App.js
import React, { useEffect, useState } from 'react';
import { StyleSheet, View, Platform, StatusBar, ActivityIndicator, TouchableOpacity, Text, Modal, TextInput, Alert } from 'react-native';
import { WebView } from 'react-native-webview';
import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

// Default fallback (static public URL). Change this placeholder before publishing.
const STATIC_URL = Constants.manifest?.extra?.backendUrl || 'http://YOUR_PUBLIC_URL';

// Try to guess local network address (common pattern) – can be overridden by saved URL.
const guessLocalUrl = async () => {
  const localIps = [
    'http://192.168.1.100:8000', // replace with your PC's LAN IP if known
    'http://192.168.0.100:8000',
    'http://10.0.0.100:8000',
    'http://127.0.0.1:8000',
  ];
  for (const url of localIps) {
    try {
      const response = await fetch(url, { method: 'HEAD', timeout: 2000 });
      if (response.ok) return url;
    } catch (_) { }
  }
  return null;
};

export default function App() {
  const [loading, setLoading] = useState(true);
  const [backendUrl, setBackendUrl] = useState(STATIC_URL);
  const [modalVisible, setModalVisible] = useState(false);
  const [inputUrl, setInputUrl] = useState('');

  // Load stored URL (tunnel) if any, otherwise try local.
  useEffect(() => {
    (async () => {
      const saved = await SecureStore.getItemAsync('backendUrl');
      if (saved) {
        setBackendUrl(saved);
        setLoading(false);
        return;
      }
      const local = await guessLocalUrl();
      if (local) {
        setBackendUrl(local);
      } else {
        setBackendUrl(STATIC_URL);
      }
      setLoading(false);
    })();
  }, []);

  const openSettings = () => setModalVisible(true);

  const saveUrl = async () => {
    if (!inputUrl) { Alert.alert('Please enter a URL'); return; }
    try {
      // quick validation
      new URL(inputUrl);
    } catch {
      Alert.alert('Invalid URL');
      return;
    }
    await SecureStore.setItemAsync('backendUrl', inputUrl);
    setBackendUrl(inputUrl);
    setModalVisible(false);
    setLoading(true);
  };

  return (
    <View style={styles.container}>
      {loading && <ActivityIndicator size="large" color="#007aff" style={StyleSheet.absoluteFill} />}
      <WebView
        source={{ uri: backendUrl }}
        onLoadEnd={() => setLoading(false)}
        startInLoadingState
        javaScriptEnabled
        domStorageEnabled
        style={{ flex: 1 }}
      />
      {/* Floating settings button */}
      <TouchableOpacity style={styles.settingsBtn} onPress={openSettings}>
        <Text style={styles.settingsText}>⚙️</Text>
      </TouchableOpacity>

      {/* Settings modal for custom/tunnel URL */}
      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Set Backend URL</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. https://abcd.ngrok.io"
              value={inputUrl}
              onChangeText={setInputUrl}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.modalBtn} onPress={saveUrl}>
                <Text style={styles.modalBtnText}>Save</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalBtn} onPress={() => setModalVisible(false)}>
                <Text style={styles.modalBtnText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    marginTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
    backgroundColor: '#fff',
  },
  settingsBtn: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: '#007aff',
    borderRadius: 30,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
  },
  settingsText: { color: '#fff', fontSize: 24 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '85%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
  },
  modalTitle: { fontSize: 18, fontWeight: '600', marginBottom: 12 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 6, padding: 8, marginBottom: 12 },
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between' },
  modalBtn: { backgroundColor: '#007aff', paddingVertical: 8, paddingHorizontal: 20, borderRadius: 6 },
  modalBtnText: { color: '#fff' },
});
