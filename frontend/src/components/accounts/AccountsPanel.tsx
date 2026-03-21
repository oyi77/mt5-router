import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { useMT5Accounts, MT5Account, CreateAccountRequest } from '@/api/accounts'
import { Plus, RefreshCw, Trash2, Power, PowerOff, Server } from 'lucide-react'

export function AccountsPanel() {
  const { accounts, isLoading, createAccount, deleteAccount, connectAccount, disconnectAccount, fetchAccounts } = useMT5Accounts()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [formData, setFormData] = useState<CreateAccountRequest>({
    login: '',
    password: '',
    server: '',
    broker: '',
    account_name: '',
    is_demo: true,
    instance_id: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      await createAccount(formData)
      setIsDialogOpen(false)
      setFormData({
        login: '',
        password: '',
        server: '',
        broker: '',
        account_name: '',
        is_demo: true,
        instance_id: '',
      })
    } catch (error) {
      console.error('Failed to create account:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConnect = async (id: number) => {
    try {
      await connectAccount(id)
    } catch (error) {
      console.error('Failed to connect:', error)
    }
  }

  const handleDisconnect = async (id: number) => {
    try {
      await disconnectAccount(id)
    } catch (error) {
      console.error('Failed to disconnect:', error)
    }
  }

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this account?')) {
      try {
        await deleteAccount(id)
      } catch (error) {
        console.error('Failed to delete account:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">MT5 Accounts</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchAccounts}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setIsDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Account
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">Loading accounts...</div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No MT5 accounts configured</p>
          <p className="text-sm">Add your MT5 account to start trading</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <Card key={account.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{account.account_name || account.login}</CardTitle>
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(account.connection_status)}`} />
                </div>
                <p className="text-sm text-muted-foreground">{account.server}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Login:</span>
                    <span className="font-mono">{account.login}</span>
                  </div>
                  {account.broker && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Broker:</span>
                      <span>{account.broker}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Type:</span>
                    <Badge variant={account.is_demo ? 'outline' : 'default'}>
                      {account.is_demo ? 'Demo' : 'Live'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <span className="capitalize">{account.connection_status}</span>
                  </div>
                  {account.connection_error && (
                    <p className="text-xs text-red-500">{account.connection_error}</p>
                  )}
                </div>
                <div className="flex gap-2 mt-4">
                  {account.connection_status === 'connected' ? (
                    <Button variant="outline" size="sm" onClick={() => handleDisconnect(account.id)}>
                      <PowerOff className="h-4 w-4 mr-1" />
                      Disconnect
                    </Button>
                  ) : (
                    <Button size="sm" onClick={() => handleConnect(account.id)}>
                      <Power className="h-4 w-4 mr-1" />
                      Connect
                    </Button>
                  )}
                  <Button variant="destructive" size="sm" onClick={() => handleDelete(account.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add MT5 Account</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="login">MT5 Login (Account Number)</Label>
              <Input
                id="login"
                type="number"
                value={formData.login}
                onChange={(e) => setFormData({ ...formData, login: e.target.value })}
                placeholder="12345678"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Your MT5 password"
              />
            </div>
            <div>
              <Label htmlFor="server">Server</Label>
              <Input
                id="server"
                value={formData.server}
                onChange={(e) => setFormData({ ...formData, server: e.target.value })}
                placeholder="MetaQuotes-Demo or your broker server"
              />
            </div>
            <div>
              <Label htmlFor="broker">Broker (Optional)</Label>
              <Input
                id="broker"
                value={formData.broker || ''}
                onChange={(e) => setFormData({ ...formData, broker: e.target.value })}
                placeholder="Your broker name"
              />
            </div>
            <div>
              <Label htmlFor="account_name">Account Name (Optional)</Label>
              <Input
                id="account_name"
                value={formData.account_name || ''}
                onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                placeholder="My Trading Account"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                id="is_demo"
                type="checkbox"
                checked={formData.is_demo}
                onChange={(e) => setFormData({ ...formData, is_demo: e.target.checked })}
              />
              <Label htmlFor="is_demo">Demo Account</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={isSubmitting || !formData.login || !formData.password || !formData.server}>
              {isSubmitting ? 'Adding...' : 'Add Account'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
