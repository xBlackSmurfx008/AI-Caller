# Capacitor Contacts Plugin Setup Guide

This guide will help you set up native contact access for iOS and Android.

> **📚 For comprehensive API documentation**, see [`docs/CONTACTS_API_DOCUMENTATION.md`](../../docs/CONTACTS_API_DOCUMENTATION.md) which includes:
> - Official Apple and Android documentation links
> - Complete API references
> - Code examples from official sources
> - Best practices and troubleshooting

## Prerequisites

1. Install Capacitor CLI globally (if not already installed):
```bash
npm install -g @capacitor/cli
```

2. Add native platforms:
```bash
cd frontend
npx cap add ios
npx cap add android
```

## iOS Setup

### 1. Add Permission to Info.plist

Open `ios/App/App/Info.plist` and add:

```xml
<key>NSContactsUsageDescription</key>
<string>This app needs access to your contacts to import them for calling and messaging.</string>
```

### 2. Create Contacts Plugin

Create `ios/App/App/ContactsPlugin.swift`:

```swift
import Foundation
import Capacitor
import Contacts

@objc(ContactsPlugin)
public class ContactsPlugin: CAPPlugin {
    
    @objc func requestPermission(_ call: CAPPluginCall) {
        let store = CNContactStore()
        store.requestAccess(for: .contacts) { granted, error in
            if let error = error {
                call.reject("Permission request failed: \(error.localizedDescription)")
                return
            }
            call.resolve(["granted": granted])
        }
    }
    
    @objc func getContacts(_ call: CAPPluginCall) {
        let store = CNContactStore()
        
        // Check authorization status
        let status = CNContactStore.authorizationStatus(for: .contacts)
        if status != .authorized {
            call.reject("Contacts permission not granted")
            return
        }
        
        let keysToFetch = [
            CNContactGivenNameKey,
            CNContactFamilyNameKey,
            CNContactPhoneNumbersKey,
            CNContactEmailAddressesKey,
            CNContactOrganizationNameKey
        ] as [CNKeyDescriptor]
        
        let request = CNContactFetchRequest(keysToFetch: keysToFetch)
        var contacts: [[String: Any]] = []
        
        do {
            try store.enumerateContacts(with: request) { contact, stop in
                var contactDict: [String: Any] = [:]
                
                // Name
                let fullName = "\(contact.givenName) \(contact.familyName)".trimmingCharacters(in: .whitespaces)
                contactDict["name"] = fullName.isEmpty ? "Unknown" : fullName
                
                // Phone numbers
                var phoneNumbers: [String] = []
                for phone in contact.phoneNumbers {
                    phoneNumbers.append(phone.value.stringValue)
                }
                contactDict["phoneNumbers"] = phoneNumbers
                
                // Emails
                var emails: [String] = []
                for email in contact.emailAddresses {
                    emails.append(email.value as String)
                }
                contactDict["emails"] = emails
                
                // Organization
                if !contact.organizationName.isEmpty {
                    contactDict["organization"] = contact.organizationName
                }
                
                contacts.append(contactDict)
            }
            
            call.resolve(["contacts": contacts])
        } catch {
            call.reject("Failed to fetch contacts: \(error.localizedDescription)")
        }
    }
}
```

### 3. Register Plugin

In `ios/App/App/AppDelegate.swift`, add the import and register:

```swift
import ContactsPlugin

// In didFinishLaunchingWithOptions, add:
self.bridge?.registerPlugin(ContactsPlugin.self)
```

Or if using Objective-C bridge, create `ios/App/App/ContactsPlugin.m`:

```objc
#import <Foundation/Foundation.h>
#import <Capacitor/Capacitor.h>

CAP_PLUGIN(ContactsPlugin, "Contacts",
    CAP_PLUGIN_METHOD(requestPermission, CAPPluginReturnPromise);
    CAP_PLUGIN_METHOD(getContacts, CAPPluginReturnPromise);
)
```

## Android Setup

### 1. Add Permission to AndroidManifest.xml

Open `android/app/src/main/AndroidManifest.xml` and add:

```xml
<uses-permission android:name="android.permission.READ_CONTACTS" />
```

### 2. Create Contacts Plugin

Create `android/app/src/main/java/com/aicaller/app/ContactsPlugin.java`:

```java
package com.aicaller.app;

import android.Manifest;
import android.content.ContentResolver;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.provider.ContactsContract;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

import java.util.ArrayList;
import java.util.List;

@CapacitorPlugin(
    name = "Contacts",
    permissions = {
        @Permission(
            strings = {Manifest.permission.READ_CONTACTS},
            alias = "contacts"
        )
    }
)
public class ContactsPlugin extends Plugin {

    private static final int PERMISSION_REQUEST_CODE = 12345;

    @PluginMethod
    public void requestPermission(PluginCall call) {
        if (ContextCompat.checkSelfPermission(
                getContext(),
                Manifest.permission.READ_CONTACTS
        ) == PackageManager.PERMISSION_GRANTED) {
            JSObject result = new JSObject();
            result.put("granted", true);
            call.resolve(result);
        } else {
            requestPermissionForAlias("contacts", call, "contactsPermissionCallback");
        }
    }

    @PermissionCallback
    private void contactsPermissionCallback(PluginCall call) {
        if (hasRequiredPermissions()) {
            JSObject result = new JSObject();
            result.put("granted", true);
            call.resolve(result);
        } else {
            JSObject result = new JSObject();
            result.put("granted", false);
            result.put("message", "Contacts permission denied");
            call.resolve(result);
        }
    }

    @PluginMethod
    public void getContacts(PluginCall call) {
        if (!hasRequiredPermissions()) {
            call.reject("Contacts permission not granted");
            return;
        }

        List<JSObject> contacts = new ArrayList<>();
        ContentResolver contentResolver = getContext().getContentResolver();

        Cursor cursor = contentResolver.query(
            ContactsContract.Contacts.CONTENT_URI,
            null,
            null,
            null,
            ContactsContract.Contacts.DISPLAY_NAME + " ASC"
        );

        if (cursor != null && cursor.getCount() > 0) {
            while (cursor.moveToNext()) {
                String contactId = cursor.getString(
                    cursor.getColumnIndex(ContactsContract.Contacts._ID)
                );
                String name = cursor.getString(
                    cursor.getColumnIndex(ContactsContract.Contacts.DISPLAY_NAME)
                );

                if (name == null || name.isEmpty()) {
                    continue;
                }

                JSObject contact = new JSObject();
                contact.put("name", name);

                // Get phone numbers
                List<String> phoneNumbers = new ArrayList<>();
                Cursor phoneCursor = contentResolver.query(
                    ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                    null,
                    ContactsContract.CommonDataKinds.Phone.CONTACT_ID + " = ?",
                    new String[]{contactId},
                    null
                );

                if (phoneCursor != null) {
                    while (phoneCursor.moveToNext()) {
                        String phone = phoneCursor.getString(
                            phoneCursor.getColumnIndex(
                                ContactsContract.CommonDataKinds.Phone.NUMBER
                            )
                        );
                        if (phone != null && !phone.isEmpty()) {
                            phoneNumbers.add(phone);
                        }
                    }
                    phoneCursor.close();
                }
                contact.put("phoneNumbers", phoneNumbers);

                // Get emails
                List<String> emails = new ArrayList<>();
                Cursor emailCursor = contentResolver.query(
                    ContactsContract.CommonDataKinds.Email.CONTENT_URI,
                    null,
                    ContactsContract.CommonDataKinds.Email.CONTACT_ID + " = ?",
                    new String[]{contactId},
                    null
                );

                if (emailCursor != null) {
                    while (emailCursor.moveToNext()) {
                        String email = emailCursor.getString(
                            emailCursor.getColumnIndex(
                                ContactsContract.CommonDataKinds.Email.DATA
                            )
                        );
                        if (email != null && !email.isEmpty()) {
                            emails.add(email);
                        }
                    }
                    emailCursor.close();
                }
                contact.put("emails", emails);

                // Get organization
                Cursor orgCursor = contentResolver.query(
                    ContactsContract.Data.CONTENT_URI,
                    new String[]{
                        ContactsContract.CommonDataKinds.Organization.COMPANY
                    },
                    ContactsContract.Data.CONTACT_ID + " = ? AND " +
                    ContactsContract.Data.MIMETYPE + " = ?",
                    new String[]{
                        contactId,
                        ContactsContract.CommonDataKinds.Organization.CONTENT_ITEM_TYPE
                    },
                    null
                );

                if (orgCursor != null && orgCursor.moveToFirst()) {
                    String organization = orgCursor.getString(0);
                    if (organization != null && !organization.isEmpty()) {
                        contact.put("organization", organization);
                    }
                    orgCursor.close();
                }

                contacts.add(contact);
            }
            cursor.close();
        }

        JSObject result = new JSObject();
        result.put("contacts", contacts);
        call.resolve(result);
    }

    private boolean hasRequiredPermissions() {
        return ContextCompat.checkSelfPermission(
            getContext(),
            Manifest.permission.READ_CONTACTS
        ) == PackageManager.PERMISSION_GRANTED;
    }
}
```

### 3. Register Plugin

In `android/app/src/main/java/com/aicaller/app/MainActivity.java`, add:

```java
import com.aicaller.app.ContactsPlugin;

// In onCreate or init, add:
this.init(savedInstanceState, new ArrayList<Class<? extends Plugin>>() {{
    add(ContactsPlugin.class);
}});
```

## Testing

1. Build and sync:
```bash
npm run build
npx cap sync
```

2. Open in native IDE:
```bash
npx cap open ios
# or
npx cap open android
```

3. Run the app and test the "Import from Phone" button!

## Notes

- iOS requires the permission description in Info.plist
- Android requires runtime permission request (handled automatically)
- The plugin will request permission when you click "Import from Phone"
- On web browsers, it falls back to Contact Picker API (Chrome/Edge Android)

