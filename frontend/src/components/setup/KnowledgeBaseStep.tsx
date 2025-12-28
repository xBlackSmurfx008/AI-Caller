import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';
import toast from 'react-hot-toast';

interface KnowledgeBaseStepProps {
  formData: any;
  onNext: (data: any) => void;
  onBack: () => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

export const KnowledgeBaseStep: React.FC<KnowledgeBaseStepProps> = ({
  formData,
  onNext,
  onBack,
  isFirstStep,
}) => {
  const [documents, setDocuments] = useState<any[]>(formData.knowledgeBase?.documents || []);
  const [urls, setUrls] = useState<string[]>(formData.knowledgeBase?.urls || []);
  const [newUrl, setNewUrl] = useState('');
  const [topK, setTopK] = useState(formData.knowledgeBase?.topK || 5);
  const [similarityThreshold, setSimilarityThreshold] = useState(
    formData.knowledgeBase?.similarityThreshold || 0.7
  );

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      Array.from(files).forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const newDoc = {
            id: Math.random().toString(36).substr(2, 9),
            name: file.name,
            type: file.type,
            size: file.size,
          };
          setDocuments([...documents, newDoc]);
          toast.success(`Uploaded ${file.name}`);
        };
        reader.readAsDataURL(file);
      });
    }
  };

  const handleAddUrl = () => {
    if (newUrl && !urls.includes(newUrl)) {
      setUrls([...urls, newUrl]);
      setNewUrl('');
      toast.success('URL added');
    }
  };

  const handleRemoveDocument = (id: string) => {
    setDocuments(documents.filter((doc) => doc.id !== id));
  };

  const handleRemoveUrl = (url: string) => {
    setUrls(urls.filter((u) => u !== url));
  };

  const handleNext = () => {
    onNext({
      knowledgeBase: {
        documents,
        urls,
        topK,
        similarityThreshold,
      },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Knowledge Base</h2>
        <p className="text-gray-600">
          Upload documents and add URLs to build your knowledge base
        </p>
      </div>

      <div className="space-y-6">
        <Card title="Upload Documents">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Files (PDF, DOCX, TXT)
              </label>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
            </div>
            {documents.length > 0 && (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="text-sm text-gray-700">{doc.name}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveDocument(doc.id)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card title="Add URLs">
          <div className="space-y-4">
            <div className="flex space-x-2">
              <Input
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="https://example.com"
                className="flex-1"
              />
              <Button variant="primary" onClick={handleAddUrl}>
                Add
              </Button>
            </div>
            {urls.length > 0 && (
              <div className="space-y-2">
                {urls.map((url) => (
                  <div
                    key={url}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="text-sm text-gray-700">{url}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveUrl(url)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card title="RAG Settings">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Top K Results: {topK}
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Similarity Threshold: {similarityThreshold.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </Card>
      </div>

      <div className="flex justify-between pt-4">
        <div>
          {!isFirstStep && (
            <Button type="button" variant="ghost" onClick={onBack}>
              Back
            </Button>
          )}
        </div>
        <Button variant="primary" onClick={handleNext}>
          Next
        </Button>
      </div>
    </div>
  );
};

