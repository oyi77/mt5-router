import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { instancesApi } from "@/api/instances"
import { tradingApi } from "@/api/trading"
import { useMetrics } from "@/hooks/useMetrics"
import { MetricsCard } from "@/components/dashboard/MetricsCard"
import { InstanceCard } from "@/components/dashboard/InstanceCard"
import { MetricsPanel } from "@/components/dashboard/MetricsPanel"
import { AccountCard } from "@/components/trading/AccountCard"
import { PositionsTable } from "@/components/trading/PositionsTable"
import { VNCViewer } from "@/components/vnc/VNCViewer"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Server, Plus, RefreshCw, Activity, Wallet, Monitor,
  LogOut
} from "lucide-react"
import { useAuth } from "@/context/AuthContext"

export function Dashboard() {
  const { user, logout } = useAuth()
  const queryClient = useQueryClient()
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("instances")
  const { systemMetrics, instanceMetrics, refetch: refetchMetrics } = useMetrics()

  // Queries
  const { data: instances = [], isLoading: instancesLoading, refetch: refetchInstances } = useQuery({
    queryKey: ['instances'],
    queryFn: instancesApi.list,
  })

  const { data: account } = useQuery({
    queryKey: ['account', selectedInstance],
    queryFn: () => tradingApi.getAccount(selectedInstance!),
    enabled: !!selectedInstance,
    refetchInterval: 5000,
  })

  const { data: positions = [] } = useQuery({
    queryKey: ['positions', selectedInstance],
    queryFn: () => tradingApi.getPositions(selectedInstance!),
    enabled: !!selectedInstance,
    refetchInterval: 3000,
  })

  // Mutations
  const createInstance = useMutation({
    mutationFn: instancesApi.create,
    onSuccess: () => refetchInstances(),
  })

  const startInstance = useMutation({
    mutationFn: instancesApi.start,
    onSuccess: () => refetchInstances(),
  })

  const stopInstance = useMutation({
    mutationFn: instancesApi.stop,
    onSuccess: () => refetchInstances(),
  })

  const restartInstance = useMutation({
    mutationFn: instancesApi.restart,
    onSuccess: () => refetchInstances(),
  })

  const deleteInstance = useMutation({
    mutationFn: instancesApi.delete,
    onSuccess: () => refetchInstances(),
  })

  const closePosition = useMutation({
    mutationFn: (ticket: number) => tradingApi.closePosition(selectedInstance!, ticket),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['positions', selectedInstance] }),
  })

  const runningInstance = instances.find(i => i.status === 'running')

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Activity className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold">MT5 Router</h1>
              <p className="text-sm text-muted-foreground">Trading Dashboard</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Welcome, {user?.username}
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricsCard
            title="Total Instances"
            value={instances.length}
            subtitle={`${instances.filter(i => i.status === 'running').length} running`}
            icon={Server}
          />
          <MetricsCard
            title="System CPU"
            value={`${systemMetrics?.cpu_percent.toFixed(1)}%`}
            icon={Activity}
            progress={systemMetrics?.cpu_percent}
          />
          <MetricsCard
            title="Memory"
            value={`${systemMetrics?.memory.percent.toFixed(1)}%`}
            icon={Server}
            progress={systemMetrics?.memory.percent}
          />
          <MetricsCard
            title="Open Positions"
            value={positions.length}
            subtitle={selectedInstance ? `$${positions.reduce((sum, p) => sum + p.profit, 0).toFixed(2)}` : "Select instance"}
            icon={Wallet}
          />
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="instances">
              <Server className="h-4 w-4 mr-2" />
              Instances
            </TabsTrigger>
            <TabsTrigger value="trading">
              <Wallet className="h-4 w-4 mr-2" />
              Trading
            </TabsTrigger>
            <TabsTrigger value="vnc">
              <Monitor className="h-4 w-4 mr-2" />
              VNC
            </TabsTrigger>
            <TabsTrigger value="monitoring">
              <Activity className="h-4 w-4 mr-2" />
              Monitoring
            </TabsTrigger>
          </TabsList>

          <TabsContent value="instances">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">MT5 Instances</h2>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => refetchInstances()}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
                <Button size="sm" onClick={() => createInstance.mutate()}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Instance
                </Button>
              </div>
            </div>
            
            {instancesLoading ? (
              <p className="text-muted-foreground">Loading instances...</p>
            ) : instances.length === 0 ? (
              <div className="text-center py-12 border rounded-lg">
                <Server className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No MT5 instances</p>
                <Button className="mt-4" onClick={() => createInstance.mutate()}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Instance
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {instances.map((instance) => (
                  <InstanceCard
                    key={instance.id}
                    instance={instance}
                    onStart={(id) => startInstance.mutate(id)}
                    onStop={(id) => stopInstance.mutate(id)}
                    onRestart={(id) => restartInstance.mutate(id)}
                    onDelete={(id) => deleteInstance.mutate(id)}
                    onViewVNC={(id) => {
                      setSelectedInstance(id)
                      setActiveTab("vnc")
                    }}
                    onViewLogs={(id) => console.log("View logs:", id)}
                    isLoading={
                      startInstance.isPending ||
                      stopInstance.isPending ||
                      restartInstance.isPending
                    }
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="trading">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Trading</h2>
                {instances.filter(i => i.status === 'running').length > 1 && (
                  <select
                    className="rounded-md border bg-background px-3 py-2"
                    value={selectedInstance || ""}
                    onChange={(e) => setSelectedInstance(e.target.value)}
                  >
                    {instances.filter(i => i.status === 'running').map((i) => (
                      <option key={i.id} value={i.id}>{i.name}</option>
                    ))}
                  </select>
                )}
              </div>
              
              <AccountCard account={account || null} />
              <PositionsTable
                positions={positions}
                onClosePosition={(ticket) => closePosition.mutate(ticket)}
                isLoading={closePosition.isPending}
              />
            </div>
          </TabsContent>

          <TabsContent value="vnc">
            {selectedInstance ? (
              <VNCViewer
                instanceId={selectedInstance}
                vncPort={instances.find(i => i.id === selectedInstance)?.vnc_port}
              />
            ) : (
              <div className="text-center py-12 border rounded-lg">
                <Monitor className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Select an instance to view VNC</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="monitoring">
            <MetricsPanel
              systemMetrics={systemMetrics}
              instanceMetrics={instanceMetrics}
            />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
