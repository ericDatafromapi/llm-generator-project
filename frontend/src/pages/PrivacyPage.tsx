import PublicLayout from '@/components/layouts/PublicLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Shield } from 'lucide-react'

export default function PrivacyPage() {
  return (
    <PublicLayout>
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <Shield className="h-16 w-16 text-primary mx-auto mb-6" />
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Privacy <span className="gradient-text">Policy</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Last updated: October 15, 2025
            </p>
          </div>

          {/* Content */}
          <Card>
            <CardHeader>
              <CardTitle>Privacy Policy</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-invert max-w-none">
              <h2>1. Introduction</h2>
              <p>
                LLMReady ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy
                explains how we collect, use, disclose, and safeguard your information when you use our Service.
              </p>

              <h2>2. Information We Collect</h2>
              
              <h3>2.1 Information You Provide</h3>
              <ul>
                <li><strong>Account Information:</strong> Email address, full name, password (encrypted)</li>
                <li><strong>Payment Information:</strong> Processed by Stripe (we don't store card details)</li>
                <li><strong>Website URLs:</strong> URLs you submit for content generation</li>
                <li><strong>Contact Information:</strong> When you contact support</li>
              </ul>

              <h3>2.2 Automatically Collected Information</h3>
              <ul>
                <li><strong>Usage Data:</strong> Generations created, websites added, features used</li>
                <li><strong>Technical Data:</strong> IP address, browser type, device information</li>
                <li><strong>Cookies:</strong> Authentication tokens, session management</li>
              </ul>

              <h2>3. How We Use Your Information</h2>
              <p>We use your information to:</p>
              <ul>
                <li>Provide and maintain the Service</li>
                <li>Process payments and subscriptions</li>
                <li>Send transactional emails (verification, notifications)</li>
                <li>Improve our Service and user experience</li>
                <li>Prevent fraud and ensure security</li>
                <li>Comply with legal obligations</li>
              </ul>

              <h2>4. Data Sharing and Disclosure</h2>
              
              <h3>4.1 Third-Party Service Providers</h3>
              <ul>
                <li><strong>Stripe:</strong> Payment processing (PCI-DSS compliant)</li>
                <li><strong>SendGrid:</strong> Email delivery</li>
                <li><strong>Cloud Hosting:</strong> Secure data storage</li>
              </ul>

              <h3>4.2 Legal Requirements</h3>
              <p>
                We may disclose your information if required by law, court order, or to protect
                our rights and safety.
              </p>

              <h2>5. Data Security</h2>
              <p>We implement industry-standard security measures:</p>
              <ul>
                <li>HTTPS encryption for all data transmission</li>
                <li>Bcrypt password hashing</li>
                <li>Regular security audits</li>
                <li>Access controls and authentication</li>
                <li>Encrypted data storage</li>
              </ul>

              <h2>6. Your Rights (GDPR)</h2>
              <p>Under GDPR, you have the right to:</p>
              <ul>
                <li><strong>Access:</strong> Request a copy of your personal data</li>
                <li><strong>Rectification:</strong> Correct inaccurate data</li>
                <li><strong>Erasure:</strong> Request deletion of your data ("right to be forgotten")</li>
                <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
                <li><strong>Object:</strong> Object to data processing</li>
                <li><strong>Withdraw Consent:</strong> At any time</li>
              </ul>

              <h2>7. Data Retention</h2>
              <p>We retain your data for:</p>
              <ul>
                <li><strong>Account data:</strong> As long as your account is active</li>
                <li><strong>Generated content:</strong> 30 days after generation</li>
                <li><strong>Payment records:</strong> 7 years (legal requirement)</li>
                <li><strong>Email verification tokens:</strong> 24 hours</li>
                <li><strong>Password reset tokens:</strong> 1 hour</li>
              </ul>

              <h2>8. Cookies and Tracking</h2>
              <p>We use cookies for:</p>
              <ul>
                <li><strong>Essential cookies:</strong> Authentication and session management (required)</li>
                <li><strong>Analytics cookies:</strong> Usage statistics (optional)</li>
              </ul>
              <p>
                You can control cookies through your browser settings. Note that disabling essential
                cookies may affect Service functionality.
              </p>

              <h2>9. Children's Privacy</h2>
              <p>
                The Service is not intended for users under 16 years of age. We do not knowingly
                collect personal information from children.
              </p>

              <h2>10. International Data Transfers</h2>
              <p>
                Your data may be transferred to and processed in countries outside the EU. We ensure
                adequate protection through:
              </p>
              <ul>
                <li>EU Standard Contractual Clauses</li>
                <li>GDPR-compliant data processors</li>
                <li>Encryption in transit and at rest</li>
              </ul>

              <h2>11. Changes to Privacy Policy</h2>
              <p>
                We may update this Privacy Policy from time to time. We will notify you of any
                material changes via email or Service notification.
              </p>

              <h2>12. Contact Us</h2>
              <p>
                For privacy-related questions or to exercise your GDPR rights, contact us at:
              </p>
              <p>
                <strong>Email:</strong> <a href="mailto:privacy@llmready.com" className="text-primary hover:underline">privacy@llmready.com</a><br />
                <strong>Data Protection Officer:</strong> <a href="mailto:dpo@llmready.com" className="text-primary hover:underline">dpo@llmready.com</a>
              </p>

              <h2>13. EU Representative</h2>
              <p>
                For EU-specific inquiries:<br />
                [Your EU Representative Details Here]
              </p>

              <div className="mt-8 p-4 bg-primary/10 border border-primary/20 rounded-lg">
                <p className="text-sm mb-0">
                  <strong>Note:</strong> This is a template privacy policy. Please customize it with your lawyer
                  to ensure full GDPR compliance and accuracy for your specific business operations.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </PublicLayout>
  )
}