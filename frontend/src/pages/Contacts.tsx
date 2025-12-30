import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { contactsApi, type Contact as APIContact, type ContactCreate } from '@/lib/api';
import { Loader2, Upload, Phone, Mail, Building, UserPlus, Search, Trash2, X } from 'lucide-react';
import { requestContactsAccess, formatContactForAPI, isNativeContactsAvailable, isContactPickerAvailable } from '@/lib/contacts';

export const Contacts = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [newContact, setNewContact] = useState<ContactCreate>({
    name: '',
    phone_number: '',
    email: '',
    organization: '',
    notes: '',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();

  // Fetch contacts
  const { data: contacts = [], isLoading, error } = useQuery<APIContact[]>({
    queryKey: ['contacts', searchTerm],
    queryFn: () => contactsApi.list(searchTerm || undefined),
  });

  // Create contact mutation
  const createContact = useMutation({
    mutationFn: contactsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success('Contact added successfully');
      setShowAddForm(false);
      setNewContact({
        name: '',
        phone_number: '',
        email: '',
        organization: '',
        notes: '',
      });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add contact');
    },
  });

  // Delete contact mutation
  const deleteContact = useMutation({
    mutationFn: contactsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success('Contact deleted');
    },
    onError: () => {
      toast.error('Failed to delete contact');
    },
  });

  // Import contacts from device (native or Contact Picker API)
  const importContacts = useMutation({
    mutationFn: async () => {
      // Request contacts access (handles permissions automatically)
      const deviceContacts = await requestContactsAccess();
      
      // Format contacts for API
      const formattedContacts = deviceContacts.map(formatContactForAPI).filter(c => c.name);
      
      if (formattedContacts.length === 0) {
        throw new Error('No contacts found or selected');
      }
      
      // Bulk create contacts
      return contactsApi.bulkCreate(formattedContacts);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success(`Successfully imported ${data.length} contact(s)`);
    },
    onError: (error: any) => {
      const errorMessage = error.message || error.response?.data?.detail || 'Failed to import contacts';
      toast.error(errorMessage);
    },
  });

  // Upload file (vCard or CSV)
  const uploadFile = useMutation({
    mutationFn: async (file: File) => {
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (extension === 'vcf') {
        return contactsApi.uploadVCard(file);
      } else if (extension === 'csv') {
        return contactsApi.uploadCSV(file);
      } else {
        throw new Error('Unsupported file type. Please upload a .vcf or .csv file');
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success(`Successfully imported ${data.contacts_created} contact(s)`);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || error.message || 'Failed to upload file');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
  });

  const handleImportContacts = async () => {
    // This will request permission and import contacts
    importContacts.mutate();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadFile.mutate(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContact.name.trim()) {
      toast.error('Name is required');
      return;
    }
    createContact.mutate(newContact, {
      onSuccess: () => {
        toast.success('Contact created successfully');
        setNewContact({ name: '', phone_number: '', email: '', organization: '' });
        setShowAddForm(false);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create contact');
      },
    });
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Contacts</h1>
        <p className="text-white/80">
          Manage your contacts and import from your phone
        </p>
      </div>

      {/* Upload Options */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Import Contacts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={handleImportContacts}
              disabled={importContacts.isPending}
              variant="primary"
              className="flex items-center gap-2"
            >
              {importContacts.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Importing Contacts...
                </>
              ) : (
                <>
                  <Phone className="w-4 h-4" />
                  Import from Phone
                </>
              )}
            </Button>
            
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadFile.isPending}
              variant="secondary"
              className="flex items-center gap-2"
            >
              {uploadFile.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload vCard/CSV File
                </>
              )}
            </Button>
            
            <input
              ref={fileInputRef}
              type="file"
              accept=".vcf,.csv"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
          
          <div className="text-sm text-gray-400 space-y-1">
            {isNativeContactsAvailable() ? (
              <p>
                <strong>Native App:</strong> Click "Import from Phone" to request permission and access all your contacts.
              </p>
            ) : isContactPickerAvailable() ? (
              <p>
                <strong>Web Browser:</strong> Click "Import from Phone" to select contacts using the Contact Picker API (Chrome/Edge Android).
              </p>
            ) : (
              <>
                <p>
                  <strong>Note:</strong> Direct contact access is not available in this browser.
                </p>
                <p>
                  For iOS Safari and unsupported browsers, export your contacts as a vCard (.vcf) file from your phone's Contacts app and upload it here.
                </p>
                <p className="mt-2 text-purple-400">
                  💡 <strong>Tip:</strong> Build the native app with Capacitor for full contact access on iOS and Android!
                </p>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Add Contact Form */}
      {showAddForm && (
        <Card className="mb-6">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Add Contact</CardTitle>
            <Button
              onClick={() => setShowAddForm(false)}
              variant="ghost"
              size="sm"
            >
              <X className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Name *
                </label>
                <Input
                  value={newContact.name}
                  onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                  placeholder="John Doe"
                  required
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Phone Number
                  </label>
                  <Input
                    type="tel"
                    value={newContact.phone_number}
                    onChange={(e) => setNewContact({ ...newContact, phone_number: e.target.value })}
                    placeholder="+1234567890"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Email
                  </label>
                  <Input
                    type="email"
                    value={newContact.email}
                    onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                    placeholder="john@example.com"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Organization
                </label>
                <Input
                  value={newContact.organization}
                  onChange={(e) => setNewContact({ ...newContact, organization: e.target.value })}
                  placeholder="Company Name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Notes
                </label>
                <Textarea
                  value={newContact.notes}
                  onChange={(e) => setNewContact({ ...newContact, notes: e.target.value })}
                  placeholder="Additional notes..."
                  rows={3}
                />
              </div>
              
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={createContact.isPending}
                  variant="primary"
                >
                  {createContact.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    'Add Contact'
                  )}
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setNewContact({
                      name: '',
                      phone_number: '',
                      email: '',
                      organization: '',
                      notes: '',
                    });
                  }}
                  variant="secondary"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search contacts by name, phone, email, or organization..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Contacts List */}
      {error ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-600">Failed to load contacts</p>
          </CardContent>
        </Card>
      ) : contacts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 italic">
              {searchTerm ? 'No contacts found matching your search.' : 'No contacts yet. Add or import contacts to get started!'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {contacts.map((contact) => (
            <ContactCard
              key={contact.id}
              contact={contact}
              onDelete={() => setDeleteConfirm({ id: contact.id, name: contact.name })}
            />
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => {
          if (deleteConfirm) {
            deleteContact.mutate(deleteConfirm.id, {
              onSuccess: () => {
                toast.success(`${deleteConfirm.name} deleted`);
                setDeleteConfirm(null);
              },
              onError: () => {
                toast.error('Failed to delete contact');
              },
            });
          }
        }}
        title="Delete Contact"
        message={`Are you sure you want to delete ${deleteConfirm?.name}? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={deleteContact.isPending}
      />
    </div>
  );
};

const ContactCard = ({ contact, onDelete }: { contact: APIContact; onDelete: () => void }) => {
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <Link to={`/contacts/${contact.id}`} className="flex-1">
            <h3 className="text-lg font-semibold text-white hover:text-purple-400 transition-colors">
              {contact.name}
            </h3>
          </Link>
          <Button
            onClick={onDelete}
            variant="ghost"
            size="sm"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="space-y-2">
          {contact.phone_number && (
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Phone className="w-4 h-4 text-gray-400" />
              <a href={`tel:${contact.phone_number}`} className="hover:text-purple-600">
                {contact.phone_number}
              </a>
            </div>
          )}
          
          {contact.email && (
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Mail className="w-4 h-4 text-gray-400" />
              <a href={`mailto:${contact.email}`} className="hover:text-purple-600">
                {contact.email}
              </a>
            </div>
          )}
          
          {contact.organization && (
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Building className="w-4 h-4 text-gray-400" />
              {contact.organization}
            </div>
          )}
          
          {contact.notes && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-sm text-gray-400">{contact.notes}</p>
            </div>
          )}
        </div>
        <div className="mt-4 pt-4 border-t border-gray-700">
          <Link to={`/contacts/${contact.id}`}>
            <Button variant="ghost" size="sm" className="w-full">
              View Details
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};

