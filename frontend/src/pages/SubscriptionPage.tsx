import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import { Check, Loader2, ExternalLink, CreditCard, TrendingUp } from 'lucide-react'
import type { Subscription } from '@/types'

const PLANS = [
  {
    name: 'Free',
    slug: 'free',
    tier: 0,
    priceMonthly: 0,
    priceYearly: 0,
    features: [
      '1 generation per month',
      '1 website',
      'up to 100 pages per generation',
      'Basic support',
      'llms.txt files',
    ],
    limits: {
      websites: 1,
      generations: 1,
      pages: 100,
    },
  },
  {
    name: 'Starter',
    slug: 'starter',
    tier: 1,
    priceMonthly: 19,
    priceYearly: 171,
    features: [
      '3 generations per month',
      '2 websites',
      'up to 200 pages per generation',
      'Priority support',
      'llms.txt files',
      'Email notifications',
    ],
    limits: {
      websites: 2,
      generations: 3,
      pages: 200,
    },
  },
  {
    name: 'Standard',
    slug: 'standard',
    tier: 2,
    priceMonthly: 39,
    priceYearly: 351,
    features: [
      '10 generations per month',
      '5 websites',
      'up to 500 pages per generation',
      'Priority support',
      'llms.txt + full content',
      'Automatic updates',
    ],
    limits: {
      websites: 5,
      generations: 10,
      pages: 500,
    },
    popular: true,
  },
  {
    name: 'Pro',
    slug: 'pro',
    tier: 3,
    priceMonthly: 79,
    priceYearly: 711,
    features: [
      '25 generations per month',
      'Unlimited websites',
      'up to 1000 pages per generation',
      'Premium support',
      'llms.txt + full content',
      'Automatic updates',
      'API access'
    ],
    limits: {
      websites: 999,
      generations: 25,
      pages: 1000,
    },
  },
]

export default function SubscriptionPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly')

  // Handle checkout result
  useEffect(() => {
    const checkoutStatus = searchParams.get('checkout')
    const upgraded = searchParams.get('upgraded')
    
    if (checkoutStatus === 'success') {
      toast.success('Payment successful! Your subscription has been updated.')
      // Force refresh subscription data
      queryClient.invalidateQueries({ queryKey: ['subscription'] })
      queryClient.refetchQueries({ queryKey: ['subscription'] })
      setSearchParams({})
    } else if (upgraded === 'true') {
      toast.success('Subscription upgraded successfully!')
      // Force refresh subscription data
      queryClient.invalidateQueries({ queryKey: ['subscription'] })
      queryClient.refetchQueries({ queryKey: ['subscription'] })
      setSearchParams({})
    } else if (checkoutStatus === 'cancelled') {
      toast.info('Checkout cancelled. You can upgrade anytime.')
      setSearchParams({})
    }
  }, [searchParams, setSearchParams, queryClient])

  // Fetch current subscription
  const { data: subscription, isLoading } = useQuery({
    queryKey: ['subscription'],
    queryFn: async () => {
      const response = await api.get<Subscription>('/api/v1/subscriptions/current')
      return response.data
    },
  })

  // Fetch user stats for downgrade validation
  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/websites/stats/user')
      return response.data
    },
  })

  // Create checkout session
  const checkoutMutation = useMutation({
    mutationFn: async ({ planSlug, interval }: { planSlug: string; interval: string }) => {
      const frontendUrl = window.location.origin
      const response = await api.post<{ checkout_url: string }>('/api/v1/subscriptions/checkout', {
        plan_type: planSlug,
        billing_interval: interval,
        success_url: `${frontendUrl}/dashboard/subscription?checkout=success`,
        cancel_url: `${frontendUrl}/dashboard/subscription?checkout=cancelled`,
      })
      return response.data
    },
    onSuccess: (data) => {
      window.location.href = data.checkout_url
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create checkout session')
    },
  })

  // Get customer portal link
  const portalMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<{ portal_url: string }>('/api/v1/subscriptions/portal')
      return response.data
    },
    onSuccess: (data) => {
      window.location.href = data.portal_url
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to access customer portal')
    },
  })

  const currentPlan = subscription?.plan_type || 'free'
  const currentTier = PLANS.find(p => p.slug === currentPlan)?.tier || 0

  const handleUpgrade = (planSlug: string) => {
    checkoutMutation.mutate({ planSlug, interval: billingInterval })
  }

  const handleManageBilling = () => {
    portalMutation.mutate()
  }

  // Check if user can downgrade to a plan
  const canDowngradeTo = (planLimits: typeof PLANS[0]['limits']) => {
    if (!stats) return true
    const websitesOk = (stats.total_websites || 0) <= planLimits.websites
    const generationsOk = (stats.generations_this_month || 0) <= planLimits.generations
    return websitesOk && generationsOk
  }

  // Get button text based on plan comparison
  const getButtonText = (plan: typeof PLANS[0]) => {
    if (plan.tier > currentTier) return `Upgrade to ${plan.name}`
    if (plan.tier < currentTier) return `Downgrade to ${plan.name}`
    return 'Current Plan'
  }

  // Calculate monthly price for yearly billing
  const getDisplayPrice = (plan: typeof PLANS[0]) => {
    if (billingInterval === 'yearly' && plan.priceYearly > 0) {
      const monthlyEquivalent = plan.priceYearly / 12
      return {
        price: plan.priceYearly,
        display: `€${monthlyEquivalent.toFixed(2)}`,
        period: 'per month',
        total: `€${plan.priceYearly}/year`,
        savings: Math.round(((plan.priceMonthly * 12 - plan.priceYearly) / (plan.priceMonthly * 12)) * 100),
      }
    }
    return {
      price: plan.priceMonthly,
      display: plan.priceMonthly === 0 ? '€0' : `€${plan.priceMonthly}`,
      period: plan.priceMonthly === 0 ? 'forever' : 'per month',
      total: null,
      savings: 0,
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Subscription</h1>
        <p className="text-muted-foreground mt-2">
          Manage your plan and billing information
        </p>
      </div>

      {/* Current Plan Status */}
      {isLoading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      ) : (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl capitalize">
                  {subscription?.plan_type} Plan
                </CardTitle>
                <CardDescription>
                  Your current subscription
                </CardDescription>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Status</p>
                <p className="text-lg font-semibold capitalize text-primary">
                  {subscription?.status}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Usage Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Generations Used</p>
                <p className="text-2xl font-bold">
                  {subscription?.generations_used} / {subscription?.generations_limit}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Period</p>
                <p className="text-sm">
                  {subscription?.current_period_start && subscription?.current_period_end ? (
                    <>
                      {new Date(subscription.current_period_start).toLocaleDateString()} -{' '}
                      {new Date(subscription.current_period_end).toLocaleDateString()}
                    </>
                  ) : (
                    'Lifetime'
                  )}
                </p>
              </div>
            </div>

            {/* Manage Billing Button */}
            {subscription?.plan_type !== 'free' && (
              <Button
                variant="outline"
                onClick={handleManageBilling}
                disabled={portalMutation.isPending}
                className="w-full sm:w-auto"
              >
                {portalMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <CreditCard className="mr-2 h-4 w-4" />
                    Manage Billing
                    <ExternalLink className="ml-2 h-3 w-3" />
                  </>
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Billing Toggle */}
      <div className="flex justify-center">
        <div className="inline-flex items-center bg-muted rounded-lg p-1">
          <Button
            variant={billingInterval === 'monthly' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setBillingInterval('monthly')}
            className="relative"
          >
            Monthly
          </Button>
          <Button
            variant={billingInterval === 'yearly' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setBillingInterval('yearly')}
            className="relative"
          >
            Yearly
            <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full font-semibold">
              -25%
            </span>
          </Button>
        </div>
      </div>

      {/* Available Plans */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Available Plans</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map((plan) => {
            const isCurrentPlan = currentPlan === plan.slug
            const isDowngrade = plan.tier < currentTier
            const canDowngrade = canDowngradeTo(plan.limits)
            const isDisabled = isDowngrade && !canDowngrade
            const pricing = getDisplayPrice(plan)

            return (
              <Card
                key={plan.name}
                className={`relative ${plan.popular ? 'border-primary shadow-lg shadow-primary/20 scale-105' : ''}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                <CardHeader>
                  <CardTitle className="text-xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold">{pricing.display}</span>
                      <span className="text-muted-foreground text-sm">/{pricing.period}</span>
                    </div>
                    {pricing.total && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {pricing.total} billed annually
                      </p>
                    )}
                    {pricing.savings > 0 && (
                      <p className="text-xs text-primary font-semibold mt-1">
                        Save {pricing.savings}% with yearly billing
                      </p>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-6">
                  {/* Features */}
                  <ul className="space-y-2.5">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-2.5">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Action Button */}
                  {isCurrentPlan ? (
                    <Button variant="outline" className="w-full" disabled>
                      Current Plan
                    </Button>
                  ) : (
                    <>
                      <Button
                        className="w-full"
                        variant={plan.popular ? 'default' : 'outline'}
                        onClick={() => handleUpgrade(plan.slug)}
                        disabled={checkoutMutation.isPending || isDisabled || (plan.slug === 'free' && currentPlan !== 'free')}
                      >
                        {checkoutMutation.isPending ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Loading...
                          </>
                        ) : (
                          <>
                            {getButtonText(plan)}
                            <TrendingUp className="ml-2 h-4 w-4" />
                          </>
                        )}
                      </Button>
                      {isDisabled && (
                        <p className="text-xs text-destructive mt-2 text-center">
                          Usage exceeds limit: {stats?.total_websites} websites (max: {plan.limits.websites})
                        </p>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* FAQ */}
      <Card>
        <CardHeader>
          <CardTitle>Frequently Asked Questions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2">What's the difference between monthly and yearly billing?</h4>
            <p className="text-sm text-muted-foreground">
              Yearly billing gives you a 25% discount compared to monthly billing. You'll be charged once per year 
              instead of monthly, saving money in the long run.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Can I change plans anytime?</h4>
            <p className="text-sm text-muted-foreground">
              Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, 
              and we'll prorate any charges.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">What happens if I exceed my limits?</h4>
            <p className="text-sm text-muted-foreground">
              You'll receive a notification when you're approaching your limits. You can either upgrade 
              your plan or wait until the next billing cycle for your quota to reset.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Can I downgrade if I'm using more than the limit?</h4>
            <p className="text-sm text-muted-foreground">
              You can only downgrade if your current usage (websites and generations) fits within the lower plan's limits. 
              Delete websites or wait for the monthly reset before downgrading.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">How do I cancel my subscription?</h4>
            <p className="text-sm text-muted-foreground">
              Click "Manage Billing" above to access your customer portal where you can cancel anytime. 
              You'll retain access until the end of your billing period.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}