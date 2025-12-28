import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { knowledgeAPI } from '../../api/knowledge';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { ConfirmationModal } from '../common/ConfirmationModal';
import { FileUploadProgress } from '../common/FileUploadProgress';
import { formatDate } from '../../utils/format';
import toast from 'react-hot-toast';

interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  errorMessage?: string;
}

export const KnowledgeBaseManager: React.FC = () => {
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    entryId: number | null;
  }>({ isOpen: false, entryId: null });
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [uploadAbortController, setUploadAbortController] = useState<AbortController | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['knowledge'],
    queryFn: () => knowledgeAPI.list(),
  });

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error('File size exceeds 10MB limit');
      return;
    }

    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
      toast.error('Invalid file type. Please upload PDF, DOCX, or TXT files.');
      return;
    }

    const abortController = new AbortController();
    setUploadAbortController(abortController);
    setUploadProgress({
      fileName: file.name,
      progress: 0,
      status: 'uploading',
    });

    try {
      // Simulate upload progress (in real implementation, use XMLHttpRequest or fetch with progress)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (!prev) return prev;
          const newProgress = Math.min(prev.progress + 10, 90);
          return { ...prev, progress: newProgress };
        });
      }, 200);

      await knowledgeAPI.upload(file);
      
      clearInterval(progressInterval);
      
      setUploadProgress({
        fileName: file.name,
        progress: 100,
        status: 'processing',
      });

      // Simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 1500));

      setUploadProgress({
        fileName: file.name,
        progress: 100,
        status: 'completed',
      });

      toast.success('Document uploaded and processed successfully');
      refetch();

      // Clear progress after 3 seconds
      setTimeout(() => {
        setUploadProgress(null);
      }, 3000);
    } catch (error: any) {
      setUploadProgress({
        fileName: file.name,
        progress: 0,
        status: 'error',
        errorMessage: error?.response?.data?.error?.message || 'Failed to upload document',
      });
      toast.error('Failed to upload document');
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setUploadProgress(null);
      }, 5000);
    } finally {
      setUploadAbortController(null);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleCancelUpload = () => {
    if (uploadAbortController) {
      uploadAbortController.abort();
      setUploadAbortController(null);
    }
    setUploadProgress(null);
    toast('Upload cancelled');
  };

  const handleAddEntry = async () => {
    console.log('handleAddEntry called');
    console.log('newTitle:', newTitle, 'newContent:', newContent);
    console.log('newTitle length:', newTitle?.length, 'newContent length:', newContent?.length);
    if (!newTitle || !newContent) {
      console.warn('Validation failed - missing title or content');
      toast.error('Please fill in both title and content');
      return;
    }

    try {
      console.log('Calling knowledgeAPI.create...');
      const result = await knowledgeAPI.create({
        title: newTitle,
        content: newContent,
      });
      console.log('Create successful:', result);
      toast.success('Knowledge entry added');
      setNewTitle('');
      setNewContent('');
      setShowAddForm(false);
      refetch();
    } catch (error: any) {
      console.error('Failed to add knowledge entry:', error);
      const errorMessage = error?.response?.data?.error?.message || error?.message || 'Failed to add knowledge entry';
      toast.error(errorMessage);
    }
  };

  const handleDeleteClick = (id: number) => {
    setDeleteConfirm({ isOpen: true, entryId: id });
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirm.entryId === null) return;

    try {
      await knowledgeAPI.delete(deleteConfirm.entryId);
      toast.success('Entry deleted');
      refetch();
      setDeleteConfirm({ isOpen: false, entryId: null });
    } catch (error) {
      toast.error('Failed to delete entry');
    }
  };

  return (
    <>
      <Card
        title="Knowledge Base"
        actions={
          <div className="flex space-x-2">
            <label className="cursor-pointer">
              <span style={{ display: 'inline-block' }}>
                <Button variant="secondary" size="sm" type="button">
                  Upload Document
                </Button>
              </span>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleUpload}
                className="hidden"
              />
            </label>
            <Button
              variant="primary"
              size="sm"
              onClick={(e) => {
                console.log('Add Entry button clicked');
                e.preventDefault();
                e.stopPropagation();
                setShowAddForm(!showAddForm);
              }}
            >
              {showAddForm ? 'Cancel' : '+ Add Entry'}
            </Button>
          </div>
        }
      >
      {showAddForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4">
          <Input
            label="Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Enter title..."
          />
          <Input
            label="Content"
            multiline
            rows={6}
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder="Enter content..."
          />
          <div className="flex justify-end">
            <Button 
              variant="primary" 
              onClick={(e) => {
                console.log('Add Entry submit button clicked');
                e.preventDefault();
                e.stopPropagation();
                handleAddEntry();
              }}
            >
              Add Entry
            </Button>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {uploadProgress && (
        <div className="mb-6">
          <FileUploadProgress
            fileName={uploadProgress.fileName}
            progress={uploadProgress.progress}
            status={uploadProgress.status}
            errorMessage={uploadProgress.errorMessage}
            onCancel={uploadProgress.status === 'uploading' ? handleCancelUpload : undefined}
          />
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : !data?.entries.length ? (
        <div className="text-center py-8 text-gray-500">
          <p>No knowledge entries found</p>
          <p className="text-sm mt-2">Upload documents or add entries to get started</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.entries.map((entry) => (
            <div
              key={entry.id}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">{entry.title}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2">{entry.content}</p>
                  {entry.source && (
                    <p className="text-xs text-gray-500 mt-2">Source: {entry.source}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-2">
                    Created: {formatDate(entry.created_at)}
                  </p>
                </div>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={(e) => {
                    console.log('Delete button clicked for entry:', entry.id);
                    e.preventDefault();
                    e.stopPropagation();
                    handleDeleteClick(entry.id);
                  }}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
      </Card>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteConfirm.isOpen}
        onClose={() => setDeleteConfirm({ isOpen: false, entryId: null })}
        onConfirm={handleDeleteConfirm}
        title="Delete Knowledge Entry"
        message="Are you sure you want to delete this entry? This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </>
  );
};

