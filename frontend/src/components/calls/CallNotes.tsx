import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { callsAPI } from '../../api/calls';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { ConfirmationModal } from '../common/ConfirmationModal';
import { formatDate } from '../../utils/format';
import toast from 'react-hot-toast';

interface CallNote {
  id: number;
  call_id: string;
  created_by_user_id: string;
  note: string;
  tags?: string[];
  category?: string;
  created_at: string;
  updated_at: string;
}

interface CallNotesProps {
  callId: string;
}

export const CallNotes: React.FC<CallNotesProps> = ({ callId }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingNote, setEditingNote] = useState<CallNote | null>(null);
  const [newNote, setNewNote] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [newTags, setNewTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<{ isOpen: boolean; noteId: number | null }>({
    isOpen: false,
    noteId: null,
  });
  const queryClient = useQueryClient();

  const { data: notes, isLoading } = useQuery({
    queryKey: ['call-notes', callId],
    queryFn: () => callsAPI.getNotes(callId),
    enabled: !!callId,
  });

  const addNoteMutation = useMutation({
    mutationFn: (data: { note: string; category?: string; tags?: string[] }) =>
      callsAPI.addNote(callId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['call-notes', callId] });
      setNewNote('');
      setNewCategory('');
      setNewTags([]);
      setTagInput('');
      setShowAddForm(false);
      toast.success('Note added successfully');
    },
    onError: () => {
      toast.error('Failed to add note');
    },
  });

  const updateNoteMutation = useMutation({
    mutationFn: ({ noteId, data }: { noteId: number; data: { note?: string; category?: string; tags?: string[] } }) =>
      callsAPI.updateNote(callId, noteId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['call-notes', callId] });
      setEditingNote(null);
      setNewTags([]);
      setTagInput('');
      toast.success('Note updated successfully');
    },
    onError: () => {
      toast.error('Failed to update note');
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: (noteId: number) => callsAPI.deleteNote(callId, noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['call-notes', callId] });
      setDeleteConfirm({ isOpen: false, noteId: null });
      toast.success('Note deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete note');
    },
  });

  const handleAddNote = () => {
    if (!newNote.trim()) {
      toast.error('Please enter a note');
      return;
    }
    addNoteMutation.mutate({
      note: newNote,
      category: newCategory || undefined,
      tags: newTags.length > 0 ? newTags : undefined,
    });
  };

  const handleUpdateNote = () => {
    if (!editingNote || !newNote.trim()) {
      toast.error('Please enter a note');
      return;
    }
    updateNoteMutation.mutate({
      noteId: editingNote.id,
      data: {
        note: newNote,
        category: newCategory || undefined,
        tags: newTags.length > 0 ? newTags : undefined,
      },
    });
  };

  const handleEdit = (note: CallNote) => {
    setEditingNote(note);
    setNewNote(note.note);
    setNewCategory(note.category || '');
    setNewTags(note.tags || []);
    setTagInput('');
    setShowAddForm(true);
  };

  const handleCancel = () => {
    setShowAddForm(false);
    setEditingNote(null);
    setNewNote('');
    setNewCategory('');
    setNewTags([]);
    setTagInput('');
  };

  const handleAddTag = () => {
    const tag = tagInput.trim();
    if (tag && !newTags.includes(tag)) {
      setNewTags([...newTags, tag]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setNewTags(newTags.filter(tag => tag !== tagToRemove));
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleDelete = (noteId: number) => {
    setDeleteConfirm({ isOpen: true, noteId });
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirm.noteId !== null) {
      deleteNoteMutation.mutate(deleteConfirm.noteId);
    }
  };

  return (
    <>
      <Card title="Call Notes">
        <div className="space-y-4">
          {!showAddForm ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowAddForm(true)}
              className="w-full"
            >
              + Add Note
            </Button>
          ) : (
            <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
              <Input
                label="Note"
                multiline
                rows={4}
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Enter your note..."
              />
              <Input
                label="Category (optional)"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                placeholder="e.g., Follow-up, Issue, Feedback"
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (optional)
                </label>
                <div className="flex gap-2 mb-2">
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleTagInputKeyDown}
                    placeholder="Enter tag and press Enter"
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={handleAddTag}
                    disabled={!tagInput.trim()}
                  >
                    Add
                  </Button>
                </div>
                {newTags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {newTags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-1 text-blue-700 hover:text-blue-900"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={editingNote ? handleUpdateNote : handleAddNote}
                  isLoading={addNoteMutation.isPending || updateNoteMutation.isPending}
                >
                  {editingNote ? 'Update' : 'Add'} Note
                </Button>
                <Button variant="ghost" size="sm" onClick={handleCancel}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="text-center py-4 text-gray-500 text-sm">Loading notes...</div>
          ) : !notes || notes.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              No notes yet. Add a note to track important information about this call.
            </div>
          ) : (
            <div className="space-y-3">
              {notes.map((note: CallNote) => (
                <div
                  key={note.id}
                  className="p-3 border border-gray-200 rounded-lg bg-white hover:bg-gray-50"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      {note.category && (
                        <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded mb-2">
                          {note.category}
                        </span>
                      )}
                      <p className="text-sm text-gray-800 whitespace-pre-wrap">{note.note}</p>
                      {note.tags && note.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {note.tags.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-gray-500 mt-2">
                        {formatDate(note.created_at)}
                        {note.updated_at !== note.created_at && ' (edited)'}
                      </p>
                    </div>
                    <div className="flex gap-1 ml-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(note)}
                        className="text-xs"
                      >
                        Edit
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(note.id)}
                        className="text-xs"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>

      <ConfirmationModal
        isOpen={deleteConfirm.isOpen}
        onClose={() => setDeleteConfirm({ isOpen: false, noteId: null })}
        onConfirm={handleDeleteConfirm}
        title="Delete Note"
        message="Are you sure you want to delete this note? This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        isLoading={deleteNoteMutation.isPending}
      />
    </>
  );
};

