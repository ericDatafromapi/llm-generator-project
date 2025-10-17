import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Globe, FileStack, TrendingUp, Plus, ArrowRight, Loader2 } from 'lucide-react'
import type { UserStats, Subscription } from '@/types'

export default function DashboardPage() {
  const { user } = useAuthStore()

  // Fetch user statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['user-stats'],
    queryFn: async () => {
      const response = await api.get<UserStats>('/api/v1/websites/stats/user')
      return response.data
    },
  })

  // Fetch current subscription
  const { data: subscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ['subscription'],
    queryFn: async () => {
      const response = await api.get<Subscription>('/api/v1/subscriptions/current')
      return response.data
    },
  })

  const isLoading = statsLoading || subscriptionLoading

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!
        </h1>
        <p className="text-muted-foreground mt-2">
          Here's an overview of your LLMReady account
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Websites</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">{stats?.total_websites || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.active_websites || 0} active
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <FileStack className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">{stats?.generations_this_month || 0}</div>
                <p className="text-xs text-muted-foreground">
                  generations completed
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Remaining</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">{stats?.generations_remaining || 0}</div>
                <p className="text-xs text-muted-foreground">
                  of {subscription?.generations_limit || 0} this month
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {stats?.success_rate?.toFixed(0) || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.successful_generations || 0} successful
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
          <CardDescription>
            Manage your subscription and usage
          </CardDescription>
        </CardHeader>
        <CardContent>
          {subscriptionLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    Plan: <span className="text-lg font-bold capitalize">{subscription?.plan_type || 'Free'}</span>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Status: <span className="capitalize">{subscription?.status || 'Active'}</span>
                  </p>
                </div>
                <Link to="/dashboard/subscription">
                  <Button>
                    Manage Plan
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>

              {/* Usage Progress */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Monthly Generations</span>
                  <span className="font-medium">
                    {subscription?.generations_used || 0} / {subscription?.generations_limit || 0}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-primary h-full transition-all duration-300"
                    style={{
                      width: `${Math.min(
                        ((subscription?.generations_used || 0) / (subscription?.generations_limit || 1)) * 100,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
          <Link to="/dashboard/websites">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <CardTitle className="group-hover:text-primary transition-colors">
                    Manage Websites
                  </CardTitle>
                  <CardDescription>
                    Add, edit, or remove your websites
                  </CardDescription>
                </div>
                <Globe className="h-8 w-8 text-primary" />
              </div>
            </CardHeader>
            <CardContent>
              <Button variant="ghost" className="w-full justify-between group-hover:bg-primary/10">
                Go to Websites
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
          <Link to="/dashboard/generations">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <CardTitle className="group-hover:text-primary transition-colors">
                    View Generations
                  </CardTitle>
                  <CardDescription>
                    Check your generation history
                  </CardDescription>
                </div>
                <FileStack className="h-8 w-8 text-primary" />
              </div>
            </CardHeader>
            <CardContent>
              <Button variant="ghost" className="w-full justify-between group-hover:bg-primary/10">
                Go to Generations
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardContent>
          </Link>
        </Card>
      </div>

      {/* Getting Started (for new users) */}
      {stats && stats.total_websites === 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
            <CardDescription>
              Create your first website to start generating llms.txt files
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  1
                </div>
                <div>
                  <p className="font-medium">Add Your Website</p>
                  <p className="text-sm text-muted-foreground">
                    Enter your website URL and configure crawling options
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  2
                </div>
                <div>
                  <p className="font-medium">Generate Content</p>
                  <p className="text-sm text-muted-foreground">
                    Click generate to create your llms.txt file
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  3
                </div>
                <div>
                  <p className="font-medium">Download & Deploy</p>
                  <p className="text-sm text-muted-foreground">
                    Download the files and upload to your website
                  </p>
                </div>
              </div>
            </div>
            <Link to="/dashboard/websites">
              <Button className="w-full">
                <Plus className="mr-2 h-4 w-4" />
                Add Your First Website
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  )
}