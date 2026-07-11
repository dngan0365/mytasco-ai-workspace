export interface User { user_id: string; full_name: string; role: string; department: string }
export interface LoginResponse { access_token: string; token_type: string; user: User }
