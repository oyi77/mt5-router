import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Monitor, Maximize, Minimize, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"

interface VNCViewerProps {
  instanceId: string
  vncPort?: string | null
}

export function VNCViewer({ instanceId, vncPort }: VNCViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)

  const vncUrl = `/api/v1/vnc/${instanceId}/vnc.html`

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
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
          <p className="text-muted-foreground">VNC not available for this instance</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card ref={containerRef} className={cn("overflow-hidden", isFullscreen && "h-screen")}>
      <CardHeader className="flex flex-row items-center justify-between py-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Monitor className="h-4 w-4" />
          VNC - {instanceId}
        </CardTitle>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => window.location.reload()}>
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
            <div className="absolute inset-0 flex items-center justify-center bg-black/50">
              <div className="text-white">Loading VNC...</div>
            </div>
          )}
          <iframe
            src={vncUrl}
            className="w-full border-0"
            style={{ height: isFullscreen ? "calc(100vh - 60px)" : "600px" }}
            onLoad={() => setIsLoading(false)}
            title="VNC Viewer"
          />
        </div>
      </CardContent>
    </Card>
  )
}
