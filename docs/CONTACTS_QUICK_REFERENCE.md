# Contacts API Quick Reference

Quick reference guide for iOS and Android contact access. For detailed documentation, see [CONTACTS_API_DOCUMENTATION.md](./CONTACTS_API_DOCUMENTATION.md).

---

## iOS Quick Reference

### Permission Setup

**Info.plist**:
```xml
<key>NSContactsUsageDescription</key>
<string>This app needs access to your contacts to import them for calling and messaging.</string>
```

### Request Permission

```swift
import Contacts

let store = CNContactStore()
store.requestAccess(for: .contacts) { granted, error in
    if granted {
        // Access granted
    }
}
```

### Fetch Contacts

```swift
let keys = [CNContactGivenNameKey, CNContactFamilyNameKey, 
            CNContactPhoneNumbersKey, CNContactEmailAddressesKey] as [CNKeyDescriptor]
let request = CNContactFetchRequest(keysToFetch: keys)

try store.enumerateContacts(with: request) { contact, stop in
    // Process contact
}
```

### Official Links

- [Contacts Framework Docs](https://developer.apple.com/documentation/contacts)
- [CNContactStore Reference](https://developer.apple.com/documentation/contacts/cncontactstore)
- [Accessing Contact Data Guide](https://developer.apple.com/documentation/contacts/accessing-a-person-s-contact-data-using-contacts-and-contactsui)

---

## Android Quick Reference

### Permission Setup

**AndroidManifest.xml**:
```xml
<uses-permission android:name="android.permission.READ_CONTACTS" />
```

### Request Runtime Permission

```java
if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS)
        != PackageManager.PERMISSION_GRANTED) {
    ActivityCompat.requestPermissions(this,
            new String[]{Manifest.permission.READ_CONTACTS},
            REQUEST_CODE);
}
```

### Query Contacts

```java
ContentResolver resolver = getContentResolver();
Cursor cursor = resolver.query(
    ContactsContract.Contacts.CONTENT_URI,
    null, null, null,
    ContactsContract.Contacts.DISPLAY_NAME + " ASC"
);

if (cursor != null) {
    while (cursor.moveToNext()) {
        String name = cursor.getString(
            cursor.getColumnIndex(ContactsContract.Contacts.DISPLAY_NAME)
        );
        // Process contact
    }
    cursor.close();
}
```

### Official Links

- [Contacts Provider Guide](https://developer.android.com/guide/topics/providers/contacts-provider)
- [ContactsContract Reference](https://developer.android.com/reference/android/provider/ContactsContract)
- [Using the Contacts API](https://developer.android.com/training/contacts-provider)

---

## Common Patterns

### Check Permission Status

**iOS**:
```swift
let status = CNContactStore.authorizationStatus(for: .contacts)
```

**Android**:
```java
int status = ContextCompat.checkSelfPermission(context, Manifest.permission.READ_CONTACTS);
```

### Handle Permission Denial

**iOS**: User can change in Settings > Privacy > Contacts

**Android**: Show rationale dialog before requesting again

---

## Version Requirements

- **iOS**: Contacts Framework requires iOS 9.0+
- **Android**: ContactsContract requires API Level 5+, Runtime permissions require API 23+

---

## Third-Party Libraries

- **iOS**: [Ohana](https://github.com/uber/ohana-ios) - Uber's contacts library
- **Android**: [contacts-android](https://github.com/vestrel00/contacts-android) - Kotlin contacts API

---

For complete documentation, see [CONTACTS_API_DOCUMENTATION.md](./CONTACTS_API_DOCUMENTATION.md).

