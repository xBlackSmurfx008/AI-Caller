import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Capacitor } from '@capacitor/core'
import { StatusBar, Style } from '@capacitor/status-bar'
import { Keyboard, KeyboardResize } from '@capacitor/keyboard'
import './index.css'
import App from './App.tsx'

// Initialize Capacitor plugins when running on native
const initCapacitor = async () => {
  if (Capacitor.isNativePlatform()) {
    try {
      // Set status bar style for iOS
      await StatusBar.setStyle({ style: Style.Dark });
      
      // Configure keyboard behavior for iOS
      // This ensures the keyboard pushes content up instead of covering it
      await Keyboard.setAccessoryBarVisible({ isVisible: true });
      await Keyboard.setScroll({ isDisabled: false });
      await Keyboard.setResizeMode({ mode: KeyboardResize.Ionic });
      
      // Listen for keyboard show/hide to handle scroll
      Keyboard.addListener('keyboardWillShow', (info) => {
        document.body.style.setProperty('--keyboard-height', `${info.keyboardHeight}px`);
        document.body.classList.add('keyboard-visible');
      });
      
      Keyboard.addListener('keyboardWillHide', () => {
        document.body.style.setProperty('--keyboard-height', '0px');
        document.body.classList.remove('keyboard-visible');
      });
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
