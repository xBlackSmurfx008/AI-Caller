import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.aiadmin.app',
  appName: 'AI Admin',
  webDir: 'dist',
  ios: {
    contentInset: 'automatic',
    preferredContentMode: 'mobile',
    scheme: 'aiadmin',
    // IMPORTANT: limitsNavigationsToAppBoundDomains was removed because it requires
    // WKAppBoundDomains in Info.plist and breaks localStorage in WKWebView.
    // This was causing blank page after login.
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#000000',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },
    Keyboard: {
      // 'ionic' mode pushes content up properly on iOS
      resize: 'ionic',
      resizeOnFullScreen: true,
    },
  },
  // For development: uncomment to enable live reload
  // server: {
  //   url: 'http://YOUR_LOCAL_IP:5173',
  //   cleartext: true,
  // },
};

export default config;
