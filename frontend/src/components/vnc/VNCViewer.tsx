import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Monitor, Maximize, Minimize, RefreshCw, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface VNCViewerProps {
  instanceId: string
  vncPort?: string | null
}

export function VNCViewer({ instanceId, vncPort }: VNCViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [key, setKey] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  const vncUrl = `/api/v1/vnc/${instanceId}/proxy/vnc.html?autoconnect=true&resize=scale&path=/api/v1/vnc/${instanceId}/proxy/websockify`

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const handleRefresh = () => {
    setIsLoading(true)
    setError(null)
    setKey(prev => prev + 1)
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  if (!vncPort) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            VNC Viewer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">VNC not available for this instance.</p>
            <p className="text-sm text-muted-foreground mt-1">Make sure the instance is running and VNC port (6081) is exposed.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card ref={containerRef} className={cn("overflow-hidden", isFullscreen && "h-screen")}>
      <CardHeader className="flex flex-row items-center justify-between py-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Monitor className="h-4 w-4" />
          VNC - {instanceId.substring(0, 12)}
          <Badge variant="outline" className="ml-2">Port {vncPort}</Badge>
        </CardTitle>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={toggleFullscreen}>
            {isFullscreen ? (
              <Minimize className="h-4 w-4" />
            ) : (
              <Maximize className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative bg-black" style={{ minHeight: "500px" }}>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-3" />
                <p className="text-white text-sm">Connecting to VNC...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-10">
              <div className="text-center">
                <AlertCircle className="h-8 w-8 text-red-400 mx-auto mb-3" />
                <p className="text-red-400 text-sm">{error}</p>
                <Button size="sm" variant="outline" className="mt-3" onClick={handleRefresh}>
                  Retry
                </Button>
              </div>
            </div>
          )}
          <iframe
            key={key}
            src={vncUrl}
            className="w-full border-0"
            style={{ height: isFullscreen ? "calc(100vh - 60px)" : "600px" }}
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setIsLoading(false)
              setError("Failed to load VNC viewer")
            }}
            title="VNC Viewer"
            allow="clipboard-read; clipboard-write"
          />
        </div>
      </CardContent>
    </Card>
  )
}
