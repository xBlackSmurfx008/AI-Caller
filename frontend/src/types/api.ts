export type ApiError = {
  error: {
    code: string;
    message: string;
    details?: any;
  };
};

export type ApiResponse<T> = {
  data?: T;
  error?: ApiError;
};

export type PaginatedResponse<T> = {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
};

