import { Link } from 'react-router-dom'
import PublicLayout from '@/components/layouts/PublicLayout'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Zap, Shield, TrendingUp, Code2, Sparkles, ArrowRight } from 'lucide-react'

export default function LandingPage() {
  return (
    <PublicLayout>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Gradient background effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-background" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/20 rounded-full blur-3xl animate-glow" />
        
        <div className="container relative mx-auto px-4 py-24 md:py-32">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
                Make Your Website{' '}
                <span className="gradient-text">AI-Discoverable</span>
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Generate standardized llms.txt files that help ChatGPT, Claude, and other AI assistants 
                accurately understand and represent your business.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register">
                <Button size="lg" className="text-lg px-8">
                  Get Started for Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline" className="text-lg px-8">
                  Sign In
                </Button>
              </Link>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                <span>Lightning Fast</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary" />
                <span>100% Secure</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                <span>SEO for AI Era</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Why Choose <span className="gradient-text">LLMReady</span>?
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              The fastest way to make your website discoverable by AI assistants
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            <Card className="card-hover">
              <CardHeader>
                <Zap className="h-10 w-10 text-primary mb-4" />
                <CardTitle>Lightning Fast</CardTitle>
                <CardDescription>
                  Generate llms.txt files in seconds, not hours. Our optimized crawler processes 
                  hundreds of pages efficiently.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <Code2 className="h-10 w-10 text-primary mb-4" />
                <CardTitle>Standards Compliant</CardTitle>
                <CardDescription>
                  Follows the official llms.txt specification. Compatible with ChatGPT, Claude, 
                  Perplexity, and all major AI platforms.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <Shield className="h-10 w-10 text-primary mb-4" />
                <CardTitle>Enterprise Security</CardTitle>
                <CardDescription>
                  Bank-level encryption, secure authentication, and complete data privacy. 
                  Your content stays yours.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <TrendingUp className="h-10 w-10 text-primary mb-4" />
                <CardTitle>Auto Updates</CardTitle>
                <CardDescription>
                  Set up once, stay current forever. Automatic regeneration keeps your llms.txt 
                  file synchronized with your site.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <Sparkles className="h-10 w-10 text-primary mb-4" />
                <CardTitle>Smart Processing</CardTitle>
                <CardDescription>
                  Advanced content extraction ensures AI assistants get the most relevant information 
                  about your business.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <ArrowRight className="h-10 w-10 text-primary mb-4" />
                <CardTitle>Easy Integration</CardTitle>
                <CardDescription>
                  One-click deployment. Download your files and upload to your website root. 
                  No technical expertise required.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <Card className="max-w-4xl mx-auto text-center overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-accent/20" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/30 rounded-full blur-3xl animate-glow" />
            
            <CardContent className="relative p-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Be AI-Discoverable?
              </h2>
              <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
                Join hundreds of websites making their content AI-ready. 
                Start with a free trial today.
              </p>
              <Link to="/register">
                <Button size="lg" className="text-lg px-8">
                  Get Started for Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <p className="text-sm text-muted-foreground mt-4">
                No credit card required • Free forever plan available
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </PublicLayout>
  )
}