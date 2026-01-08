import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

// 简化版 Select 组件（不依赖 @radix-ui/react-select）
const SelectContext = React.createContext({ value: '', onValueChange: () => {} })

const Select = ({ value, onValueChange, children, ...props }) => {
    const [open, setOpen] = React.useState(false)
    
    return (
        <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
            <div className="relative" {...props}>
                {children}
            </div>
        </SelectContext.Provider>
    )
}

const SelectTrigger = React.forwardRef(({ className, children, ...props }, ref) => {
    const { open, setOpen } = React.useContext(SelectContext)
    
    return (
        <button
            ref={ref}
            type="button"
            onClick={() => setOpen(!open)}
            className={cn(
                "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                className
            )}
            {...props}
        >
            {children}
            <ChevronDown className="h-4 w-4 opacity-50" />
        </button>
    )
})
SelectTrigger.displayName = "SelectTrigger"

const SelectValue = ({ placeholder, ...props }) => {
    const { value } = React.useContext(SelectContext)
    return <span {...props}>{value || placeholder}</span>
}

const SelectContent = React.forwardRef(({ className, children, ...props }, ref) => {
    const { open, setOpen } = React.useContext(SelectContext)
    const contentRef = React.useRef(null)
    
    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (contentRef.current && !contentRef.current.contains(event.target)) {
                setOpen(false)
            }
        }
        
        if (open) {
            document.addEventListener('mousedown', handleClickOutside)
            return () => document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [open, setOpen])
    
    if (!open) return null
    
    return (
        <div
            ref={contentRef}
            className={cn(
                "absolute z-50 mt-1 max-h-96 min-w-[8rem] overflow-auto rounded-md border bg-white shadow-md",
                className
            )}
            {...props}
        >
            {children}
        </div>
    )
})
SelectContent.displayName = "SelectContent"

const SelectItem = React.forwardRef(({ className, children, value: itemValue, ...props }, ref) => {
    const { value, onValueChange, setOpen } = React.useContext(SelectContext)
    const isSelected = value === itemValue
    
    return (
        <div
            ref={ref}
            onClick={() => {
                onValueChange(itemValue)
                setOpen(false)
            }}
            className={cn(
                "relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground",
                isSelected && "bg-accent text-accent-foreground",
                className
            )}
            {...props}
        >
            {children}
        </div>
    )
})
SelectItem.displayName = "SelectItem"

export {
    Select,
    SelectValue,
    SelectTrigger,
    SelectContent,
    SelectItem,
}

