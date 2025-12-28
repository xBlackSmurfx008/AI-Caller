import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { phoneNumbersApi } from '../../api/phoneNumbers';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import type { PhoneNumberSearchRequest } from '../../types/phoneNumber';

const searchSchema = z.object({
  country_code: z.string().min(2, 'Country code is required'),
  area_code: z.string().optional(),
  limit: z.number().min(1).max(100).default(20),
});

type SearchFormData = z.infer<typeof searchSchema>;

interface PhoneNumberProvisioningProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PhoneNumberProvisioning: React.FC<PhoneNumberProvisioningProps> = ({
  isOpen,
  onClose,
}) => {
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedNumber, setSelectedNumber] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
    defaultValues: {
      country_code: 'US',
      limit: 20,
    },
  });

  const purchaseMutation = useMutation({
    mutationFn: (phoneNumber: string) => phoneNumbersApi.purchase({ phone_number: phoneNumber }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phone-numbers'] });
      toast.success('Phone number purchased successfully');
      onClose();
      setSearchResults([]);
      setSelectedNumber(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to purchase phone number');
    },
  });

  const onSearch = async (data: SearchFormData) => {
    setIsSearching(true);
    try {
      const results = await phoneNumbersApi.searchAvailable({
        country_code: data.country_code,
        area_code: data.area_code || undefined,
        limit: data.limit,
      });
      setSearchResults(results);
      if (results.length === 0) {
        toast.info('No available numbers found');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to search phone numbers');
    } finally {
      setIsSearching(false);
    }
  };

  const handlePurchase = () => {
    if (selectedNumber) {
      purchaseMutation.mutate(selectedNumber);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Purchase Phone Number" size="large">
      <div className="space-y-6">
        {/* Search Form */}
        <form onSubmit={handleSubmit(onSearch)} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Input
              label="Country Code"
              {...register('country_code')}
              error={errors.country_code?.message}
              placeholder="US"
            />

            <Input
              label="Area Code (optional)"
              {...register('area_code')}
              error={errors.area_code?.message}
              placeholder="415"
            />

            <Input
              label="Limit"
              type="number"
              {...register('limit', { valueAsNumber: true })}
              error={errors.limit?.message}
            />
          </div>

          <Button type="submit" variant="primary" disabled={isSearching}>
            {isSearching ? <LoadingSpinner size="sm" /> : 'Search Available Numbers'}
          </Button>
        </form>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Available Numbers ({searchResults.length})
            </h3>
            <div className="max-h-96 overflow-y-auto space-y-2">
              {searchResults.map((number, index) => (
                <div
                  key={index}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedNumber === number.phone_number
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                  onClick={() => setSelectedNumber(number.phone_number)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {number.phone_number}
                      </div>
                      {number.friendly_name && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {number.friendly_name}
                        </div>
                      )}
                      {number.locality && number.region && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {number.locality}, {number.region}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {number.capabilities?.voice && <Badge variant="info">Voice</Badge>}
                      {number.capabilities?.SMS && <Badge variant="info">SMS</Badge>}
                      {number.capabilities?.MMS && <Badge variant="info">MMS</Badge>}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {selectedNumber && (
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="secondary" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handlePurchase}
                  disabled={purchaseMutation.isPending}
                >
                  {purchaseMutation.isPending ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    `Purchase ${selectedNumber}`
                  )}
                </Button>
              </div>
            )}
          </div>
        )}

        {searchResults.length === 0 && !isSearching && (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            Search for available phone numbers to get started
          </div>
        )}
      </div>
    </Modal>
  );
};

