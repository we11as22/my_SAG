'use client'

import { Filter, Layers, Box, Database } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from '@/components/ui/select'

export type FilterType = string  // Changed to string to support dynamic source IDs: 'all' | 'default' | 'global' | source_config_id

interface Source {
  id: string
  name: string
}

interface AttributeFilterProps {
  value: FilterType
  onChange: (value: FilterType) => void
  sources: Source[]  // Dynamic source list
  counts?: {
    all: number
    default: number
    global: number
    [key: string]: number  // Dynamic counts per source
  }
}

export function AttributeFilter({ value, onChange, sources, counts }: AttributeFilterProps) {
  // 获取当前选中项的显示文本
  const getDisplayText = () => {
    const count = counts?.[value] || 0

    if (value === 'all') return `All Attributes (${count})`
    if (value === 'default') return `System Attributes (${count})`
    if (value === 'global') return `Custom Attributes (${count})`

    const source = sources.find(s => s.id === value)
    return source ? `${source.name} (${count})` : 'Select filter'
  }

  // 获取图标颜色
  const getIconColor = (type: string) => {
    if (type === 'all') return 'text-gray-400'
    if (type === 'default') return 'text-gray-700' // 系统默认：深灰
    if (type === 'global') return 'text-gray-500' // 通用：中灰
    return 'text-emerald-500' // 信息源：蓝绿色
  }

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[240px] bg-white border-gray-200 hover:border-gray-300 focus:ring-blue-500 transition-all">
        <SelectValue>
            <div className="flex items-center gap-2">
              {value === 'all' && <Layers className={`w-4 h-4 ${getIconColor('all')}`} />}
              {value === 'default' && <Box className={`w-4 h-4 ${getIconColor('default')}`} />}
              {value === 'global' && <Database className={`w-4 h-4 ${getIconColor('global')}`} />}
              {!['all', 'default', 'global'].includes(value) && <Database className={`w-4 h-4 ${getIconColor(value)}`} />}
              <span className="text-sm">{getDisplayText()}</span>
            </div>
          </SelectValue>
        </SelectTrigger>
        
        <SelectContent className="bg-white border-gray-200 shadow-lg">
          <SelectGroup>
            <SelectLabel className="text-xs text-gray-500 font-semibold">Basic Filters</SelectLabel>
            {/* All attributes - always shown */}
            <SelectItem value="all" className="cursor-pointer">
              <div className="flex items-center gap-2">
                <Layers className={`w-4 h-4 ${getIconColor('all')}`} />
                <span>All Attributes</span>
                {counts?.all !== undefined && (
                  <span className="ml-auto text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {counts.all}
                  </span>
                )}
              </div>
            </SelectItem>
            {/* System attributes - only shown when count > 0 */}
            {(counts?.default ?? 0) > 0 && (
              <SelectItem value="default" className="cursor-pointer">
                <div className="flex items-center gap-2">
                  <Box className={`w-4 h-4 ${getIconColor('default')}`} />
                  <span>System Attributes</span>
                  <span className="ml-auto text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {counts?.default ?? 0}
                  </span>
                </div>
              </SelectItem>
            )}
            {/* Custom attributes - only shown when count > 0 */}
            {(counts?.global ?? 0) > 0 && (
              <SelectItem value="global" className="cursor-pointer">
                <div className="flex items-center gap-2">
                  <Database className={`w-4 h-4 ${getIconColor('global')}`} />
                  <span>Custom Attributes</span>
                  <span className="ml-auto text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {counts?.global ?? 0}
                  </span>
                </div>
              </SelectItem>
            )}
          </SelectGroup>

          {/* 信息源专属 - 只显示有属性的信息源 */}
          {sources.filter(source => (counts?.[source.id] ?? 0) > 0).length > 0 && (
            <>
              <SelectSeparator className="my-1" />
              <SelectGroup>
                <SelectLabel className="text-xs text-gray-500 font-semibold">Source Specific</SelectLabel>
                {sources.filter(source => (counts?.[source.id] ?? 0) > 0).map((source) => {
                  const count = counts?.[source.id] || 0
                  return (
                    <SelectItem key={source.id} value={source.id} className="cursor-pointer">
                      <div className="flex items-center gap-2">
                        <Database className={`w-4 h-4 ${getIconColor('source')}`} />
                        <span>{source.name}</span>
                        <span className="ml-auto text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                          {count}
                        </span>
                      </div>
                    </SelectItem>
                  )
                })}
              </SelectGroup>
            </>
          )}
        </SelectContent>
      </Select>
  )
}
