import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, RefreshCw, ExternalLink, Filter, CheckCircle, XCircle } from 'lucide-react';
import { documentationApi } from '../api/documentation';
import { toast } from 'react-hot-toast';

interface Vendor {
  name: string;
  display_name: string;
  base_url: string;
  last_synced: string | null;
  document_count: number;
  doc_types: string[];
}

interface DocumentationResult {
  id: string;
  title: string;
  content: string;
  url: string;
  vendor: string | null;
  doc_type: string | null;
  score: number;
  metadata: Record<string, any>;
}

export default function DocumentationManagement() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const [selectedDocType, setSelectedDocType] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch vendors
  const { data: vendorsData, isLoading: vendorsLoading } = useQuery({
    queryKey: ['documentation', 'vendors'],
    queryFn: documentationApi.getVendors,
  });

  // Search documentation
  const { data: searchResults, isLoading: searchLoading, refetch: refetchSearch } = useQuery({
    queryKey: ['documentation', 'search', searchQuery, selectedVendor, selectedDocType],
    queryFn: () => documentationApi.searchDocumentation({
      query: searchQuery,
      vendor: selectedVendor || undefined,
      doc_type: selectedDocType || undefined,
      top_k: 10,
    }),
    enabled: searchQuery.length > 0,
  });

  // Sync mutation
  const syncMutation = useMutation({
    mutationFn: (vendor: string) => documentationApi.syncVendor(vendor),
    onSuccess: (_, vendor) => {
      toast.success(`Documentation sync started for ${vendor}`);
      queryClient.invalidateQueries({ queryKey: ['documentation', 'vendors'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to start sync');
    },
  });

  const handleSync = (vendor: string) => {
    if (confirm(`Start documentation sync for ${vendor}? This may take several minutes.`)) {
      syncMutation.mutate(vendor);
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      refetchSearch();
    }
  };

  const vendors = vendorsData?.vendors || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Documentation Management</h1>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Search and manage vendor documentation (OpenAI, Twilio, RingCentral, HubSpot, Google/Gemini)
        </p>
      </div>

      {/* Vendors Overview */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Documentation Sources</h2>
        {vendorsLoading ? (
          <div className="text-center py-8 text-gray-500">Loading vendors...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vendors.map((vendor: Vendor) => (
              <div
                key={vendor.name}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{vendor.display_name}</h3>
                  <button
                    onClick={() => handleSync(vendor.name)}
                    disabled={syncMutation.isPending}
                    className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50"
                    title="Sync documentation"
                  >
                    <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                  </button>
                </div>
                <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <div>Documents: {vendor.document_count}</div>
                  <div>
                    Last synced:{' '}
                    {vendor.last_synced
                      ? new Date(vendor.last_synced).toLocaleDateString()
                      : 'Never'}
                  </div>
                  {vendor.doc_types.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {vendor.doc_types.slice(0, 3).map((type) => (
                        <span
                          key={type}
                          className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs"
                        >
                          {type.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Search Documentation</h2>
        
        <div className="space-y-4">
          {/* Search Input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search documentation..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || searchLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Search
            </button>
          </div>

          {/* Filters */}
          <div className="flex gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Filters:</span>
            </div>
            <select
              value={selectedVendor || ''}
              onChange={(e) => setSelectedVendor(e.target.value || null)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm"
            >
              <option value="">All Vendors</option>
              {vendors.map((v: Vendor) => (
                <option key={v.name} value={v.name}>
                  {v.display_name}
                </option>
              ))}
            </select>
            <select
              value={selectedDocType || ''}
              onChange={(e) => setSelectedDocType(e.target.value || null)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm"
            >
              <option value="">All Types</option>
              <option value="api_reference">API Reference</option>
              <option value="guide">Guide</option>
              <option value="tutorial">Tutorial</option>
              <option value="example">Example</option>
              <option value="troubleshooting">Troubleshooting</option>
            </select>
          </div>

          {/* Search Results */}
          {searchLoading && (
            <div className="text-center py-8 text-gray-500">Searching...</div>
          )}
          {searchResults && (
            <div className="space-y-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Found {searchResults.total_results} results
                {searchResults.vendors.length > 0 && (
                  <span className="ml-2">
                    from {searchResults.vendors.join(', ')}
                  </span>
                )}
              </div>
              {searchResults.results.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No results found. Try a different search query.
                </div>
              ) : (
                <div className="space-y-3">
                  {searchResults.results.map((result: DocumentationResult) => (
                    <div
                      key={result.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                            {result.title}
                          </h3>
                          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                            {result.vendor && (
                              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 rounded text-xs">
                                {result.vendor.toUpperCase()}
                              </span>
                            )}
                            {result.doc_type && (
                              <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                                {result.doc_type.replace('_', ' ')}
                              </span>
                            )}
                            <span className="text-xs">
                              Score: {(result.score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        {result.url && (
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700 dark:text-blue-400"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                        {result.content}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

