export type User = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  full_name: string;
  email: string;
  password: string;
};
