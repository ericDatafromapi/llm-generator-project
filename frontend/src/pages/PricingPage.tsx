import { useState } from 'react'
import { Link } from 'react-router-dom'
import PublicLayout from '@/components/layouts/PublicLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Check, ArrowRight } from 'lucide-react'

const PLANS = [
  {
    name: 'Free',
    priceMonthly: 0,
    priceYearly: 0,
    features: [
      '1 generation per month',
      '1 website',
      '100 pages per generation',
      'Basic support',
      'llms.txt files',
    ],
  },
  {
    name: 'Starter',
    priceMonthly: 19,
    priceYearly: 171,
    features: [
      '3 generations per month',
      '2 websites',
      '200 pages per generation',
      'Priority support',
      'llms.txt files',
      'Email notifications',
    ],
  },
  {
    name: 'Standard',
    priceMonthly: 39,
    priceYearly: 351,
    features: [
      '10 generations per month',
      '5 websites',
      '500 pages per generation',
      'Priority support',
      'llms.txt + full content',
      'Automatic updates',
    ],
    popular: true,
  },
  {
    name: 'Pro',
    priceMonthly: 79,
    priceYearly: 711,
    features: [
      '25 generations per month',
      'Unlimited websites',
      '1000 pages per generation',
      'Premium support',
      'llms.txt + full content',
      'Automatic updates',
      'API access'
    ],
  },
]

export default function PricingPage() {
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly')

  const getDisplayPrice = (plan: typeof PLANS[0]) => {
    if (billingInterval === 'yearly' && plan.priceYearly > 0) {
      const monthlyEquivalent = plan.priceYearly / 12
      return {
        display: `€${monthlyEquivalent.toFixed(2)}`,
        period: 'per month',
        total: `€${plan.priceYearly}/year`,
        savings: Math.round(((plan.priceMonthly * 12 - plan.priceYearly) / (plan.priceMonthly * 12)) * 100),
      }
    }
    return {
      display: plan.priceMonthly === 0 ? '€0' : `€${plan.priceMonthly}`,
      period: plan.priceMonthly === 0 ? 'forever' : 'per month',
      total: null,
      savings: 0,
    }
  }

  return (
    <PublicLayout>
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">Simple, Transparent</span> Pricing
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that fits your needs. Upgrade, downgrade, or cancel anytime.
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="inline-flex items-center bg-muted rounded-lg p-1">
            <Button
              variant={billingInterval === 'monthly' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setBillingInterval('monthly')}
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

        {/* Plans Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto mb-16">
          {PLANS.map((plan) => {
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
                      <span className="text-muted-foreground text-sm">/ {pricing.period}</span>
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
                  <ul className="space-y-2.5">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-2.5">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link to="/register">
                    <Button className="w-full" variant={plan.popular ? 'default' : 'outline'}>
                      Get Started
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I change plans anytime?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, 
                  and we'll prorate any charges.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">What's the difference between monthly and yearly billing?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Yearly billing gives you a 25% discount. You pay once per year instead of monthly, 
                  saving significant money over time.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I cancel my subscription?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Absolutely! Cancel anytime from your account dashboard. You'll retain access until 
                  the end of your billing period, with no penalties or fees.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Do you offer refunds?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  We offer a 7-day money-back guarantee on all paid plans. Contact support within 7 days 
                  of purchase for a full refund, no questions asked.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </PublicLayout>
  )
}