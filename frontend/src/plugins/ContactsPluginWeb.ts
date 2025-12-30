/**
 * Web implementation of Contacts Plugin
 * Falls back to Contact Picker API on web
 */

import { WebPlugin } from '@capacitor/core';
import type { ContactsPlugin, Contact } from './definitions';

export class ContactsPluginWeb extends WebPlugin implements ContactsPlugin {
  async requestPermission(): Promise<{ granted: boolean; message?: string }> {
    // On web, check if Contact Picker API is available
    if (
      'contacts' in navigator &&
      'select' in (navigator as any).contacts &&
      typeof (navigator as any).contacts.select === 'function'
    ) {
      return { granted: true };
    }
    return {
      granted: false,
      message: 'Contact Picker API is not supported in this browser',
    };
  }

  async getContacts(): Promise<{ contacts: Contact[] }> {
    // Use Contact Picker API
    if (
      'contacts' in navigator &&
      'select' in (navigator as any).contacts &&
      typeof (navigator as any).contacts.select === 'function'
    ) {
      try {
        const contacts = await (navigator as any).contacts.select(
          ['name', 'tel', 'email', 'org'],
          { multiple: true }
        );

        if (!contacts || contacts.length === 0) {
          return { contacts: [] };
        }

        const formattedContacts: Contact[] = contacts.map((contact: any) => {
          const result: Contact = {
            name: '',
            phoneNumbers: [],
            emails: [],
          };

          // Extract name
          if (contact.name) {
            if (Array.isArray(contact.name)) {
              result.name = contact.name.join(' ');
            } else {
              result.name = String(contact.name);
            }
          }

          // Extract phone numbers
          if (contact.tel) {
            const telArray = Array.isArray(contact.tel) ? contact.tel : [contact.tel];
            result.phoneNumbers = telArray.map((tel: any) => {
              if (typeof tel === 'string') return tel;
              return tel.value || tel.number || String(tel);
            });
          }

          // Extract emails
          if (contact.email) {
            const emailArray = Array.isArray(contact.email) ? contact.email : [contact.email];
            result.emails = emailArray.map((email: any) => {
              if (typeof email === 'string') return email;
              return email.value || email.address || String(email);
            });
          }

          // Extract organization
          if (contact.org) {
            result.organization = String(contact.org);
          }

          return result;
        });

        return { contacts: formattedContacts };
      } catch (error: any) {
        if (error.name === 'AbortError') {
          throw new Error('Contact selection was cancelled');
        }
        throw error;
      }
    }

    throw new Error('Contact Picker API is not available');
  }
}

