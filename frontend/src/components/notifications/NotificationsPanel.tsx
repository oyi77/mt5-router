import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi, AlertRule } from '@/api/notifications'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Bell, Send, Trash2, Settings } from 'lucide-react'

export function NotificationsPanel() {
  const queryClient = useQueryClient()
  const [telegramToken, setTelegramToken] = useState('')
  const [telegramChatId, setTelegramChatId] = useState('')
  const [showTelegramConfig, setShowTelegramConfig] = useState(false)

  const { data: alerts = [] } = useQuery({
    queryKey: ['alerts'],
    queryFn: notificationsApi.listAlerts,
  })

  const configureTelegram = useMutation({
    mutationFn: notificationsApi.configureTelegram,
    onSuccess: () => {
      setShowTelegramConfig(false)
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

  const testTelegram = useMutation({
    mutationFn: notificationsApi.testTelegram,
  })

  const deleteAlert = useMutation({
    mutationFn: notificationsApi.deleteAlert,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const toggleAlert = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      notificationsApi.updateAlert(id, is_active),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => setShowTelegramConfig(!showTelegramConfig)}>
            <Settings className="h-4 w-4 mr-2" />
            Configure Telegram
          </Button>
        </CardHeader>
        <CardContent>
          {showTelegramConfig && (
            <div className="mb-4 p-4 border rounded-lg space-y-3">
              <div>
                <label className="text-sm font-medium">Bot Token</label>
                <Input
                  type="password"
                  placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                  value={telegramToken}
                  onChange={(e) => setTelegramToken(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Chat ID</label>
                <Input
                  placeholder="-1001234567890"
                  value={telegramChatId}
                  onChange={(e) => setTelegramChatId(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => configureTelegram.mutate({ bot_token: telegramToken, chat_id: telegramChatId })}
                  disabled={!telegramToken || !telegramChatId}
                >
                  Save Configuration
                </Button>
                <Button variant="outline" onClick={() => testTelegram.mutate()}>
                  <Send className="h-4 w-4 mr-2" />
                  Test
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <h3 className="font-medium">Alert Rules ({alerts.length})</h3>
            {alerts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No alert rules configured</p>
            ) : (
              <div className="space-y-2">
                {alerts.map((alert: AlertRule) => (
                  <div key={alert.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <Badge variant={alert.is_active ? 'success' : 'secondary'}>
                        {alert.type}
                      </Badge>
                      <span className="ml-2 text-sm">
                        {alert.symbol} {alert.condition} {alert.value}
                      </span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        via {alert.channel}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => toggleAlert.mutate({ id: alert.id, is_active: !alert.is_active })}
                      >
                        {alert.is_active ? 'Disable' : 'Enable'}
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => deleteAlert.mutate(alert.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
