'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, X } from 'lucide-react'

interface ClearTasksDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  isLoading?: boolean
}

export function ClearTasksDialog({
  open,
  onClose,
  onConfirm,
  isLoading = false,
}: ClearTasksDialogProps) {
  if (!open) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* 背景遮罩 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/20 backdrop-blur-md"
        />

        {/* 对话框内容 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', stiffness: 380, damping: 30 }}
          className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden"
        >
          {/* 头部 */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-800">Confirm Clear Tasks</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* 内容 */}
          <div className="px-6 py-4">
            <p className="text-sm text-gray-600">
              Are you sure you want to clear all <span className="font-semibold text-gray-800">completed</span> and <span className="font-semibold text-gray-800">failed</span> tasks?
            </p>
            <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-100">
              <p className="text-xs text-red-700">
                <strong>Warning:</strong> After deletion, the history of these tasks will be permanently cleared and cannot be recovered. This action cannot be undone.
              </p>
            </div>
          </div>

          {/* 按钮 */}
          <div className="flex gap-3 px-6 py-4 bg-gray-50">
            <motion.button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </motion.button>
            <motion.button
              type="button"
              onClick={onConfirm}
              disabled={isLoading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Clearing...' : 'Confirm Clear'}
            </motion.button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
