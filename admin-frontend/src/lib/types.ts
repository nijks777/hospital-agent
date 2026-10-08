export type UserRole = "platform_admin" | "hospital_admin";

export type User = {
  id: string;
  username: string;
  email: string | null;
  role: UserRole;
  hospital_id: string | null;
};
