import { useState } from 'react';
import toast from 'react-hot-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { usePreferences, useCreatePreference, useUpdatePreference, useDeletePreference, type PreferenceEntry, type PreferenceEntryCreate } from '@/lib/hooks';
import { Loader2, Search, Trash2, X, Plus, Star, AlertCircle, Globe, MapPin, Phone, Link as LinkIcon, Tag } from 'lucide-react';

const PREFERENCE_TYPES = ['VENDOR', 'PROVIDER', 'WEBSITE', 'LOCATION', 'TOOL', 'AVOID'] as const;
const PRIORITIES = ['PRIMARY', 'SECONDARY', 'AVOID'] as const;
const COMMON_CATEGORIES = [
  'groceries',
  'travel',
  'healthcare',
  'restaurants',
  'shopping',
  'services',
  'locations',
  'tools',
  'research',
  'other'
];

export const TrustedList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingEntry, setEditingEntry] = useState<PreferenceEntry | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [newEntry, setNewEntry] = useState<PreferenceEntryCreate>({
    type: 'VENDOR',
    category: 'other',
    name: '',
    priority: 'PRIMARY',
    tags: [],
  });

  // Fetch preferences
  const { data: preferences = [], isLoading, error } = usePreferences({
    search: searchTerm || undefined,
    category: categoryFilter || undefined,
    type: typeFilter || undefined,
  });

  // Create preference mutation
  const createPreference = useCreatePreference();
  
  // Update preference mutation
  const updatePreference = useUpdatePreference();
  
  // Delete preference mutation
  const deletePreference = useDeletePreference();

  const resetForm = () => {
    setNewEntry({
      type: 'VENDOR',
      category: 'other',
      name: '',
      priority: 'PRIMARY',
      tags: [],
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEntry.name.trim()) {
      toast.error('Name is required');
      return;
    }

    if (editingEntry) {
      updatePreference.mutate(
        { entryId: editingEntry.id, data: newEntry },
        {
          onSuccess: () => {
            toast.success('Preference updated');
            setEditingEntry(null);
            resetForm();
            setShowAddForm(false);
          },
          onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to update preference');
          },
        }
      );
    } else {
      createPreference.mutate(newEntry, {
        onSuccess: () => {
          toast.success('Preference added successfully');
          setShowAddForm(false);
          resetForm();
        },
        onError: (error: any) => {
          toast.error(error.response?.data?.detail || 'Failed to add preference');
        },
      });
    }
  };

  const handleEdit = (entry: PreferenceEntry) => {
    setEditingEntry(entry);
    setNewEntry({
      type: entry.type,
      category: entry.category,
      name: entry.name,
      priority: entry.priority,
      tags: entry.tags || [],
      url: entry.url,
      phone: entry.phone,
      address: entry.address,
      notes: entry.notes,
      constraints: entry.constraints,
      related_contact_id: entry.related_contact_id,
    });
    setShowAddForm(true);
  };

  const handleCancel = () => {
    setShowAddForm(false);
    setEditingEntry(null);
    resetForm();
  };

  const addTag = (tag: string) => {
    if (tag && !newEntry.tags?.includes(tag)) {
      setNewEntry({ ...newEntry, tags: [...(newEntry.tags || []), tag] });
    }
  };

  const removeTag = (tag: string) => {
    setNewEntry({ ...newEntry, tags: newEntry.tags?.filter(t => t !== tag) || [] });
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

  const groupedPreferences = preferences.reduce((acc, pref) => {
    const category = pref.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(pref);
    return acc;
  }, {} as Record<string, PreferenceEntry[]>);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Trusted List</h1>
        <p className="text-white/80">
          Your favorites & defaults — vendors, providers, locations, and tools the AI will use automatically
        </p>
      </div>

      {/* Add/Edit Form */}
      <Card className="mb-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{editingEntry ? 'Edit Preference' : 'Add Preference'}</CardTitle>
          <Button
            onClick={() => {
              if (showAddForm) {
                handleCancel();
              } else {
                setShowAddForm(true);
                setEditingEntry(null);
                resetForm();
              }
            }}
            variant="secondary"
            size="sm"
          >
            {showAddForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          </Button>
        </CardHeader>
        {showAddForm && (
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Type *
                  </label>
                  <select
                    value={newEntry.type}
                    onChange={(e) => setNewEntry({ ...newEntry, type: e.target.value as any })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
                    required
                  >
                    {PREFERENCE_TYPES.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Category *
                  </label>
                  <select
                    value={newEntry.category}
                    onChange={(e) => setNewEntry({ ...newEntry, category: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
                    required
                  >
                    {COMMON_CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Name *
                </label>
                <Input
                  value={newEntry.name}
                  onChange={(e) => setNewEntry({ ...newEntry, name: e.target.value })}
                  placeholder="e.g., Whole Foods, Dr. Smith, Google Calendar"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Priority *
                </label>
                <select
                  value={newEntry.priority}
                  onChange={(e) => setNewEntry({ ...newEntry, priority: e.target.value as any })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
                  required
                >
                  {PRIORITIES.map(pri => (
                    <option key={pri} value={pri}>{pri}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    URL
                  </label>
                  <Input
                    type="url"
                    value={newEntry.url || ''}
                    onChange={(e) => setNewEntry({ ...newEntry, url: e.target.value })}
                    placeholder="https://example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Phone
                  </label>
                  <Input
                    type="tel"
                    value={newEntry.phone || ''}
                    onChange={(e) => setNewEntry({ ...newEntry, phone: e.target.value })}
                    placeholder="+1234567890"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Address
                </label>
                <Textarea
                  value={newEntry.address || ''}
                  onChange={(e) => setNewEntry({ ...newEntry, address: e.target.value })}
                  placeholder="Street address, city, state, zip"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tags (comma-separated or press Enter)
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {newEntry.tags?.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-sm"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="hover:text-red-400"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <Input
                  placeholder="Add tag and press Enter"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      const tag = e.currentTarget.value.trim();
                      if (tag) {
                        addTag(tag);
                        e.currentTarget.value = '';
                      }
                    }
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Notes
                </label>
                <Textarea
                  value={newEntry.notes || ''}
                  onChange={(e) => setNewEntry({ ...newEntry, notes: e.target.value })}
                  placeholder="Additional notes, preferences, or constraints..."
                  rows={3}
                />
              </div>

              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={createPreference.isPending || updatePreference.isPending}
                  variant="primary"
                >
                  {(createPreference.isPending || updatePreference.isPending) ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      {editingEntry ? 'Updating...' : 'Adding...'}
                    </>
                  ) : (
                    editingEntry ? 'Update Preference' : 'Add Preference'
                  )}
                </Button>
                <Button
                  type="button"
                  onClick={handleCancel}
                  variant="secondary"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        )}
      </Card>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search preferences..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex flex-wrap gap-4">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
              >
                <option value="">All Categories</option>
                {COMMON_CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-600"
              >
                <option value="">All Types</option>
                {PREFERENCE_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recently Used Section */}
      {preferences.length > 0 && !searchTerm && !categoryFilter && !typeFilter && (
        <Card className="bg-slate-900/50 border-slate-700 mb-6">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-400" />
              Recently Used
            </CardTitle>
          </CardHeader>
          <CardContent>
            {preferences.filter((p) => p.last_used_at).length === 0 ? (
              <p className="text-slate-400 text-sm">No recently used preferences</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {preferences
                  .filter((p) => p.last_used_at)
                  .sort((a, b) => {
                    const dateA = new Date(a.last_used_at!).getTime();
                    const dateB = new Date(b.last_used_at!).getTime();
                    return dateB - dateA;
                  })
                  .slice(0, 4)
                  .map((pref) => (
                    <div
                      key={pref.id}
                      className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 hover:border-purple-500/50 transition-colors cursor-pointer"
                      onClick={() => handleEdit(pref)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {pref.priority === 'PRIMARY' && (
                          <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                        )}
                        <span className="font-medium text-white text-sm truncate">
                          {pref.name}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 capitalize">{pref.category}</p>
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Preferences List */}
      {error ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <p className="text-red-400">Failed to load preferences</p>
          </CardContent>
        </Card>
      ) : preferences.length === 0 ? (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <Star className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
            <p className="text-slate-400 mb-2">
              {searchTerm || categoryFilter || typeFilter
                ? 'No preferences found matching your filters.'
                : 'No preferences yet'}
            </p>
            <p className="text-sm text-slate-500 mb-4">
              Add your trusted vendors, providers, and defaults to get started!
            </p>
            <Button onClick={() => setShowAddForm(true)} variant="primary">
              Add Your First Preference
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedPreferences).map(([category, prefs]) => (
            <div key={category}>
              <h2 className="text-xl font-semibold text-white mb-4 capitalize">{category}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {prefs.map((pref) => (
                  <PreferenceCard
                    key={pref.id}
                    preference={pref}
                    onEdit={() => handleEdit(pref)}
                    onDelete={() => setDeleteConfirm({ id: pref.id, name: pref.name })}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => {
          if (deleteConfirm) {
            deletePreference.mutate(deleteConfirm.id, {
              onSuccess: () => {
                toast.success(`${deleteConfirm.name} deleted`);
                setDeleteConfirm(null);
              },
              onError: () => {
                toast.error('Failed to delete preference');
              },
            });
          }
        }}
        title="Delete Preference"
        message={`Are you sure you want to delete "${deleteConfirm?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={deletePreference.isPending}
      />
    </div>
  );
};

const PreferenceCard = ({
  preference,
  onEdit,
  onDelete,
}: {
  preference: PreferenceEntry;
  onEdit: () => void;
  onDelete: () => void;
}) => {
  const getPriorityIcon = () => {
    switch (preference.priority) {
      case 'PRIMARY':
        return <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />;
      case 'AVOID':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getTypeIcon = () => {
    switch (preference.type) {
      case 'WEBSITE':
        return <Globe className="w-4 h-4" />;
      case 'LOCATION':
        return <MapPin className="w-4 h-4" />;
      case 'PROVIDER':
        return <Phone className="w-4 h-4" />;
      default:
        return <Tag className="w-4 h-4" />;
    }
  };

  return (
    <Card className="hover:border-purple-600 transition-colors">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            {getTypeIcon()}
            <h3 className="text-lg font-semibold text-white">{preference.name}</h3>
            {getPriorityIcon()}
          </div>
          <div className="flex gap-1">
            <Button
              onClick={onEdit}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
            >
              Edit
            </Button>
            <Button
              onClick={onDelete}
              variant="ghost"
              size="sm"
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-gray-400">
            <span className="font-medium">Type:</span>
            <span className="text-gray-300">{preference.type}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <span className="font-medium">Priority:</span>
            <span className={`font-semibold ${
              preference.priority === 'PRIMARY' ? 'text-yellow-500' :
              preference.priority === 'AVOID' ? 'text-red-500' :
              'text-gray-300'
            }`}>
              {preference.priority}
            </span>
          </div>

          {preference.url && (
            <div className="flex items-center gap-2 text-gray-300">
              <LinkIcon className="w-4 h-4 text-gray-400" />
              <a
                href={preference.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-purple-600 truncate"
              >
                {preference.url}
              </a>
            </div>
          )}

          {preference.phone && (
            <div className="flex items-center gap-2 text-gray-300">
              <Phone className="w-4 h-4 text-gray-400" />
              <a href={`tel:${preference.phone}`} className="hover:text-purple-600">
                {preference.phone}
              </a>
            </div>
          )}

          {preference.address && (
            <div className="flex items-start gap-2 text-gray-300">
              <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
              <span className="text-sm">{preference.address}</span>
            </div>
          )}

          {preference.tags && preference.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {preference.tags.map(tag => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-purple-600/20 text-purple-300 rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {preference.notes && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-sm text-gray-400">{preference.notes}</p>
            </div>
          )}

          {preference.last_used_at && (
            <div className="mt-2 text-xs text-gray-500">
              Last used: {new Date(preference.last_used_at).toLocaleDateString()}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

