import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { billingApi } from '@/api/billing'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { CreditCard, Check, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

export function BillingPanel() {
  const queryClient = useQueryClient()
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly')

  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: billingApi.getSubscription,
  })

  const { data: usage } = useQuery({
    queryKey: ['usage'],
    queryFn: billingApi.getUsage,
  })

  const { data: tiers } = useQuery({
    queryKey: ['tiers'],
    queryFn: billingApi.getTiers,
  })

  const { data: invoices } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => billingApi.getInvoices(10),
  })

  const createCheckout = useMutation({
    mutationFn: ({ tier, period }: { tier: string; period: 'monthly' | 'yearly' }) =>
      billingApi.createCheckout(tier, period),
    onSuccess: (data) => {
      window.location.href = data.url
    }
  })

  const cancelSubscription = useMutation({
    mutationFn: () => billingApi.cancelSubscription(false),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscription'] }),
  })

  const reactivate = useMutation({
    mutationFn: billingApi.reactivateSubscription,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscription'] }),
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Current Plan
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold capitalize">{subscription?.tier || 'Free'}</h3>
              <p className="text-muted-foreground">
                {subscription?.status === 'active' ? 'Active' : subscription?.status}
                {subscription?.current_period_end && (
                  <> • Renews {new Date(subscription.current_period_end).toLocaleDateString()}</>
                )}
              </p>
            </div>
            <div className="flex gap-2">
              {subscription?.cancel_at_period_end ? (
                <Button onClick={() => reactivate.mutate()}>
                  Reactivate Subscription
                </Button>
              ) : subscription?.tier !== 'free' ? (
                <Button variant="outline" onClick={() => cancelSubscription.mutate()}>
                  Cancel Subscription
                </Button>
              ) : null}
              <Button variant="outline" onClick={() => window.open('/api/v1/billing/portal', '_blank')}>
                <ExternalLink className="h-4 w-4 mr-2" />
                Billing Portal
              </Button>
            </div>
          </div>

          {usage && (
            <div className="mt-6 grid grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <div className="flex justify-between mb-2">
                  <span>Servers</span>
                  <span>{usage.usage.servers.current} / {usage.usage.servers.unlimited ? '∞' : usage.usage.servers.limit}</span>
                </div>
                {!usage.usage.servers.unlimited && (
                  <Progress value={(usage.usage.servers.current / usage.usage.servers.limit) * 100} />
                )}
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex justify-between mb-2">
                  <span>Instances</span>
                  <span>{usage.usage.instances.current} / {usage.usage.instances.unlimited ? '∞' : usage.usage.instances.limit}</span>
                </div>
                {!usage.usage.instances.unlimited && (
                  <Progress value={(usage.usage.instances.current / usage.usage.instances.limit) * 100} />
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Available Plans</h2>
          <div className="flex gap-2 p-1 bg-muted rounded-lg">
            <Button
              size="sm"
              variant={billingPeriod === 'monthly' ? 'secondary' : 'ghost'}
              onClick={() => setBillingPeriod('monthly')}
            >
              Monthly
            </Button>
            <Button
              size="sm"
              variant={billingPeriod === 'yearly' ? 'secondary' : 'ghost'}
              onClick={() => setBillingPeriod('yearly')}
            >
              Yearly <Badge variant="success" className="ml-2">Save 17%</Badge>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tiers && Object.entries(tiers).map(([key, tier]) => {
            const isCurrentPlan = subscription?.tier === key
            const price = billingPeriod === 'monthly' ? tier.price_monthly : tier.price_yearly
            
            return (
              <Card key={key} className={cn(
                "relative",
                isCurrentPlan && "border-primary ring-2 ring-primary"
              )}>
                {isCurrentPlan && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge>Current Plan</Badge>
                  </div>
                )}
                <CardHeader>
                  <CardTitle>{tier.name}</CardTitle>
                  <CardDescription>
                    <span className="text-3xl font-bold text-foreground">${(price / 100).toFixed(0)}</span>
                    <span className="text-muted-foreground">/{billingPeriod === 'monthly' ? 'mo' : 'yr'}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-4">
                    {tier.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className="w-full" 
                    variant={isCurrentPlan ? "outline" : "default"}
                    disabled={isCurrentPlan || price === 0}
                    onClick={() => createCheckout.mutate({ tier: key, period: billingPeriod })}
                  >
                    {isCurrentPlan ? 'Current Plan' : price === 0 ? 'Contact Sales' : 'Upgrade'}
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {invoices && invoices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Invoices</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Date</th>
                  <th className="text-right py-2">Amount</th>
                  <th className="text-center py-2">Status</th>
                  <th className="text-right py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-b">
                    <td className="py-2">{new Date(invoice.created).toLocaleDateString()}</td>
                    <td className="py-2 text-right">${(invoice.amount / 100).toFixed(2)}</td>
                    <td className="py-2 text-center">
                      <Badge variant={invoice.status === 'paid' ? 'success' : 'secondary'}>
                        {invoice.status}
                      </Badge>
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex gap-2 justify-end">
                        {invoice.invoice_url && (
                          <Button size="sm" variant="ghost" onClick={() => window.open(invoice.invoice_url!, '_blank')}>
                            View
                          </Button>
                        )}
                        {invoice.pdf_url && (
                          <Button size="sm" variant="ghost" onClick={() => window.open(invoice.pdf_url!, '_blank')}>
                            PDF
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
