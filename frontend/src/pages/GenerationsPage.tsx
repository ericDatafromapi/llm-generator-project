import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  FileStack,
  Download,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter,
  Calendar as CalendarIcon,
  X
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { format } from 'date-fns'
import type { Generation, PaginatedResponse } from '@/types'
import { RecommendationCard } from '@/components/RecommendationCard'
import { DeploymentTipsModal } from '@/components/DeploymentTipsModal'

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    icon: Clock,
    className: 'text-yellow-500',
    bgClass: 'bg-yellow-500/10 border-yellow-500/20',
  },
  processing: {
    label: 'Processing',
    icon: Loader2,
    className: 'text-blue-500 animate-spin',
    bgClass: 'bg-blue-500/10 border-blue-500/20',
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle,
    className: 'text-green-500',
    bgClass: 'bg-green-500/10 border-green-500/20',
  },
  failed: {
    label: 'Failed',
    icon: XCircle,
    className: 'text-red-500',
    bgClass: 'bg-red-500/10 border-red-500/20',
  },
}

export default function GenerationsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [dateFilter, setDateFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecommendation, setSelectedRecommendation] = useState<Generation | null>(null)

  // Fetch generations with auto-refresh for active ones
  const { data: generationsData, isLoading } = useQuery({
    queryKey: ['generations', statusFilter],
    queryFn: async () => {
      let url = '/api/v1/generations/history?per_page=100'
      if (statusFilter !== 'all') {
        url += `&status=${statusFilter}`
      }
      const response = await api.get<PaginatedResponse<Generation>>(url)
      return response.data
    },
    // Auto-refresh every 5 seconds if there are pending/processing generations
    refetchInterval: (query) => {
      const hasActiveGenerations = query?.state?.data?.items?.some(
        (gen: Generation) => gen.status === 'pending' || gen.status === 'processing'
      )
      return hasActiveGenerations ? 5000 : false
    },
  })

  // Filter generations by search query and date
  const filteredGenerations = generationsData?.items.filter((gen) => {
    // Search filter (by website name or URL)
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const websiteName = (gen.website_name || '').toLowerCase()
      const websiteUrl = (gen.website_url || '').toLowerCase()
      if (!websiteName.includes(query) && !websiteUrl.includes(query)) {
        return false
      }
    }
    
    // Date filter
    if (dateFilter !== 'all') {
      const genDate = new Date(gen.created_at)
      const now = new Date()
      const daysDiff = Math.floor((now.getTime() - genDate.getTime()) / (1000 * 60 * 60 * 24))
      
      switch (dateFilter) {
        case 'today':
          if (daysDiff > 0) return false
          break
        case 'week':
          if (daysDiff > 7) return false
          break
        case 'month':
          if (daysDiff > 30) return false
          break
      }
    }
    
    return true
  })

  const handleDownload = async (generationId: string) => {
    try {
      const response = await api.get(`/api/v1/generations/${generationId}/download`, {
        responseType: 'blob',
      })
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `llmready-${generationId}.zip`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      console.error('Download failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Generations</h1>
        <p className="text-muted-foreground mt-2">
          View and download your generation history
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by website name or URL..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Filter Row */}
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Status Filter Dropdown */}
              <div className="flex-1">
                <Label className="text-sm text-muted-foreground mb-2 block">Status</Label>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="w-full justify-between">
                      <span className="flex items-center gap-2">
                        <Filter className="h-4 w-4" />
                        {statusFilter === 'all' ? 'All Statuses' :
                         statusFilter === 'completed' ? 'Completed' :
                         statusFilter === 'processing' ? 'Processing' :
                         statusFilter === 'pending' ? 'Pending' : 'Failed'}
                      </span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56">
                    <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuRadioGroup value={statusFilter} onValueChange={setStatusFilter}>
                      <DropdownMenuRadioItem value="all">All Statuses</DropdownMenuRadioItem>
                      <DropdownMenuRadioItem value="completed">Completed</DropdownMenuRadioItem>
                      <DropdownMenuRadioItem value="processing">Processing</DropdownMenuRadioItem>
                      <DropdownMenuRadioItem value="pending">Pending</DropdownMenuRadioItem>
                      <DropdownMenuRadioItem value="failed">Failed</DropdownMenuRadioItem>
                    </DropdownMenuRadioGroup>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Date Filter - Dropdown Only */}
              <div className="flex-1">
                <Label className="text-sm text-muted-foreground mb-2 block">Time Period</Label>
                <div className="flex gap-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" className="w-full justify-between">
                        <span className="flex items-center gap-2">
                          <CalendarIcon className="h-4 w-4" />
                          {dateFilter === 'all' ? 'All Time' :
                           dateFilter === 'today' ? 'Today' :
                           dateFilter === 'week' ? 'Last 7 Days' : 'Last 30 Days'}
                        </span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56">
                      <DropdownMenuLabel>Filter by Date</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuRadioGroup value={dateFilter} onValueChange={setDateFilter}>
                        <DropdownMenuRadioItem value="all">All Time</DropdownMenuRadioItem>
                        <DropdownMenuRadioItem value="today">Today</DropdownMenuRadioItem>
                        <DropdownMenuRadioItem value="week">Last 7 Days</DropdownMenuRadioItem>
                        <DropdownMenuRadioItem value="month">Last 30 Days</DropdownMenuRadioItem>
                      </DropdownMenuRadioGroup>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  
                  {/* Clear filter */}
                  {dateFilter !== 'all' && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setDateFilter('all')}
                      title="Clear date filter"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Generations List */}
      {isLoading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      ) : filteredGenerations && filteredGenerations.length > 0 ? (
        <div className="space-y-4">
          {filteredGenerations.map((generation) => {
            const statusConfig = STATUS_CONFIG[generation.status]
            const StatusIcon = statusConfig.icon

            return (
              <Card key={generation.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <CardTitle className="text-base">
                          {generation.website_name || 'Website'}
                        </CardTitle>
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${statusConfig.bgClass}`}>
                          <StatusIcon className={`h-3 w-3 ${statusConfig.className}`} />
                          {statusConfig.label}
                        </span>
                      </div>
                      <CardDescription className="space-y-1">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-muted-foreground">ID:</span>
                          <code className="text-xs">{generation.id.slice(0, 8)}</code>
                        </div>
                        <div>Created {format(new Date(generation.created_at), 'PPp')}</div>
                      </CardDescription>
                    </div>

                    {generation.status === 'completed' && (
                      <Button
                        size="sm"
                        onClick={() => handleDownload(generation.id)}
                      >
                        <Download className="mr-2 h-3 w-3" />
                        Download
                      </Button>
                    )}
                  </div>
                </CardHeader>

                {generation.status === 'completed' && (
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Files</p>
                        <p className="font-medium">{generation.total_files || 0}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Size</p>
                        <p className="font-medium">
                          {generation.file_size
                            ? `${(generation.file_size / 1024 / 1024).toFixed(2)} MB`
                            : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Started</p>
                        <p className="font-medium">
                          {generation.started_at
                            ? format(new Date(generation.started_at), 'p')
                            : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Completed</p>
                        <p className="font-medium">
                          {generation.completed_at
                            ? format(new Date(generation.completed_at), 'p')
                            : 'N/A'}
                        </p>
                      </div>
                    </div>

                    {/* Show recommendation card if available */}
                    {generation.recommendation && generation.file_size && generation.total_pages && (
                      <RecommendationCard
                        recommendation={generation.recommendation}
                        fileSize={generation.file_size}
                        totalPages={generation.total_pages}
                        onShowTips={() => setSelectedRecommendation(generation)}
                      />
                    )}
                  </CardContent>
                )}

                {generation.status === 'failed' && generation.error_message && (
                  <CardContent>
                    <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20">
                      <p className="text-sm text-destructive">{generation.error_message}</p>
                    </div>
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileStack className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No generations yet</h3>
            <p className="text-sm text-muted-foreground mb-4 text-center max-w-sm">
              {statusFilter !== 'all'
                ? `No ${statusFilter} generations found`
                : 'Start your first generation from the Websites page'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Deployment Tips Modal */}
      {selectedRecommendation?.recommendation && (
        <DeploymentTipsModal
          open={!!selectedRecommendation}
          onOpenChange={(open) => !open && setSelectedRecommendation(null)}
          recommendation={selectedRecommendation.recommendation}
        />
      )}
    </div>
  )
}