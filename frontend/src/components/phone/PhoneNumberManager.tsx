import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { phoneNumbersApi } from '../../api/phoneNumbers';
import { agentsAPI } from '../../api/agents';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { ConfirmationModal } from '../common/ConfirmationModal';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import type { PhoneNumber, PhoneNumberCreate } from '../../types/phoneNumber';
import { PhoneNumberProvisioning } from './PhoneNumberProvisioning';
import { PhoneNumberAssignment } from './PhoneNumberAssignment';

const phoneNumberSchema = z.object({
  phone_number: z.string().regex(/^\+[1-9]\d{1,14}$/, 'Must be E.164 format (e.g., +1234567890)'),
  friendly_name: z.string().optional(),
  country_code: z.string().min(2, 'Country code is required'),
  region: z.string().optional(),
  webhook_url: z.string().url().optional().or(z.literal('')),
  webhook_method: z.enum(['GET', 'POST']).default('POST'),
  is_active: z.boolean().default(true),
});

type PhoneNumberFormData = z.infer<typeof phoneNumberSchema>;

export const PhoneNumberManager: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProvisioningOpen, setIsProvisioningOpen] = useState(false);
  const [isAssignmentOpen, setIsAssignmentOpen] = useState(false);
  const [selectedPhone, setSelectedPhone] = useState<PhoneNumber | null>(null);
  const [editingPhone, setEditingPhone] = useState<PhoneNumber | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    phoneId: string | null;
  }>({ isOpen: false, phoneId: null });

  const queryClient = useQueryClient();

  const { data: phoneNumbers, isLoading } = useQuery({
    queryKey: ['phone-numbers'],
    queryFn: () => phoneNumbersApi.list(),
  });

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsAPI.list(),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PhoneNumberFormData>({
    resolver: zodResolver(phoneNumberSchema),
    defaultValues: {
      webhook_method: 'POST',
      is_active: true,
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: PhoneNumberCreate) => phoneNumbersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phone-numbers'] });
      toast.success('Phone number added successfully');
      setIsModalOpen(false);
      reset();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add phone number');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PhoneNumberCreate> }) =>
      phoneNumbersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phone-numbers'] });
      toast.success('Phone number updated successfully');
      setIsModalOpen(false);
      setEditingPhone(null);
      reset();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update phone number');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => phoneNumbersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phone-numbers'] });
      toast.success('Phone number released successfully');
      setDeleteConfirm({ isOpen: false, phoneId: null });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to release phone number');
    },
  });

  const handleCreate = () => {
    setEditingPhone(null);
    reset({
      phone_number: '',
      friendly_name: '',
      country_code: 'US',
      region: '',
      webhook_url: '',
      webhook_method: 'POST',
      is_active: true,
    });
    setIsModalOpen(true);
  };

  const handleEdit = (phone: PhoneNumber) => {
    setEditingPhone(phone);
    reset({
      phone_number: phone.phone_number,
      friendly_name: phone.friendly_name || '',
      country_code: phone.country_code,
      region: phone.region || '',
      webhook_url: phone.webhook_url || '',
      webhook_method: (phone.webhook_method || 'POST') as 'GET' | 'POST',
      is_active: phone.is_active,
    });
    setIsModalOpen(true);
  };

  const handleDelete = (phoneId: string) => {
    setDeleteConfirm({ isOpen: true, phoneId });
  };

  const confirmDelete = () => {
    if (deleteConfirm.phoneId) {
      deleteMutation.mutate(deleteConfirm.phoneId);
    }
  };

  const onSubmit = (data: PhoneNumberFormData) => {
    const phoneData: PhoneNumberCreate = {
      phone_number: data.phone_number,
      friendly_name: data.friendly_name || undefined,
      country_code: data.country_code,
      region: data.region || undefined,
      webhook_url: data.webhook_url || undefined,
      webhook_method: data.webhook_method,
      is_active: data.is_active,
      status: 'active',
    };

    if (editingPhone) {
      updateMutation.mutate({ id: editingPhone.id, data: phoneData });
    } else {
      createMutation.mutate(phoneData);
    }
  };

  const handleAssign = (phone: PhoneNumber) => {
    setSelectedPhone(phone);
    setIsAssignmentOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Phone Numbers</h2>
        <div className="flex gap-2">
          <Button onClick={() => setIsProvisioningOpen(true)} variant="primary">
            Purchase Number
          </Button>
          <Button onClick={handleCreate} variant="primary">
            Add Phone Number
          </Button>
        </div>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Phone Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Capabilities
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {phoneNumbers && phoneNumbers.length > 0 ? (
                phoneNumbers.map((phone) => (
                  <tr key={phone.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {phone.phone_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {phone.friendly_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant={phone.status === 'active' ? 'success' : phone.status === 'pending' ? 'warning' : 'danger'}
                      >
                        {phone.status}
                      </Badge>
                      {!phone.is_active && (
                        <Badge variant="danger" className="ml-2">
                          Inactive
                        </Badge>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex gap-1">
                        {phone.capabilities?.voice && <Badge variant="info">Voice</Badge>}
                        {phone.capabilities?.SMS && <Badge variant="info">SMS</Badge>}
                        {phone.capabilities?.MMS && <Badge variant="info">MMS</Badge>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <Button
                          onClick={() => handleAssign(phone)}
                          variant="secondary"
                          size="sm"
                        >
                          Assign
                        </Button>
                        <Button
                          onClick={() => handleEdit(phone)}
                          variant="secondary"
                          size="sm"
                        >
                          Edit
                        </Button>
                        <Button
                          onClick={() => handleDelete(phone.id)}
                          variant="danger"
                          size="sm"
                        >
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    No phone numbers found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingPhone(null);
          reset();
        }}
        title={editingPhone ? 'Edit Phone Number' : 'Add Phone Number'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Phone Number (E.164 format)"
            {...register('phone_number')}
            error={errors.phone_number?.message}
            placeholder="+1234567890"
            disabled={!!editingPhone}
          />

          <Input
            label="Friendly Name"
            {...register('friendly_name')}
            error={errors.friendly_name?.message}
            placeholder="Main Office Line"
          />

          <Input
            label="Country Code"
            {...register('country_code')}
            error={errors.country_code?.message}
            placeholder="US"
          />

          <Input
            label="Region"
            {...register('region')}
            error={errors.region?.message}
            placeholder="California"
          />

          <Input
            label="Webhook URL"
            {...register('webhook_url')}
            error={errors.webhook_url?.message}
            placeholder="https://example.com/webhook"
          />

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                {...register('is_active')}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Active</span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsModalOpen(false);
                setEditingPhone(null);
                reset();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={createMutation.isPending || updateMutation.isPending}>
              {editingPhone ? 'Update' : 'Add'} Phone Number
            </Button>
          </div>
        </form>
      </Modal>

      {/* Provisioning Modal */}
      {isProvisioningOpen && (
        <PhoneNumberProvisioning
          isOpen={isProvisioningOpen}
          onClose={() => setIsProvisioningOpen(false)}
        />
      )}

      {/* Assignment Modal */}
      {isAssignmentOpen && selectedPhone && (
        <PhoneNumberAssignment
          isOpen={isAssignmentOpen}
          onClose={() => {
            setIsAssignmentOpen(false);
            setSelectedPhone(null);
          }}
          phoneNumber={selectedPhone}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmationModal
        isOpen={deleteConfirm.isOpen}
        onClose={() => setDeleteConfirm({ isOpen: false, phoneId: null })}
        onConfirm={confirmDelete}
        title="Release Phone Number"
        message="Are you sure you want to release this phone number? This action cannot be undone."
        confirmText="Release"
        variant="danger"
      />
    </div>
  );
};

