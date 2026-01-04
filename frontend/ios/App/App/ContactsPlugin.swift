import Foundation
import Capacitor
import Contacts

@objc(ContactsPlugin)
public class ContactsPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "ContactsPlugin"
    public let jsName = "Contacts"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "requestPermission", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getContacts", returnType: CAPPluginReturnPromise)
    ]
    
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

