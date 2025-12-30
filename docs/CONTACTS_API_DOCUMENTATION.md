# iOS and Android Contacts API - Official Documentation Reference

This document compiles official resources, APIs, and best practices for accessing contacts on iOS and Android platforms. All information is sourced from official Apple and Google documentation, GitHub repositories, and developer resources.

---

## Table of Contents

1. [iOS Contacts Framework](#ios-contacts-framework)
2. [Android Contacts Provider](#android-contacts-provider)
3. [Permissions and Privacy](#permissions-and-privacy)
4. [Official Resources](#official-resources)
5. [Code Examples](#code-examples)
6. [Best Practices](#best-practices)
7. [Third-Party Libraries](#third-party-libraries)

---

## iOS Contacts Framework

### Overview

The **Contacts framework** (iOS 9+) is Apple's modern API for accessing and managing user contacts. It replaced the deprecated Address Book framework.

### Official Documentation

- **Main Documentation**: [Contacts Framework - Apple Developer](https://developer.apple.com/documentation/contacts)
- **Accessing Contact Data Guide**: [Accessing a Person's Contact Data Using Contacts and ContactsUI](https://developer.apple.com/documentation/contacts/accessing-a-person-s-contact-data-using-contacts-and-contactsui)
- **API Reference**: [CNContactStore Class Reference](https://developer.apple.com/documentation/contacts/cncontactstore)
- **CNContact Class**: [CNContact - Apple Developer](https://developer.apple.com/documentation/contacts/cncontact)

### Key Classes

#### CNContactStore
The central class for accessing contacts. Provides methods to:
- Request permission (`requestAccess(for:completionHandler:)`)
- Fetch contacts (`enumerateContacts(with:usingBlock:)`)
- Save contacts (`save(_:didSaveContacts:)`)

#### CNContact
Represents a single contact with properties:
- `givenName`, `familyName`
- `phoneNumbers` (array of `CNLabeledValue<CNPhoneNumber>`)
- `emailAddresses` (array of `CNLabeledValue<NSString>`)
- `organizationName`
- `postalAddresses`
- `imageData`

#### CNMutableContact
Mutable version of `CNContact` for creating/updating contacts.

### Permission Requirements

**Required**: `NSContactsUsageDescription` in `Info.plist`

```xml
<key>NSContactsUsageDescription</key>
<string>This app needs access to your contacts to import them for calling and messaging.</string>
```

### Authorization Status

```swift
import Contacts

let status = CNContactStore.authorizationStatus(for: .contacts)
switch status {
case .authorized:
    // Access granted
case .denied, .restricted:
    // Access denied
case .notDetermined:
    // Request permission
}
```

### Requesting Permission

```swift
let store = CNContactStore()
store.requestAccess(for: .contacts) { granted, error in
    if granted {
        // Access granted
    } else {
        // Handle denial
    }
}
```

### Fetching Contacts

```swift
let keysToFetch = [
    CNContactGivenNameKey,
    CNContactFamilyNameKey,
    CNContactPhoneNumbersKey,
    CNContactEmailAddressesKey,
    CNContactOrganizationNameKey
] as [CNKeyDescriptor]

let request = CNContactFetchRequest(keysToFetch: keysToFetch)
var contacts: [CNContact] = []

do {
    try store.enumerateContacts(with: request) { contact, stop in
        contacts.append(contact)
    }
} catch {
    print("Error fetching contacts: \(error)")
}
```

### Creating/Updating Contacts

```swift
let contact = CNMutableContact()
contact.givenName = "John"
contact.familyName = "Doe"

let phoneNumber = CNLabeledValue(
    label: CNLabelPhoneNumberMobile,
    value: CNPhoneNumber(stringValue: "+1234567890")
)
contact.phoneNumbers = [phoneNumber]

let saveRequest = CNSaveRequest()
saveRequest.add(contact, toContainerWithIdentifier: nil)

do {
    try store.execute(saveRequest)
} catch {
    print("Error saving contact: \(error)")
}
```

### Official GitHub Resources

- **Apple Sample Code**: Search for "Contacts" in [Apple Sample Code](https://developer.apple.com/sample-code/)
- **Swift Package Manager**: Contacts framework is part of the system frameworks

---

## Android Contacts Provider

### Overview

The **Contacts Provider** is Android's content provider that manages the device's central repository of contact data. It allows apps to read, insert, update, and delete contacts.

### Official Documentation

- **Main Guide**: [Contacts Provider - Android Developers](https://developer.android.com/guide/topics/providers/contacts-provider)
- **ContactsContract Reference**: [ContactsContract - Android Developers](https://developer.android.com/reference/android/provider/ContactsContract)
- **Using the Contacts API**: [Using the Contacts API](https://developer.android.com/training/contacts-provider)
- **People API (Google)**: [People API - Google Developers](https://developers.google.com/people/v1/contacts)

### Key Classes

#### ContactsContract.Contacts
Main table containing contact summary information.

#### ContactsContract.CommonDataKinds.Phone
Phone number data for contacts.

#### ContactsContract.CommonDataKinds.Email
Email address data for contacts.

#### ContactsContract.Data
Generic data table for all contact information.

### Permission Requirements

**Required in AndroidManifest.xml**:
```xml
<uses-permission android:name="android.permission.READ_CONTACTS" />
<uses-permission android:name="android.permission.WRITE_CONTACTS" />
```

**Runtime Permission** (Android 6.0+):
Must request `READ_CONTACTS` permission at runtime.

### Requesting Runtime Permission

```java
if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS)
        != PackageManager.PERMISSION_GRANTED) {
    ActivityCompat.requestPermissions(
        this,
        new String[]{Manifest.permission.READ_CONTACTS},
        REQUEST_READ_CONTACTS
    );
}
```

### Handling Permission Result

```java
@Override
public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
    if (requestCode == REQUEST_READ_CONTACTS) {
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            // Permission granted, fetch contacts
        } else {
            // Permission denied
        }
    }
}
```

### Querying Contacts

```java
ContentResolver contentResolver = getContentResolver();

// Query contacts
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
        
        // Get phone numbers
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
            }
            phoneCursor.close();
        }
    }
    cursor.close();
}
```

### Inserting Contacts

```java
ContentValues values = new ContentValues();
values.put(ContactsContract.RawContacts.ACCOUNT_TYPE, accountType);
values.put(ContactsContract.RawContacts.ACCOUNT_NAME, accountName);

Uri rawContactUri = contentResolver.insert(
    ContactsContract.RawContacts.CONTENT_URI,
    values
);
long rawContactId = ContentUris.parseId(rawContactUri);

// Add name
values.clear();
values.put(ContactsContract.Data.RAW_CONTACT_ID, rawContactId);
values.put(ContactsContract.Data.MIMETYPE, 
    ContactsContract.CommonDataKinds.StructuredName.CONTENT_ITEM_TYPE);
values.put(ContactsContract.CommonDataKinds.StructuredName.DISPLAY_NAME, "John Doe");
contentResolver.insert(ContactsContract.Data.CONTENT_URI, values);

// Add phone
values.clear();
values.put(ContactsContract.Data.RAW_CONTACT_ID, rawContactId);
values.put(ContactsContract.Data.MIMETYPE,
    ContactsContract.CommonDataKinds.Phone.CONTENT_ITEM_TYPE);
values.put(ContactsContract.CommonDataKinds.Phone.NUMBER, "+1234567890");
values.put(ContactsContract.CommonDataKinds.Phone.TYPE,
    ContactsContract.CommonDataKinds.Phone.TYPE_MOBILE);
contentResolver.insert(ContactsContract.Data.CONTENT_URI, values);
```

### Official GitHub Resources

- **Android Samples**: [Android Samples Repository](https://github.com/android)
- **Contacts Provider Examples**: Search for "contacts" in Android samples

---

## Permissions and Privacy

### iOS Privacy Requirements

1. **Info.plist Entry**: Must include `NSContactsUsageDescription`
2. **User Consent**: System automatically prompts user
3. **Privacy Settings**: Users can revoke access in Settings > Privacy > Contacts
4. **App Store Review**: Apple reviews permission usage descriptions

**Human Interface Guidelines**: [Requesting Permission - Apple HIG](https://developer.apple.com/design/human-interface-guidelines/patterns/requesting-permission/)

### Android Privacy Requirements

1. **Manifest Declaration**: Declare permissions in `AndroidManifest.xml`
2. **Runtime Request**: Request permissions at runtime (API 23+)
3. **Permission Rationale**: Explain why permission is needed before requesting
4. **Privacy Settings**: Users can manage permissions in Settings > Apps > Permissions

**Material Design Guidelines**: [Permissions - Material Design](https://material.io/design/platform-guidance/android-permissions.html)

### Best Practices

1. **Request Only When Needed**: Don't request permission on app launch
2. **Explain Why**: Provide clear explanation before requesting
3. **Handle Denial Gracefully**: Don't block app functionality if denied
4. **Respect User Choice**: Never request again if user denied
5. **Minimize Data**: Only request access to fields you need
6. **Secure Storage**: Encrypt contact data if storing locally
7. **Transparent Usage**: Clearly state how contact data is used

---

## Official Resources

### Apple Official Resources

1. **Developer Documentation**
   - [Contacts Framework Documentation](https://developer.apple.com/documentation/contacts)
   - [CNContactStore Reference](https://developer.apple.com/documentation/contacts/cncontactstore)
   - [CNContact Reference](https://developer.apple.com/documentation/contacts/cncontact)

2. **Guides and Tutorials**
   - [Accessing Contact Data Guide](https://developer.apple.com/documentation/contacts/accessing-a-person-s-contact-data-using-contacts-and-contactsui)
   - [WWDC Videos](https://developer.apple.com/videos/) - Search for "Contacts"

3. **Human Interface Guidelines**
   - [Requesting Permission](https://developer.apple.com/design/human-interface-guidelines/patterns/requesting-permission/)

4. **Developer Forums**
   - [Apple Developer Forums](https://developer.apple.com/forums/) - Search "Contacts"

### Android Official Resources

1. **Developer Documentation**
   - [Contacts Provider Guide](https://developer.android.com/guide/topics/providers/contacts-provider)
   - [ContactsContract Reference](https://developer.android.com/reference/android/provider/ContactsContract)
   - [Using the Contacts API](https://developer.android.com/training/contacts-provider)

2. **Code Samples**
   - [Android Samples](https://github.com/android)
   - [Android Code Search](https://cs.android.com/) - Search for ContactsContract

3. **Material Design**
   - [Permissions Guidelines](https://material.io/design/platform-guidance/android-permissions.html)

4. **Google Developers**
   - [People API Documentation](https://developers.google.com/people/v1/contacts)

### GitHub Official Resources

#### Apple
- **Swift Evolution**: [Swift Evolution Repository](https://github.com/apple/swift-evolution)
- **Sample Code**: Search Apple's official sample code repositories

#### Android
- **Android Open Source Project**: [AOSP Repository](https://github.com/aosp-mirror)
- **Android Samples**: [Android Samples](https://github.com/android)
- **AndroidX**: [AndroidX Contacts](https://github.com/androidx/androidx) - Check for Contacts-related libraries

---

## Code Examples

### Complete iOS Example

```swift
import Contacts
import UIKit

class ContactsManager {
    private let store = CNContactStore()
    
    func requestAccess(completion: @escaping (Bool) -> Void) {
        store.requestAccess(for: .contacts) { granted, error in
            DispatchQueue.main.async {
                completion(granted)
            }
        }
    }
    
    func fetchContacts() -> [CNContact] {
        let keysToFetch = [
            CNContactGivenNameKey,
            CNContactFamilyNameKey,
            CNContactPhoneNumbersKey,
            CNContactEmailAddressesKey,
            CNContactOrganizationNameKey
        ] as [CNKeyDescriptor]
        
        let request = CNContactFetchRequest(keysToFetch: keysToFetch)
        var contacts: [CNContact] = []
        
        do {
            try store.enumerateContacts(with: request) { contact, stop in
                contacts.append(contact)
            }
        } catch {
            print("Error: \(error)")
        }
        
        return contacts
    }
}
```

### Complete Android Example

```java
import android.Manifest;
import android.content.ContentResolver;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.provider.ContactsContract;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class ContactsManager {
    private static final int PERMISSION_REQUEST_CODE = 100;
    private Activity activity;
    
    public ContactsManager(Activity activity) {
        this.activity = activity;
    }
    
    public void requestPermission() {
        if (ContextCompat.checkSelfPermission(activity, Manifest.permission.READ_CONTACTS)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(activity,
                    new String[]{Manifest.permission.READ_CONTACTS},
                    PERMISSION_REQUEST_CODE);
        }
    }
    
    public List<Contact> fetchContacts() {
        List<Contact> contacts = new ArrayList<>();
        ContentResolver contentResolver = activity.getContentResolver();
        
        Cursor cursor = contentResolver.query(
            ContactsContract.Contacts.CONTENT_URI,
            null,
            null,
            null,
            ContactsContract.Contacts.DISPLAY_NAME + " ASC"
        );
        
        if (cursor != null && cursor.getCount() > 0) {
            while (cursor.moveToNext()) {
                String id = cursor.getString(
                    cursor.getColumnIndex(ContactsContract.Contacts._ID)
                );
                String name = cursor.getString(
                    cursor.getColumnIndex(ContactsContract.Contacts.DISPLAY_NAME)
                );
                
                Contact contact = new Contact(id, name);
                contact.setPhoneNumbers(getPhoneNumbers(contentResolver, id));
                contact.setEmails(getEmails(contentResolver, id));
                contacts.add(contact);
            }
            cursor.close();
        }
        
        return contacts;
    }
    
    private List<String> getPhoneNumbers(ContentResolver resolver, String contactId) {
        List<String> phones = new ArrayList<>();
        Cursor phoneCursor = resolver.query(
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
                phones.add(phone);
            }
            phoneCursor.close();
        }
        
        return phones;
    }
    
    private List<String> getEmails(ContentResolver resolver, String contactId) {
        List<String> emails = new ArrayList<>();
        Cursor emailCursor = resolver.query(
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
                emails.add(email);
            }
            emailCursor.close();
        }
        
        return emails;
    }
}
```

---

## Best Practices

### iOS Best Practices

1. **Request Permission Contextually**: Request when user performs an action that needs contacts
2. **Use Specific Keys**: Only request contact keys you actually need
3. **Handle Errors**: Always handle permission denial gracefully
4. **Background Threads**: Perform contact operations on background threads
5. **Cache Results**: Cache contact data to avoid repeated queries
6. **Respect Privacy**: Never share contact data without explicit user consent

### Android Best Practices

1. **Check Permission First**: Always check permission status before accessing
2. **Request at Runtime**: Request permissions at runtime, not just in manifest
3. **Explain Rationale**: Show explanation dialog before requesting permission
4. **Handle All Cases**: Handle granted, denied, and "don't ask again" cases
5. **Use ContentResolver Efficiently**: Close cursors and use projections
6. **Background Operations**: Perform contact queries on background threads
7. **Batch Operations**: Use batch operations for multiple contact updates

### Cross-Platform Considerations

1. **Unified API**: Use a wrapper/abstraction layer for cross-platform apps
2. **Consistent UX**: Provide similar user experience across platforms
3. **Error Handling**: Handle platform-specific errors consistently
4. **Testing**: Test on both platforms with various permission states
5. **Privacy Compliance**: Ensure compliance with GDPR, CCPA, etc.

---

## Third-Party Libraries

### iOS Libraries

#### Ohana (Uber Engineering)
- **GitHub**: [Ohana - iOS Contacts Library](https://github.com/uber/ohana-ios)
- **Description**: Modular iOS contacts library
- **Features**: 
  - Modular architecture
  - Contact deduplication
  - Background processing
- **License**: Apache 2.0

### Android Libraries

#### Contacts-Android
- **GitHub**: [contacts-android](https://github.com/vestrel00/contacts-android)
- **Description**: Modern Kotlin-based Contacts API
- **Features**:
  - Kotlin-first API
  - No ContentProviders/cursors
  - Type-safe queries
- **License**: Apache 2.0

#### Contact Store
- **Website**: [Contact Store Documentation](https://alexstyl.github.io/contactstore/)
- **Description**: Modern API for Android contacts
- **Features**:
  - Coroutines support
  - Modern developer experience
  - Type-safe

### Cross-Platform

#### Capacitor Contacts Plugin
- **Note**: Official Capacitor plugin may not exist, but custom plugins can be created
- **Capacitor Docs**: [Capacitor Plugin Development](https://capacitorjs.com/docs/plugins)

---

## Version Compatibility

### iOS

- **Contacts Framework**: iOS 9.0+
- **CNContactStore**: iOS 9.0+
- **Deprecated**: Address Book framework (iOS 9.0+)

### Android

- **ContactsContract**: API Level 5+
- **Runtime Permissions**: API Level 23+ (Android 6.0)
- **Scoped Storage**: API Level 29+ (Android 10) - affects contact access patterns

---

## Troubleshooting

### iOS Common Issues

1. **Permission Denied**: Check `Info.plist` has `NSContactsUsageDescription`
2. **No Contacts Returned**: Verify keys requested match contact data
3. **Performance**: Use background threads for large contact lists
4. **Memory**: Release contact objects when done

### Android Common Issues

1. **Permission Denied**: Check manifest and runtime permission request
2. **Empty Cursor**: Verify projection columns match data
3. **Performance**: Use projections to limit data retrieved
4. **Null Pointer**: Always check cursor != null before use

---

## Additional Resources

### Apple Developer Resources
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [WWDC Videos](https://developer.apple.com/videos/)
- [Apple Developer Forums](https://developer.apple.com/forums/)

### Android Developer Resources
- [Android Developers](https://developer.android.com/)
- [Android Code Search](https://cs.android.com/)
- [Android Developers Blog](https://android-developers.googleblog.com/)

### Privacy and Compliance
- [Apple Privacy Guidelines](https://developer.apple.com/app-store/review/guidelines/#privacy)
- [Android Privacy Best Practices](https://developer.android.com/training/best-permissions)
- [GDPR Compliance](https://gdpr.eu/)

---

## Last Updated

This document was compiled from official sources as of December 2024. Always refer to the latest official documentation for the most current information.

---

## Quick Reference

### iOS Permission Key
```xml
<key>NSContactsUsageDescription</key>
<string>Your description here</string>
```

### Android Permission
```xml
<uses-permission android:name="android.permission.READ_CONTACTS" />
```

### iOS Request Permission
```swift
store.requestAccess(for: .contacts) { granted, error in }
```

### Android Request Permission
```java
ActivityCompat.requestPermissions(activity, 
    new String[]{Manifest.permission.READ_CONTACTS}, 
    REQUEST_CODE);
```

---

**Note**: This documentation is compiled from official sources. For the most up-to-date information, always refer to the official Apple and Google developer documentation.

