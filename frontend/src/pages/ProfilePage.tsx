import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import {
  User,
  Mail,
  Key,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Shield,
  RefreshCw
} from 'lucide-react'

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirm_password: z.string()
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
})

type PasswordFormData = z.infer<typeof passwordSchema>

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  // Fetch current user details with auto-refresh
  const { data: currentUser, isLoading, refetch } = useQuery({
    queryKey: ['current-user'],
    queryFn: async () => {
      const response = await api.get('/api/v1/auth/me')
      return response.data
    },
    // Refetch aggressively to catch verification changes
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: 5000, // Check every 5 seconds
    staleTime: 0, // Always consider data stale
  })

  // Password change form
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  })

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: async (data: { current_password: string; new_password: string }) => {
      const response = await api.post('/api/v1/auth/change-password', data)
      return response.data
    },
    onSuccess: () => {
      toast.success('Password changed successfully!')
      reset()
      setIsChangingPassword(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to change password')
    },
  })

  // Resend verification email mutation
  const resendVerificationMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/api/v1/auth/email-verification/resend-authenticated')
      return response.data
    },
    onSuccess: async (data) => {
      toast.success(data.message || 'Verification email sent!')
      // Invalidate and refetch user data
      await queryClient.invalidateQueries({ queryKey: ['current-user'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to send verification email')
    },
  })

  const onPasswordSubmit = async (data: PasswordFormData) => {
    changePasswordMutation.mutate({
      current_password: data.current_password,
      new_password: data.new_password,
    })
  }

  const handleResendVerification = () => {
    resendVerificationMutation.mutate()
  }

  const handleRefresh = async () => {
    // Invalidate cache and force refetch
    await queryClient.invalidateQueries({ queryKey: ['current-user'] })
    await refetch()
    toast.success('Profile refreshed!')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account settings and preferences
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isLoading}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              <CardTitle>Profile Information</CardTitle>
            </div>
            <CardDescription>
              Your account details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <div className="flex items-center gap-2">
                <Input
                  value={currentUser?.full_name || 'N/A'}
                  disabled
                  className="bg-muted"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Email Address</Label>
              <div className="flex items-center gap-2">
                <Input
                  value={currentUser?.email || 'N/A'}
                  disabled
                  className="bg-muted"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Account Created</Label>
              <div className="flex items-center gap-2">
                <Input
                  value={currentUser?.created_at ? new Date(currentUser.created_at).toLocaleDateString() : 'N/A'}
                  disabled
                  className="bg-muted"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Email Verification Status */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-primary" />
              <CardTitle>Email Verification</CardTitle>
            </div>
            <CardDescription>
              Verify your email address
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Verification Status */}
            <div className="flex items-center gap-3 p-4 rounded-lg border">
              {currentUser?.is_verified ? (
                <>
                  <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-green-500">Email Verified</p>
                    <p className="text-sm text-muted-foreground">
                      Your email address has been verified
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <AlertCircle className="h-6 w-6 text-yellow-500 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-yellow-500">Email Not Verified</p>
                    <p className="text-sm text-muted-foreground">
                      Please verify your email address
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* Resend Verification */}
            {!currentUser?.is_verified && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  Didn't receive the verification email? Check your spam folder or request a new one.
                </p>
                <Button
                  onClick={handleResendVerification}
                  disabled={resendVerificationMutation.isPending}
                  className="w-full"
                  variant="outline"
                >
                  {resendVerificationMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Mail className="mr-2 h-4 w-4" />
                      Resend Verification Email
                    </>
                  )}
                </Button>
              </div>
            )}

            {currentUser?.is_verified && (
              <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-md">
                <p className="text-sm text-green-500">
                  ✓ Your account is fully verified and activated
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Password Management */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5 text-primary" />
            <CardTitle>Password Management</CardTitle>
          </div>
          <CardDescription>
            Change your password to keep your account secure
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!isChangingPassword ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                We recommend using a strong password that you're not using elsewhere.
              </p>
              <Button onClick={() => setIsChangingPassword(true)}>
                <Key className="mr-2 h-4 w-4" />
                Change Password
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onPasswordSubmit)} className="space-y-4">
              {/* Current Password */}
              <div className="space-y-2">
                <Label htmlFor="current_password">Current Password *</Label>
                <Input
                  id="current_password"
                  type="password"
                  placeholder="Enter your current password"
                  {...register('current_password')}
                />
                {errors.current_password && (
                  <p className="text-sm text-destructive">{errors.current_password.message}</p>
                )}
              </div>

              {/* New Password */}
              <div className="space-y-2">
                <Label htmlFor="new_password">New Password *</Label>
                <Input
                  id="new_password"
                  type="password"
                  placeholder="Enter your new password"
                  {...register('new_password')}
                />
                {errors.new_password && (
                  <p className="text-sm text-destructive">{errors.new_password.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Must be at least 8 characters with uppercase, lowercase, and number
                </p>
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm New Password *</Label>
                <Input
                  id="confirm_password"
                  type="password"
                  placeholder="Confirm your new password"
                  {...register('confirm_password')}
                />
                {errors.confirm_password && (
                  <p className="text-sm text-destructive">{errors.confirm_password.message}</p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsChangingPassword(false)
                    reset()
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={changePasswordMutation.isPending}
                >
                  {changePasswordMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Changing...
                    </>
                  ) : (
                    'Change Password'
                  )}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      {/* Security Notice */}
      <Card className="border-primary/20">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Security Tips</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <span>Use a unique password that you don't use on other websites</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <span>Make sure your password is at least 8 characters long</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <span>Include a mix of uppercase, lowercase, numbers, and symbols</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <span>Keep your email verified to receive important security notifications</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}