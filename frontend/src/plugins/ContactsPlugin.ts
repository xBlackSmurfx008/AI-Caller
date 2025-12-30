/**
 * Custom Capacitor Plugin for Native Contact Access
 * 
 * This plugin provides native iOS/Android contact access.
 * To use this, you need to:
 * 1. Add the native plugin code to your iOS/Android projects
 * 2. Register the plugin in your native code
 */

import { registerPlugin } from '@capacitor/core';
import type { ContactsPlugin, Contact } from './definitions';

const Contacts = registerPlugin<ContactsPlugin>('Contacts', {
  web: () => import('./ContactsPluginWeb').then(m => new m.ContactsPluginWeb()),
});

export type { ContactsPlugin, Contact };
export { Contacts };

