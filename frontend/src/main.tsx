import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Capacitor } from '@capacitor/core'
import { StatusBar, Style } from '@capacitor/status-bar'
import { Keyboard } from '@capacitor/keyboard'
import './index.css'
import App from './App.tsx'

// Initialize Capacitor plugins when running on native
const initCapacitor = async () => {
  if (Capacitor.isNativePlatform()) {
    try {
      // Set status bar style for iOS
      await StatusBar.setStyle({ style: Style.Dark });
      
      // Configure keyboard behavior
      Keyboard.setAccessoryBarVisible({ isVisible: true });
    } catch (e) {
      console.log('Capacitor plugin init:', e);
    }
  }
};

initCapacitor();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
