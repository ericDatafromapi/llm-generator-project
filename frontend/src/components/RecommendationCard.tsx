import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Info, CheckCircle2 } from 'lucide-react'
import type { FileRecommendation } from '@/types'

interface RecommendationCardProps {
  recommendation: FileRecommendation
  fileSize: number
  totalPages: number
  onShowTips: () => void
}

export function RecommendationCard({ 
  recommendation, 
  fileSize, 
  totalPages,
  onShowTips 
}: RecommendationCardProps) {
  const fileSizeMB = (fileSize / (1024 * 1024)).toFixed(2)
  
  const getBadgeColor = (type: string) => {
    switch (type) {
      case 'minimal':
        return 'bg-green-500/10 text-green-700 border-green-500/20'
      case 'standard':
        return 'bg-blue-500/10 text-blue-700 border-blue-500/20'
      case 'complete':
        return 'bg-purple-500/10 text-purple-700 border-purple-500/20'
      default:
        return 'bg-gray-500/10 text-gray-700 border-gray-500/20'
    }
  }

  return (
    <Card className="border-2">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">Deployment Recommendation</CardTitle>
            </div>
            <CardDescription>
              Based on your website size and content
            </CardDescription>
          </div>
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${getBadgeColor(recommendation.type)}`}>
            {recommendation.title}
          </span>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Stats Summary */}
        <div className="grid grid-cols-2 gap-4 p-3 rounded-lg bg-muted/50">
          <div>
            <p className="text-sm text-muted-foreground">Total Pages</p>
            <p className="text-lg font-semibold">{totalPages}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Size</p>
            <p className="text-lg font-semibold">{fileSizeMB} MB</p>
          </div>
        </div>

        {/* Recommendation */}
        <div className="space-y-2">
          <p className="text-sm font-medium">{recommendation.description}</p>
          <div className="space-y-1.5">
            {recommendation.files.map((file, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <code className="px-2 py-0.5 rounded bg-muted text-xs font-mono">{file}</code>
              </div>
            ))}
          </div>
        </div>

        {/* Learn More Button */}
        <Button 
          variant="outline" 
          className="w-full"
          onClick={onShowTips}
        >
          <Info className="mr-2 h-4 w-4" />
          View Deployment Instructions
        </Button>
      </CardContent>
    </Card>
  )
}