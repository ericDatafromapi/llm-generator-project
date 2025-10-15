import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { FileRecommendation } from '@/types'
import { CheckCircle2, Download, Upload, FolderOpen, AlertCircle } from 'lucide-react'

interface DeploymentTipsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  recommendation: FileRecommendation
}

export function DeploymentTipsModal({
  open,
  onOpenChange,
  recommendation,
}: DeploymentTipsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Deployment Instructions</DialogTitle>
          <DialogDescription>
            Step-by-step guide to deploy your LLM-ready files
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Why These Files */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              Why We Recommend This Setup
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {recommendation.reason}
            </p>
            <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                <strong>Recommended files for your site:</strong>
              </p>
              <ul className="mt-2 space-y-1">
                {recommendation.files.map((file, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-200">
                    <CheckCircle2 className="h-3 w-3" />
                    <code className="font-mono">{file}</code>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Deployment Steps */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-green-600" />
              Deployment Steps
            </h3>
            <ol className="space-y-4">
              <li className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                  1
                </div>
                <div className="flex-1">
                  <p className="font-medium mb-1">Download Your Files</p>
                  <p className="text-sm text-muted-foreground">
                    Click the "Download" button to get your generated ZIP file.
                  </p>
                </div>
              </li>

              <li className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                  2
                </div>
                <div className="flex-1">
                  <p className="font-medium mb-1">Extract the ZIP Archive</p>
                  <p className="text-sm text-muted-foreground">
                    Unzip the downloaded file to access the generated content.
                  </p>
                </div>
              </li>

              <li className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                  3
                </div>
                <div className="flex-1">
                  <p className="font-medium mb-1">Select Your Files</p>
                  <p className="text-sm text-muted-foreground mb-2">
                    Based on your website size, we recommend uploading:
                  </p>
                  <ul className="space-y-1">
                    {recommendation.files.map((file, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="h-3 w-3 text-green-600" />
                        <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">{file}</code>
                      </li>
                    ))}
                  </ul>
                </div>
              </li>

              <li className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                  4
                </div>
                <div className="flex-1">
                  <p className="font-medium mb-1">Upload to Your Website Root</p>
                  <p className="text-sm text-muted-foreground">
                    Upload the selected files/folders to the root directory of your website (where your index.html or homepage is located). This ensures AI assistants can discover and use them.
                  </p>
                </div>
              </li>
            </ol>
          </div>

          {/* Additional Notes */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Important Notes</h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>
                • These are <strong>recommendations</strong> based on your site size. You're free to upload whichever files work best for your needs.
              </p>
              <p>
                • The <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">llms.txt</code> file is the primary discovery file that AI assistants look for.
              </p>
              <p>
                • Files must be accessible at your domain root (e.g., <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">https://yourdomain.com/llms.txt</code>).
              </p>
              <p>
                • After uploading, test accessibility by visiting the file URLs directly in your browser.
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}