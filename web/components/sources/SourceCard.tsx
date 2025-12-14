'use client'

import { motion } from 'framer-motion'
import { Database, Edit2, Trash2, MoreVertical, FileText, Search, MessageSquare, Box } from 'lucide-react'
import { Source } from '@/types'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { formatDate } from '@/lib/utils'

interface SourceCardProps {
  source: Source
  documentCount?: number
  onEdit?: (source: Source) => void
  onDelete?: (source: Source) => void
  index?: number
}

export function SourceCard({
  source,
  documentCount,
  onEdit,
  onDelete,
  index = 0,
}: SourceCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      whileHover={{ y: -5 }}
      className="relative border-0 rounded-lg p-6 bg-white/80 backdrop-blur-sm shadow-lg hover:shadow-xl transition-all duration-300"
    >
      {/* Top right: Action menu */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              title="More actions"
            >
              <MoreVertical className="w-4 h-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-32">
            <DropdownMenuItem
              onClick={() => onEdit?.(source)}
              className="cursor-pointer text-sm"
            >
              <Edit2 className="w-4 h-4 mr-2" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDelete?.(source)}
              className="cursor-pointer text-sm text-red-600 focus:text-red-600"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Vertical layout: Icon + Content */}
      <div className="space-y-4">
        {/* Top: Icon + Source name */}
        <div className="flex items-center gap-3 mb-2">
          <div className="p-1.5 rounded-lg shrink-0 bg-emerald-50">
            <Database className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg text-gray-900 truncate">
              {source.name}
            </h3>
          </div>
        </div>

        {/* Description */}
        {source.description && (
          <p className="text-sm text-gray-600 line-clamp-2">
            {source.description}
          </p>
        )}

        {/* Information display */}
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Documents:</span>
            <span className="font-medium text-gray-700">{documentCount ?? '...'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Created:</span>
            <span className="font-medium text-gray-700">{formatDate(source.created_time)}</span>
          </div>
        </div>

        {/* Bottom action buttons */}
        <div className="flex gap-2 pt-2">
          {/* Documents button */}
          <button
            onClick={() => {
              window.location.href = `/documents?source_config_id=${source.id}`
            }}
            className="flex-1 h-9 px-3 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 shadow-sm transition-all flex items-center justify-center"
            title="Documents"
          >
            <FileText className="w-4 h-4" />
          </button>

          {/* Search button */}
          <button
            onClick={() => {
              window.location.href = `/search?source_config_id=${source.id}`
            }}
            className="w-9 h-9 p-0 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 shadow-sm transition-all flex items-center justify-center"
            title="Search"
          >
            <Search className="w-4 h-4" />
          </button>

          {/* Chat button */}
          <button
            onClick={() => {
              window.location.href = `/chat?source_config_id=${source.id}`
            }}
            className="w-9 h-9 p-0 rounded-lg bg-purple-50 text-purple-600 hover:bg-purple-100 shadow-sm transition-all flex items-center justify-center"
            title="Chat"
          >
            <MessageSquare className="w-4 h-4" />
          </button>

          {/* Entity types button */}
          <button
            onClick={() => {
              window.location.href = `/settings/entity?source_config_id=${source.id}`
            }}
            className="w-9 h-9 p-0 rounded-lg bg-yellow-50 text-yellow-600 hover:bg-yellow-100 shadow-sm transition-all flex items-center justify-center"
            title="Entity Types"
          >
            <Box className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  )
}
