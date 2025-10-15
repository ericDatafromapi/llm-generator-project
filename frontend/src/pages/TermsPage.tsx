import PublicLayout from '@/components/layouts/PublicLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText } from 'lucide-react'

export default function TermsPage() {
  return (
    <PublicLayout>
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <FileText className="h-16 w-16 text-primary mx-auto mb-6" />
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Terms of <span className="gradient-text">Service</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Last updated: October 15, 2025
            </p>
          </div>

          {/* Content */}
          <Card>
            <CardHeader>
              <CardTitle>Terms of Service</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-invert max-w-none">
              <h2>1. Acceptance of Terms</h2>
              <p>
                By accessing and using LLMReady ("the Service"), you agree to be bound by these Terms of Service.
                If you do not agree to these terms, please do not use the Service.
              </p>

              <h2>2. Description of Service</h2>
              <p>
                LLMReady provides AI-optimized content generation services, converting websites into
                LLM-ready documentation formats including llms.txt files and markdown content.
              </p>

              <h2>3. Subscription Plans</h2>
              <p>
                The Service offers multiple subscription tiers (Free, Starter, Standard, Pro) with
                varying features and usage limits. Detailed pricing and features are available on our
                Pricing page.
              </p>

              <h2>4. EU 14-Day Cooling-Off Period</h2>
              <p>
                <strong>Important for EU Customers:</strong> You have the right to cancel your subscription
                within 14 days of purchase for a refund, in accordance with EU Consumer Rights Directive (2011/83/EU).
              </p>
              <p>
                <strong>Usage-Based Refund:</strong> If you use the Service during the 14-day period
                (by creating content generations), we reserve the right to charge for the service provided:
              </p>
              <ul>
                <li>Refund Amount = Total Paid - (Generations Created × Price per Generation)</li>
                <li>Price per Generation varies by plan (€2.37 - €6.33 per generation)</li>
                <li>Minimum usage charge of €10 if service was used</li>
                <li>Maximum 10 generations for full refund eligibility</li>
              </ul>
              <p>
                By subscribing, you expressly request immediate access to the Service and acknowledge
                that usage during the cooling-off period will result in usage charges as described above.
              </p>

              <h2>5. Payment and Billing</h2>
              <p>
                - Subscriptions are billed monthly or yearly based on your selection<br />
                - Automatic renewal unless canceled<br />
                - Proration applies to plan changes<br />
                - Payments processed securely via Stripe<br />
                - Failed payments result in a 3-day grace period before service suspension
              </p>

              <h2>6. Cancellation Policy</h2>
              <p>
                <strong>Within 14 days:</strong> Eligible for partial refund (total paid minus usage charges)<br />
                <strong>After 14 days:</strong> Cancel at period end, access maintained until period expires<br />
                <strong>After cancellation:</strong> Account downgraded to Free plan
              </p>

              <h2>7. Usage Limits and Quotas</h2>
              <p>
                Each plan has specific limits on websites, generations per month, and pages per generation.
                Exceeding these limits requires upgrading to a higher tier plan.
              </p>

              <h2>8. Acceptable Use</h2>
              <p>
                You agree not to:
              </p>
              <ul>
                <li>Use the Service for illegal purposes</li>
                <li>Attempt to bypass usage limits or quotas</li>
                <li>Abuse the 14-day cooling-off period</li>
                <li>Share your account credentials</li>
                <li>Reverse engineer or copy the Service</li>
              </ul>

              <h2>9. Data and Privacy</h2>
              <p>
                Your use of the Service is also governed by our Privacy Policy. We process
                personal data in accordance with GDPR and applicable data protection laws.
              </p>

              <h2>10. Intellectual Property</h2>
              <p>
                Content generated through the Service belongs to you. The Service itself,
                including all software, designs, and trademarks, remains our property.
              </p>

              <h2>11. Limitation of Liability</h2>
              <p>
                The Service is provided "as is" without warranties. We are not liable for
                indirect damages, data loss, or business interruption.
              </p>

              <h2>12. Changes to Terms</h2>
              <p>
                We reserve the right to modify these terms at any time. Continued use of
                the Service after changes constitutes acceptance of the modified terms.
              </p>

              <h2>13. Governing Law</h2>
              <p>
                These terms are governed by the laws of France and the European Union.
                Disputes are subject to the jurisdiction of French courts.
              </p>

              <h2>14. Contact Information</h2>
              <p>
                For questions about these Terms of Service, please contact us at:
                <br />
                <a href="mailto:support@llmready.com" className="text-primary hover:underline">
                  support@llmready.com
                </a>
              </p>

              <div className="mt-8 p-4 bg-primary/10 border border-primary/20 rounded-lg">
                <p className="text-sm">
                  <strong>Note:</strong> This is a template. Please customize these terms with your lawyer
                  to ensure full compliance with applicable laws in your jurisdiction.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </PublicLayout>
  )
}