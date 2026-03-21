import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { serversApi, ServerHealth } from '@/api/servers'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Server, Plus, RefreshCw, Trash2, Activity, 
  Cpu, HardDrive, MemoryStick, ChevronDown, ChevronUp 
} from 'lucide-react'
import { cn } from '@/lib/utils'

export function ServersPanel() {
  const queryClient = useQueryClient()
  const [showAddForm, setShowAddForm] = useState(false)
  const [expandedServer, setExpandedServer] = useState<number | null>(null)
  const [newServer, setNewServer] = useState({
    name: '',
    host: '',
    port: 22,
    username: 'root',
    private_key: '',
    password: '',
    use_key_auth: true
  })

  const { data: servers = [], isLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
  })

  const createServer = useMutation({
    mutationFn: serversApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] })
      setShowAddForm(false)
      setNewServer({ name: '', host: '', port: 22, username: 'root', private_key: '', password: '', use_key_auth: true })
    }
  })

  const deleteServer = useMutation({
    mutationFn: serversApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['servers'] }),
  })

  const checkHealth = useMutation({
    mutationFn: serversApi.checkHealth,
  })

  const healthData = useQuery({
    queryKey: ['serverHealth'],
    queryFn: async () => {
      const results: Record<number, ServerHealth> = {}
      for (const server of servers) {
        try {
          results[server.id] = await serversApi.checkHealth(server.id)
        } catch (e) {
          results[server.id] = { server_id: server.id, status: 'error', metrics: null, instances: [], checked_at: new Date().toISOString() } as any
        }
      }
      return results
    },
    enabled: servers.length > 0,
    refetchInterval: 30000,
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success'
      case 'unhealthy': return 'warning'
      case 'offline': return 'destructive'
      default: return 'secondary'
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            SSH Servers ({servers.length})
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ['serverHealth'] })}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => setShowAddForm(!showAddForm)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Server
            </Button>
          </div>
        </CardHeader>
      </Card>

      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add SSH Server</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input placeholder="My VPS 1" value={newServer.name} onChange={e => setNewServer({...newServer, name: e.target.value})} />
              </div>
              <div>
                <label className="text-sm font-medium">Host</label>
                <Input placeholder="192.168.1.100" value={newServer.host} onChange={e => setNewServer({...newServer, host: e.target.value})} />
              </div>
              <div>
                <label className="text-sm font-medium">Port</label>
                <Input type="number" placeholder="22" value={newServer.port} onChange={e => setNewServer({...newServer, port: parseInt(e.target.value)})} />
              </div>
              <div>
                <label className="text-sm font-medium">Username</label>
                <Input placeholder="root" value={newServer.username} onChange={e => setNewServer({...newServer, username: e.target.value})} />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input type="radio" checked={newServer.use_key_auth} onChange={() => setNewServer({...newServer, use_key_auth: true})} />
                  SSH Key
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" checked={!newServer.use_key_auth} onChange={() => setNewServer({...newServer, use_key_auth: false})} />
                  Password
                </label>
              </div>
              
              {newServer.use_key_auth ? (
                <div>
                  <label className="text-sm font-medium">Private Key</label>
                  <textarea 
                    className="w-full h-32 p-2 border rounded-md bg-background font-mono text-sm"
                    placeholder="-----BEGIN RSA PRIVATE KEY-----..."
                    value={newServer.private_key}
                    onChange={e => setNewServer({...newServer, private_key: e.target.value})}
                  />
                </div>
              ) : (
                <div>
                  <label className="text-sm font-medium">Password</label>
                  <Input type="password" value={newServer.password} onChange={e => setNewServer({...newServer, password: e.target.value})} />
                </div>
              )}
            </div>
            
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowAddForm(false)}>Cancel</Button>
              <Button 
                onClick={() => createServer.mutate(newServer)}
                disabled={!newServer.name || !newServer.host || !newServer.username}
              >
                Add Server
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <p className="text-muted-foreground">Loading servers...</p>
      ) : servers.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Server className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No SSH servers configured</p>
            <Button className="mt-4" onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add First Server
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {servers.map((server) => {
            const health = healthData.data?.[server.id]
            const isExpanded = expandedServer === server.id
            
            return (
              <Card key={server.id} className={cn(
                "transition-all",
                server.health_status === 'healthy' && "border-green-500/30",
                server.health_status === 'unhealthy' && "border-yellow-500/30",
                server.health_status === 'offline' && "border-red-500/30"
              )}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-3 h-3 rounded-full",
                        server.health_status === 'healthy' && "bg-green-500 animate-pulse",
                        server.health_status === 'unhealthy' && "bg-yellow-500",
                        server.health_status === 'offline' && "bg-red-500",
                        server.health_status === 'unknown' && "bg-gray-500"
                      )} />
                      <div>
                        <CardTitle className="text-lg">{server.name}</CardTitle>
                        <p className="text-sm text-muted-foreground">{server.username}@{server.host}:{server.port}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusColor(server.health_status) as any}>
                        {server.health_status}
                      </Badge>
                      <Button size="sm" variant="outline" onClick={() => checkHealth.mutate(server.id)}>
                        <Activity className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setExpandedServer(isExpanded ? null : server.id)}>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => deleteServer.mutate(server.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                {isExpanded && health?.metrics && (
                  <CardContent className="pt-0 border-t">
                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <Cpu className="h-4 w-4" />
                          <span>CPU</span>
                          <span className="ml-auto font-mono">{health.metrics.cpu_percent}%</span>
                        </div>
                        <Progress value={health.metrics.cpu_percent} />
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <MemoryStick className="h-4 w-4" />
                          <span>Memory</span>
                          <span className="ml-auto font-mono">{health.metrics.memory?.percent}%</span>
                        </div>
                        <Progress value={health.metrics.memory?.percent} />
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <HardDrive className="h-4 w-4" />
                          <span>Disk</span>
                          <span className="ml-auto font-mono">{health.metrics.disk?.percent}%</span>
                        </div>
                        <Progress value={health.metrics.disk?.percent} />
                      </div>
                    </div>
                    
                    {health.instances && health.instances.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium mb-2">MT5 Instances ({health.instances.length})</h4>
                        <div className="grid grid-cols-2 gap-2">
                          {health.instances.map((instance) => (
                            <div key={instance.id} className="flex items-center justify-between p-2 border rounded">
                              <span className="text-sm truncate">{instance.name}</span>
                              <Badge variant={instance.status.includes('Up') ? 'success' : 'secondary'} className="text-xs">
                                {instance.status.includes('Up') ? 'Running' : 'Stopped'}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
