import { z } from 'zod';

export const phoneNumberSchema = z.string().regex(/^\+?[1-9]\d{1,14}$/, {
  message: 'Invalid phone number format',
});

export const emailSchema = z.string().email({
  message: 'Invalid email address',
});

export const apiKeySchema = z.string().min(1, {
  message: 'API key is required',
});

export const businessNameSchema = z.string().min(1, {
  message: 'Business name is required',
}).max(100, {
  message: 'Business name must be less than 100 characters',
});

