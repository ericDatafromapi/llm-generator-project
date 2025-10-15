// User types
export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_verified: boolean
  role: string
  created_at: string
  updated_at: string
  last_login_at: string | null
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Subscription types
export type PlanType = 'free' | 'standard' | 'pro'

export interface Subscription {
  id: string
  user_id: string
  plan_type: PlanType
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  stripe_price_id: string | null
  status: string
  current_period_start: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  generations_limit: number
  generations_used: number
  created_at: string
  updated_at: string
}

// Website types
export interface Website {
  id: string
  user_id: string
  url: string
  name: string
  description: string | null
  include_patterns: string | null
  exclude_patterns: string | null
  max_pages: number
  use_playwright: boolean
  timeout: number
  is_active: boolean
  last_generated_at: string | null
  generation_count: number
  created_at: string
  updated_at: string
}

export interface WebsiteCreate {
  url: string
  name: string
  description?: string
  include_patterns?: string
  exclude_patterns?: string
  max_pages?: number
  use_playwright?: boolean
  timeout?: number
  is_active?: boolean
}

export interface WebsiteUpdate {
  name?: string
  description?: string
  include_patterns?: string
  exclude_patterns?: string
  max_pages?: number
  use_playwright?: boolean
  timeout?: number
  is_active?: boolean
}

// Generation types
export type GenerationStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Generation {
  id: string
  user_id: string
  website_id: string
  status: GenerationStatus
  file_path: string | null
  file_size: number | null
  total_files: number | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

// Statistics types
export interface WebsiteStats {
  website_id: string
  website_name: string
  website_url: string
  total_generations: number
  successful_generations: number
  failed_generations: number
  last_generation_at: string | null
  success_rate: number
}

export interface UserStats {
  total_websites: number
  active_websites: number
  total_generations: number
  successful_generations: number
  failed_generations: number
  generations_this_month: number
  generations_remaining: number
  success_rate: number
}

// Paginated response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

// API Error
export interface ApiError {
  detail: string
}