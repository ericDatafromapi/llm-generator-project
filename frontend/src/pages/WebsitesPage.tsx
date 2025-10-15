import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { toast } from 'sonner'
import { Globe, Plus, Pencil, Trash2, Loader2, Play, ExternalLink } from 'lucide-react'
import type { Website, WebsiteCreate, PaginatedResponse } from '@/types'
import { format } from 'date-fns'

const websiteSchema = z.object({
  url: z.string().url('Must be a valid URL'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().optional(),
  include_patterns: z.string().optional(),
  exclude_patterns: z.string().optional(),
  max_pages: z.number().min(10).max(1000).default(100),
  use_playwright: z.boolean().default(false),
  timeout: z.number().min(60).max(600).default(300),
})

type WebsiteFormData = z.infer<typeof websiteSchema>

export default function WebsitesPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingWebsite, setEditingWebsite] = useState<Website | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<Website | null>(null)

  // Fetch websites
  const { data: websitesData, isLoading } = useQuery({
    queryKey: ['websites'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Website>>('/api/v1/websites?per_page=100')
      return response.data
    },
  })

  // Create website mutation
  const createMutation = useMutation({
    mutationFn: async (data: WebsiteFormData) => {
      const response = await api.post<Website>('/api/v1/websites', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      toast.success('Website created successfully!')
      setIsDialogOpen(false)
      reset()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create website')
    },
  })

  // Update website mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<WebsiteFormData> }) => {
      const response = await api.put<Website>(`/api/v1/websites/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      toast.success('Website updated successfully!')
      setIsDialogOpen(false)
      setEditingWebsite(null)
      reset()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update website')
    },
  })

  // Delete website mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/websites/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      toast.success('Website deleted successfully!')
      setDeleteConfirm(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete website')
    },
  })

  // Start generation mutation
  const startGenerationMutation = useMutation({
    mutationFn: async (websiteId: string) => {
      const response = await api.post('/api/v1/generations/start', {
        website_id: websiteId,
      })
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Generation started! Check the Generations page for progress.')
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      queryClient.invalidateQueries({ queryKey: ['generations'] })
      // Navigate to generations page to see progress
      setTimeout(() => {
        navigate('/dashboard/generations')
      }, 1500)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start generation')
    },
  })

  // Form
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<WebsiteFormData>({
    resolver: zodResolver(websiteSchema),
    defaultValues: {
      max_pages: 100,
      use_playwright: false,
      timeout: 300,
    },
  })

  const onSubmit = async (data: WebsiteFormData) => {
    if (editingWebsite) {
      updateMutation.mutate({ id: editingWebsite.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleEdit = (website: Website) => {
    setEditingWebsite(website)
    setValue('url', website.url)
    setValue('name', website.name)
    setValue('description', website.description || '')
    setValue('include_patterns', website.include_patterns || '')
    setValue('exclude_patterns', website.exclude_patterns || '')
    setValue('max_pages', website.max_pages)
    setValue('use_playwright', website.use_playwright)
    setValue('timeout', website.timeout)
    setIsDialogOpen(true)
  }

  const handleAddNew = () => {
    setEditingWebsite(null)
    reset()
    setIsDialogOpen(true)
  }

  const handleStartGeneration = (websiteId: string) => {
    startGenerationMutation.mutate(websiteId)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Websites</h1>
          <p className="text-muted-foreground mt-2">
            Manage your websites and configurations
          </p>
        </div>
        <Button onClick={handleAddNew}>
          <Plus className="mr-2 h-4 w-4" />
          Add Website
        </Button>
      </div>

      {/* Websites List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : websitesData && websitesData.items.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {websitesData.items.map((website) => (
            <Card key={website.id} className="hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Globe className="h-4 w-4 text-primary" />
                      {website.name}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-1">
                      <a
                        href={website.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-primary transition-colors truncate flex items-center gap-1"
                      >
                        {website.url}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </CardDescription>
                  </div>
                </div>
                {website.description && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {website.description}
                  </p>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Stats */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Generations</p>
                    <p className="font-medium">{website.generation_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Max Pages</p>
                    <p className="font-medium">{website.max_pages}</p>
                  </div>
                </div>

                {website.last_generated_at && (
                  <p className="text-xs text-muted-foreground">
                    Last generated: {format(new Date(website.last_generated_at), 'PPp')}
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => handleStartGeneration(website.id)}
                  >
                    <Play className="mr-2 h-3 w-3" />
                    Generate
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(website)}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => setDeleteConfirm(website)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Globe className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No websites yet</h3>
            <p className="text-sm text-muted-foreground mb-4 text-center max-w-sm">
              Add your first website to start generating llms.txt files
            </p>
            <Button onClick={handleAddNew}>
              <Plus className="mr-2 h-4 w-4" />
              Add Your First Website
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Add/Edit Website Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingWebsite ? 'Edit Website' : 'Add New Website'}
            </DialogTitle>
            <DialogDescription>
              {editingWebsite
                ? 'Update your website configuration'
                : 'Add a new website to generate llms.txt files'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* URL */}
            <div className="space-y-2">
              <Label htmlFor="url">Website URL *</Label>
              <Input
                id="url"
                placeholder="https://example.com"
                {...register('url')}
              />
              {errors.url && (
                <p className="text-sm text-destructive">{errors.url.message}</p>
              )}
            </div>

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Website Name *</Label>
              <Input
                id="name"
                placeholder="My Awesome Site"
                {...register('name')}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Input
                id="description"
                placeholder="A brief description of this website"
                {...register('description')}
              />
            </div>

            {/* Include Patterns */}
            <div className="space-y-2">
              <Label htmlFor="include_patterns">Include Patterns (optional)</Label>
              <Input
                id="include_patterns"
                placeholder="docs,blog,faq"
                {...register('include_patterns')}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated URL patterns to include
              </p>
            </div>

            {/* Exclude Patterns */}
            <div className="space-y-2">
              <Label htmlFor="exclude_patterns">Exclude Patterns (optional)</Label>
              <Input
                id="exclude_patterns"
                placeholder="login,admin,cart"
                {...register('exclude_patterns')}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated URL patterns to exclude
              </p>
            </div>

            {/* Max Pages */}
            <div className="space-y-2">
              <Label htmlFor="max_pages">Maximum Pages</Label>
              <Input
                id="max_pages"
                type="number"
                {...register('max_pages', { valueAsNumber: true })}
              />
              {errors.max_pages && (
                <p className="text-sm text-destructive">{errors.max_pages.message}</p>
              )}
            </div>

            {/* Advanced Options */}
            <div className="space-y-3 pt-2 border-t">
              <h3 className="text-sm font-medium">Advanced Options</h3>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="use_playwright"
                  {...register('use_playwright')}
                  className="rounded border-input"
                />
                <Label htmlFor="use_playwright" className="cursor-pointer">
                  Use JavaScript rendering (slower but handles dynamic content)
                </Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  {...register('timeout', { valueAsNumber: true })}
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsDialogOpen(false)
                  setEditingWebsite(null)
                  reset()
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {createMutation.isPending || updateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {editingWebsite ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  <>{editingWebsite ? 'Update Website' : 'Create Website'}</>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Website</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{deleteConfirm?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteConfirm(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete Website'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}