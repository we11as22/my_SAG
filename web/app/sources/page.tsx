'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Plus, Database } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Source } from '@/types'
import { SourceCard } from '@/components/sources/SourceCard'
import { SourceDialog, SourceFormData } from '@/components/sources/SourceDialog'
import { DeleteConfirmDialog } from '@/components/settings/DeleteConfirmDialog'
import { toast } from 'sonner'

export default function SourcesPage() {
  const queryClient = useQueryClient()

  // Dialog state
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)

  // Get source list
  const { data: sourcesData, isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => apiClient.getSources(),
  })

  const sources = sourcesData?.data || []

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (data: SourceFormData) => apiClient.createSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setIsCreateDialogOpen(false)
      toast.success('Source created successfully')
    },
    onError: (error: any) => {
      console.error('Create source error:', error)
      const errorMessage = error.response?.data?.error?.message || error.message || 'Failed to create source'
      toast.error(errorMessage)
    },
  })

  // Update Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SourceFormData }) =>
      apiClient.updateSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setIsEditDialogOpen(false)
      setSelectedSource(null)
      toast.success('Source updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to update')
    },
  })

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setIsDeleteDialogOpen(false)
      setSelectedSource(null)
      toast.success('Source deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to delete')
    },
  })

  // Handler functions
  const handleCreate = (data: SourceFormData) => {
    createMutation.mutate(data)
  }

  const handleEdit = (source: Source) => {
    setSelectedSource(source)
    setIsEditDialogOpen(true)
  }

  const handleUpdate = (data: SourceFormData) => {
    if (selectedSource) {
      updateMutation.mutate({ id: selectedSource.id, data })
    }
  }

  const handleDelete = (source: Source) => {
    setSelectedSource(source)
    setIsDeleteDialogOpen(true)
  }

  const handleConfirmDelete = () => {
    if (selectedSource) {
      deleteMutation.mutate(selectedSource.id)
    }
  }

  return (
    <div className="space-y-8 pb-8">
      {/* Page title */}
      <motion.div
        className="flex justify-between items-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 shadow-md">
            <Database className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800">Source Management</h1>
            <p className="text-gray-500 text-xs">Manage different data sources, isolate data from different sources</p>
          </div>
        </div>
        <button
          onClick={() => setIsCreateDialogOpen(true)}
          className="h-11 w-11 p-0 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 shadow-lg hover:shadow-xl transition-all flex items-center justify-center"
        >
          <Plus className="w-5 h-5" />
        </button>
      </motion.div>

      {/* Source list */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-gray-100 flex items-center justify-center animate-pulse">
            <Database className="w-5 h-5 text-gray-400 animate-spin" />
          </div>
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      ) : sources.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="text-center py-12"
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-gray-100 flex items-center justify-center">
            <Plus className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-sm font-medium text-gray-700 mb-1">No sources yet</p>
          <p className="text-xs text-gray-500">Click the "+" button in the top right to create a new source</p>
        </motion.div>
      ) : (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {sources.map((source: Source, index: number) => (
            <SourceCard
              key={source.id}
              source={source}
              documentCount={source.document_count}
              onEdit={handleEdit}
              onDelete={handleDelete}
              index={index}
            />
          ))}
        </motion.div>
      )}

      {/* Dialogs */}
      <SourceDialog
        open={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
      />

      <SourceDialog
        open={isEditDialogOpen}
        onClose={() => {
          setIsEditDialogOpen(false)
          setSelectedSource(null)
        }}
        onSubmit={handleUpdate}
        source={selectedSource}
        isLoading={updateMutation.isPending}
      />

      <DeleteConfirmDialog
        open={isDeleteDialogOpen}
        onClose={() => {
          setIsDeleteDialogOpen(false)
          setSelectedSource(null)
        }}
        onConfirm={handleConfirmDelete}
        entityType={selectedSource as any}
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
