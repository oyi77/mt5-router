import * as React from "react"
import { cn } from "@/lib/utils"

interface DialogProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children: React.ReactNode
}

const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  return <>{children}</>
}

interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
}

const DialogContent = React.forwardRef<HTMLDivElement, DialogContentProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
          className
        )}
        {...props}
      >
        <div className="bg-background rounded-lg border p-6 shadow-lg w-full max-w-lg">
          {children}
        </div>
      </div>
    )
  }
)
DialogContent.displayName = "DialogContent"

interface DialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
}

const DialogHeader: React.FC<DialogHeaderProps> = ({ className, children, ...props }) => {
  return (
    <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)} {...props}>
      {children}
    </div>
  )
}

interface DialogTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children?: React.ReactNode
}

const DialogTitle = React.forwardRef<HTMLHeadingElement, DialogTitleProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <h2
        ref={ref}
        className={cn("text-lg font-semibold leading-none tracking-tight", className)}
        {...props}
      >
        {children}
      </h2>
    )
  }
)
DialogTitle.displayName = "DialogTitle"

interface DialogFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
}

const DialogFooter: React.FC<DialogFooterProps> = ({ className, children, ...props }) => {
  return (
    <div
      className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-4", className)}
      {...props}
    >
      {children}
    </div>
  )
}

export { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter }