export interface Contact {
  name: string;
  phoneNumbers?: string[];
  emails?: string[];
  organization?: string;
}

export interface ContactsPlugin {
  requestPermission(): Promise<{ granted: boolean; message?: string }>;
  getContacts(): Promise<{ contacts: Contact[] }>;
}

